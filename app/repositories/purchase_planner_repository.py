from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.repositories.database_adapter import create_connection


class PurchasePlannerRepository:
    @staticmethod
    def _cursor(connection: Any) -> Any:
        try:
            return connection.cursor(dictionary=True)
        except TypeError:
            return connection.cursor()

    @staticmethod
    def _row_to_dict(cursor: Any, row: Any) -> dict[str, Any]:
        if row is None:
            return {}

        if isinstance(row, dict):
            return row

        description = getattr(cursor, "description", None)

        if not description:
            return {}

        columns = [column[0] for column in description]
        return dict(zip(columns, row))

    def obtener_configuracion(self) -> dict[str, Any]:
        connection = create_connection()
        cursor = self._cursor(connection)

        try:
            cursor.execute(
                """
                SELECT
                    id,
                    dias_cobertura_objetivo,
                    multiplicador_stock_minimo,
                    monto_minimo_alerta,
                    planeacion_automatica
                FROM configuracion_compras
                ORDER BY id ASC
                LIMIT 1
                """
            )

            row = cursor.fetchone()
            return self._row_to_dict(cursor, row)

        except Exception:
            return {
                "dias_cobertura_objetivo": 30,
                "multiplicador_stock_minimo": 2,
                "monto_minimo_alerta": 0,
                "planeacion_automatica": 1,
            }

        finally:
            cursor.close()
            connection.close()

    def obtener_medicamentos_para_compra(
        self,
        multiplicador_stock_minimo: float = 2,
    ) -> list[dict[str, Any]]:
        connection = create_connection()
        cursor = self._cursor(connection)

        try:
            cursor.execute(
                """
                SELECT
                    m.id,
                    m.nombre,
                    m.lote,
                    m.stock,
                    m.stock_minimo,
                    m.precio,
                    m.caducidad,
                    m.proveedorId AS proveedor_id,
                    m.categoriaId AS categoria_id,

                    GREATEST(
                        CEIL(
                            (m.stock_minimo * %s) - m.stock
                        ),
                        1
                    ) AS cantidad_recomendada,

                    ROUND(
                        GREATEST(
                            CEIL(
                                (m.stock_minimo * %s) - m.stock
                            ),
                            1
                        ) * m.precio,
                        2
                    ) AS costo_estimado,

                    CASE
                        WHEN m.stock = 0 THEN 'AGOTADO'
                        WHEN m.stock <= GREATEST(
                            1,
                            FLOOR(m.stock_minimo * 0.5)
                        ) THEN 'CRITICO'
                        ELSE 'BAJO_STOCK'
                    END AS nivel_riesgo

                FROM medicamentos AS m

                WHERE m.stock <= m.stock_minimo
                  AND m.caducidad >= CURDATE()

                ORDER BY
                    CASE
                        WHEN m.stock = 0 THEN 1
                        WHEN m.stock <= GREATEST(
                            1,
                            FLOOR(m.stock_minimo * 0.5)
                        ) THEN 2
                        ELSE 3
                    END,
                    m.stock ASC,
                    m.nombre ASC
                """,
                (
                    multiplicador_stock_minimo,
                    multiplicador_stock_minimo,
                ),
            )

            rows = cursor.fetchall()

            return [
                self._row_to_dict(cursor, row)
                for row in rows
            ]

        finally:
            cursor.close()
            connection.close()

    def crear_ordenes_desde_plan(
        self,
        medicamentos: list[dict[str, Any]],
        usuario_id: int | None = None,
    ) -> list[dict[str, Any]]:
        if not medicamentos:
            return []

        grouped: dict[int | None, list[dict[str, Any]]] = defaultdict(list)

        for medicine in medicamentos:
            grouped[medicine.get("proveedor_id")].append(medicine)

        connection = create_connection()
        created_orders: list[dict[str, Any]] = []

        try:
            try:
                connection.start_transaction()
            except AttributeError:
                try:
                    connection.autocommit = False
                except Exception:
                    pass

            for provider_id, items in grouped.items():
                total = round(
                    sum(
                        float(item.get("costo_estimado") or 0)
                        for item in items
                    ),
                    2,
                )

                order_cursor = connection.cursor()

                try:
                    order_cursor.execute(
                        """
                        INSERT INTO ordenes_compra (
                            proveedor_id,
                            estado,
                            total_estimado,
                            motivo,
                            usuario_id
                        )
                        VALUES (%s, 'BORRADOR', %s, %s, %s)
                        """,
                        (
                            provider_id,
                            total,
                            "Plan automático de reposición",
                            usuario_id,
                        ),
                    )

                    order_id = int(order_cursor.lastrowid)

                finally:
                    order_cursor.close()

                detail_cursor = connection.cursor()

                try:
                    for item in items:
                        quantity = int(
                            item.get("cantidad_recomendada") or 1
                        )
                        price = float(item.get("precio") or 0)
                        subtotal = round(quantity * price, 2)

                        detail_cursor.execute(
                            """
                            INSERT INTO orden_compra_detalles (
                                orden_id,
                                medicamento_id,
                                cantidad,
                                precio_unitario,
                                subtotal
                            )
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (
                                order_id,
                                int(item["id"]),
                                quantity,
                                price,
                                subtotal,
                            ),
                        )

                finally:
                    detail_cursor.close()

                created_orders.append(
                    {
                        "orden_id": order_id,
                        "proveedor_id": provider_id,
                        "estado": "BORRADOR",
                        "total_estimado": total,
                        "total_productos": len(items),
                    }
                )

            connection.commit()
            return created_orders

        except Exception:
            try:
                connection.rollback()
            except Exception:
                pass

            raise

        finally:
            connection.close()


purchase_planner_repository = PurchasePlannerRepository()

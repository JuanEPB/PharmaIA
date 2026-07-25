from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.repositories.database_adapter import create_connection


class ConversationalActionRepository:
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

    def buscar_medicamento_por_nombre(
        self,
        nombre: str,
    ) -> list[dict[str, Any]]:
        connection = create_connection()
        cursor = self._cursor(connection)

        try:
            normalized = str(nombre or "").strip()

            cursor.execute(
                """
                SELECT
                    id,
                    nombre,
                    lote,
                    caducidad,
                    stock,
                    stock_minimo,
                    precio,
                    proveedorId AS proveedor_id,
                    categoriaId AS categoria_id
                FROM medicamentos
                WHERE LOWER(nombre) = LOWER(%s)
                   OR LOWER(nombre) LIKE LOWER(%s)
                ORDER BY
                    CASE
                        WHEN LOWER(nombre) = LOWER(%s) THEN 0
                        ELSE 1
                    END,
                    nombre ASC
                LIMIT 10
                """,
                (
                    normalized,
                    f"%{normalized}%",
                    normalized,
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

    def obtener_medicamentos_criticos(
        self,
    ) -> list[dict[str, Any]]:
        connection = create_connection()
        cursor = self._cursor(connection)

        try:
            cursor.execute(
                """
                SELECT
                    id,
                    nombre,
                    lote,
                    stock,
                    stock_minimo,
                    precio,
                    proveedorId AS proveedor_id,
                    GREATEST(
                        (stock_minimo * 2) - stock,
                        1
                    ) AS cantidad_recomendada
                FROM medicamentos
                WHERE stock <= stock_minimo
                  AND caducidad >= CURDATE()
                ORDER BY
                    stock ASC,
                    nombre ASC
                """
            )

            rows = cursor.fetchall()

            return [
                self._row_to_dict(cursor, row)
                for row in rows
            ]

        finally:
            cursor.close()
            connection.close()

    def crear_ordenes_para_criticos(
        self,
        usuario_id: int | None = None,
    ) -> list[dict[str, Any]]:
        medicines = self.obtener_medicamentos_criticos()

        if not medicines:
            return []

        grouped: dict[int | None, list[dict[str, Any]]] = defaultdict(list)

        for medicine in medicines:
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
                total = 0.0

                for item in items:
                    quantity = int(item.get("cantidad_recomendada") or 1)
                    price = float(item.get("precio") or 0)
                    total += quantity * price

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
                            round(total, 2),
                            "Reposición automática de medicamentos críticos",
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
                        "total_estimado": round(total, 2),
                        "total_productos": len(items),
                        "productos": [
                            {
                                "medicamento_id": int(item["id"]),
                                "nombre": item["nombre"],
                                "stock_actual": int(
                                    item.get("stock") or 0
                                ),
                                "stock_minimo": int(
                                    item.get("stock_minimo") or 0
                                ),
                                "cantidad_solicitada": int(
                                    item.get(
                                        "cantidad_recomendada"
                                    ) or 1
                                ),
                            }
                            for item in items
                        ],
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


conversational_action_repository = ConversationalActionRepository()

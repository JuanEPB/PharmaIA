from __future__ import annotations

from typing import Any

from app.repositories.database_adapter import create_connection


class DepletionPredictionRepository:
    @staticmethod
    def _is_missing_table_error(error: Exception) -> bool:
        errno = getattr(error, "errno", None)
        message = str(error).lower()

        return errno == 1146 or (
            "movimientos_inventario" in message
            and (
                "doesn't exist" in message
                or "does not exist" in message
                or "no such table" in message
            )
        )

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
                    dias_historial,
                    dias_cobertura_objetivo,
                    dias_stock_seguridad,
                    riesgo_critico_dias,
                    riesgo_alto_dias,
                    riesgo_medio_dias,
                    incluir_caducidad_como_consumo,
                    activo
                FROM configuracion_prediccion_agotamiento
                ORDER BY id ASC
                LIMIT 1
                """
            )

            row = cursor.fetchone()

            return self._row_to_dict(cursor, row) or {
                "dias_historial": 30,
                "dias_cobertura_objetivo": 30,
                "dias_stock_seguridad": 7,
                "riesgo_critico_dias": 7,
                "riesgo_alto_dias": 14,
                "riesgo_medio_dias": 30,
                "incluir_caducidad_como_consumo": 0,
                "activo": 1,
            }

        except Exception:
            return {
                "dias_historial": 30,
                "dias_cobertura_objetivo": 30,
                "dias_stock_seguridad": 7,
                "riesgo_critico_dias": 7,
                "riesgo_alto_dias": 14,
                "riesgo_medio_dias": 30,
                "incluir_caducidad_como_consumo": 0,
                "activo": 1,
            }

        finally:
            cursor.close()
            connection.close()

    def buscar_medicamentos(
        self,
        nombre: str,
    ) -> list[dict[str, Any]]:
        connection = create_connection()
        cursor = self._cursor(connection)

        try:
            clean_name = str(nombre or "").strip()

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
                    farmacia_id,
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
                    caducidad ASC,
                    id ASC
                LIMIT 20
                """,
                (
                    clean_name,
                    f"%{clean_name}%",
                    clean_name,
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

    def obtener_medicamento(
        self,
        medicamento_id: int,
    ) -> dict[str, Any]:
        connection = create_connection()
        cursor = self._cursor(connection)

        try:
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
                    farmacia_id,
                    proveedorId AS proveedor_id,
                    categoriaId AS categoria_id
                FROM medicamentos
                WHERE id = %s
                """,
                (medicamento_id,),
            )

            row = cursor.fetchone()
            return self._row_to_dict(cursor, row)

        finally:
            cursor.close()
            connection.close()

    def obtener_consumo_historico(
        self,
        medicamento_id: int,
        dias_historial: int,
        incluir_caducidad: bool = False,
    ) -> dict[str, Any]:
        connection = create_connection()
        cursor = self._cursor(connection)

        movement_types = ["SALIDA"]

        if incluir_caducidad:
            movement_types.append("CADUCIDAD")

        placeholders = ", ".join(["%s"] * len(movement_types))

        query = f"""
            SELECT
                COALESCE(SUM(cantidad), 0) AS unidades_consumidas,
                COUNT(*) AS total_movimientos,
                COUNT(DISTINCT DATE(creado_en)) AS dias_con_movimiento,
                MIN(creado_en) AS primer_movimiento,
                MAX(creado_en) AS ultimo_movimiento
            FROM movimientos_inventario
            WHERE medicamento_id = %s
              AND tipo IN ({placeholders})
              AND creado_en >= DATE_SUB(
                    NOW(),
                    INTERVAL %s DAY
              )
        """

        parameters = [
            medicamento_id,
            *movement_types,
            dias_historial,
        ]

        try:
            cursor.execute(
                query,
                tuple(parameters),
            )

            row = cursor.fetchone()
            return self._row_to_dict(cursor, row)
        except Exception as exc:
            if self._is_missing_table_error(exc):
                return {
                    "unidades_consumidas": 0,
                    "total_movimientos": 0,
                    "dias_con_movimiento": 0,
                    "primer_movimiento": None,
                    "ultimo_movimiento": None,
                }
            raise

        finally:
            cursor.close()
            connection.close()

    def obtener_consumo_diario(
        self,
        medicamento_id: int,
        dias_historial: int,
        incluir_caducidad: bool = False,
    ) -> list[dict[str, Any]]:
        connection = create_connection()
        cursor = self._cursor(connection)

        movement_types = ["SALIDA"]

        if incluir_caducidad:
            movement_types.append("CADUCIDAD")

        placeholders = ", ".join(["%s"] * len(movement_types))

        query = f"""
            SELECT
                DATE(creado_en) AS fecha,
                SUM(cantidad) AS unidades
            FROM movimientos_inventario
            WHERE medicamento_id = %s
              AND tipo IN ({placeholders})
              AND creado_en >= DATE_SUB(
                    NOW(),
                    INTERVAL %s DAY
              )
            GROUP BY DATE(creado_en)
            ORDER BY fecha ASC
        """

        parameters = [
            medicamento_id,
            *movement_types,
            dias_historial,
        ]

        try:
            cursor.execute(
                query,
                tuple(parameters),
            )

            rows = cursor.fetchall()

            return [
                self._row_to_dict(cursor, row)
                for row in rows
            ]
        except Exception as exc:
            if self._is_missing_table_error(exc):
                return []
            raise

        finally:
            cursor.close()
            connection.close()

    def obtener_candidatos_prediccion(self) -> list[dict[str, Any]]:
        connection = create_connection()
        cursor = self._cursor(connection)

        try:
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
                    farmacia_id,
                    proveedorId AS proveedor_id,
                    categoriaId AS categoria_id
                FROM medicamentos
                WHERE caducidad >= CURDATE()
                ORDER BY nombre ASC, caducidad ASC
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

    def guardar_prediccion(
        self,
        prediction: dict[str, Any],
    ) -> None:
        self.guardar_predicciones([prediction])

    def guardar_predicciones(
        self,
        predictions: list[dict[str, Any]],
    ) -> None:
        if not predictions:
            return

        values = [
            self._prediction_values(prediction)
            for prediction in predictions
        ]

        connection = create_connection()
        cursor = connection.cursor()

        try:
            cursor.executemany(
                """
                INSERT INTO ia_predicciones_inventario (
                    medicamento_id,
                    farmacia_id,
                    tipo_prediccion,
                    riesgo,
                    valor_estimado,
                    dias_estimados,
                    confianza,
                    detalles
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                values,
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def _prediction_values(
        self,
        prediction: dict[str, Any],
    ) -> tuple[Any, ...]:
        medicine = prediction.get("medicamento") or {}
        medicine_id = int(medicine["id"])

        return (
            medicine_id,
            medicine.get("farmacia_id"),
            "AGOTAMIENTO",
            prediction.get("nivel_riesgo"),
            prediction.get("consumo_promedio_diario"),
            prediction.get("cobertura_estimada_dias"),
            self._confidence_to_decimal(
                prediction.get("confianza_prediccion")
            ),
            self._to_json(prediction),
        )

    @staticmethod
    def _confidence_to_decimal(confidence: Any) -> float:
        mapping = {
            "BAJA": 0.35,
            "MEDIA": 0.65,
            "ALTA": 0.9,
        }

        return mapping.get(
            str(confidence or "").upper(),
            0.0,
        )

    @staticmethod
    def _to_json(value: Any) -> str:
        import json
        from datetime import date, datetime
        from decimal import Decimal

        def default(item: Any) -> str:
            if isinstance(item, (date, datetime)):
                return item.isoformat()

            if isinstance(item, Decimal):
                return str(item)

            return str(item)

        return json.dumps(
            value,
            ensure_ascii=False,
            default=default,
        )


depletion_prediction_repository = DepletionPredictionRepository()

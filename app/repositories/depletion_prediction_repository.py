from __future__ import annotations

from typing import Any

from app.repositories.database_adapter import create_connection


class DepletionPredictionRepository:
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


depletion_prediction_repository = DepletionPredictionRepository()

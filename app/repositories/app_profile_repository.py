from __future__ import annotations

from typing import Any

from app.repositories.database_adapter import (
    database_connection,
    dictionary_cursor,
)


class AppProfileRepository:
    @staticmethod
    def _normalize_row(
        cursor: Any,
        row: Any,
    ) -> dict[str, Any]:
        if row is None:
            return {}

        if isinstance(row, dict):
            return row

        description = getattr(cursor, "description", None)

        if not description:
            return {}

        columns = [column[0] for column in description]
        return dict(zip(columns, row))

    def _fetch_one(
        self,
        query: str,
        parameters: tuple[Any, ...] = (),
    ) -> dict[str, Any]:
        with database_connection() as connection:
            with dictionary_cursor(connection) as cursor:
                cursor.execute(query, parameters)
                return self._normalize_row(cursor, cursor.fetchone())

    def obtener_empresa_activa(self) -> dict[str, Any]:
        query = """
            SELECT
                e.id,
                e.nombre,
                e.rfc,
                e.direccion,
                e.email_contacto,
                e.telefono_contacto,
                e.estado,
                p.nombre AS plan,
                p.IA AS ia_habilitada,
                p.movil AS movil_habilitado
            FROM empresa AS e
            LEFT JOIN plan AS p
                ON p.id = e.plan_id
            ORDER BY e.id ASC
            LIMIT 1
        """

        return self._fetch_one(query)

    def obtener_farmacia_activa(self) -> dict[str, Any]:
        query = """
            SELECT
                f.id,
                f.nombre,
                f.rfc,
                f.direccion,
                f.telefono,
                f.email,
                f.lema,
                f.logo_url,
                f.activo,
                f.empresa_id
            FROM farmacia AS f
            WHERE f.activo = 1
            ORDER BY f.id ASC
            LIMIT 1
        """

        return self._fetch_one(query)

    def obtener_metricas_operativas(self) -> dict[str, Any]:
        query = """
            SELECT
                COUNT(*) AS total_medicamentos,
                COALESCE(SUM(stock), 0) AS unidades_inventario,
                COALESCE(SUM(stock * precio), 0) AS valor_inventario,
                COALESCE(SUM(CASE WHEN stock = 0 THEN 1 ELSE 0 END), 0)
                    AS medicamentos_agotados,
                COALESCE(
                    SUM(
                        CASE
                            WHEN stock > 0
                                AND stock <= stock_minimo
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS medicamentos_bajo_stock,
                COALESCE(
                    SUM(
                        CASE
                            WHEN caducidad < CURDATE()
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS medicamentos_caducados,
                COALESCE(
                    SUM(
                        CASE
                            WHEN caducidad >= CURDATE()
                                AND caducidad <= DATE_ADD(
                                    CURDATE(),
                                    INTERVAL 30 DAY
                                )
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS medicamentos_por_caducar_30_dias
            FROM medicamentos
        """

        return self._fetch_one(query)

    def obtener_metricas_ia(self) -> dict[str, Any]:
        query = """
            SELECT
                (
                    SELECT COUNT(*)
                    FROM ia_memoria_conversacion
                ) AS sesiones_con_memoria,
                (
                    SELECT COUNT(*)
                    FROM ia_acciones_conversacionales
                    WHERE estado = 'PENDIENTE'
                ) AS acciones_pendientes,
                (
                    SELECT COUNT(*)
                    FROM ia_acciones_conversacionales
                    WHERE estado = 'EJECUTADA'
                ) AS acciones_ejecutadas,
                (
                    SELECT COUNT(*)
                    FROM ia_feedback_aprendizaje
                    WHERE estado = 'PENDIENTE_REVISION'
                ) AS feedback_pendiente,
                (
                    SELECT COUNT(*)
                    FROM ia_predicciones_inventario
                ) AS predicciones_guardadas
        """

        try:
            return self._fetch_one(query)
        except Exception:
            return {
                "sesiones_con_memoria": 0,
                "acciones_pendientes": 0,
                "acciones_ejecutadas": 0,
                "feedback_pendiente": 0,
                "predicciones_guardadas": 0,
            }


app_profile_repository = AppProfileRepository()

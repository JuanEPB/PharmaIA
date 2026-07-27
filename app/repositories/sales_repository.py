from __future__ import annotations

from typing import Any

from app.repositories.database_adapter import (
    database_connection,
    dictionary_cursor,
)


class SalesRepository:
    @staticmethod
    def _normalize_row(cursor: Any, row: Any) -> dict[str, Any]:
        if row is None:
            return {}

        if isinstance(row, dict):
            return row

        description = getattr(cursor, "description", None)

        if not description:
            return {}

        columns = [column[0] for column in description]
        return dict(zip(columns, row))

    def obtener_venta(self, venta_id: int) -> dict[str, Any]:
        with database_connection() as connection:
            with dictionary_cursor(connection) as cursor:
                cursor.execute(
                    """
                    SELECT
                        v.id,
                        v.total,
                        v.usuarioId AS usuario_id,
                        v.fecha,
                        v.farmacia_id,
                        u.nombre AS usuario_nombre,
                        u.apellido AS usuario_apellido,
                        f.nombre AS farmacia_nombre
                    FROM venta AS v
                    LEFT JOIN usuarios AS u
                        ON u.id = v.usuarioId
                    LEFT JOIN farmacia AS f
                        ON f.id = v.farmacia_id
                    WHERE v.id = %s
                    LIMIT 1
                    """,
                    (venta_id,),
                )
                return self._normalize_row(cursor, cursor.fetchone())

    def obtener_detalle_venta(self, venta_id: int) -> list[dict[str, Any]]:
        with database_connection() as connection:
            with dictionary_cursor(connection) as cursor:
                cursor.execute(
                    """
                    SELECT
                        vd.id,
                        vd.cantidad,
                        vd.precioUnitario AS precio_unitario,
                        vd.ventaId AS venta_id,
                        vd.medicamentoId AS medicamento_id,
                        m.nombre AS medicamento_nombre,
                        m.lote AS medicamento_lote
                    FROM venta_detalle AS vd
                    LEFT JOIN medicamentos AS m
                        ON m.id = vd.medicamentoId
                    WHERE vd.ventaId = %s
                    ORDER BY vd.id ASC
                    """,
                    (venta_id,),
                )
                rows = cursor.fetchall()
                return [
                    self._normalize_row(cursor, row)
                    for row in rows
                ]


sales_repository = SalesRepository()

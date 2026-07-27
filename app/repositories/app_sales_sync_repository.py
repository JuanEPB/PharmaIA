from __future__ import annotations

import json
from typing import Any

from app.repositories.database_adapter import (
    database_connection,
    dictionary_cursor,
)


class AppSalesSyncRepository:
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

    def upsert_sale(self, sale: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps(
            sale.get("payload") or sale,
            ensure_ascii=False,
            default=str,
        )

        with database_connection() as connection:
            with dictionary_cursor(connection) as cursor:
                cursor.execute(
                    """
                    INSERT INTO app_ventas_sincronizadas (
                        venta_local_id,
                        total,
                        fecha,
                        cliente_nombre,
                        farmacia_nombre,
                        origen,
                        estado,
                        payload
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        total = VALUES(total),
                        fecha = VALUES(fecha),
                        cliente_nombre = VALUES(cliente_nombre),
                        farmacia_nombre = VALUES(farmacia_nombre),
                        origen = VALUES(origen),
                        estado = VALUES(estado),
                        payload = VALUES(payload)
                    """,
                    (
                        sale["venta_local_id"],
                        sale["total"],
                        sale.get("fecha"),
                        sale.get("cliente_nombre"),
                        sale.get("farmacia_nombre"),
                        sale.get("origen", "app_movil"),
                        sale.get("estado", "sincronizada"),
                        payload,
                    ),
                )
                connection.commit()

                cursor.execute(
                    """
                    SELECT
                        id,
                        venta_local_id,
                        total,
                        fecha,
                        cliente_nombre,
                        farmacia_nombre,
                        origen,
                        estado,
                        created_at,
                        updated_at
                    FROM app_ventas_sincronizadas
                    WHERE venta_local_id = %s
                    LIMIT 1
                    """,
                    (sale["venta_local_id"],),
                )

                return self._normalize_row(cursor, cursor.fetchone())

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 100))

        with database_connection() as connection:
            with dictionary_cursor(connection) as cursor:
                cursor.execute(
                    f"""
                    SELECT
                        id,
                        venta_local_id,
                        total,
                        fecha,
                        cliente_nombre,
                        farmacia_nombre,
                        origen,
                        estado,
                        created_at,
                        updated_at
                    FROM app_ventas_sincronizadas
                    ORDER BY created_at DESC
                    LIMIT {safe_limit}
                    """
                )
                rows = cursor.fetchall()
                return [
                    self._normalize_row(cursor, row)
                    for row in rows
                ]


app_sales_sync_repository = AppSalesSyncRepository()

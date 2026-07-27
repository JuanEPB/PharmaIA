from __future__ import annotations

from datetime import datetime
from typing import Any

from app.repositories.app_sales_sync_repository import (
    app_sales_sync_repository,
)


class AppSalesSyncService:
    @staticmethod
    def _customer_name(sale: dict[str, Any]) -> str:
        user = sale.get("usuario") or {}
        name = (
            f"{user.get('nombre') or 'Cliente'} "
            f"{user.get('apellido') or ''}"
        ).strip()
        return name or "Cliente"

    @staticmethod
    def _parse_date(value: Any) -> str | None:
        if not value:
            return None

        text = str(value)

        try:
            return datetime.fromisoformat(
                text.replace("Z", "+00:00")
            ).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return text[:19].replace("T", " ")

    def sync_sale(
        self,
        sale: dict[str, Any],
        pharmacy: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        local_id = str(sale.get("_id") or sale.get("id") or "").strip()

        if not local_id:
            raise ValueError("La venta local requiere _id.")

        details = sale.get("detalles") or []

        if not isinstance(details, list) or not details:
            raise ValueError("La venta requiere al menos un producto.")

        synced = app_sales_sync_repository.upsert_sale(
            {
                "venta_local_id": local_id,
                "total": float(sale.get("total") or 0),
                "fecha": self._parse_date(sale.get("fecha")),
                "cliente_nombre": self._customer_name(sale),
                "farmacia_nombre": (
                    (pharmacy or {}).get("nombre")
                    or sale.get("farmacia_nombre")
                    or "App movil"
                ),
                "origen": "app_movil",
                "estado": "sincronizada",
                "payload": {
                    "venta": sale,
                    "farmacia": pharmacy or {},
                },
            }
        )

        return {
            "sincronizada": True,
            "sync_id": synced.get("id"),
            "venta_local_id": synced.get("venta_local_id"),
            "estado": synced.get("estado"),
            "mensaje": "Venta sincronizada con Pharma Neural V2.",
        }

    def list_recent(self, limit: int = 20) -> dict[str, Any]:
        sales = app_sales_sync_repository.list_recent(limit)
        return {
            "total": len(sales),
            "ventas": sales,
        }


app_sales_sync_service = AppSalesSyncService()

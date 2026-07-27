from __future__ import annotations

from datetime import date
from typing import Any

from app.repositories.sales_repository import sales_repository
from app.services.stock_alert_report_service import (
    stock_alert_report_service,
)
from app.utils.pdf import build_simple_pdf, build_ticket_pdf


class PdfExportService:
    @staticmethod
    def _money(value: Any) -> str:
        try:
            amount = float(value or 0)
        except (TypeError, ValueError):
            amount = 0.0

        return f"${amount:,.2f}"

    def generar_ticket_venta_pdf(self, venta_id: int) -> bytes:
        sale = sales_repository.obtener_venta(venta_id)

        if not sale:
            raise ValueError("La venta indicada no existe.")

        details = sales_repository.obtener_detalle_venta(venta_id)

        ticket_items = []
        for item in details:
            quantity = int(item.get("cantidad") or 0)
            price = float(item.get("precio_unitario") or 0)
            subtotal = quantity * price
            ticket_items.append(
                {
                    "name": item.get("medicamento_nombre")
                    or "Medicamento",
                    "quantity": quantity,
                    "unit_price": self._money(price),
                    "subtotal": self._money(subtotal),
                }
            )

        customer_name = (
            f"{sale.get('usuario_nombre') or 'Cliente'} "
            f"{sale.get('usuario_apellido') or ''}"
        ).strip()

        return build_ticket_pdf(
            title=sale.get("farmacia_nombre") or "PharmaControl",
            subtitle="Comprobante profesional de venta",
            folio=sale.get("id"),
            date_text=sale.get("fecha") or "",
            business_name=sale.get("farmacia_nombre")
            or "Sin farmacia",
            customer_name=customer_name,
            items=ticket_items,
            total=self._money(sale.get("total")),
            footer="Gracias por su compra.",
        )

    def generar_reporte_bajo_stock_pdf(
        self,
        limite: int = 100,
    ) -> bytes:
        report = stock_alert_report_service.generar_reporte_bajo_stock(
            limite=limite
        )
        lines = [
            f"Fecha: {date.today().isoformat()}",
            f"Medicamentos a revisar: {report['total_medicamentos']}",
            f"Unidades sugeridas: {report['unidades_sugeridas']}",
            f"Costo estimado: {self._money(report['costo_estimado'])}",
            "",
            "Alertas:",
        ]

        for alert in report["alertas"][:80]:
            lines.append(
                f"- {alert.get('nombre')} | stock "
                f"{alert.get('stock')} | minimo "
                f"{alert.get('stock_minimo')} | "
                f"{alert.get('estado')}"
            )

        if not report["alertas"]:
            lines.append("No hay alertas de bajo stock.")

        return build_simple_pdf(
            title="Reporte de bajo stock",
            lines=lines,
        )


pdf_export_service = PdfExportService()

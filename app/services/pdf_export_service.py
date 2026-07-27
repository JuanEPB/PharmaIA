from __future__ import annotations

from datetime import date
from typing import Any

from app.repositories.sales_repository import sales_repository
from app.services.stock_alert_report_service import (
    stock_alert_report_service,
)
from app.utils.pdf import build_simple_pdf


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
        lines = [
            f"Venta #{sale.get('id')}",
            f"Fecha: {sale.get('fecha')}",
            f"Farmacia: {sale.get('farmacia_nombre') or 'Sin farmacia'}",
            f"Usuario: {sale.get('usuario_nombre') or 'Sin usuario'} "
            f"{sale.get('usuario_apellido') or ''}".strip(),
            "",
            "Detalle:",
        ]

        if not details:
            lines.append("Sin productos registrados.")

        for item in details:
            quantity = int(item.get("cantidad") or 0)
            price = float(item.get("precio_unitario") or 0)
            subtotal = quantity * price
            lines.append(
                f"- {item.get('medicamento_nombre') or 'Medicamento'} "
                f"x {quantity} | {self._money(price)} | "
                f"{self._money(subtotal)}"
            )

        lines.extend(
            [
                "",
                f"Total: {self._money(sale.get('total'))}",
                "",
                "Gracias por su compra.",
            ]
        )

        return build_simple_pdf(
            title="Ticket de venta",
            lines=lines,
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

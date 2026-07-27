from __future__ import annotations

from datetime import date
from html import escape
from typing import Any

from app.services.inventory_statistics_service import (
    inventory_statistics_service,
)


class StockAlertReportService:
    @staticmethod
    def _money(value: Any) -> str:
        try:
            amount = float(value or 0)
        except (TypeError, ValueError):
            amount = 0.0

        return f"${amount:,.2f}"

    @staticmethod
    def _row(alert: dict[str, Any]) -> str:
        stock = int(alert.get("stock") or 0)
        stock_minimum = int(alert.get("stock_minimo") or 0)
        quantity = int(alert.get("cantidad_recomendada") or 0)
        price = float(alert.get("precio") or 0)
        estimated_cost = quantity * price

        return f"""
        <tr>
          <td>{escape(str(alert.get("nombre") or "Sin nombre"))}</td>
          <td>{escape(str(alert.get("lote") or "Sin lote"))}</td>
          <td class="center">{stock}</td>
          <td class="center">{stock_minimum}</td>
          <td class="center">{quantity}</td>
          <td>{escape(str(alert.get("estado") or "BAJO_STOCK"))}</td>
          <td class="right">{StockAlertReportService._money(estimated_cost)}</td>
        </tr>
        """

    def generar_reporte_bajo_stock(
        self,
        limite: int = 100,
    ) -> dict[str, Any]:
        alerts = inventory_statistics_service.obtener_alertas(limite)
        low_stock_alerts = [
            alert
            for alert in alerts
            if str(alert.get("estado") or "") in {
                "AGOTADO",
                "CRITICO",
                "PRECAUCION",
            }
        ]

        total_units = sum(
            int(alert.get("cantidad_recomendada") or 0)
            for alert in low_stock_alerts
        )
        total_cost = sum(
            int(alert.get("cantidad_recomendada") or 0)
            * float(alert.get("precio") or 0)
            for alert in low_stock_alerts
        )

        rows = "\n".join(
            self._row(alert)
            for alert in low_stock_alerts
        )

        if not rows:
            rows = """
            <tr>
              <td colspan="7" class="empty">
                No hay medicamentos con bajo stock en este momento.
              </td>
            </tr>
            """

        html = f"""
        <!doctype html>
        <html lang="es">
        <head>
          <meta charset="utf-8" />
          <title>Reporte de bajo stock</title>
          <style>
            body {{
              font-family: Arial, sans-serif;
              color: #111827;
              margin: 28px;
            }}
            .header {{
              border-bottom: 3px solid #2563eb;
              padding-bottom: 14px;
              margin-bottom: 18px;
            }}
            .eyebrow {{
              color: #2563eb;
              font-size: 11px;
              font-weight: 700;
              letter-spacing: 1px;
              text-transform: uppercase;
            }}
            h1 {{
              margin: 6px 0 4px;
              font-size: 26px;
            }}
            .muted {{
              color: #6b7280;
              font-size: 13px;
            }}
            .metrics {{
              display: grid;
              grid-template-columns: repeat(3, 1fr);
              gap: 10px;
              margin: 18px 0;
            }}
            .metric {{
              border: 1px solid #e5e7eb;
              border-radius: 8px;
              padding: 12px;
            }}
            .metric strong {{
              display: block;
              font-size: 22px;
              margin-bottom: 3px;
            }}
            table {{
              width: 100%;
              border-collapse: collapse;
              margin-top: 12px;
              font-size: 12px;
            }}
            th {{
              text-align: left;
              background: #eff6ff;
              color: #1f2937;
              padding: 9px;
              border: 1px solid #dbeafe;
            }}
            td {{
              padding: 9px;
              border: 1px solid #e5e7eb;
              vertical-align: top;
            }}
            .center {{ text-align: center; }}
            .right {{ text-align: right; }}
            .empty {{
              text-align: center;
              color: #6b7280;
              padding: 22px;
            }}
            .footer {{
              margin-top: 16px;
              color: #6b7280;
              font-size: 11px;
            }}
          </style>
        </head>
        <body>
          <div class="header">
            <div class="eyebrow">Pharma Neural</div>
            <h1>Reporte de bajo stock</h1>
            <div class="muted">Generado el {date.today().isoformat()}</div>
          </div>

          <div class="metrics">
            <div class="metric">
              <strong>{len(low_stock_alerts)}</strong>
              Medicamentos a revisar
            </div>
            <div class="metric">
              <strong>{total_units}</strong>
              Unidades sugeridas
            </div>
            <div class="metric">
              <strong>{self._money(total_cost)}</strong>
              Costo estimado
            </div>
          </div>

          <table>
            <thead>
              <tr>
                <th>Medicamento</th>
                <th>Lote</th>
                <th class="center">Stock</th>
                <th class="center">Mínimo</th>
                <th class="center">Comprar</th>
                <th>Estado</th>
                <th class="right">Costo estimado</th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>

          <div class="footer">
            Este reporte es una sugerencia operativa. Valida proveedor,
            existencia externa y presupuesto antes de confirmar compras.
          </div>
        </body>
        </html>
        """

        return {
            "titulo": "Reporte de bajo stock",
            "fecha": date.today().isoformat(),
            "total_medicamentos": len(low_stock_alerts),
            "unidades_sugeridas": total_units,
            "costo_estimado": round(total_cost, 2),
            "alertas": low_stock_alerts,
            "html": html,
        }


stock_alert_report_service = StockAlertReportService()

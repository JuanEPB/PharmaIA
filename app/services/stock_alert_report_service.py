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
    def _status_label(status: Any) -> str:
        labels = {
            "AGOTADO": "Agotado",
            "CRITICO": "Critico",
            "PRECAUCION": "Bajo stock",
        }

        return labels.get(str(status or "").upper(), "Bajo stock")

    @staticmethod
    def _status_class(status: Any) -> str:
        normalized = str(status or "").upper()

        if normalized == "AGOTADO":
            return "danger"
        if normalized == "CRITICO":
            return "critical"
        return "warning"

    @staticmethod
    def _row(alert: dict[str, Any]) -> str:
        stock = int(alert.get("stock") or 0)
        stock_minimum = int(alert.get("stock_minimo") or 0)
        quantity = int(alert.get("cantidad_recomendada") or 0)
        price = float(alert.get("precio") or 0)
        estimated_cost = quantity * price
        status = alert.get("estado") or "PRECAUCION"
        recommendation = str(
            alert.get("recomendacion")
            or "Revisar reposicion del medicamento."
        )

        return f"""
        <tr>
          <td class="medicine">
            <strong>{escape(str(alert.get("nombre") or "Sin nombre"))}</strong>
            <span>{escape(recommendation)}</span>
          </td>
          <td>{escape(str(alert.get("lote") or "Sin lote"))}</td>
          <td class="center">{stock}</td>
          <td class="center">{stock_minimum}</td>
          <td class="center buy">{quantity}</td>
          <td>
            <em class="badge {StockAlertReportService._status_class(status)}">
              {StockAlertReportService._status_label(status)}
            </em>
          </td>
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
        average_cost = (
            total_cost / len(low_stock_alerts)
            if low_stock_alerts
            else 0
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

        generated_at = date.today().strftime("%d/%m/%Y")

        html = f"""
        <!doctype html>
        <html lang="es">
        <head>
          <meta charset="utf-8" />
          <title>Reporte profesional de bajo stock</title>
          <style>
            @page {{
              size: A4;
              margin: 18mm 16mm;
            }}
            * {{
              box-sizing: border-box;
            }}
            body {{
              margin: 0;
              color: #172033;
              background: #ffffff;
              font-family: Arial, Helvetica, sans-serif;
            }}
            .topbar {{
              display: table;
              width: 100%;
              padding-bottom: 14px;
              margin-bottom: 20px;
              border-bottom: 2px solid #d9e4f5;
            }}
            .brand {{
              display: table-cell;
              width: 65%;
              vertical-align: top;
            }}
            .brand-mark {{
              display: inline-block;
              width: 34px;
              height: 34px;
              line-height: 34px;
              text-align: center;
              border-radius: 8px;
              color: #ffffff;
              background: #0f172a;
              font-weight: 800;
              margin-right: 8px;
            }}
            .brand-name {{
              display: inline-block;
              padding-top: 7px;
              vertical-align: top;
              color: #0f172a;
              font-size: 18px;
              font-weight: 800;
            }}
            .doc-meta {{
              display: table-cell;
              vertical-align: top;
              text-align: right;
              color: #64748b;
              font-size: 12px;
              line-height: 1.5;
            }}
            .eyebrow {{
              margin-bottom: 8px;
              color: #2563eb;
              font-size: 11px;
              font-weight: 800;
              letter-spacing: 1px;
              text-transform: uppercase;
            }}
            h1 {{
              margin: 0;
              color: #0f172a;
              font-size: 28px;
              line-height: 1.15;
            }}
            .subtitle {{
              max-width: 640px;
              margin-top: 8px;
              color: #475569;
              font-size: 13px;
              line-height: 1.55;
            }}
            .metrics {{
              display: table;
              width: 100%;
              margin: 20px 0 18px;
            }}
            .metric {{
              display: table-cell;
              width: 25%;
              padding: 12px;
              border: 1px solid #dbe4ef;
              border-left-width: 0;
              background: #f8fafc;
            }}
            .metric:first-child {{
              border-left-width: 1px;
            }}
            .metric strong {{
              display: block;
              margin-bottom: 3px;
              color: #0f172a;
              font-size: 22px;
            }}
            .metric span {{
              color: #64748b;
              font-size: 10px;
              font-weight: 800;
              text-transform: uppercase;
            }}
            .summary {{
              margin-bottom: 16px;
              padding: 12px 14px;
              border: 1px solid #dbe4ef;
              border-left: 4px solid #2563eb;
              background: #f8fafc;
              color: #334155;
              font-size: 12px;
              line-height: 1.55;
            }}
            .section-title {{
              margin: 18px 0 8px;
              color: #0f172a;
              font-size: 15px;
              font-weight: 800;
            }}
            table {{
              width: 100%;
              border-collapse: collapse;
              font-size: 11px;
            }}
            th {{
              padding: 9px 8px;
              border: 1px solid #0f172a;
              background: #0f172a;
              color: #ffffff;
              text-align: left;
              font-size: 10px;
              letter-spacing: 0.3px;
              text-transform: uppercase;
            }}
            td {{
              padding: 9px 8px;
              border: 1px solid #e2e8f0;
              vertical-align: top;
            }}
            tbody tr:nth-child(even) {{
              background: #f8fafc;
            }}
            .medicine strong {{
              display: block;
              margin-bottom: 4px;
              color: #0f172a;
              font-size: 12px;
            }}
            .medicine span {{
              display: block;
              color: #64748b;
              font-size: 10.5px;
              line-height: 1.4;
            }}
            .center {{ text-align: center; }}
            .right {{ text-align: right; }}
            .buy {{
              color: #2563eb;
              font-weight: 800;
            }}
            .badge {{
              display: inline-block;
              padding: 4px 8px;
              border-radius: 999px;
              font-size: 10px;
              font-style: normal;
              font-weight: 800;
              white-space: nowrap;
            }}
            .badge.danger {{
              color: #991b1b;
              background: #fee2e2;
            }}
            .badge.critical {{
              color: #92400e;
              background: #fef3c7;
            }}
            .badge.warning {{
              color: #1d4ed8;
              background: #dbeafe;
            }}
            .empty {{
              padding: 22px;
              color: #64748b;
              text-align: center;
            }}
            .footer {{
              margin-top: 22px;
              padding-top: 10px;
              border-top: 1px solid #dbe4ef;
              color: #64748b;
              font-size: 11px;
              line-height: 1.5;
            }}
          </style>
        </head>
        <body>
          <div class="topbar">
            <div class="brand">
              <span class="brand-mark">PN</span>
              <span class="brand-name">Pharma Neural</span>
            </div>
            <div class="doc-meta">
              Reporte operativo<br />
              Generado: {generated_at}
            </div>
          </div>

          <div class="eyebrow">Bandeja interna de alertas</div>
          <h1>Reporte profesional de bajo stock</h1>
          <p class="subtitle">
            Consolidado de medicamentos que requieren reposicion por
            agotamiento, nivel critico o inventario por debajo del minimo.
          </p>

          <div class="metrics">
            <div class="metric">
              <strong>{len(low_stock_alerts)}</strong>
              <span>Medicamentos</span>
            </div>
            <div class="metric">
              <strong>{total_units}</strong>
              <span>Unidades sugeridas</span>
            </div>
            <div class="metric">
              <strong>{self._money(total_cost)}</strong>
              <span>Costo total</span>
            </div>
            <div class="metric">
              <strong>{self._money(average_cost)}</strong>
              <span>Promedio por producto</span>
            </div>
          </div>

          <div class="summary">
            Prioridad sugerida: revisar primero productos agotados y criticos.
            Las cantidades son estimaciones operativas calculadas con stock
            minimo y existencia actual.
          </div>

          <div class="section-title">Detalle de reposicion</div>
          <table>
            <thead>
              <tr>
                <th>Medicamento y recomendacion</th>
                <th>Lote</th>
                <th class="center">Stock</th>
                <th class="center">Minimo</th>
                <th class="center">Comprar</th>
                <th>Estado</th>
                <th class="right">Costo estimado</th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>

          <div class="footer">
            Este reporte no ejecuta compras ni modifica inventario. Valida
            proveedor, existencia externa, presupuesto y autorizacion antes de
            confirmar ordenes de compra.
          </div>
        </body>
        </html>
        """

        return {
            "titulo": "Reporte profesional de bajo stock",
            "fecha": date.today().isoformat(),
            "total_medicamentos": len(low_stock_alerts),
            "unidades_sugeridas": total_units,
            "costo_estimado": round(total_cost, 2),
            "alertas": low_stock_alerts,
            "html": html,
        }


stock_alert_report_service = StockAlertReportService()

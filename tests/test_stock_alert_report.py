from unittest.mock import patch

from app.services.stock_alert_report_service import (
    StockAlertReportService,
)


def test_low_stock_report_builds_printable_html() -> None:
    service = StockAlertReportService()

    with patch(
        "app.services.stock_alert_report_service."
        "inventory_statistics_service.obtener_alertas",
        return_value=[
            {
                "nombre": "GENOPRAZOL 20 MG CAP",
                "lote": "GEN-01",
                "stock": 2,
                "stock_minimo": 10,
                "precio": 50,
                "estado": "CRITICO",
                "cantidad_recomendada": 18,
            },
            {
                "nombre": "Vitamina C",
                "estado": "PROXIMO_A_CADUCAR",
                "cantidad_recomendada": 0,
            },
        ],
    ):
        result = service.generar_reporte_bajo_stock()

    assert result["total_medicamentos"] == 1
    assert result["unidades_sugeridas"] == 18
    assert result["costo_estimado"] == 900
    assert "GENOPRAZOL 20 MG CAP" in result["html"]
    assert "<table>" in result["html"]

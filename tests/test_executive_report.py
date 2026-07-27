from unittest.mock import patch

from app.services.executive_report_service import ExecutiveReportService


def test_executive_report_builds_narrative() -> None:
    service = ExecutiveReportService()

    dashboard = {
        "estado_predictivo": "CRITICO",
        "puntaje_riesgo": 82,
        "resumen": {
            "total_medicamentos": 20,
            "agotados": 2,
            "bajo_stock": 3,
            "caducados": 1,
            "por_caducar_30_dias": 4,
        },
        "indicadores": {
            "alertas_activas": 6,
            "predicciones_riesgo": 5,
            "medicamentos_para_compra": 3,
            "costo_compra_estimado": 2500,
        },
    }

    recommendations = {
        "total": 2,
        "recomendaciones": [
            {
                "accion": "Retirar medicamentos caducados.",
            },
            {
                "accion": "Generar órdenes de compra.",
            },
        ],
    }

    with patch(
        "app.services.executive_report_service."
        "predictive_dashboard_service.obtener_dashboard",
        return_value=dashboard,
    ), patch(
        "app.services.executive_report_service."
        "recommendation_service.generar_recomendaciones",
        return_value=recommendations,
    ):
        result = service.generar_reporte(limite=5)

    assert result["titulo"] == "Reporte Ejecutivo IA de Inventario"
    assert result["estado"] == "CRITICO"
    assert "puntaje 82/100" in result["resumen"]
    assert len(result["acciones_prioritarias"]) == 2


def test_executive_report_headline_for_normal_status() -> None:
    assert (
        ExecutiveReportService._headline("NORMAL")
        == "El inventario se encuentra estable."
    )

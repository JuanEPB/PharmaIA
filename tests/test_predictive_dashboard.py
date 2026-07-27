from unittest.mock import patch

from app.services.predictive_dashboard_service import (
    PredictiveDashboardService,
)


def test_predictive_dashboard_builds_consolidated_view() -> None:
    service = PredictiveDashboardService()

    summary = {
        "total_medicamentos": 10,
        "agotados": 1,
        "bajo_stock": 2,
        "caducados": 1,
    }

    alerts = [
        {
            "id": 1,
            "nombre": "Paracetamol",
            "estado": "CRITICO",
            "prioridad": 3,
        }
    ]

    predictions = {
        "total": 1,
        "predicciones": [
            {
                "medicamento": {
                    "id": 1,
                    "nombre": "Paracetamol",
                },
                "nivel_riesgo": "CRITICO",
                "cobertura_estimada_dias": 4,
            }
        ],
    }

    purchase_plan = {
        "requiere_compra": True,
        "total_medicamentos": 2,
        "costo_estimado": 1500,
    }

    with patch(
        "app.services.predictive_dashboard_service."
        "inventory_statistics_service.obtener_resumen",
        return_value=summary,
    ), patch(
        "app.services.predictive_dashboard_service."
        "inventory_statistics_service.obtener_alertas",
        return_value=alerts,
    ), patch(
        "app.services.predictive_dashboard_service."
        "depletion_prediction_service.predecir_inventario",
        return_value=predictions,
    ), patch(
        "app.services.predictive_dashboard_service."
        "purchase_planner_service.generar_plan",
        return_value=purchase_plan,
    ):
        result = service.obtener_dashboard(limite=5)

    assert result["estado_predictivo"] in {
        "NORMAL",
        "PRECAUCION",
        "ALTO",
        "CRITICO",
    }
    assert result["indicadores"]["alertas_activas"] == 1
    assert result["indicadores"]["predicciones_riesgo"] == 1
    assert result["indicadores"]["medicamentos_para_compra"] == 2
    assert result["recomendaciones"]
    assert "Estado predictivo" in result["resumen_ejecutivo"]


def test_predictive_dashboard_normal_without_risks() -> None:
    score = PredictiveDashboardService._risk_score(
        summary={
            "total_medicamentos": 10,
            "agotados": 0,
            "caducados": 0,
        },
        predictions=[],
        purchase_plan={
            "total_medicamentos": 0,
        },
    )

    assert score == 0
    assert PredictiveDashboardService._status_from_score(score) == "NORMAL"

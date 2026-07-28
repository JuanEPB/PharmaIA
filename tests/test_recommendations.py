from unittest.mock import patch

from app.services.recommendation_service import RecommendationService


def test_recommendations_prioritize_critical_items() -> None:
    service = RecommendationService()

    with patch(
        "app.services.recommendation_service."
        "inventory_statistics_service.obtener_resumen",
        return_value={
            "caducados": 1,
        },
    ), patch(
        "app.services.recommendation_service."
        "inventory_statistics_service.obtener_alertas",
        return_value=[
            {
                "id": 1,
            }
        ],
    ), patch(
        "app.services.recommendation_service."
        "depletion_prediction_service.predecir_inventario",
        return_value={
            "predicciones": [
                {
                    "medicamento": {
                        "nombre": "Paracetamol",
                    },
                    "nivel_riesgo": "CRITICO",
                    "cobertura_estimada_dias": 3,
                    "cantidad_compra_recomendada": 20,
                }
            ]
        },
    ), patch(
        "app.services.recommendation_service."
        "purchase_planner_service.generar_plan",
        return_value={
            "requiere_compra": True,
            "total_medicamentos": 2,
            "costo_estimado": 1200,
        },
    ), patch(
        "app.services.recommendation_service."
        "anomaly_detection_service.detectar_anomalias",
        return_value={
            "total_anomalias": 1,
            "anomalias_criticas": 1,
        },
    ):
        result = service.generar_recomendaciones(limite=10)

    assert result["total"] >= 4
    assert result["recomendaciones"][0]["prioridad"] == "CRITICA"
    assert result["recomendaciones"][0]["explicacion_app"]
    assert result["recomendaciones"][0]["accion_app"]
    assert result["recomendaciones"][0]["bloquea_acciones"] is True
    assert result["fuentes"]["anomalias"] == 1
    assert result["fuentes"]["plan_compra"] is True


def test_recommendations_fallback_to_monitoring() -> None:
    service = RecommendationService()

    with patch(
        "app.services.recommendation_service."
        "inventory_statistics_service.obtener_resumen",
        return_value={
            "caducados": 0,
        },
    ), patch(
        "app.services.recommendation_service."
        "inventory_statistics_service.obtener_alertas",
        return_value=[],
    ), patch(
        "app.services.recommendation_service."
        "depletion_prediction_service.predecir_inventario",
        return_value={
            "predicciones": [],
        },
    ), patch(
        "app.services.recommendation_service."
        "purchase_planner_service.generar_plan",
        return_value={
            "requiere_compra": False,
        },
    ), patch(
        "app.services.recommendation_service."
        "anomaly_detection_service.detectar_anomalias",
        return_value={
            "total_anomalias": 0,
            "anomalias_criticas": 0,
        },
    ):
        result = service.generar_recomendaciones(limite=10)

    assert result["total"] == 1
    assert result["recomendaciones"][0]["tipo"] == "MONITOREO"
    assert result["recomendaciones"][0]["accion_app"] == (
        "Ver resumen de inventario"
    )

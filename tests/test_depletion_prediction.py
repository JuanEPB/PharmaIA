from datetime import date, timedelta
from unittest.mock import patch

from app.services.depletion_prediction_service import (
    DepletionPredictionService,
)


def test_daily_average_includes_days_without_consumption() -> None:
    service = DepletionPredictionService()

    today = date.today()

    rows = [
        {
            "fecha": today,
            "unidades": 10,
        },
        {
            "fecha": today - timedelta(days=1),
            "unidades": 5,
        },
    ]

    result = service._daily_statistics(
        daily_rows=rows,
        history_days=5,
    )

    assert result["promedio_diario"] == 3


def test_risk_level_high() -> None:
    configuration = {
        "riesgo_critico_dias": 7,
        "riesgo_alto_dias": 14,
        "riesgo_medio_dias": 30,
    }

    result = DepletionPredictionService._risk_level(
        coverage_days=8,
        stock=40,
        configuration=configuration,
    )

    assert result == "ALTO"


def test_depletion_prediction() -> None:
    service = DepletionPredictionService()

    today = date.today()

    daily_rows = [
        {
            "fecha": today - timedelta(days=index),
            "unidades": 5,
        }
        for index in range(8)
    ]

    with patch(
        "app.services.depletion_prediction_service."
        "depletion_prediction_repository.obtener_configuracion",
        return_value={
            "dias_historial": 8,
            "dias_cobertura_objetivo": 30,
            "dias_stock_seguridad": 7,
            "riesgo_critico_dias": 7,
            "riesgo_alto_dias": 14,
            "riesgo_medio_dias": 30,
            "incluir_caducidad_como_consumo": 0,
        },
    ), patch(
        "app.services.depletion_prediction_service."
        "depletion_prediction_repository.obtener_medicamento",
        return_value={
            "id": 1,
            "nombre": "Paracetamol",
            "lote": "PAR-001",
            "caducidad": today + timedelta(days=365),
            "stock": 40,
            "stock_minimo": 10,
        },
    ), patch(
        "app.services.depletion_prediction_service."
        "depletion_prediction_repository.obtener_consumo_historico",
        return_value={
            "unidades_consumidas": 40,
            "total_movimientos": 8,
            "dias_con_movimiento": 8,
        },
    ), patch(
        "app.services.depletion_prediction_service."
        "depletion_prediction_repository.obtener_consumo_diario",
        return_value=daily_rows,
    ), patch(
        "app.services.depletion_prediction_service."
        "depletion_prediction_repository.guardar_prediccion",
    ) as save_prediction:
        result = service.predecir_medicamento(1)

    assert result["consumo_promedio_diario"] == 5
    assert result["cobertura_estimada_dias"] == 8
    assert result["nivel_riesgo"] == "ALTO"
    assert result["cantidad_compra_recomendada"] == 145
    save_prediction.assert_called_once()


def test_no_history_returns_no_date() -> None:
    service = DepletionPredictionService()

    with patch(
        "app.services.depletion_prediction_service."
        "depletion_prediction_repository.obtener_configuracion",
        return_value={
            "dias_historial": 30,
            "dias_cobertura_objetivo": 30,
            "dias_stock_seguridad": 7,
            "riesgo_critico_dias": 7,
            "riesgo_alto_dias": 14,
            "riesgo_medio_dias": 30,
        },
    ), patch(
        "app.services.depletion_prediction_service."
        "depletion_prediction_repository.obtener_medicamento",
        return_value={
            "id": 1,
            "nombre": "Paracetamol",
            "lote": "PAR-001",
            "caducidad": date.today() + timedelta(days=365),
            "stock": 40,
            "stock_minimo": 10,
        },
    ), patch(
        "app.services.depletion_prediction_service."
        "depletion_prediction_repository.obtener_consumo_historico",
        return_value={
            "unidades_consumidas": 0,
            "total_movimientos": 0,
            "dias_con_movimiento": 0,
        },
    ), patch(
        "app.services.depletion_prediction_service."
        "depletion_prediction_repository.obtener_consumo_diario",
        return_value=[],
    ), patch(
        "app.services.depletion_prediction_service."
        "depletion_prediction_repository.guardar_prediccion",
        side_effect=RuntimeError("sin tabla"),
    ):
        result = service.predecir_medicamento(1)

    assert result["cobertura_estimada_dias"] is None
    assert result["fecha_probable_agotamiento"] is None
    assert result["confianza_prediccion"] == "BAJA"

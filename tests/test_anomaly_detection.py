from unittest.mock import patch

from app.services.anomaly_detection_service import (
    AnomalyDetectionService,
)


def test_detects_inconsistent_and_large_exit() -> None:
    service = AnomalyDetectionService()

    movements = [
        {
            "id": 1,
            "medicamento_id": 10,
            "medicamento": "Paracetamol",
            "tipo": "SALIDA",
            "cantidad": 90,
            "stock_anterior": 100,
            "stock_nuevo": 20,
        }
    ]

    with patch(
        "app.services.anomaly_detection_service."
        "inventory_movement_repository.listar_movimientos",
        return_value=movements,
    ):
        result = service.detectar_anomalias(limite=100)

    anomaly_types = {
        anomaly["tipo_anomalia"]
        for anomaly in result["anomalias"]
    }

    assert result["estado"] == "REQUIERE_REVISION"
    assert "STOCK_INCONSISTENTE" in anomaly_types
    assert "SALIDA_ELEVADA" in anomaly_types


def test_no_anomalies_for_regular_entry() -> None:
    service = AnomalyDetectionService()

    movements = [
        {
            "id": 1,
            "medicamento_id": 10,
            "medicamento": "Paracetamol",
            "tipo": "ENTRADA",
            "cantidad": 5,
            "stock_anterior": 10,
            "stock_nuevo": 15,
        }
    ]

    with patch(
        "app.services.anomaly_detection_service."
        "inventory_movement_repository.listar_movimientos",
        return_value=movements,
    ):
        result = service.detectar_anomalias(limite=100)

    assert result["estado"] == "SIN_ANOMALIAS"
    assert result["total_anomalias"] == 0

from unittest.mock import patch

from app.services.inventory_statistics_service import (
    InventoryStatisticsService,
)


def test_inventory_summary() -> None:
    service = InventoryStatisticsService()

    repository_data = {
        "total_medicamentos": 10,
        "unidades_disponibles": 150,
        "agotados": 1,
        "bajo_stock": 2,
        "caducados": 1,
        "por_caducar_30_dias": 1,
        "valor_total_inventario": 12500.50,
        "promedio_stock": 15,
        "precio_promedio": 83.34,
    }

    with patch(
        "app.services.inventory_statistics_service."
        "inventory_repository.obtener_resumen",
        return_value=repository_data,
    ):
        result = service.obtener_resumen()

    assert result["total_medicamentos"] == 10
    assert result["unidades_disponibles"] == 150
    assert result["agotados"] == 1
    assert result["bajo_stock"] == 2
    assert result["valor_total_inventario"] == 12500.50
    assert result["estado_general"] == "CRITICO"


def test_inventory_status_normal() -> None:
    service = InventoryStatisticsService()

    result = service._calculate_general_status(
        agotados=0,
        bajo_stock=0,
        caducados=0,
        total=20,
    )

    assert result == "NORMAL"


def test_inventory_status_without_data() -> None:
    service = InventoryStatisticsService()

    result = service._calculate_general_status(
        agotados=0,
        bajo_stock=0,
        caducados=0,
        total=0,
    )

    assert result == "SIN_DATOS"


def test_critical_recommendation() -> None:
    service = InventoryStatisticsService()

    recommendation = service._build_recommendation(
        state="CRITICO",
        medicine="Paracetamol",
        quantity=16,
        days=90,
    )

    assert "16 unidades" in recommendation
    assert "Paracetamol" in recommendation

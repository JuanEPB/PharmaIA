from unittest.mock import patch

from app.services.purchase_planner_service import (
    PurchasePlannerService,
)


def test_generate_purchase_plan() -> None:
    service = PurchasePlannerService()

    medicines = [
        {
            "id": 1,
            "nombre": "Paracetamol",
            "stock": 2,
            "stock_minimo": 10,
            "precio": 50,
            "proveedor_id": 1,
            "cantidad_recomendada": 18,
            "costo_estimado": 900,
            "nivel_riesgo": "CRITICO",
        },
        {
            "id": 2,
            "nombre": "Ibuprofeno",
            "stock": 5,
            "stock_minimo": 10,
            "precio": 40,
            "proveedor_id": 2,
            "cantidad_recomendada": 15,
            "costo_estimado": 600,
            "nivel_riesgo": "BAJO_STOCK",
        },
    ]

    with patch(
        "app.services.purchase_planner_service."
        "purchase_planner_repository.obtener_configuracion",
        return_value={
            "multiplicador_stock_minimo": 2,
            "planeacion_automatica": 1,
            "monto_minimo_alerta": 0,
        },
    ), patch(
        "app.services.purchase_planner_service."
        "purchase_planner_repository."
        "obtener_medicamentos_para_compra",
        return_value=medicines,
    ):
        result = service.generar_plan()

    assert result["requiere_compra"] is True
    assert result["total_medicamentos"] == 2
    assert result["medicamentos_criticos"] == 1
    assert result["total_proveedores"] == 2
    assert result["costo_estimado"] == 1500


def test_empty_purchase_plan() -> None:
    service = PurchasePlannerService()

    with patch(
        "app.services.purchase_planner_service."
        "purchase_planner_repository.obtener_configuracion",
        return_value={
            "multiplicador_stock_minimo": 2,
        },
    ), patch(
        "app.services.purchase_planner_service."
        "purchase_planner_repository."
        "obtener_medicamentos_para_compra",
        return_value=[],
    ):
        result = service.generar_plan()

    assert result["requiere_compra"] is False
    assert result["total_medicamentos"] == 0
    assert result["costo_estimado"] == 0

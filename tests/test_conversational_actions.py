from app.services.conversational_action_service import (
    ConversationalActionService,
)


def test_parse_entry_action() -> None:
    service = ConversationalActionService()

    result = service._parse_stock_action(
        "Agrega 20 cajas de Paracetamol"
    )

    assert result is not None
    assert result["tipo_movimiento"] == "ENTRADA"
    assert result["cantidad"] == 20
    assert result["medicamento_consulta"] == "paracetamol"


def test_parse_exit_action() -> None:
    service = ConversationalActionService()

    result = service._parse_stock_action(
        "Descuenta 3 Amoxicilinas por venta"
    )

    assert result is not None
    assert result["tipo_movimiento"] == "SALIDA"
    assert result["cantidad"] == 3
    assert result["motivo"] == "venta"


def test_parse_purchase_order() -> None:
    service = ConversationalActionService()

    result = service._parse_purchase_order_action(
        "Genera una orden de compra para los medicamentos críticos"
    )

    assert result is not None
    assert result["tipo_accion"] == "GENERAR_ORDEN_CRITICOS"


def test_confirmation_words() -> None:
    service = ConversationalActionService()

    assert service._is_confirmation("confirmar")
    assert service._is_confirmation("Sí, hazlo")


def test_cancellation_words() -> None:
    service = ConversationalActionService()

    assert service._is_cancellation("cancelar")
    assert service._is_cancellation("no")

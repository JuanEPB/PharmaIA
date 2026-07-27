import asyncio

from app.routes import build_welcome_response
from app.routes import chat
from app.schemas import ChatRequest
from app.services.conversation_memory import conversation_memory


def teardown_function() -> None:
    conversation_memory.clear()


def test_welcome_response_includes_options() -> None:
    result = build_welcome_response(
        "sesion-test"
    )

    assert result["sesion_id"] == "sesion-test"
    assert "Hola" in result["respuesta"]
    assert result["contexto"]["tipo"] == "BIENVENIDA"
    assert len(result["opciones"]) >= 5
    assert {
        "dashboard_predictivo",
        "plan_compras",
        "alertas",
        "agotamiento",
        "reporte",
    }.issubset(
        {
            option["id"]
            for option in result["opciones"]
        }
    )


def test_purchase_confirmation_uses_pending_context(monkeypatch) -> None:
    conversation_memory.update(
        "sesion-compra",
        accion_pendiente={
            "tipo_accion": "CONFIRMAR_PLAN_COMPRA",
            "plan": {
                "requiere_compra": True,
            },
        },
    )

    def fake_execute(session_id: str, usuario_id=None):
        assert session_id == "sesion-compra"
        return {
            "ejecutada": True,
            "respuesta": "Se generó la orden de compra.",
            "ordenes": [],
        }

    monkeypatch.setattr(
        "app.routes.purchase_planner_service.ejecutar_plan",
        fake_execute,
    )

    result = asyncio.run(
        chat(
            ChatRequest(
                mensaje="sí",
                sesion_id="sesion-compra",
            )
        )
    )

    assert result["respuesta"] == "Se generó la orden de compra."
    assert result["contexto"]["tipo"] == "PLAN_COMPRA_CONFIRMADO"

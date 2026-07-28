import asyncio

from app.routes import build_welcome_response
from app.routes import chat
from app.schemas import ChatRequest
from app.services.assistant_service import AssistantService
from app.services.conversation_service import ConversationService
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


def test_medicine_search_cleans_natural_request_words() -> None:
    service = AssistantService()

    assert (
        service._extraer_busqueda_general(
            "Dame informacion de GENOPRAZOL"
        )
        == "genoprazol"
    )
    assert (
        service._extraer_busqueda_general(
            "quiero datos sobre CAFIASPIRINA"
        )
        == "cafiaspirina"
    )


def test_conversation_extracts_medicine_from_stock_question() -> None:
    service = ConversationService()

    assert (
        service._extract_medicine_from_text(
            "cuanto stock tiene GENOPRAZOL"
        )
        == "GENOPRAZOL"
    )


def test_direct_medicine_stock_question_returns_detail(monkeypatch) -> None:
    service = AssistantService()

    monkeypatch.setattr(
        "app.services.assistant_service.inventory_service.buscar",
        lambda nombre: [
            {
                "nombre": "GENOPRAZOL 20 MG CAP",
                "stock": 20,
                "stock_minimo": 10,
                "lote": "650240036415",
                "caducidad": "2026-07-29",
                "precio": 85,
            }
        ],
    )

    result = service.procesar_mensaje(
        "cuanto stock tiene GENOPRAZOL"
    )

    assert result["intencion"] == "detalle_medicamento"
    assert "GENOPRAZOL 20 MG CAP tiene 20" in result["respuesta"]
    assert result["entidades"]["medicamento"] == "genoprazol"


def test_conversation_prefers_structured_medicine_over_response_text() -> None:
    service = ConversationService()

    result = service._extract_medicine(
        {
            "respuesta": "GENOPRAZOL tiene 20 unidades. Stock minimo: 10.",
            "datos": [
                {
                    "nombre": "GENOPRAZOL 20 MG CAP",
                }
            ],
            "entidades": {
                "medicamento": "genoprazol",
            },
        }
    )

    assert result == "genoprazol"

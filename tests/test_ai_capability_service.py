from app.core.permissions import build_current_user
from app.services.ai_capability_service import AiCapabilityService


def test_ai_capabilities_include_enabled_state_for_role() -> None:
    user = build_current_user(x_user_role="vendedor")

    result = AiCapabilityService().obtener_capacidades(user)

    capabilities = {
        item["id"]: item
        for item in result["capacidades"]
    }

    assert capabilities["chat_inventario"]["habilitado_para_usuario"]
    assert not capabilities["plan_compras"]["habilitado_para_usuario"]
    assert "avisos automaticos" in (
        capabilities["notificaciones_ia"]["descripcion"].lower()
    )


def test_ai_capabilities_admin_can_execute_ai_actions() -> None:
    user = build_current_user(x_user_role="admin")

    result = AiCapabilityService().obtener_capacidades(user)

    capabilities = {
        item["id"]: item
        for item in result["capacidades"]
    }

    assert capabilities["plan_compras"]["habilitado_para_usuario"]
    assert capabilities["agente_autonomo"]["habilitado_para_usuario"]

from app.services import app_profile_service as profile_module


class FakeProfileRepository:
    def obtener_empresa_activa(self) -> dict:
        return {
            "id": 1,
            "nombre": "Farmacia Demo",
            "plan": "Premium",
        }

    def obtener_farmacia_activa(self) -> dict:
        return {
            "id": 1,
            "nombre": "Sucursal Centro",
        }

    def obtener_metricas_operativas(self) -> dict:
        return {
            "total_medicamentos": 10,
            "medicamentos_bajo_stock": 2,
        }

    def obtener_metricas_ia(self) -> dict:
        return {
            "sesiones_con_memoria": 3,
            "acciones_pendientes": 1,
            "feedback_pendiente": 2,
        }


def test_app_profile_contains_app_and_ai_context(monkeypatch) -> None:
    monkeypatch.setattr(
        profile_module,
        "app_profile_repository",
        FakeProfileRepository(),
    )

    profile = profile_module.AppProfileService().obtener_perfil()

    assert profile["app"]["version"] == "2.0.0"
    assert profile["empresa"]["nombre"] == "Farmacia Demo"
    assert "chat_ia" in profile["modulos"]
    assert "feedback pendiente de aprendizaje" in profile["ia"]["puede_ver"]
    assert profile["ia"]["metricas"]["acciones_pendientes"] == 1

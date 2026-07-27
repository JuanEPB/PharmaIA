import importlib
from pathlib import Path

from app.services.conversation_memory import ConversationMemory
from app.services import learning_feedback_service as feedback_module
from app.services.learning_feedback_service import LearningFeedbackService


memory_module = importlib.import_module(
    "app.services.conversation_memory"
)


class FakeAIRepository:
    def __init__(self) -> None:
        self.memory: dict[str, dict] = {}
        self.saved_events: list[dict] = []
        self.updated_statuses: list[tuple[str, str]] = []
        self.saved_actions: list[dict] = []

    def get_conversation_memory(self, session_id: str) -> dict:
        return self.memory.get(session_id, {})

    def upsert_conversation_memory(
        self,
        session_id: str,
        context: dict,
    ) -> None:
        self.memory[session_id] = context

    def delete_conversation_memory(self, session_id: str) -> bool:
        return self.memory.pop(session_id, None) is not None

    def save_learning_feedback(self, event: dict) -> None:
        self.saved_events.append(event)

    def update_learning_feedback_status(
        self,
        event_id: str,
        status: str,
    ) -> None:
        self.updated_statuses.append((event_id, status))

    def save_conversational_action(self, **kwargs) -> None:
        self.saved_actions.append(kwargs)


def test_conversation_memory_persists_updates(monkeypatch) -> None:
    fake_repository = FakeAIRepository()
    monkeypatch.setattr(
        memory_module,
        "ai_operational_repository",
        fake_repository,
    )

    memory = ConversationMemory()
    result = memory.update(
        "sesion-db",
        ultimo_mensaje="hola",
        ultima_respuesta="respuesta",
    )

    assert result["ultimo_mensaje"] == "hola"
    assert fake_repository.memory["sesion-db"]["ultima_respuesta"] == (
        "respuesta"
    )


def test_conversation_memory_reads_database_fallback(monkeypatch) -> None:
    fake_repository = FakeAIRepository()
    fake_repository.memory["sesion-db"] = {
        "ultimo_mensaje": "desde bd",
    }
    monkeypatch.setattr(
        memory_module,
        "ai_operational_repository",
        fake_repository,
    )

    memory = ConversationMemory()

    assert memory.get("sesion-db")["ultimo_mensaje"] == "desde bd"


def test_default_learning_feedback_persists_to_database(
    monkeypatch,
) -> None:
    fake_repository = FakeAIRepository()
    queue_path = (
        Path(__file__).resolve().parent
        / ".tmp"
        / "learning_queue_persistence.jsonl"
    )
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue_path.unlink(missing_ok=True)

    monkeypatch.setattr(
        feedback_module,
        "LEARNING_QUEUE_PATH",
        queue_path,
    )
    monkeypatch.setattr(
        feedback_module,
        "ai_operational_repository",
        fake_repository,
    )

    service = LearningFeedbackService(
        queue_path=feedback_module.LEARNING_QUEUE_PATH,
    )

    try:
        event = service.capture_user_feedback(
            message="que compro",
            response="compra X",
            helpful=False,
            session_id="sesion-db",
            intent="planear_compras",
        )

        service.update_event_status(
            event["id"],
            "aprobado_para_entrenamiento",
        )

        assert fake_repository.saved_events[0]["mensaje"] == "que compro"
        assert fake_repository.updated_statuses == [
            (
                event["id"],
                "aprobado_para_entrenamiento",
            )
        ]
    finally:
        queue_path.unlink(missing_ok=True)

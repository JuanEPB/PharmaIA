from pathlib import Path

from app.services.learning_feedback_service import LearningFeedbackService


TEST_QUEUE_PATH = Path(__file__).resolve().parent / ".tmp" / "learning_queue.jsonl"


def clean_queue() -> None:
    if TEST_QUEUE_PATH.exists():
        TEST_QUEUE_PATH.unlink()


def test_capture_low_confidence_message() -> None:
    clean_queue()

    service = LearningFeedbackService(
        queue_path=TEST_QUEUE_PATH,
        low_confidence_threshold=0.65,
    )

    captured = service.capture_if_needed(
        message="que medicina se acaba primero",
        prediction={
            "intencion": "desconocido",
            "intencion_detectada": "predecir_agotamiento",
            "confianza": 0.42,
            "porcentaje": 42,
            "predicciones": [],
        },
    )

    assert captured
    assert "que medicina se acaba primero" in TEST_QUEUE_PATH.read_text(
        encoding="utf-8"
    )

    clean_queue()


def test_skip_high_confidence_message() -> None:
    clean_queue()

    service = LearningFeedbackService(
        queue_path=TEST_QUEUE_PATH,
        low_confidence_threshold=0.65,
    )

    captured = service.capture_if_needed(
        message="medicamentos agotados",
        prediction={
            "intencion": "consultar_agotados",
            "confianza": 0.97,
        },
    )

    assert not captured
    assert not TEST_QUEUE_PATH.exists()


def test_capture_user_feedback() -> None:
    clean_queue()

    service = LearningFeedbackService(
        queue_path=TEST_QUEUE_PATH,
    )

    event = service.capture_user_feedback(
        message="que debo comprar",
        response="Compra Paracetamol.",
        helpful=False,
        session_id="sesion-test",
        intent="planear_compras",
        correction="Debe mostrar cantidades y proveedor.",
    )

    content = TEST_QUEUE_PATH.read_text(
        encoding="utf-8"
    )

    assert event["tipo"] == "feedback_usuario"
    assert event["estado"] == "pendiente_revision"
    assert "Debe mostrar cantidades" in content

    clean_queue()

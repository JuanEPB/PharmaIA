from app.services.learning_feedback_service import LearningFeedbackService


def test_capture_low_confidence_message(tmp_path) -> None:
    queue_path = tmp_path / "learning_queue.jsonl"
    service = LearningFeedbackService(
        queue_path=queue_path,
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
    assert "que medicina se acaba primero" in queue_path.read_text(
        encoding="utf-8"
    )


def test_skip_high_confidence_message(tmp_path) -> None:
    queue_path = tmp_path / "learning_queue.jsonl"
    service = LearningFeedbackService(
        queue_path=queue_path,
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
    assert not queue_path.exists()

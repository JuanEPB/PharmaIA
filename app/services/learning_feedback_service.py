from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[2]
LEARNING_QUEUE_PATH = PROJECT_DIR / "training" / "learning_queue.jsonl"


class LearningFeedbackService:
    """
    Guarda mensajes difíciles para revisarlos y convertirlos en
    ejemplos de entrenamiento.
    """

    def __init__(
        self,
        queue_path: Path = LEARNING_QUEUE_PATH,
        low_confidence_threshold: float = 0.65,
    ) -> None:
        self.queue_path = queue_path
        self.low_confidence_threshold = low_confidence_threshold

    def should_capture(
        self,
        prediction: dict[str, Any],
    ) -> bool:
        intent = str(
            prediction.get("intencion") or ""
        )
        confidence = float(
            prediction.get("confianza") or 0
        )

        return (
            intent == "desconocido"
            or confidence < self.low_confidence_threshold
        )

    def capture_if_needed(
        self,
        message: str,
        prediction: dict[str, Any],
    ) -> bool:
        clean_message = (message or "").strip()

        if not clean_message:
            return False

        if not self.should_capture(prediction):
            return False

        self.queue_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        event = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "mensaje": clean_message,
            "intencion": prediction.get("intencion"),
            "intencion_detectada": prediction.get(
                "intencion_detectada"
            ),
            "confianza": prediction.get("confianza"),
            "porcentaje": prediction.get("porcentaje"),
            "predicciones": prediction.get(
                "predicciones",
                [],
            ),
            "estado": "pendiente_revision",
        }

        with self.queue_path.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                json.dumps(
                    event,
                    ensure_ascii=False,
                )
                + "\n"
            )

        return True

    def capture_user_feedback(
        self,
        *,
        message: str,
        response: str,
        helpful: bool,
        session_id: str,
        intent: str | None = None,
        correction: str | None = None,
    ) -> dict[str, Any]:
        clean_message = (message or "").strip()
        clean_response = (response or "").strip()

        if not clean_message:
            raise ValueError("El mensaje original es requerido.")

        self.queue_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        event = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "tipo": "feedback_usuario",
            "sesion_id": session_id,
            "mensaje": clean_message,
            "respuesta": clean_response,
            "intencion": intent,
            "util": helpful,
            "correccion": (
                (correction or "").strip()
                if correction
                else None
            ),
            "estado": (
                "aprobado_para_entrenamiento"
                if helpful
                else "pendiente_revision"
            ),
        }

        with self.queue_path.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                json.dumps(
                    event,
                    ensure_ascii=False,
                )
                + "\n"
            )

        return event


learning_feedback_service = LearningFeedbackService()

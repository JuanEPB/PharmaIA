from __future__ import annotations

import json
import uuid
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
            "id": str(uuid.uuid4()),
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
            "id": str(uuid.uuid4()),
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

    def list_events(
        self,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if not self.queue_path.exists():
            return []

        events: list[dict[str, Any]] = []

        with self.queue_path.open("r", encoding="utf-8") as file:
            for index, line in enumerate(file):
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                event.setdefault("id", f"legacy-{index}")

                if status and event.get("estado") != status:
                    continue

                events.append(event)

        events.sort(
            key=lambda item: str(item.get("timestamp") or ""),
            reverse=True,
        )

        return events[: max(1, min(limit, 500))]

    def update_event_status(
        self,
        event_id: str,
        status: str,
    ) -> dict[str, Any]:
        if status not in {
            "pendiente_revision",
            "aprobado_para_entrenamiento",
            "rechazado",
        }:
            raise ValueError("Estado de aprendizaje inválido.")

        if not self.queue_path.exists():
            raise ValueError("No hay eventos de aprendizaje registrados.")

        updated_event: dict[str, Any] | None = None
        events: list[dict[str, Any]] = []

        with self.queue_path.open("r", encoding="utf-8") as file:
            for index, line in enumerate(file):
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                event.setdefault("id", f"legacy-{index}")

                if event.get("id") == event_id:
                    event["estado"] = status
                    event["revisado_en"] = datetime.now(
                        timezone.utc
                    ).isoformat()
                    updated_event = event

                events.append(event)

        if updated_event is None:
            raise ValueError("No encontré el evento de aprendizaje.")

        self.queue_path.parent.mkdir(parents=True, exist_ok=True)

        with self.queue_path.open("w", encoding="utf-8") as file:
            for event in events:
                file.write(
                    json.dumps(event, ensure_ascii=False)
                    + "\n"
                )

        return updated_event


learning_feedback_service = LearningFeedbackService()

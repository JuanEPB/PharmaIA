from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.learning_feedback_service import (
    learning_feedback_service,
)


router = APIRouter(
    prefix="/aprendizaje",
    tags=["Aprendizaje IA"],
)


class UserFeedbackRequest(BaseModel):
    mensaje: str = Field(..., min_length=1, max_length=1000)
    respuesta: str = Field(default="", max_length=4000)
    util: bool
    sesion_id: str = Field(default="app-movil", min_length=1, max_length=100)
    intencion: str | None = Field(default=None, max_length=100)
    correccion: str | None = Field(default=None, max_length=1000)


class LearningReviewRequest(BaseModel):
    estado: str = Field(..., min_length=1, max_length=50)


@router.post(
    "/feedback",
    summary="Registrar feedback del usuario para aprendizaje",
)
async def register_learning_feedback(
    request: UserFeedbackRequest,
) -> dict[str, Any]:
    try:
        event = learning_feedback_service.capture_user_feedback(
            message=request.mensaje,
            response=request.respuesta,
            helpful=request.util,
            session_id=request.sesion_id,
            intent=request.intencion,
            correction=request.correccion,
        )

        return {
            "registrado": True,
            "estado": event["estado"],
            "mensaje": (
                "Gracias. Usaré esta señal para mejorar futuras "
                "respuestas."
            ),
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/eventos",
    summary="Listar eventos de aprendizaje pendientes o revisados",
)
async def list_learning_events(
    estado: str | None = None,
    limite: int = 100,
) -> dict[str, Any]:
    events = learning_feedback_service.list_events(
        status=estado,
        limit=limite,
    )

    return {
        "total": len(events),
        "eventos": events,
    }


@router.patch(
    "/eventos/{event_id}",
    summary="Aprobar o rechazar un evento de aprendizaje",
)
async def review_learning_event(
    event_id: str,
    request: LearningReviewRequest,
) -> dict[str, Any]:
    try:
        event = learning_feedback_service.update_event_status(
            event_id=event_id,
            status=request.estado,
        )

        return {
            "actualizado": True,
            "evento": event,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

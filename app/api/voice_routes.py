from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.voice_assistant_service import voice_assistant_service


router = APIRouter(
    prefix="/voz",
    tags=["Voz"],
)


class VoiceTranscriptRequest(BaseModel):
    transcripcion: str = Field(
        ...,
        min_length=1,
        max_length=1000,
    )
    sesion_id: str = Field(
        default="voz-general",
        min_length=1,
        max_length=100,
    )


@router.post(
    "/transcripcion",
    summary="Procesar una transcripción de voz",
)
async def process_voice_transcript(
    request: VoiceTranscriptRequest,
) -> dict[str, Any]:
    try:
        return await voice_assistant_service.procesar_transcripcion(
            transcripcion=request.transcripcion,
            sesion_id=request.sesion_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible procesar la voz. "
                f"Detalle: {exc}"
            ),
        ) from exc

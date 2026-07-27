from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.vision_label_service import vision_label_service


router = APIRouter(
    prefix="/vision",
    tags=["Visión artificial"],
)


class LabelAnalysisRequest(BaseModel):
    texto: str = Field(
        ...,
        min_length=1,
        description=(
            "Texto reconocido de una etiqueta mediante OCR "
            "o captura externa."
        ),
    )
    origen: str | None = Field(
        default=None,
        max_length=120,
        description="Nombre del archivo, cámara o fuente del texto.",
    )


@router.post(
    "/etiqueta",
    summary="Analizar texto de etiqueta de medicamento",
)
async def analyze_label(
    request: LabelAnalysisRequest,
) -> dict[str, Any]:
    try:
        return vision_label_service.analizar_etiqueta(
            texto=request.texto,
            origen=request.origen,
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
                "No fue posible analizar la etiqueta. "
                f"Detalle: {exc}"
            ),
        ) from exc

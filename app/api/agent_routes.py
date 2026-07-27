from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.autonomous_agent_service import (
    autonomous_agent_service,
)


router = APIRouter(
    prefix="/agente",
    tags=["Agente autónomo"],
)


class AutonomousCycleRequest(BaseModel):
    autorizar_acciones: bool = Field(
        default=False,
        description=(
            "Si es false, el agente solo planifica. Si es true, "
            "puede ejecutar acciones permitidas."
        ),
    )
    usuario_id: int | None = Field(default=None, ge=1)
    sesion_id: str = Field(
        default="agente-autonomo",
        min_length=1,
        max_length=100,
    )


@router.post(
    "/autonomo/ciclo",
    summary="Ejecutar ciclo del agente autónomo",
)
async def run_autonomous_cycle(
    request: AutonomousCycleRequest,
) -> dict[str, Any]:
    try:
        return autonomous_agent_service.planificar_ciclo(
            autorizar_acciones=request.autorizar_acciones,
            usuario_id=request.usuario_id,
            sesion_id=request.sesion_id,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible ejecutar el ciclo autónomo. "
                f"Detalle: {exc}"
            ),
        ) from exc

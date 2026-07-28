from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.core.permissions import AuthenticatedUser, get_current_user
from app.services.ai_capability_service import ai_capability_service


router = APIRouter(
    prefix="/ia",
    tags=["Capacidades IA para app"],
)


@router.get(
    "/capacidades",
    summary="Listar capacidades IA disponibles para la app",
)
async def get_ai_capabilities(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, Any]:
    return ai_capability_service.obtener_capacidades(current_user)

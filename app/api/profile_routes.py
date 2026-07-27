from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.services.app_profile_service import app_profile_service
from app.repositories.ai_operational_repository import (
    ai_operational_repository,
)


router = APIRouter(
    prefix="/perfil",
    tags=["Perfil de la app"],
)


@router.get(
    "",
    summary="Obtener perfil operativo de la app y la IA",
)
async def get_app_profile() -> dict[str, Any]:
    try:
        return app_profile_service.obtener_perfil()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible obtener el perfil de la app. "
                f"Detalle: {exc}"
            ),
        ) from exc


@router.get(
    "/ia/acciones",
    summary="Listar acciones conversacionales recientes",
)
async def get_ai_actions(
    limite: int = 50,
) -> dict[str, Any]:
    try:
        actions = ai_operational_repository.list_conversational_actions(
            limit=max(1, min(limite, 200))
        )
        return {
            "total": len(actions),
            "acciones": actions,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible obtener acciones IA. "
                f"Detalle: {exc}"
            ),
        ) from exc


@router.get(
    "/ia/predicciones",
    summary="Listar predicciones IA recientes",
)
async def get_ai_predictions(
    limite: int = 50,
) -> dict[str, Any]:
    try:
        predictions = ai_operational_repository.list_inventory_predictions(
            limit=max(1, min(limite, 200))
        )
        return {
            "total": len(predictions),
            "predicciones": predictions,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible obtener predicciones IA. "
                f"Detalle: {exc}"
            ),
        ) from exc

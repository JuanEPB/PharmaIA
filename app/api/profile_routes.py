from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.services.app_profile_service import app_profile_service


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

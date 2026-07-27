from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.services.recommendation_service import recommendation_service


router = APIRouter(
    prefix="/recomendaciones",
    tags=["Recomendaciones automáticas"],
)


@router.get(
    "",
    summary="Obtener recomendaciones automáticas del inventario",
)
async def get_recommendations(
    limite: int = Query(default=10, ge=1, le=50),
) -> dict[str, Any]:
    try:
        return recommendation_service.generar_recomendaciones(
            limite=limite
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible generar recomendaciones. "
                f"Detalle: {exc}"
            ),
        ) from exc

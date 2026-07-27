from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.services.predictive_dashboard_service import (
    predictive_dashboard_service,
)


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard predictivo"],
)


@router.get(
    "/predictivo",
    summary="Obtener dashboard predictivo del inventario",
)
async def get_predictive_dashboard(
    limite: int = Query(
        default=10,
        ge=1,
        le=50,
    ),
) -> dict[str, Any]:
    try:
        return predictive_dashboard_service.obtener_dashboard(
            limite=limite
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible generar el dashboard predictivo. "
                f"Detalle: {exc}"
            ),
        ) from exc

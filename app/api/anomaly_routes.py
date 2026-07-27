from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.services.anomaly_detection_service import (
    anomaly_detection_service,
)


router = APIRouter(
    prefix="/inventario/anomalias",
    tags=["Detección de anomalías"],
)


@router.get(
    "",
    summary="Detectar anomalías en movimientos de inventario",
)
async def get_inventory_anomalies(
    limite: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    try:
        return anomaly_detection_service.detectar_anomalias(
            limite=limite
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible detectar anomalías. "
                f"Detalle: {exc}"
            ),
        ) from exc

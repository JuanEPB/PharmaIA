from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.services.executive_report_service import (
    executive_report_service,
)


router = APIRouter(
    prefix="/reportes",
    tags=["Reportes IA"],
)


@router.get(
    "/ejecutivo",
    summary="Generar reporte ejecutivo IA del inventario",
)
async def get_executive_report(
    limite: int = Query(default=5, ge=1, le=20),
) -> dict[str, Any]:
    try:
        return executive_report_service.generar_reporte(
            limite=limite
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible generar el reporte ejecutivo. "
                f"Detalle: {exc}"
            ),
        ) from exc

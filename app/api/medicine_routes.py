from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.services.inventory_service import inventory_service


router = APIRouter(
    prefix="/api/medicamentos",
    tags=["Medicamentos app"],
)


@router.get(
    "/all",
    summary="Listar medicamentos para appMovil",
)
async def get_all_medicines() -> list[dict[str, Any]]:
    try:
        return inventory_service.obtener_todos()

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible obtener los medicamentos. "
                f"Detalle: {exc}"
            ),
        ) from exc

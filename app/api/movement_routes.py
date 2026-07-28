from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.permissions import AuthenticatedUser, require_permission
from app.schemas import InventoryMovementRequest
from app.services.inventory_movement_service import (
    VALID_MOVEMENT_TYPES,
    inventory_movement_service,
)

router = APIRouter(
    prefix="/inventario/movimientos",
    tags=["Movimientos de inventario"],
)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_inventory_movement(
    request: InventoryMovementRequest,
    current_user: AuthenticatedUser = Depends(
        require_permission("inventory:write")
    ),
) -> dict[str, Any]:
    try:
        return inventory_movement_service.registrar_movimiento(
            medicamento_id=request.medicamento_id,
            tipo=request.tipo,
            cantidad=request.cantidad,
            motivo=request.motivo,
            usuario_id=request.usuario_id or current_user.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"No fue posible registrar el movimiento. Detalle: {exc}") from exc


@router.get("")
async def list_inventory_movements(
    medicamento_id: int | None = Query(default=None, ge=1),
    tipo: str | None = Query(default=None),
    usuario_id: int | None = Query(default=None, ge=1),
    limite: int = Query(default=100, ge=1, le=500),
    pagina: int = Query(default=1, ge=1),
) -> dict[str, Any]:
    try:
        return inventory_movement_service.listar_movimientos(
            medicamento_id=medicamento_id,
            tipo=tipo,
            usuario_id=usuario_id,
            limite=limite,
            pagina=pagina,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"No fue posible consultar los movimientos. Detalle: {exc}") from exc


@router.get("/tipos")
async def get_movement_types() -> dict[str, Any]:
    return {"tipos": sorted(VALID_MOVEMENT_TYPES)}


@router.get("/medicamento/{medicamento_id}")
async def get_medicine_history(
    medicamento_id: int,
    limite: int = Query(default=100, ge=1, le=500),
    pagina: int = Query(default=1, ge=1),
) -> dict[str, Any]:
    try:
        return inventory_movement_service.obtener_historial_medicamento(
            medicamento_id=medicamento_id,
            limite=limite,
            pagina=pagina,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"No fue posible consultar el historial. Detalle: {exc}") from exc


@router.get("/medicamento/{medicamento_id}/ultimo")
async def get_last_medicine_movement(medicamento_id: int) -> dict[str, Any]:
    try:
        return inventory_movement_service.obtener_ultimo_movimiento(medicamento_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"No fue posible consultar el último movimiento. Detalle: {exc}") from exc

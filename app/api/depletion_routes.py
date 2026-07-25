from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.services.depletion_prediction_service import (
    depletion_prediction_service,
)


router = APIRouter(
    prefix="/predicciones/agotamiento",
    tags=["Predicción de agotamiento"],
)


@router.get(
    "/medicamento/{medicamento_id}",
    summary="Predecir agotamiento por ID de medicamento",
)
async def predict_depletion_by_id(
    medicamento_id: int,
) -> dict[str, Any]:
    try:
        return depletion_prediction_service.predecir_medicamento(
            medicamento_id
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible calcular la predicción. "
                f"Detalle: {exc}"
            ),
        ) from exc


@router.get(
    "/buscar",
    summary="Predecir agotamiento por nombre",
)
async def predict_depletion_by_name(
    nombre: str = Query(
        ...,
        min_length=2,
    ),
) -> dict[str, Any]:
    try:
        return depletion_prediction_service.predecir_por_nombre(
            nombre
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible calcular la predicción. "
                f"Detalle: {exc}"
            ),
        ) from exc


@router.get(
    "",
    summary="Consultar predicciones del inventario",
)
async def predict_inventory_depletion(
    solo_riesgo: bool = Query(
        default=True,
    ),
) -> dict[str, Any]:
    try:
        return depletion_prediction_service.predecir_inventario(
            solo_riesgo=solo_riesgo
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible calcular las predicciones. "
                f"Detalle: {exc}"
            ),
        ) from exc

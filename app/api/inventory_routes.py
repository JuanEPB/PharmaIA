from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.services.inventory_statistics_service import (
    inventory_statistics_service,
)
from app.services.stock_alert_report_service import (
    stock_alert_report_service,
)


router = APIRouter(
    prefix="/inventario",
    tags=["Dashboard de inventario"],
)


@router.get(
    "/resumen",
    summary="Obtener resumen general del inventario",
)
async def get_inventory_summary() -> dict[str, Any]:
    try:
        return inventory_statistics_service.obtener_resumen()

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible obtener el resumen del inventario. "
                f"Detalle: {exc}"
            ),
        ) from exc


@router.get(
    "/alertas",
    summary="Obtener alertas inteligentes del inventario",
)
async def get_inventory_alerts(
    limite: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
) -> dict[str, Any]:
    try:
        alerts = inventory_statistics_service.obtener_alertas(
            limite
        )

        return {
            "total": len(alerts),
            "alertas": alerts,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible obtener las alertas. "
                f"Detalle: {exc}"
            ),
        ) from exc


@router.get(
    "/alertas/reporte-bajo-stock",
    summary="Generar reporte imprimible de bajo stock",
)
async def get_low_stock_report(
    limite: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
) -> dict[str, Any]:
    try:
        return stock_alert_report_service.generar_reporte_bajo_stock(
            limite
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible generar el reporte de bajo stock. "
                f"Detalle: {exc}"
            ),
        ) from exc


@router.get(
    "/estadisticas/categorias",
    summary="Obtener estadísticas por categoría",
)
async def get_category_statistics() -> dict[str, Any]:
    try:
        data = inventory_statistics_service.obtener_categorias()

        return {
            "total_categorias": len(data),
            "categorias": data,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible obtener las estadísticas "
                f"por categoría. Detalle: {exc}"
            ),
        ) from exc


@router.get(
    "/estadisticas/proveedores",
    summary="Obtener estadísticas por proveedor",
)
async def get_provider_statistics() -> dict[str, Any]:
    try:
        data = inventory_statistics_service.obtener_proveedores()

        return {
            "total_proveedores": len(data),
            "proveedores": data,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible obtener las estadísticas "
                f"por proveedor. Detalle: {exc}"
            ),
        ) from exc


@router.get(
    "/ranking-stock",
    summary="Obtener medicamentos con mayor y menor stock",
)
async def get_stock_ranking(
    limite: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
) -> dict[str, Any]:
    try:
        return inventory_statistics_service.obtener_ranking_stock(
            limite
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible obtener el ranking de stock. "
                f"Detalle: {exc}"
            ),
        ) from exc

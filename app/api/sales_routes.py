from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from app.core.permissions import AuthenticatedUser, require_permission
from app.services.app_sales_sync_service import app_sales_sync_service
from app.services.pdf_export_service import pdf_export_service


router = APIRouter(
    prefix="/ventas",
    tags=["Ventas"],
)


class AppSaleSyncRequest(BaseModel):
    venta: dict = Field(..., description="Venta local generada por appMovil")
    farmacia: dict | None = Field(
        default=None,
        description="Perfil local de farmacia usado por la app",
    )


@router.post(
    "/sincronizar",
    status_code=status.HTTP_201_CREATED,
    summary="Sincronizar una venta local de la app movil",
)
async def sync_app_sale(request: AppSaleSyncRequest) -> dict:
    try:
        return app_sales_sync_service.sync_sale(
            request.venta,
            request.farmacia,
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
                "No fue posible sincronizar la venta. "
                f"Detalle: {exc}"
            ),
        ) from exc


@router.get(
    "/sincronizadas",
    summary="Listar ventas sincronizadas desde la app movil",
)
async def list_synced_app_sales(limite: int = 20) -> dict:
    return app_sales_sync_service.list_recent(limite)


@router.get(
    "/{venta_id}/ticket.pdf",
    summary="Descargar ticket de venta en PDF",
)
async def download_sale_ticket_pdf(
    venta_id: int,
    current_user: AuthenticatedUser = Depends(
        require_permission("reports:export")
    ),
) -> Response:
    try:
        pdf = pdf_export_service.generar_ticket_venta_pdf(venta_id)
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="ticket-venta-{venta_id}.pdf"'
                )
            },
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
                "No fue posible generar el PDF de la venta. "
                f"Detalle: {exc}"
            ),
        ) from exc

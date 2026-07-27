from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status

from app.services.pdf_export_service import pdf_export_service


router = APIRouter(
    prefix="/ventas",
    tags=["Ventas"],
)


@router.get(
    "/{venta_id}/ticket.pdf",
    summary="Descargar ticket de venta en PDF",
)
async def download_sale_ticket_pdf(venta_id: int) -> Response:
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

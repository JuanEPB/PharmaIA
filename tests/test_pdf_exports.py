from app.services.pdf_export_service import PdfExportService
from app.utils.pdf import build_simple_pdf


def test_build_simple_pdf_returns_pdf_bytes() -> None:
    pdf = build_simple_pdf(
        title="Ticket",
        lines=["Venta #1", "Total $100.00"],
    )

    assert pdf.startswith(b"%PDF-1.4")
    assert b"%%EOF" in pdf


def test_sale_ticket_pdf_contains_pdf_header(monkeypatch) -> None:
    service = PdfExportService()

    monkeypatch.setattr(
        "app.services.pdf_export_service.sales_repository.obtener_venta",
        lambda venta_id: {
            "id": venta_id,
            "fecha": "2026-07-27",
            "total": 100,
            "farmacia_nombre": "Farmacia Demo",
            "usuario_nombre": "Juan",
            "usuario_apellido": "Pina",
        },
    )
    monkeypatch.setattr(
        "app.services.pdf_export_service."
        "sales_repository.obtener_detalle_venta",
        lambda venta_id: [
            {
                "cantidad": 2,
                "precio_unitario": 50,
                "medicamento_nombre": "Paracetamol",
            }
        ],
    )

    pdf = service.generar_ticket_venta_pdf(1)

    assert pdf.startswith(b"%PDF-1.4")

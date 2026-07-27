from app.services.app_sales_sync_service import AppSalesSyncService


def test_sync_sale_persists_local_app_sale(monkeypatch) -> None:
    service = AppSalesSyncService()
    saved_sale = {}

    def fake_upsert(sale):
        saved_sale.update(sale)
        return {
            "id": 7,
            "venta_local_id": sale["venta_local_id"],
            "estado": sale["estado"],
        }

    monkeypatch.setattr(
        "app.services.app_sales_sync_service."
        "app_sales_sync_repository.upsert_sale",
        fake_upsert,
    )

    result = service.sync_sale(
        {
            "_id": "venta-123",
            "fecha": "2026-07-27T10:00:00.000Z",
            "total": 120,
            "usuario": {"nombre": "Ana", "apellido": "Lopez"},
            "detalles": [
                {"medicamento": {"nombre": "Paracetamol"}, "cantidad": 2}
            ],
        },
        {"nombre": "Farmacia Centro"},
    )

    assert result["sincronizada"] is True
    assert result["sync_id"] == 7
    assert saved_sale["venta_local_id"] == "venta-123"
    assert saved_sale["cliente_nombre"] == "Ana Lopez"
    assert saved_sale["farmacia_nombre"] == "Farmacia Centro"


def test_sync_sale_requires_details() -> None:
    service = AppSalesSyncService()

    try:
        service.sync_sale({"_id": "venta-123", "detalles": []})
    except ValueError as exc:
        assert "producto" in str(exc)
    else:
        raise AssertionError("Expected ValueError")

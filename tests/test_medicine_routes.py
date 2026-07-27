import asyncio

from app.api.medicine_routes import get_all_medicines


def test_app_medicines_endpoint_returns_database_medicines(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.medicine_routes.inventory_service.obtener_todos",
        lambda: [
            {
                "id": 1,
                "nombre": "GENOPRAZOL 20 MG CAP",
                "stock": 20,
            }
        ],
    )

    response = asyncio.run(get_all_medicines())

    assert response[0]["nombre"] == "GENOPRAZOL 20 MG CAP"

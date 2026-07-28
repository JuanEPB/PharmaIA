import asyncio

from app.middleware.auth import ApiKeyAuthMiddleware


class FakeSettings:
    AUTH_ENABLED = True
    API_KEYS = {"clave-demo"}
    PUBLIC_PATHS = {"/", "/health", "/docs", "/redoc", "/openapi.json"}


class FakeURL:
    def __init__(self, path: str) -> None:
        self.path = path


class FakeRequest:
    def __init__(
        self,
        path: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.url = FakeURL(path)
        self.headers = headers or {}


async def ok_response(request: FakeRequest):
    return {"status": "ok", "path": request.url.path}


def run_dispatch(
    path: str,
    headers: dict[str, str] | None = None,
):
    middleware = ApiKeyAuthMiddleware(
        app=lambda scope, receive, send: None,
        app_settings=FakeSettings(),
    )

    return asyncio.run(
        middleware.dispatch(
            FakeRequest(path, headers),
            ok_response,
        )
    )


def test_public_path_does_not_require_api_key() -> None:
    response = run_dispatch("/")

    assert response["status"] == "ok"


def test_protected_path_rejects_missing_api_key() -> None:
    response = run_dispatch("/inventario/resumen")

    assert response.status_code == 401


def test_protected_path_accepts_valid_api_key() -> None:
    response = run_dispatch(
        "/inventario/resumen",
        {"X-API-Key": "clave-demo"},
    )

    assert response["status"] == "ok"

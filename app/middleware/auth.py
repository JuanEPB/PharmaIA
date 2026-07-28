from __future__ import annotations

from collections.abc import Callable

from fastapi import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config.settings import Settings, settings


class ApiKeyAuthMiddleware(BaseHTTPMiddleware):
    """Protect API routes with a shared API key when auth is enabled."""

    def __init__(
        self,
        app,
        app_settings: Settings = settings,
    ) -> None:
        super().__init__(app)
        self.settings = app_settings

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        if self._is_public_request(request):
            return await call_next(request)

        if not self.settings.AUTH_ENABLED:
            return await call_next(request)

        if not self.settings.API_KEYS:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "detail": (
                        "Autenticacion habilitada, pero no hay "
                        "API_KEYS configuradas."
                    )
                },
            )

        provided_key = request.headers.get("X-API-Key", "").strip()

        if provided_key not in self.settings.API_KEYS:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "API key invalida o ausente."
                },
            )

        return await call_next(request)

    def _is_public_request(
        self,
        request: Request,
    ) -> bool:
        path = request.url.path.rstrip("/") or "/"

        if path in self.settings.PUBLIC_PATHS:
            return True

        return path.startswith(
            (
                "/docs/",
                "/redoc/",
                "/static/",
            )
        )

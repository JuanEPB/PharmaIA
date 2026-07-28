from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.services.auth_service import AuthenticationError, auth_service


router = APIRouter(
    prefix="/auth",
    tags=["Autenticacion"],
)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=1, max_length=255)


@router.post(
    "/login",
    summary="Iniciar sesion con usuario de base de datos",
)
async def login(
    request: LoginRequest,
) -> dict[str, Any]:
    try:
        return auth_service.login(
            identifier=request.email,
            password=request.password,
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


@router.get(
    "/me",
    summary="Validar token de sesion",
)
async def me(
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    scheme, _, token = str(authorization or "").partition(" ")

    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token bearer requerido.",
        )

    try:
        return {
            "usuario": auth_service.verify_token(token),
        }
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

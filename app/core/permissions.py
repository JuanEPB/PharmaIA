from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status


ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {
        "inventory:read",
        "inventory:write",
        "ai:read",
        "ai:execute",
        "learning:review",
        "reports:export",
    },
    "supervisor": {
        "inventory:read",
        "inventory:write",
        "ai:read",
        "ai:execute",
        "learning:review",
        "reports:export",
    },
    "encargado": {
        "inventory:read",
        "inventory:write",
        "ai:read",
        "ai:execute",
        "reports:export",
    },
    "vendedor": {
        "inventory:read",
        "ai:read",
    },
}


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: int | None
    role: str
    permissions: set[str]

    def can(self, permission: str) -> bool:
        return permission in self.permissions


def build_current_user(
    x_user_id: str | None = None,
    x_user_role: str | None = None,
) -> AuthenticatedUser:
    role = (x_user_role or "admin").strip().lower()

    if role not in ROLE_PERMISSIONS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Rol no permitido: {role}",
        )

    user_id = None
    if x_user_id:
        try:
            user_id = int(x_user_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="X-User-Id debe ser numerico.",
            ) from exc

    return AuthenticatedUser(
        user_id=user_id,
        role=role,
        permissions=set(ROLE_PERMISSIONS[role]),
    )


def get_current_user(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_user_role: str | None = Header(default=None, alias="X-User-Role"),
) -> AuthenticatedUser:
    return build_current_user(
        x_user_id=x_user_id,
        x_user_role=x_user_role,
    )


def require_permission(permission: str):
    async def checker(
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        if not current_user.can(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "El usuario no tiene permiso para esta accion: "
                    f"{permission}"
                ),
            )

        return current_user

    return checker

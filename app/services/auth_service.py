from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.permissions import ROLE_PERMISSIONS
from app.database.connection import get_connection

try:
    import bcrypt
except ImportError:  # pragma: no cover - depends on installed environment
    bcrypt = None


ROLE_MAP = {
    "admin": "admin",
    "supervisor": "supervisor",
    "encargado": "encargado",
    "vendedor": "vendedor",
    "usuario": "vendedor",
}


class AuthenticationError(ValueError):
    pass


class AuthService:
    TOKEN_TTL_MINUTES = 8 * 60

    def login(
        self,
        identifier: str,
        password: str,
    ) -> dict[str, Any]:
        clean_identifier = str(identifier or "").strip().lower()

        if not clean_identifier or not password:
            raise AuthenticationError("Correo y contrasena son obligatorios.")

        user = self._find_user(clean_identifier)

        if not user:
            raise AuthenticationError("Usuario o contrasena incorrectos.")

        stored_password = self._get_password_value(user)

        if not self._verify_password(password, stored_password):
            raise AuthenticationError("Usuario o contrasena incorrectos.")

        role = self._normalize_role(user.get("rol"))
        token = self._create_token(user_id=user.get("id"), role=role)

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": self.TOKEN_TTL_MINUTES * 60,
            "usuario": {
                "id": user.get("id"),
                "nombre": user.get("nombre"),
                "apellido": user.get("apellido"),
                "email": user.get("email"),
                "rol": role,
                "permisos": sorted(ROLE_PERMISSIONS[role]),
            },
            "headers_recomendados": {
                "Authorization": f"Bearer {token}",
                "X-User-Id": str(user.get("id")),
                "X-User-Role": role,
            },
        }

    def verify_token(
        self,
        token: str,
    ) -> dict[str, Any]:
        try:
            payload_part, signature = token.split(".", 1)
        except ValueError as exc:
            raise AuthenticationError("Token invalido.") from exc

        expected_signature = self._sign(payload_part)

        if not secrets.compare_digest(signature, expected_signature):
            raise AuthenticationError("Token invalido.")

        try:
            payload_json = base64.urlsafe_b64decode(
                self._pad_base64(payload_part)
            ).decode("utf-8")
            payload = json.loads(payload_json)
        except Exception as exc:
            raise AuthenticationError("Token invalido.") from exc

        expires_at = int(payload.get("exp") or 0)

        if expires_at < int(datetime.now(timezone.utc).timestamp()):
            raise AuthenticationError("Token expirado.")

        role = self._normalize_role(payload.get("role"))

        return {
            "id": payload.get("sub"),
            "rol": role,
            "permisos": sorted(ROLE_PERMISSIONS[role]),
        }

    def _find_user(
        self,
        identifier: str,
    ) -> dict[str, Any] | None:
        with get_connection() as connection:
            cursor = connection.cursor(dictionary=True)

            try:
                cursor.execute(
                    """
                    SELECT *
                    FROM usuarios
                    WHERE LOWER(email) = %s
                    LIMIT 1
                    """,
                    (identifier,),
                )
                return cursor.fetchone()
            finally:
                cursor.close()

    @staticmethod
    def _get_password_value(
        user: dict[str, Any],
    ) -> str:
        for column, value in user.items():
            normalized = str(column).lower()

            if normalized.startswith("contrase") or normalized in {
                "password",
                "contrasena",
                "clave",
            }:
                return str(value or "")

        return ""

    @staticmethod
    def _verify_password(
        plain_password: str,
        stored_password: str,
    ) -> bool:
        stored_password = str(stored_password or "").strip()

        if not stored_password:
            return False

        if stored_password.startswith(("$2a$", "$2b$", "$2y$")):
            if bcrypt is None:
                raise AuthenticationError(
                    "El servidor necesita instalar bcrypt para validar "
                    "esta contrasena."
                )

            return bool(
                bcrypt.checkpw(
                    plain_password.encode("utf-8"),
                    stored_password.encode("utf-8"),
                )
            )

        sha256_password = hashlib.sha256(
            plain_password.encode("utf-8")
        ).hexdigest()

        return secrets.compare_digest(sha256_password, stored_password)

    @staticmethod
    def _normalize_role(
        role: Any,
    ) -> str:
        normalized = str(role or "vendedor").strip().lower()
        mapped_role = ROLE_MAP.get(normalized, normalized)

        if mapped_role not in ROLE_PERMISSIONS:
            return "vendedor"

        return mapped_role

    def _create_token(
        self,
        user_id: Any,
        role: str,
    ) -> str:
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=self.TOKEN_TTL_MINUTES
        )
        payload = {
            "sub": user_id,
            "role": role,
            "exp": int(expires_at.timestamp()),
        }
        payload_json = json.dumps(
            payload,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
        payload_part = base64.urlsafe_b64encode(payload_json).decode(
            "ascii"
        ).rstrip("=")

        return f"{payload_part}.{self._sign(payload_part)}"

    def _sign(
        self,
        payload_part: str,
    ) -> str:
        secret = self._token_secret()
        digest = hmac.new(
            secret.encode("utf-8"),
            payload_part.encode("ascii"),
            hashlib.sha256,
        ).digest()

        return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

    @staticmethod
    def _token_secret() -> str:
        return (
            os.getenv("AUTH_TOKEN_SECRET")
            or os.getenv("API_KEYS", "")
            or "pharma-neural-development-secret"
        )

    @staticmethod
    def _pad_base64(
        value: str,
    ) -> bytes:
        return (value + "=" * (-len(value) % 4)).encode("ascii")


auth_service = AuthService()

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta
from threading import RLock
from typing import Any

from app.repositories.ai_operational_repository import (
    ai_operational_repository,
)


class ConversationMemory:
    """
    Memoria conversacional temporal almacenada en RAM.

    La memoria se identifica mediante sesion_id y conserva:
    - último medicamento consultado;
    - última intención;
    - último mensaje;
    - última respuesta;
    - fecha de actualización.

    Esta implementación es adecuada para desarrollo y pruebas.

    Para producción se recomienda sustituirla por Redis o una base
    de datos persistente.
    """

    def __init__(self, expiration_minutes: int = 60) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}
        self._expiration = timedelta(minutes=expiration_minutes)
        self._lock = RLock()

    @staticmethod
    def _normalize_session_id(session_id: str) -> str:
        return str(session_id or "").strip()

    @staticmethod
    def _now() -> datetime:
        return datetime.now()

    def _is_expired(self, session: dict[str, Any]) -> bool:
        updated_at = session.get("_updated_at")

        if not isinstance(updated_at, datetime):
            return True

        return self._now() - updated_at > self._expiration

    def _remove_expired_sessions(self) -> None:
        expired_session_ids = [
            session_id
            for session_id, session in self._sessions.items()
            if self._is_expired(session)
        ]

        for session_id in expired_session_ids:
            self._sessions.pop(session_id, None)

    def get(self, session_id: str) -> dict[str, Any]:
        normalized_id = self._normalize_session_id(session_id)

        if not normalized_id:
            return {}

        with self._lock:
            self._remove_expired_sessions()

            session = self._sessions.get(normalized_id)

            if not session:
                try:
                    return ai_operational_repository.get_conversation_memory(
                        normalized_id
                    )
                except Exception:
                    return {}

            public_session = {
                key: value
                for key, value in session.items()
                if not key.startswith("_")
            }

            return deepcopy(public_session)

    def update(
        self,
        session_id: str,
        **values: Any,
    ) -> dict[str, Any]:
        normalized_id = self._normalize_session_id(session_id)

        if not normalized_id:
            raise ValueError(
                "El identificador de sesión no puede estar vacío."
            )

        with self._lock:
            self._remove_expired_sessions()

            session = self._sessions.get(normalized_id, {})

            for key, value in values.items():
                if value is not None:
                    session[key] = value

            session["_updated_at"] = self._now()
            self._sessions[normalized_id] = session

            public_session = {
                key: value
                for key, value in session.items()
                if not key.startswith("_")
            }

        try:
            ai_operational_repository.upsert_conversation_memory(
                normalized_id,
                public_session,
            )
        except Exception:
            pass

        return deepcopy(public_session)

    def delete(self, session_id: str) -> bool:
        normalized_id = self._normalize_session_id(session_id)

        if not normalized_id:
            return False

        with self._lock:
            deleted = self._sessions.pop(normalized_id, None) is not None

        try:
            deleted = (
                ai_operational_repository.delete_conversation_memory(
                    normalized_id
                )
                or deleted
            )
        except Exception:
            pass

        return deleted

    def clear(self) -> None:
        with self._lock:
            self._sessions.clear()

    def count(self) -> int:
        with self._lock:
            self._remove_expired_sessions()
            return len(self._sessions)


conversation_memory = ConversationMemory(
    expiration_minutes=60,
)

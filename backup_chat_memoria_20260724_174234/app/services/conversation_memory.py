from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta
from threading import RLock
from typing import Any


class ConversationMemory:
    """
    Memoria conversacional temporal almacenada en memoria RAM.

    Cada sesión puede conservar:
    - Último medicamento consultado.
    - Última intención detectada.
    - Última respuesta.
    - Datos adicionales de contexto.
    """

    def __init__(self, expiration_minutes: int = 60) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}
        self._expiration = timedelta(minutes=expiration_minutes)
        self._lock = RLock()

    def _now(self) -> datetime:
        return datetime.now()

    def _is_expired(self, session: dict[str, Any]) -> bool:
        updated_at = session.get("updated_at")

        if not isinstance(updated_at, datetime):
            return True

        return self._now() - updated_at > self._expiration

    def _clean_expired_sessions(self) -> None:
        expired_ids = [
            session_id
            for session_id, session in self._sessions.items()
            if self._is_expired(session)
        ]

        for session_id in expired_ids:
            self._sessions.pop(session_id, None)

    def get(self, session_id: str) -> dict[str, Any]:
        normalized_id = str(session_id or "").strip()

        if not normalized_id:
            return {}

        with self._lock:
            self._clean_expired_sessions()

            session = self._sessions.get(normalized_id)

            if not session:
                return {}

            return deepcopy(
                {
                    key: value
                    for key, value in session.items()
                    if key != "updated_at"
                }
            )

    def update(self, session_id: str, **values: Any) -> dict[str, Any]:
        normalized_id = str(session_id or "").strip()

        if not normalized_id:
            raise ValueError("El identificador de sesión es obligatorio.")

        with self._lock:
            self._clean_expired_sessions()

            current = self._sessions.get(normalized_id, {})

            for key, value in values.items():
                if value is not None:
                    current[key] = value

            current["updated_at"] = self._now()
            self._sessions[normalized_id] = current

            return self.get(normalized_id)

    def delete(self, session_id: str) -> bool:
        normalized_id = str(session_id or "").strip()

        if not normalized_id:
            return False

        with self._lock:
            return self._sessions.pop(normalized_id, None) is not None

    def clear(self) -> None:
        with self._lock:
            self._sessions.clear()

    def count(self) -> int:
        with self._lock:
            self._clean_expired_sessions()
            return len(self._sessions)


conversation_memory = ConversationMemory(expiration_minutes=60)

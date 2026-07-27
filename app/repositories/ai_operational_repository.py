from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.repositories.database_adapter import create_connection


def _json_default(value: Any) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return str(value)

    return str(value)


def to_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        default=_json_default,
    )


def from_json(value: Any) -> Any:
    if value in (None, ""):
        return None

    if isinstance(value, (dict, list)):
        return value

    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return None


class AIOperationalRepository:
    @staticmethod
    def _cursor(connection: Any) -> Any:
        try:
            return connection.cursor(dictionary=True)
        except TypeError:
            return connection.cursor()

    @staticmethod
    def _row_to_dict(cursor: Any, row: Any) -> dict[str, Any]:
        if row is None:
            return {}

        if isinstance(row, dict):
            return row

        description = getattr(cursor, "description", None)

        if not description:
            return {}

        columns = [column[0] for column in description]
        return dict(zip(columns, row))

    def get_conversation_memory(self, session_id: str) -> dict[str, Any]:
        connection = create_connection()
        cursor = self._cursor(connection)

        try:
            cursor.execute(
                """
                SELECT contexto
                FROM ia_memoria_conversacion
                WHERE sesion_id = %s
                LIMIT 1
                """,
                (session_id,),
            )
            row = self._row_to_dict(cursor, cursor.fetchone())
            context = from_json(row.get("contexto"))
            return context if isinstance(context, dict) else {}
        finally:
            cursor.close()
            connection.close()

    def upsert_conversation_memory(
        self,
        session_id: str,
        context: dict[str, Any],
    ) -> None:
        connection = create_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO ia_memoria_conversacion (
                    sesion_id,
                    contexto,
                    ultimo_mensaje,
                    ultima_respuesta
                )
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    contexto = VALUES(contexto),
                    ultimo_mensaje = VALUES(ultimo_mensaje),
                    ultima_respuesta = VALUES(ultima_respuesta),
                    actualizado_en = CURRENT_TIMESTAMP
                """,
                (
                    session_id,
                    to_json(context),
                    context.get("ultimo_mensaje"),
                    context.get("ultima_respuesta"),
                ),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def delete_conversation_memory(self, session_id: str) -> bool:
        connection = create_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                DELETE FROM ia_memoria_conversacion
                WHERE sesion_id = %s
                """,
                (session_id,),
            )
            deleted = cursor.rowcount > 0
            connection.commit()
            return deleted
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def save_learning_feedback(self, event: dict[str, Any]) -> None:
        connection = create_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO ia_feedback_aprendizaje (
                    evento_id,
                    sesion_id,
                    pregunta,
                    respuesta,
                    intencion_detectada,
                    intencion_esperada,
                    calificacion,
                    comentario,
                    estado,
                    metadatos
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    respuesta = VALUES(respuesta),
                    intencion_detectada = VALUES(intencion_detectada),
                    intencion_esperada = VALUES(intencion_esperada),
                    calificacion = VALUES(calificacion),
                    comentario = VALUES(comentario),
                    estado = VALUES(estado),
                    metadatos = VALUES(metadatos),
                    actualizado_en = CURRENT_TIMESTAMP
                """,
                (
                    event.get("id"),
                    event.get("sesion_id"),
                    event.get("mensaje"),
                    event.get("respuesta"),
                    event.get("intencion")
                    or event.get("intencion_detectada"),
                    event.get("correccion"),
                    1 if event.get("util") is True else 0,
                    event.get("correccion"),
                    self._map_learning_status(
                        str(event.get("estado") or "")
                    ),
                    to_json(event),
                ),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def update_learning_feedback_status(
        self,
        event_id: str,
        status: str,
    ) -> None:
        connection = create_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                UPDATE ia_feedback_aprendizaje
                SET estado = %s,
                    actualizado_en = CURRENT_TIMESTAMP
                WHERE evento_id = %s
                """,
                (
                    self._map_learning_status(status),
                    event_id,
                ),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def save_conversational_action(
        self,
        *,
        session_id: str,
        action_type: str,
        status: str,
        parameters: dict[str, Any] | None = None,
        result: dict[str, Any] | None = None,
        user_id: int | None = None,
        error_message: str | None = None,
    ) -> None:
        connection = create_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO ia_acciones_conversacionales (
                    sesion_id,
                    usuario_id,
                    tipo_accion,
                    estado,
                    parametros,
                    resultado,
                    mensaje_error
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    session_id,
                    user_id,
                    action_type,
                    status,
                    to_json(parameters or {}),
                    to_json(result or {}),
                    error_message,
                ),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def _map_learning_status(status: str) -> str:
        mapping = {
            "pendiente_revision": "PENDIENTE_REVISION",
            "aprobado_para_entrenamiento": "APROBADO",
            "rechazado": "DESCARTADO",
            "revisado": "REVISADO",
        }
        return mapping.get(status.lower(), "PENDIENTE_REVISION")


ai_operational_repository = AIOperationalRepository()

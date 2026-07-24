from __future__ import annotations

import inspect
import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.services.conversation_memory import conversation_memory


class ConversationService:
    """
    Orquestador de conversaciones con memoria temporal.

    Este servicio intenta reutilizar el AssistantService existente sin
    depender de un nombre único para su método principal.
    """

    FOLLOW_UP_PATTERNS = {
        "stock": (
            "cuanto stock",
            "cuánto stock",
            "que stock",
            "qué stock",
            "existencia",
            "existencias",
            "cuantos quedan",
            "cuántos quedan",
            "cuantas unidades",
            "cuántas unidades",
        ),
        "caducidad": (
            "cuando caduca",
            "cuándo caduca",
            "fecha de caducidad",
            "caducidad",
            "cuando vence",
            "cuándo vence",
            "esta caducado",
            "está caducado",
            "esta vencido",
            "está vencido",
        ),
        "precio": (
            "cuanto cuesta",
            "cuánto cuesta",
            "precio",
            "que precio",
            "qué precio",
            "costo",
        ),
        "proveedor": (
            "quien lo provee",
            "quién lo provee",
            "proveedor",
            "quien es su proveedor",
            "quién es su proveedor",
            "de quien viene",
            "de quién viene",
        ),
        "categoria": (
            "categoria",
            "categoría",
            "de que categoria",
            "de qué categoría",
            "a que categoria",
            "a qué categoría",
        ),
        "lote": (
            "lote",
            "cual es su lote",
            "cuál es su lote",
            "numero de lote",
            "número de lote",
        ),
        "detalle": (
            "dame los detalles",
            "muestra los detalles",
            "informacion completa",
            "información completa",
            "dime todo",
            "más información",
            "mas informacion",
        ),
    }

    MEDICINE_KEYS = (
        "medicamento",
        "medicine",
        "producto",
        "nombre",
        "name",
    )

    def __init__(self) -> None:
        self.assistant = self._build_assistant()

    def _build_assistant(self) -> Any:
        try:
            from app.services.assistant_service import AssistantService

            return AssistantService()
        except Exception as exc:
            raise RuntimeError(
                f"No fue posible inicializar AssistantService: {exc}"
            ) from exc

    @staticmethod
    def _normalize(value: Any) -> str:
        text = str(value or "").strip().lower()
        text = unicodedata.normalize("NFD", text)
        return "".join(
            character
            for character in text
            if unicodedata.category(character) != "Mn"
        )

    @staticmethod
    def _serialize(value: Any) -> Any:
        if isinstance(value, (date, datetime)):
            return value.isoformat()

        if isinstance(value, Decimal):
            return float(value)

        if isinstance(value, dict):
            return {
                key: ConversationService._serialize(item)
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple, set)):
            return [
                ConversationService._serialize(item)
                for item in value
            ]

        return value

    def _detect_follow_up(self, message: str) -> str | None:
        normalized = self._normalize(message)

        for intent, patterns in self.FOLLOW_UP_PATTERNS.items():
            if any(self._normalize(pattern) in normalized for pattern in patterns):
                return intent

        return None

    def _looks_like_follow_up(self, message: str) -> bool:
        normalized = self._normalize(message)

        references = (
            "lo ",
            "la ",
            "su ",
            "ese ",
            "esa ",
            "este ",
            "esta ",
            "el medicamento",
            "y cuanto",
            "y cuando",
            "y quien",
            "y cual",
            "y qué",
            "y que",
        )

        return (
            self._detect_follow_up(message) is not None
            or normalized.startswith(references)
        )

    def _extract_medicine_from_value(self, value: Any) -> str | None:
        if isinstance(value, dict):
            for key in self.MEDICINE_KEYS:
                candidate = value.get(key)

                if isinstance(candidate, str) and candidate.strip():
                    return candidate.strip()

            for nested_value in value.values():
                result = self._extract_medicine_from_value(nested_value)

                if result:
                    return result

        if isinstance(value, list):
            for item in value:
                result = self._extract_medicine_from_value(item)

                if result:
                    return result

        return None

    def _extract_medicine_from_response(self, response: Any) -> str | None:
        result = self._extract_medicine_from_value(response)

        if result:
            return result

        if isinstance(response, str):
            patterns = (
                r"medicamento\s*[:\-]\s*([A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 .\-]+)",
                r"producto\s*[:\-]\s*([A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 .\-]+)",
            )

            for pattern in patterns:
                match = re.search(pattern, response, flags=re.IGNORECASE)

                if match:
                    candidate = match.group(1).strip(" .,-")

                    if candidate:
                        return candidate

        return None

    def _find_callable(self) -> Any:
        method_names = (
            "procesar_consulta",
            "procesar_mensaje",
            "responder",
            "chat",
            "process",
            "process_message",
            "handle_message",
        )

        for method_name in method_names:
            method = getattr(self.assistant, method_name, None)

            if callable(method):
                return method

        if callable(self.assistant):
            return self.assistant

        raise RuntimeError(
            "AssistantService no contiene un método compatible. "
            "Se esperaba procesar_consulta(), procesar_mensaje(), "
            "responder(), chat() o process()."
        )

    async def _call_assistant(self, message: str) -> Any:
        method = self._find_callable()
        result = method(message)

        if inspect.isawaitable(result):
            result = await result

        return result

    async def _answer_follow_up(
        self,
        message: str,
        medicine: str,
        follow_up_intent: str,
    ) -> Any:
        prompts = {
            "stock": f"¿Cuánto stock tiene el medicamento {medicine}?",
            "caducidad": f"¿Cuándo caduca el medicamento {medicine}?",
            "precio": f"¿Cuál es el precio del medicamento {medicine}?",
            "proveedor": f"¿Quién es el proveedor del medicamento {medicine}?",
            "categoria": f"¿Cuál es la categoría del medicamento {medicine}?",
            "lote": f"¿Cuál es el lote del medicamento {medicine}?",
            "detalle": f"Muéstrame toda la información del medicamento {medicine}.",
        }

        contextual_message = prompts.get(
            follow_up_intent,
            f"{message} El medicamento del que hablamos es {medicine}.",
        )

        return await self._call_assistant(contextual_message)

    async def chat(self, message: str, session_id: str) -> dict[str, Any]:
        clean_message = str(message or "").strip()
        clean_session_id = str(session_id or "").strip()

        if not clean_message:
            raise ValueError("El mensaje no puede estar vacío.")

        if not clean_session_id:
            raise ValueError("El identificador de sesión es obligatorio.")

        context = conversation_memory.get(clean_session_id)
        last_medicine = context.get("ultimo_medicamento")
        follow_up_intent = self._detect_follow_up(clean_message)

        if (
            last_medicine
            and self._looks_like_follow_up(clean_message)
            and follow_up_intent
        ):
            assistant_response = await self._answer_follow_up(
                message=clean_message,
                medicine=last_medicine,
                follow_up_intent=follow_up_intent,
            )
        else:
            assistant_response = await self._call_assistant(clean_message)

        serialized_response = self._serialize(assistant_response)

        detected_medicine = self._extract_medicine_from_response(
            serialized_response
        )

        effective_medicine = detected_medicine or last_medicine

        updated_context = conversation_memory.update(
            clean_session_id,
            ultimo_mensaje=clean_message,
            ultima_intencion=follow_up_intent,
            ultimo_medicamento=effective_medicine,
            ultima_respuesta=serialized_response,
        )

        return {
            "respuesta": serialized_response,
            "sesion_id": clean_session_id,
            "contexto": updated_context,
        }

    def get_context(self, session_id: str) -> dict[str, Any]:
        return conversation_memory.get(session_id)

    def delete_context(self, session_id: str) -> bool:
        return conversation_memory.delete(session_id)


conversation_service = ConversationService()

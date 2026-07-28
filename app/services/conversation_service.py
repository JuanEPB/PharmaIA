from __future__ import annotations

import inspect
import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable

from app.services.conversation_memory import conversation_memory


class ConversationService:
    """
    Integra el AssistantService existente con memoria conversacional.

    El servicio no reemplaza la lógica actual de inteligencia artificial.
    Únicamente agrega contexto a las preguntas de seguimiento.
    """

    FOLLOW_UP_PATTERNS: dict[str, tuple[str, ...]] = {
        "stock": (
            "cuanto stock",
            "que stock tiene",
            "cuantos quedan",
            "cuantas quedan",
            "cuantas unidades",
            "existencia",
            "existencias",
            "disponibles",
            "hay disponibles",
        ),
        "caducidad": (
            "cuando caduca",
            "cuando vence",
            "fecha de caducidad",
            "caducidad",
            "vencimiento",
            "esta caducado",
            "esta vencido",
        ),
        "precio": (
            "cuanto cuesta",
            "que precio tiene",
            "cual es su precio",
            "precio",
            "costo",
        ),
        "proveedor": (
            "quien lo provee",
            "quien la provee",
            "quien es el proveedor",
            "cual es el proveedor",
            "proveedor",
            "de quien viene",
        ),
        "categoria": (
            "de que categoria",
            "cual es su categoria",
            "categoria",
            "tipo de medicamento",
        ),
        "lote": (
            "cual es el lote",
            "numero de lote",
            "que lote tiene",
            "lote",
        ),
        "detalle": (
            "dame los detalles",
            "muestra los detalles",
            "informacion completa",
            "dime todo",
            "mas informacion",
            "todos sus datos",
        ),
    }

    REFERENCE_WORDS = (
        "lo",
        "la",
        "el",
        "ese",
        "esa",
        "este",
        "esta",
        "su",
        "del mismo",
        "de ese",
        "de esa",
        "y cuanto",
        "y cuando",
        "y quien",
        "y cual",
        "y el",
        "y la",
    )

    MEDICINE_KEYS = (
        "medicamento",
        "nombre_medicamento",
        "producto",
        "nombre",
        "medicine",
        "name",
    )

    ASSISTANT_METHOD_NAMES = (
        "procesar_consulta",
        "procesar_mensaje",
        "procesar",
        "responder",
        "chat",
        "process_message",
        "process",
        "handle_message",
        "handle",
    )

    def __init__(self) -> None:
        self.assistant = self._create_assistant()

    @staticmethod
    def _create_assistant() -> Any:
        try:
            from app.services.assistant_service import AssistantService

            return AssistantService()

        except Exception as exc:
            raise RuntimeError(
                "No fue posible inicializar AssistantService. "
                f"Detalle: {exc}"
            ) from exc

    @staticmethod
    def normalize(value: Any) -> str:
        text = str(value or "").strip().lower()
        normalized = unicodedata.normalize("NFD", text)

        return "".join(
            character
            for character in normalized
            if unicodedata.category(character) != "Mn"
        )

    @classmethod
    def serialize(cls, value: Any) -> Any:
        if isinstance(value, (date, datetime)):
            return value.isoformat()

        if isinstance(value, Decimal):
            return float(value)

        if isinstance(value, dict):
            return {
                str(key): cls.serialize(item)
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple, set)):
            return [
                cls.serialize(item)
                for item in value
            ]

        return value

    def _find_assistant_method(self) -> Callable[..., Any]:
        for method_name in self.ASSISTANT_METHOD_NAMES:
            method = getattr(self.assistant, method_name, None)

            if callable(method):
                return method

        if callable(self.assistant):
            return self.assistant

        raise RuntimeError(
            "AssistantService no tiene un método principal compatible. "
            "Se esperaba uno de estos métodos: "
            + ", ".join(self.ASSISTANT_METHOD_NAMES)
        )

    async def _execute_assistant(self, message: str) -> Any:
        method = self._find_assistant_method()

        result = method(message)

        if inspect.isawaitable(result):
            result = await result

        return result

    def _detect_follow_up_intent(
        self,
        message: str,
    ) -> str | None:
        normalized_message = self.normalize(message)

        for intent, patterns in self.FOLLOW_UP_PATTERNS.items():
            for pattern in patterns:
                if self.normalize(pattern) in normalized_message:
                    return intent

        return None

    def _contains_reference(
        self,
        message: str,
    ) -> bool:
        normalized_message = self.normalize(message)

        words = set(
            re.findall(
                r"[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]+",
                normalized_message,
            )
        )

        for reference in self.REFERENCE_WORDS:
            normalized_reference = self.normalize(reference)

            if " " in normalized_reference:
                if normalized_reference in normalized_message:
                    return True
            elif normalized_reference in words:
                return True

        return normalized_message.startswith("y ")

    def _extract_medicine_from_dict(
        self,
        value: dict[str, Any],
    ) -> str | None:
        for key in ("entidades", "datos"):
            nested_value = value.get(key)
            medicine = self._extract_medicine(nested_value)

            if medicine:
                return medicine

        for key in self.MEDICINE_KEYS:
            candidate = value.get(key)

            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()

        for nested_key, nested_value in value.items():
            if nested_key in {"respuesta", "mensaje"}:
                continue

            medicine = self._extract_medicine(nested_value)

            if medicine:
                return medicine

        return None

    def _extract_medicine_from_text(
        self,
        text: str,
    ) -> str | None:
        patterns = (
            r"(?:medicamento|producto|nombre)\s*[:\-]\s*"
            r"([A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 .\-]{1,80})",
            r"(?:información|informacion|datos)\s+(?:de|del)\s+"
            r"([A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 .\-]{1,80})",
            r"(?:stock|existencia|existencias|precio|caducidad|vence|"
            r"lote|proveedor|categoria|categoría)\s+(?:de|del|tiene|"
            r"para)?\s*"
            r"([A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 .\-]{1,80})",
            r"(?:cuanto|cuánto|cuando|cuándo|cual|cuál|quien|quién)\s+"
            r"(?:stock|precio|caduca|vence|lote|proveedor|categoria|"
            r"categoría)\s+(?:tiene|de|del|es|para)?\s*"
            r"([A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 .\-]{1,80})",
        )

        for pattern in patterns:
            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if not match:
                continue

            medicine = match.group(1).strip(" .,:;-")

            stop_words = (
                "stock",
                "precio",
                "caducidad",
                "proveedor",
                "categoria",
                "categoría",
                "lote",
            )

            for stop_word in stop_words:
                medicine = re.split(
                    rf"\b{re.escape(stop_word)}\b",
                    medicine,
                    maxsplit=1,
                    flags=re.IGNORECASE,
                )[0].strip()

            if medicine:
                return medicine

        return None

    def _extract_medicine(
        self,
        value: Any,
    ) -> str | None:
        if isinstance(value, dict):
            return self._extract_medicine_from_dict(value)

        if isinstance(value, (list, tuple)):
            for item in value:
                medicine = self._extract_medicine(item)

                if medicine:
                    return medicine

        if isinstance(value, str):
            return self._extract_medicine_from_text(value)

        return None

    def _build_contextual_message(
        self,
        original_message: str,
        medicine: str,
        follow_up_intent: str,
    ) -> str:
        prompts = {
            "stock": (
                f"¿Cuánto stock tiene el medicamento {medicine}?"
            ),
            "caducidad": (
                f"¿Cuándo caduca el medicamento {medicine}?"
            ),
            "precio": (
                f"¿Cuál es el precio del medicamento {medicine}?"
            ),
            "proveedor": (
                f"¿Quién es el proveedor del medicamento {medicine}?"
            ),
            "categoria": (
                f"¿Cuál es la categoría del medicamento {medicine}?"
            ),
            "lote": (
                f"¿Cuál es el lote del medicamento {medicine}?"
            ),
            "detalle": (
                f"Muéstrame toda la información del medicamento {medicine}."
            ),
        }

        return prompts.get(
            follow_up_intent,
            (
                f"{original_message}. "
                f"El medicamento del contexto actual es {medicine}."
            ),
        )

    async def chat(
        self,
        message: str,
        session_id: str,
    ) -> dict[str, Any]:
        clean_message = str(message or "").strip()
        clean_session_id = str(session_id or "").strip()

        if not clean_message:
            raise ValueError(
                "El mensaje no puede estar vacío."
            )

        if not clean_session_id:
            raise ValueError(
                "El identificador de sesión es obligatorio."
            )

        previous_context = conversation_memory.get(
            clean_session_id
        )

        previous_medicine = previous_context.get(
            "ultimo_medicamento"
        )

        follow_up_intent = self._detect_follow_up_intent(
            clean_message
        )

        has_reference = self._contains_reference(
            clean_message
        )

        used_memory = bool(
            previous_medicine
            and follow_up_intent
            and (
                has_reference
                or len(clean_message.split()) <= 7
            )
        )

        effective_message = clean_message
        explicit_medicine = self._extract_medicine_from_text(
            clean_message
        )

        if used_memory:
            effective_message = self._build_contextual_message(
                original_message=clean_message,
                medicine=previous_medicine,
                follow_up_intent=follow_up_intent,
            )
        elif follow_up_intent and explicit_medicine:
            effective_message = self._build_contextual_message(
                original_message=clean_message,
                medicine=explicit_medicine,
                follow_up_intent=follow_up_intent,
            )

        assistant_result = await self._execute_assistant(
            effective_message
        )

        serialized_result = self.serialize(
            assistant_result
        )

        detected_medicine = self._extract_medicine(
            serialized_result
        )

        effective_medicine = (
            detected_medicine
            or previous_medicine
        )

        updated_context = conversation_memory.update(
            clean_session_id,
            ultimo_mensaje=clean_message,
            ultimo_mensaje_procesado=effective_message,
            ultima_intencion=follow_up_intent,
            ultimo_medicamento=effective_medicine,
            ultima_respuesta=serialized_result,
        )

        return {
            "respuesta": serialized_result,
            "sesion_id": clean_session_id,
            "memoria_utilizada": used_memory,
            "contexto": updated_context,
        }

    def get_context(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        return conversation_memory.get(session_id)

    def delete_context(
        self,
        session_id: str,
    ) -> bool:
        return conversation_memory.delete(session_id)


conversation_service = ConversationService()

from __future__ import annotations

from typing import Any

from app.services.conversation_service import conversation_service


class VoiceAssistantService:
    @staticmethod
    def _clean_transcript(transcript: str) -> str:
        return " ".join(
            str(transcript or "").strip().split()
        )

    @staticmethod
    def _extract_speakable_text(result: dict[str, Any]) -> str:
        response = result.get("respuesta")

        if isinstance(response, str):
            return response

        if isinstance(response, dict):
            nested = response.get("respuesta")
            if isinstance(nested, str):
                return nested

        return (
            "Tu solicitud fue procesada. Revisa los detalles "
            "en la respuesta del sistema."
        )

    async def procesar_transcripcion(
        self,
        transcripcion: str,
        sesion_id: str,
    ) -> dict[str, Any]:
        clean_transcript = self._clean_transcript(
            transcripcion
        )

        if not clean_transcript:
            raise ValueError(
                "La transcripción no puede estar vacía."
            )

        result = await conversation_service.chat(
            message=clean_transcript,
            session_id=sesion_id,
        )

        speakable_text = self._extract_speakable_text(
            result
        )

        return {
            "transcripcion": clean_transcript,
            "sesion_id": sesion_id,
            "respuesta_texto": speakable_text,
            "tts_sugerido": {
                "idioma": "es-MX",
                "texto": speakable_text,
            },
            "resultado": result,
        }


voice_assistant_service = VoiceAssistantService()

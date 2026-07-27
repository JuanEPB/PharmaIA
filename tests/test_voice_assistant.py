from unittest.mock import AsyncMock, patch

import pytest

from app.services.voice_assistant_service import VoiceAssistantService


@pytest.mark.anyio
async def test_voice_transcript_returns_tts_payload() -> None:
    service = VoiceAssistantService()

    with patch(
        "app.services.voice_assistant_service."
        "conversation_service.chat",
        new=AsyncMock(
            return_value={
                "respuesta": {
                    "respuesta": "Hay 2 medicamentos con bajo stock."
                }
            }
        ),
    ):
        result = await service.procesar_transcripcion(
            transcripcion="  medicamentos con bajo stock  ",
            sesion_id="voz-1",
        )

    assert result["transcripcion"] == "medicamentos con bajo stock"
    assert result["respuesta_texto"] == "Hay 2 medicamentos con bajo stock."
    assert result["tts_sugerido"]["idioma"] == "es-MX"


def test_voice_rejects_empty_transcript() -> None:
    service = VoiceAssistantService()

    with pytest.raises(ValueError, match="transcripción"):
        import asyncio

        asyncio.run(
            service.procesar_transcripcion(
                transcripcion=" ",
                sesion_id="voz-1",
            )
        )

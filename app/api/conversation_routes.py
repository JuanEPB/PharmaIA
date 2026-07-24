from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.conversation_service import conversation_service


router = APIRouter(
    prefix="/conversation",
    tags=["Conversación inteligente"],
)


class ConversationRequest(BaseModel):
    mensaje: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        examples=["Muéstrame el Paracetamol"],
    )

    sesion_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        examples=["usuario-001"],
    )


class ConversationResponse(BaseModel):
    respuesta: Any
    sesion_id: str
    contexto: dict[str, Any]


@router.post(
    "/chat",
    response_model=ConversationResponse,
    summary="Conversar con memoria contextual",
)
async def conversation_chat(
    request: ConversationRequest,
) -> ConversationResponse:
    try:
        result = await conversation_service.chat(
            message=request.mensaje,
            session_id=request.sesion_id,
        )

        return ConversationResponse(**result)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la conversación: {exc}",
        ) from exc


@router.get(
    "/{sesion_id}/context",
    summary="Consultar el contexto de una sesión",
)
async def get_conversation_context(
    sesion_id: str,
) -> dict[str, Any]:
    context = conversation_service.get_context(sesion_id)

    return {
        "sesion_id": sesion_id,
        "contexto": context,
        "tiene_contexto": bool(context),
    }


@router.delete(
    "/{sesion_id}",
    summary="Eliminar la memoria de una sesión",
)
async def delete_conversation_context(
    sesion_id: str,
) -> dict[str, Any]:
    deleted = conversation_service.delete_context(sesion_id)

    return {
        "sesion_id": sesion_id,
        "eliminado": deleted,
        "mensaje": (
            "La memoria de la conversación fue eliminada."
            if deleted
            else "La sesión no tenía memoria almacenada."
        ),
    }

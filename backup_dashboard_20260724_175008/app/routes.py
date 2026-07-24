from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.schemas import (
    ChatRequest,
    ChatResponse,
    ContextResponse,
    DeleteContextResponse,
)
from app.services.conversation_service import conversation_service


router = APIRouter(
    tags=["Asistente inteligente"],
)


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Consultar el asistente con memoria conversacional",
    description=(
        "Procesa una consulta en lenguaje natural y conserva el contexto "
        "utilizando el campo sesion_id."
    ),
)
async def chat(
    request: ChatRequest,
) -> ChatResponse:
    try:
        result = await conversation_service.chat(
            message=request.mensaje,
            session_id=request.sesion_id,
        )

        return ChatResponse(**result)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Ocurrió un error inesperado al procesar "
                f"la consulta: {exc}"
            ),
        ) from exc


@router.get(
    "/chat/context/{sesion_id}",
    response_model=ContextResponse,
    summary="Consultar la memoria de una conversación",
)
async def get_chat_context(
    sesion_id: str,
) -> ContextResponse:
    context = conversation_service.get_context(
        sesion_id
    )

    return ContextResponse(
        sesion_id=sesion_id,
        tiene_contexto=bool(context),
        contexto=context,
    )


@router.delete(
    "/chat/context/{sesion_id}",
    response_model=DeleteContextResponse,
    summary="Eliminar la memoria de una conversación",
)
async def delete_chat_context(
    sesion_id: str,
) -> DeleteContextResponse:
    deleted = conversation_service.delete_context(
        sesion_id
    )

    return DeleteContextResponse(
        sesion_id=sesion_id,
        eliminado=deleted,
        mensaje=(
            "La memoria de la conversación fue eliminada correctamente."
            if deleted
            else "La sesión no tenía memoria almacenada."
        ),
    )


@router.get(
    "/health",
    summary="Verificar el estado del servicio",
)
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "Pharma Neural Assistant",
        "chat_memory": "enabled",
    }

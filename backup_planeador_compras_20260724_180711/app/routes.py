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
from app.services.conversational_action_service import (
    conversational_action_service,
)


router = APIRouter(
    tags=["Asistente inteligente"],
)


@router.post(
    "/chat",
    summary="Consultar o ejecutar acciones con el asistente",
    description=(
        "Responde consultas en lenguaje natural y permite ejecutar "
        "acciones de inventario mediante confirmación explícita."
    ),
)
async def chat(
    request: ChatRequest,
) -> dict[str, Any]:
    try:
        action_result = conversational_action_service.process(
            message=request.mensaje,
            session_id=request.sesion_id,
            usuario_id=getattr(
                request,
                "usuario_id",
                None,
            ),
        )

        if action_result is not None:
            return {
                "respuesta": action_result.get("respuesta"),
                "sesion_id": request.sesion_id,
                "memoria_utilizada": True,
                "contexto": action_result,
            }

        result = await conversation_service.chat(
            message=request.mensaje,
            session_id=request.sesion_id,
        )

        return result

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
                "Ocurrió un error al procesar la solicitud. "
                f"Detalle: {exc}"
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
            "La memoria de la conversación fue eliminada."
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
        "conversational_actions": "enabled",
    }

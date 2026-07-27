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
from app.services.depletion_prediction_service import depletion_prediction_service
from app.services.purchase_planner_service import purchase_planner_service


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
        normalized_prediction_message = request.mensaje.strip().lower()

        prediction_prefixes = (
            "cuando se agotara ",
            "cuándo se agotará ",
            "cuando se acaba ",
            "cuándo se acaba ",
            "predice el agotamiento de ",
            "calcula el agotamiento de ",
        )

        for prediction_prefix in prediction_prefixes:
            if normalized_prediction_message.startswith(
                prediction_prefix
            ):
                medicine_name = request.mensaje[
                    len(prediction_prefix):
                ].strip(" ?.!,;:")

                prediction = (
                    depletion_prediction_service
                    .predecir_por_nombre(medicine_name)
                )

                return {
                    "respuesta": (
                        depletion_prediction_service
                        .construir_respuesta_chat(prediction)
                    ),
                    "sesion_id": request.sesion_id,
                    "memoria_utilizada": False,
                    "contexto": {
                        "tipo": "PREDICCION_AGOTAMIENTO",
                        "prediccion": prediction,
                    },
                }

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

        normalized_message = request.mensaje.strip().lower()

        planning_triggers = {
            "hola",
            "buenos días",
            "buenos dias",
            "buenas tardes",
            "buenas noches",
            "inicio",
            "analiza el inventario",
            "revisa el inventario",
            "qué debo comprar",
            "que debo comprar",
        }

        if normalized_message in planning_triggers:
            suggestion = (
                purchase_planner_service
                .generar_sugerencia_automatica(
                    request.sesion_id
                )
            )

            if suggestion is not None:
                return {
                    "respuesta": suggestion["respuesta"],
                    "sesion_id": request.sesion_id,
                    "memoria_utilizada": True,
                    "contexto": suggestion,
                }

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



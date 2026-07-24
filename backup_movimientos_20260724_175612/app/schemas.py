from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    mensaje: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Consulta enviada al asistente inteligente.",
        examples=[
            "Muéstrame el Paracetamol"
        ],
    )

    sesion_id: str = Field(
        default="sesion-general",
        min_length=1,
        max_length=100,
        description=(
            "Identificador utilizado para conservar el contexto "
            "de la conversación."
        ),
        examples=[
            "usuario-001"
        ],
    )


class ChatResponse(BaseModel):
    respuesta: Any
    sesion_id: str
    memoria_utilizada: bool = False
    contexto: dict[str, Any] = Field(
        default_factory=dict
    )


class ContextResponse(BaseModel):
    sesion_id: str
    tiene_contexto: bool
    contexto: dict[str, Any] = Field(
        default_factory=dict
    )


class DeleteContextResponse(BaseModel):
    sesion_id: str
    eliminado: bool
    mensaje: str

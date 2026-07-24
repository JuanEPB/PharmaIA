from typing import Any

from pydantic import BaseModel, Field


class PreguntaRequest(BaseModel):
    mensaje: str = Field(
        ...,
        min_length=1,
        examples=[
            "¿Qué medicamentos tienen poco stock?"
        ],
    )


class PrediccionResponse(BaseModel):
    intencion: str
    confianza: float


class PreguntaResponse(BaseModel):
    respuesta: str
    intencion: str
    confianza: float
    porcentaje: float

    mensaje: str | None = None
    total: int = 0

    predicciones: list[PrediccionResponse] = []

    # MySQL devuelve objetos/diccionarios, no solamente textos.
    datos: list[Any] = []

    entidades: dict[str, Any] | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    estado: str
    servicio: str | None = None
    modelo: str | None = None

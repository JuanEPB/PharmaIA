from pydantic import BaseModel, Field


class PreguntaRequest(BaseModel):
    mensaje: str = Field(
        ...,
        min_length=1,
        max_length=500,
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
    predicciones: list[PrediccionResponse]
    datos: list

from fastapi import APIRouter

from app.api.schemas import (
    PreguntaRequest,
    PreguntaResponse,
)
from app.services.assistant_service import (
    assistant_service,
)


router = APIRouter(
    prefix="/api",
    tags=["Asistente"],
)


@router.get("/health")
def health():
    return {
        "estado": "ok",
        "modelo": "PyTorch",
        "servicio": "Pharma Neural Assistant",
    }


@router.post(
    "/chat",
    response_model=PreguntaResponse,
)
def chat(
    pregunta: PreguntaRequest,
):
    return assistant_service.procesar_pregunta(
        pregunta.mensaje
    )

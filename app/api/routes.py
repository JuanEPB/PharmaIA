import traceback

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.api.schemas import PreguntaRequest
from app.database.connection import test_connection
from app.services.assistant_service import procesar_mensaje


router = APIRouter(
    tags=["Asistente"],
)


@router.get("/health")
def health():
    """
    Verifica el funcionamiento de la API,
    el modelo y la conexión con MySQL.
    """

    database_status = test_connection()

    return {
        "estado": "activo",
        "servicio": "Pharma Neural Assistant",
        "base_datos": database_status,
    }


@router.post("/chat")
def chat(request: PreguntaRequest):
    """
    Procesa un mensaje utilizando el modelo de IA
    y consulta MySQL cuando la intención lo requiera.
    """

    try:
        resultado = procesar_mensaje(
            request.mensaje
        )

        return resultado

    except Exception as error:

        traceback.print_exc()

        return JSONResponse(
            status_code=500,
            content={
                "respuesta": (
                    "Ocurrió un error interno al procesar "
                    "la solicitud."
                ),
                "intencion": "error_interno",
                "confianza": 0.0,
                "porcentaje": 0.0,
                "mensaje": request.mensaje,
                "total": 0,
                "predicciones": [],
                "datos": [],
                "error": str(error),
                "tipo_error": type(error).__name__,
            },
        )

from app.ai.predictor import predictor
from app.utils.responses import obtener_respuesta


class AssistantService:
    def procesar_pregunta(
        self,
        mensaje: str,
    ) -> dict:
        resultado = predictor.predecir(mensaje)

        intencion = resultado["intencion"]

        respuesta = obtener_respuesta(
            intencion
        )

        return {
            "respuesta": respuesta,
            "intencion": intencion,
            "confianza": resultado["confianza"],
            "porcentaje": resultado["porcentaje"],
            "predicciones": resultado["predicciones"],
            "datos": [],
        }


assistant_service = AssistantService()

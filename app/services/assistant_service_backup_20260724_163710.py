import re
import unicodedata
from typing import Any

from app.ai.predictor import predictor
from app.services.inventory_service import inventory_service
from app.utils.responses import obtener_respuesta


class AssistantService:
    """
    Servicio principal del asistente.

    Responsabilidades:
    - Procesar el mensaje del usuario.
    - Obtener la intención desde el modelo PyTorch.
    - Ejecutar consultas de inventario.
    - Construir la respuesta final.
    """

    def procesar_mensaje(
        self,
        mensaje: str,
    ) -> dict[str, Any]:

        mensaje = (mensaje or "").strip()

        if not mensaje:
            return self._respuesta_error(
                mensaje="Debes escribir un mensaje.",
                codigo="mensaje_vacio",
            )

        try:
            prediccion = predictor.predict(mensaje)

            intencion = prediccion.get(
                "intencion",
                "desconocido",
            )

            confianza = float(
                prediccion.get(
                    "confianza",
                    0.0,
                )
            )

            porcentaje = float(
                prediccion.get(
                    "porcentaje",
                    confianza * 100,
                )
            )

            return self._ejecutar_intencion(
                mensaje=mensaje,
                intencion=intencion,
                confianza=confianza,
                porcentaje=porcentaje,
                prediccion=prediccion,
            )

        except ConnectionError as error:
            return {
                "respuesta": (
                    "Entendí tu solicitud, pero no pude conectarme "
                    "con la base de datos."
                ),
                "mensaje": mensaje,
                "intencion": "error_base_datos",
                "confianza": 0.0,
                "porcentaje": 0.0,
                "datos": [],
                "error": str(error),
            }

        except Exception as error:
            return {
                "respuesta": (
                    "Ocurrió un error al procesar tu solicitud."
                ),
                "mensaje": mensaje,
                "intencion": "error_interno",
                "confianza": 0.0,
                "porcentaje": 0.0,
                "datos": [],
                "error": str(error),
            }

    def _ejecutar_intencion(
        self,
        mensaje: str,
        intencion: str,
        confianza: float,
        porcentaje: float,
        prediccion: dict[str, Any],
    ) -> dict[str, Any]:

        if intencion == "consultar_bajo_stock":
            return self._consultar_bajo_stock(
                mensaje=mensaje,
                intencion=intencion,
                confianza=confianza,
                porcentaje=porcentaje,
                prediccion=prediccion,
            )

        if intencion == "consultar_agotados":
            return self._consultar_agotados(
                mensaje=mensaje,
                intencion=intencion,
                confianza=confianza,
                porcentaje=porcentaje,
                prediccion=prediccion,
            )

        if intencion in {
            "consultar_inventario",
            "listar_medicamentos",
            "obtener_medicamentos",
        }:
            return self._consultar_inventario(
                mensaje=mensaje,
                intencion=intencion,
                confianza=confianza,
                porcentaje=porcentaje,
                prediccion=prediccion,
            )

        if intencion == "buscar_medicamento":
            return self._buscar_medicamento(
                mensaje=mensaje,
                intencion=intencion,
                confianza=confianza,
                porcentaje=porcentaje,
                prediccion=prediccion,
            )

        respuesta = obtener_respuesta(intencion)

        return self._construir_respuesta(
            respuesta=respuesta,
            mensaje=mensaje,
            intencion=intencion,
            confianza=confianza,
            porcentaje=porcentaje,
            datos=[],
            prediccion=prediccion,
        )

    def _consultar_bajo_stock(
        self,
        mensaje: str,
        intencion: str,
        confianza: float,
        porcentaje: float,
        prediccion: dict[str, Any],
    ) -> dict[str, Any]:

        medicamentos = inventory_service.obtener_bajo_stock()

        total = len(medicamentos)

        if total == 0:
            respuesta = (
                "No encontré medicamentos con bajo stock."
            )
        elif total == 1:
            respuesta = (
                "Encontré 1 medicamento con bajo stock."
            )
        else:
            respuesta = (
                f"Encontré {total} medicamentos con bajo stock."
            )

        return self._construir_respuesta(
            respuesta=respuesta,
            mensaje=mensaje,
            intencion=intencion,
            confianza=confianza,
            porcentaje=porcentaje,
            datos=medicamentos,
            prediccion=prediccion,
        )

    def _consultar_agotados(
        self,
        mensaje: str,
        intencion: str,
        confianza: float,
        porcentaje: float,
        prediccion: dict[str, Any],
    ) -> dict[str, Any]:

        medicamentos = inventory_service.obtener_agotados()

        total = len(medicamentos)

        if total == 0:
            respuesta = (
                "No hay medicamentos agotados."
            )
        elif total == 1:
            respuesta = (
                "Encontré 1 medicamento agotado."
            )
        else:
            respuesta = (
                f"Encontré {total} medicamentos agotados."
            )

        return self._construir_respuesta(
            respuesta=respuesta,
            mensaje=mensaje,
            intencion=intencion,
            confianza=confianza,
            porcentaje=porcentaje,
            datos=medicamentos,
            prediccion=prediccion,
        )

    def _consultar_inventario(
        self,
        mensaje: str,
        intencion: str,
        confianza: float,
        porcentaje: float,
        prediccion: dict[str, Any],
    ) -> dict[str, Any]:

        medicamentos = inventory_service.obtener_todos()

        total = len(medicamentos)

        respuesta = (
            f"El inventario contiene {total} medicamentos."
        )

        return self._construir_respuesta(
            respuesta=respuesta,
            mensaje=mensaje,
            intencion=intencion,
            confianza=confianza,
            porcentaje=porcentaje,
            datos=medicamentos,
            prediccion=prediccion,
        )

    def _buscar_medicamento(
        self,
        mensaje: str,
        intencion: str,
        confianza: float,
        porcentaje: float,
        prediccion: dict[str, Any],
    ) -> dict[str, Any]:

        nombre = self._extraer_nombre_medicamento(
            mensaje
        )

        if not nombre:
            return self._construir_respuesta(
                respuesta=(
                    "Indícame el nombre del medicamento "
                    "que deseas buscar."
                ),
                mensaje=mensaje,
                intencion=intencion,
                confianza=confianza,
                porcentaje=porcentaje,
                datos=[],
                prediccion=prediccion,
            )

        medicamentos = inventory_service.buscar(nombre)

        total = len(medicamentos)

        if total == 0:
            respuesta = (
                f"No encontré medicamentos relacionados "
                f"con '{nombre}'."
            )
        elif total == 1:
            respuesta = (
                f"Encontré 1 medicamento relacionado "
                f"con '{nombre}'."
            )
        else:
            respuesta = (
                f"Encontré {total} medicamentos relacionados "
                f"con '{nombre}'."
            )

        resultado = self._construir_respuesta(
            respuesta=respuesta,
            mensaje=mensaje,
            intencion=intencion,
            confianza=confianza,
            porcentaje=porcentaje,
            datos=medicamentos,
            prediccion=prediccion,
        )

        resultado["entidades"] = {
            "medicamento": nombre,
        }

        return resultado

    def _extraer_nombre_medicamento(
        self,
        mensaje: str,
    ) -> str:

        texto = self._normalizar_texto(mensaje)

        patrones = [
            r"^(?:busca|buscar|encuentra|encontrar)\s+",
            r"^(?:consulta|consultar)\s+",
            r"^(?:informacion|información)\s+(?:de|sobre)\s+",
            r"^(?:dame|muestra)\s+(?:informacion|información)\s+(?:de|sobre)\s+",
            r"^(?:quiero|necesito)\s+(?:buscar|encontrar)\s+",
            r"^(?:medicamento|producto)\s+",
        ]

        for patron in patrones:
            texto = re.sub(
                patron,
                "",
                texto,
                flags=re.IGNORECASE,
            )

        palabras_genericas = {
            "medicamento",
            "medicamentos",
            "producto",
            "productos",
            "por",
            "favor",
        }

        palabras = [
            palabra
            for palabra in texto.split()
            if palabra not in palabras_genericas
        ]

        nombre = " ".join(palabras).strip()

        return nombre

    @staticmethod
    def _normalizar_texto(
        texto: str,
    ) -> str:

        texto = texto.lower().strip()

        texto = unicodedata.normalize(
            "NFD",
            texto,
        )

        texto = "".join(
            caracter
            for caracter in texto
            if unicodedata.category(caracter) != "Mn"
        )

        texto = re.sub(
            r"[^a-z0-9ñ\s-]",
            " ",
            texto,
        )

        texto = re.sub(
            r"\s+",
            " ",
            texto,
        )

        return texto.strip()

    @staticmethod
    def _construir_respuesta(
        respuesta: str,
        mensaje: str,
        intencion: str,
        confianza: float,
        porcentaje: float,
        datos: list,
        prediccion: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "respuesta": respuesta,
            "mensaje": mensaje,
            "intencion": intencion,
            "confianza": round(
                confianza,
                4,
            ),
            "porcentaje": round(
                porcentaje,
                2,
            ),
            "total": len(datos),
            "datos": datos,
            "predicciones": prediccion.get(
                "predicciones",
                [],
            ),
        }

    @staticmethod
    def _respuesta_error(
        mensaje: str,
        codigo: str,
    ) -> dict[str, Any]:

        return {
            "respuesta": mensaje,
            "mensaje": "",
            "intencion": codigo,
            "confianza": 0.0,
            "porcentaje": 0.0,
            "total": 0,
            "datos": [],
            "predicciones": [],
        }


assistant_service = AssistantService()


def procesar_mensaje(
    mensaje: str,
) -> dict[str, Any]:
    """
    Función de compatibilidad para las rutas existentes.
    """

    return assistant_service.procesar_mensaje(
        mensaje
    )

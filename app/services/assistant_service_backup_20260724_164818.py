import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.ai.predictor import predictor
from app.services.inventory_service import inventory_service
from app.utils.responses import obtener_respuesta


class AssistantService:
    """
    Servicio central del asistente farmacéutico.
    """

    def procesar_mensaje(
        self,
        mensaje: str,
    ) -> dict[str, Any]:

        mensaje = (mensaje or "").strip()

        if not mensaje:
            return self._respuesta(
                respuesta="Debes escribir un mensaje.",
                mensaje="",
                intencion="mensaje_vacio",
            )

        try:
            # Las consultas directas permiten utilizar nuevas
            # funciones sin volver a entrenar el modelo.
            intencion_directa = (
                self._detectar_intencion_directa(
                    mensaje
                )
            )

            if intencion_directa:
                return self._ejecutar_consulta_directa(
                    mensaje=mensaje,
                    intencion=intencion_directa,
                )

            prediccion = predictor.predict(mensaje)

            intencion = prediccion.get(
                "intencion",
                prediccion.get(
                    "intencion_detectada",
                    "desconocido",
                ),
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

            return self._ejecutar_intencion_modelo(
                mensaje=mensaje,
                intencion=intencion,
                confianza=confianza,
                porcentaje=porcentaje,
                prediccion=prediccion,
            )

        except Exception as error:
            return self._respuesta(
                respuesta=(
                    "Ocurrió un error al procesar "
                    "tu solicitud."
                ),
                mensaje=mensaje,
                intencion="error_interno",
                error=str(error),
            )

    def _detectar_intencion_directa(
        self,
        mensaje: str,
    ) -> str | None:

        texto = self._normalizar_texto(mensaje)

        if any(
            frase in texto
            for frase in [
                "resumen del inventario",
                "resumen de inventario",
                "estado del inventario",
                "estadisticas del inventario",
                "estadisticas de inventario",
            ]
        ):
            return "resumen_inventario"

        if any(
            frase in texto
            for frase in [
                "caducados",
                "caducadas",
                "ya caducaron",
                "ya vencieron",
                "medicamentos vencidos",
                "productos vencidos",
            ]
        ):
            return "consultar_caducados"

        if any(
            frase in texto
            for frase in [
                "este mes",
                "mes actual",
            ]
        ) and any(
            palabra in texto
            for palabra in [
                "caduca",
                "caducan",
                "vence",
                "vencen",
            ]
        ):
            return "consultar_caducidad_mes"

        if any(
            frase in texto
            for frase in [
                "por caducar",
                "proximos a caducar",
                "proximas a caducar",
                "por vencer",
                "proximos a vencer",
                "proximas a vencer",
                "caducan en",
                "vencen en",
            ]
        ):
            return "consultar_por_caducar"

        if any(
            frase in texto
            for frase in [
                "poco stock",
                "bajo stock",
                "stock bajo",
                "por agotarse",
                "casi agotados",
            ]
        ):
            return "consultar_bajo_stock"

        if any(
            frase in texto
            for frase in [
                "agotados",
                "sin stock",
                "stock cero",
                "no tienen stock",
            ]
        ):
            return "consultar_agotados"

        if any(
            frase in texto
            for frase in [
                "todos los medicamentos",
                "lista de medicamentos",
                "listar medicamentos",
                "ver inventario",
                "mostrar inventario",
            ]
        ):
            return "consultar_inventario"

        return None

    def _ejecutar_consulta_directa(
        self,
        mensaje: str,
        intencion: str,
    ) -> dict[str, Any]:

        if intencion == "consultar_caducados":
            return self._consultar_caducados(
                mensaje
            )

        if intencion == "consultar_por_caducar":
            dias = self._extraer_dias(mensaje)

            return self._consultar_por_caducar(
                mensaje=mensaje,
                dias=dias,
            )

        if intencion == "consultar_caducidad_mes":
            return self._consultar_caducidad_mes(
                mensaje
            )

        if intencion == "resumen_inventario":
            return self._consultar_resumen(
                mensaje
            )

        if intencion == "consultar_bajo_stock":
            return self._consultar_bajo_stock(
                mensaje=mensaje,
                confianza=1.0,
                porcentaje=100.0,
            )

        if intencion == "consultar_agotados":
            return self._consultar_agotados(
                mensaje=mensaje,
                confianza=1.0,
                porcentaje=100.0,
            )

        if intencion == "consultar_inventario":
            return self._consultar_inventario(
                mensaje=mensaje,
                confianza=1.0,
                porcentaje=100.0,
            )

        return self._respuesta(
            respuesta=(
                "No pude identificar la consulta."
            ),
            mensaje=mensaje,
            intencion="desconocido",
        )

    def _ejecutar_intencion_modelo(
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
                confianza=confianza,
                porcentaje=porcentaje,
                predicciones=prediccion.get(
                    "predicciones",
                    [],
                ),
            )

        if intencion == "consultar_agotados":
            return self._consultar_agotados(
                mensaje=mensaje,
                confianza=confianza,
                porcentaje=porcentaje,
                predicciones=prediccion.get(
                    "predicciones",
                    [],
                ),
            )

        if intencion in {
            "consultar_inventario",
            "listar_medicamentos",
            "obtener_medicamentos",
        }:
            return self._consultar_inventario(
                mensaje=mensaje,
                confianza=confianza,
                porcentaje=porcentaje,
                predicciones=prediccion.get(
                    "predicciones",
                    [],
                ),
            )

        if intencion == "buscar_medicamento":

            nombre = self._extraer_nombre_medicamento(
                mensaje
            )

            return self._buscar_medicamento(
                mensaje=mensaje,
                nombre=nombre,
                confianza=confianza,
                porcentaje=porcentaje,
                predicciones=prediccion.get(
                    "predicciones",
                    [],
                ),
            )

        respuesta = obtener_respuesta(intencion)

        return self._respuesta(
            respuesta=respuesta,
            mensaje=mensaje,
            intencion=intencion,
            confianza=confianza,
            porcentaje=porcentaje,
            predicciones=prediccion.get(
                "predicciones",
                [],
            ),
        )

    def _consultar_bajo_stock(
        self,
        mensaje: str,
        confianza: float = 1.0,
        porcentaje: float = 100.0,
        predicciones: list | None = None,
    ) -> dict[str, Any]:

        medicamentos = (
            inventory_service.obtener_bajo_stock()
        )

        nombres = self._obtener_nombres(
            medicamentos
        )

        if not medicamentos:
            texto = (
                "No hay medicamentos con bajo stock."
            )
        else:
            texto = (
                f"Encontré {len(medicamentos)} "
                f"medicamento(s) con bajo stock: "
                f"{nombres}."
            )

        return self._respuesta(
            respuesta=texto,
            mensaje=mensaje,
            intencion="consultar_bajo_stock",
            confianza=confianza,
            porcentaje=porcentaje,
            datos=medicamentos,
            predicciones=predicciones,
        )

    def _consultar_agotados(
        self,
        mensaje: str,
        confianza: float = 1.0,
        porcentaje: float = 100.0,
        predicciones: list | None = None,
    ) -> dict[str, Any]:

        medicamentos = (
            inventory_service.obtener_agotados()
        )

        nombres = self._obtener_nombres(
            medicamentos
        )

        if not medicamentos:
            texto = (
                "No hay medicamentos agotados."
            )
        else:
            texto = (
                f"Encontré {len(medicamentos)} "
                f"medicamento(s) agotado(s): "
                f"{nombres}."
            )

        return self._respuesta(
            respuesta=texto,
            mensaje=mensaje,
            intencion="consultar_agotados",
            confianza=confianza,
            porcentaje=porcentaje,
            datos=medicamentos,
            predicciones=predicciones,
        )

    def _consultar_inventario(
        self,
        mensaje: str,
        confianza: float = 1.0,
        porcentaje: float = 100.0,
        predicciones: list | None = None,
    ) -> dict[str, Any]:

        medicamentos = (
            inventory_service.obtener_todos()
        )

        texto = (
            f"El inventario contiene "
            f"{len(medicamentos)} medicamento(s)."
        )

        return self._respuesta(
            respuesta=texto,
            mensaje=mensaje,
            intencion="consultar_inventario",
            confianza=confianza,
            porcentaje=porcentaje,
            datos=medicamentos,
            predicciones=predicciones,
        )

    def _consultar_caducados(
        self,
        mensaje: str,
    ) -> dict[str, Any]:

        medicamentos = (
            inventory_service.obtener_caducados()
        )

        nombres = self._obtener_nombres(
            medicamentos
        )

        if not medicamentos:
            texto = (
                "No encontré medicamentos caducados."
            )
        else:
            texto = (
                f"Encontré {len(medicamentos)} "
                f"medicamento(s) caducado(s): "
                f"{nombres}."
            )

        return self._respuesta(
            respuesta=texto,
            mensaje=mensaje,
            intencion="consultar_caducados",
            confianza=1.0,
            porcentaje=100.0,
            datos=medicamentos,
        )

    def _consultar_por_caducar(
        self,
        mensaje: str,
        dias: int,
    ) -> dict[str, Any]:

        medicamentos = (
            inventory_service.obtener_por_caducar(
                dias
            )
        )

        nombres = self._obtener_nombres(
            medicamentos
        )

        if not medicamentos:
            texto = (
                f"No hay medicamentos que caduquen "
                f"durante los próximos {dias} días."
            )
        else:
            texto = (
                f"Encontré {len(medicamentos)} "
                f"medicamento(s) que caducan durante "
                f"los próximos {dias} días: "
                f"{nombres}."
            )

        return self._respuesta(
            respuesta=texto,
            mensaje=mensaje,
            intencion="consultar_por_caducar",
            confianza=1.0,
            porcentaje=100.0,
            datos=medicamentos,
            entidades={
                "dias": dias,
            },
        )

    def _consultar_caducidad_mes(
        self,
        mensaje: str,
    ) -> dict[str, Any]:

        medicamentos = (
            inventory_service
            .obtener_caducidad_mes_actual()
        )

        nombres = self._obtener_nombres(
            medicamentos
        )

        if not medicamentos:
            texto = (
                "No hay medicamentos que caduquen "
                "durante el mes actual."
            )
        else:
            texto = (
                f"Encontré {len(medicamentos)} "
                f"medicamento(s) que caducan este mes: "
                f"{nombres}."
            )

        return self._respuesta(
            respuesta=texto,
            mensaje=mensaje,
            intencion="consultar_caducidad_mes",
            confianza=1.0,
            porcentaje=100.0,
            datos=medicamentos,
        )

    def _consultar_resumen(
        self,
        mensaje: str,
    ) -> dict[str, Any]:

        resumen = inventory_service.obtener_resumen()

        texto = (
            "Resumen del inventario: "
            f"{resumen.get('total_medicamentos', 0)} "
            "medicamentos registrados, "
            f"{resumen.get('unidades_totales', 0)} "
            "unidades disponibles, "
            f"{resumen.get('bajo_stock', 0)} "
            "con bajo stock, "
            f"{resumen.get('agotados', 0)} agotados, "
            f"{resumen.get('caducados', 0)} caducados "
            f"y {resumen.get('por_caducar', 0)} "
            "próximos a caducar."
        )

        return self._respuesta(
            respuesta=texto,
            mensaje=mensaje,
            intencion="resumen_inventario",
            confianza=1.0,
            porcentaje=100.0,
            datos=[resumen],
        )

    def _buscar_medicamento(
        self,
        mensaje: str,
        nombre: str,
        confianza: float,
        porcentaje: float,
        predicciones: list | None = None,
    ) -> dict[str, Any]:

        if not nombre:
            return self._respuesta(
                respuesta=(
                    "Indícame el nombre del medicamento "
                    "que deseas buscar."
                ),
                mensaje=mensaje,
                intencion="buscar_medicamento",
                confianza=confianza,
                porcentaje=porcentaje,
                predicciones=predicciones,
            )

        medicamentos = inventory_service.buscar(
            nombre
        )

        nombres = self._obtener_nombres(
            medicamentos
        )

        if not medicamentos:
            texto = (
                f"No encontré medicamentos relacionados "
                f"con '{nombre}'."
            )
        else:
            texto = (
                f"Encontré {len(medicamentos)} "
                f"resultado(s): {nombres}."
            )

        return self._respuesta(
            respuesta=texto,
            mensaje=mensaje,
            intencion="buscar_medicamento",
            confianza=confianza,
            porcentaje=porcentaje,
            datos=medicamentos,
            predicciones=predicciones,
            entidades={
                "medicamento": nombre,
            },
        )

    @staticmethod
    def _extraer_dias(
        mensaje: str,
    ) -> int:

        coincidencia = re.search(
            r"\b(\d{1,3})\s*dias?\b",
            AssistantService._normalizar_texto(
                mensaje
            ),
        )

        if not coincidencia:
            return 30

        dias = int(coincidencia.group(1))

        return max(
            1,
            min(
                dias,
                365,
            ),
        )

    def _extraer_nombre_medicamento(
        self,
        mensaje: str,
    ) -> str:

        texto = self._normalizar_texto(
            mensaje
        )

        patrones = [
            r"^(busca|buscar|encuentra|encontrar)\s+",
            r"^(consulta|consultar)\s+",
            r"^(dame|muestra)\s+informacion\s+(de|sobre)\s+",
            r"^informacion\s+(de|sobre)\s+",
            r"^(medicamento|producto)\s+",
        ]

        for patron in patrones:
            texto = re.sub(
                patron,
                "",
                texto,
                flags=re.IGNORECASE,
            )

        palabras_ignoradas = {
            "el",
            "la",
            "los",
            "las",
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
            if palabra not in palabras_ignoradas
        ]

        return " ".join(palabras).strip()

    @staticmethod
    def _obtener_nombres(
        registros: list[dict],
    ) -> str:

        nombres = [
            str(registro.get("nombre", "")).strip()
            for registro in registros
            if registro.get("nombre")
        ]

        if not nombres:
            return ""

        limite = 8

        visibles = nombres[:limite]

        texto = ", ".join(visibles)

        restantes = len(nombres) - limite

        if restantes > 0:
            texto += (
                f" y {restantes} medicamento(s) más"
            )

        return texto

    @staticmethod
    def _normalizar_texto(
        texto: str,
    ) -> str:

        texto = (texto or "").lower().strip()

        texto = unicodedata.normalize(
            "NFD",
            texto,
        )

        texto = "".join(
            caracter
            for caracter in texto
            if unicodedata.category(
                caracter
            ) != "Mn"
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
    def _serializar(
        valor: Any,
    ) -> Any:

        if isinstance(
            valor,
            (date, datetime),
        ):
            return valor.isoformat()

        if isinstance(
            valor,
            Decimal,
        ):
            return float(valor)

        if isinstance(valor, list):
            return [
                AssistantService._serializar(
                    elemento
                )
                for elemento in valor
            ]

        if isinstance(valor, dict):
            return {
                clave: AssistantService._serializar(
                    contenido
                )
                for clave, contenido in valor.items()
            }

        return valor

    @classmethod
    def _respuesta(
        cls,
        respuesta: str,
        mensaje: str,
        intencion: str,
        confianza: float = 0.0,
        porcentaje: float = 0.0,
        datos: list | None = None,
        predicciones: list | None = None,
        entidades: dict | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:

        datos = datos or []
        predicciones = predicciones or []

        resultado = {
            "respuesta": respuesta,
            "mensaje": mensaje,
            "intencion": intencion,
            "confianza": round(
                float(confianza),
                4,
            ),
            "porcentaje": round(
                float(porcentaje),
                2,
            ),
            "total": len(datos),
            "predicciones": predicciones,
            "datos": datos,
            "entidades": entidades,
            "error": error,
        }

        return cls._serializar(resultado)


assistant_service = AssistantService()


def procesar_mensaje(
    mensaje: str,
) -> dict[str, Any]:

    return assistant_service.procesar_mensaje(
        mensaje
    )

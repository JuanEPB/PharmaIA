import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.ai.predictor import predictor
from app.services.learning_feedback_service import (
    learning_feedback_service,
)
from app.services.inventory_service import inventory_service
from app.services.purchase_planner_service import purchase_planner_service
from app.utils.responses import obtener_respuesta


class AssistantService:
    """
    Asistente inteligente conectado al inventario.
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
            intencion_directa = (
                self._detectar_intencion_directa(
                    mensaje
                )
            )

            if intencion_directa:
                return self._ejecutar_directa(
                    mensaje,
                    intencion_directa,
                )

            prediccion = predictor.predict(mensaje)
            learning_feedback_service.capture_if_needed(
                message=mensaje,
                prediction=prediccion,
            )

            intencion = prediccion.get(
                "intencion",
                prediccion.get(
                    "intencion_detectada",
                    "desconocido",
                ),
            )

            confianza = float(
                prediccion.get("confianza", 0)
            )

            porcentaje = float(
                prediccion.get(
                    "porcentaje",
                    confianza * 100,
                )
            )

            if intencion == "consultar_bajo_stock":
                return self._consultar_bajo_stock(
                    mensaje,
                    confianza,
                    porcentaje,
                    prediccion,
                )

            if intencion == "consultar_agotados":
                return self._consultar_agotados(
                    mensaje,
                    confianza,
                    porcentaje,
                    prediccion,
                )

            if intencion == "consultar_caducidades":
                return self._consultar_por_caducar(
                    mensaje,
                    self._extraer_dias(mensaje),
                )

            if intencion == "resumen_inventario":
                return self._consultar_resumen(
                    mensaje
                )

            if intencion in {
                "consultar_inventario",
                "listar_medicamentos",
                "obtener_medicamentos",
            }:
                return self._consultar_inventario(
                    mensaje,
                    confianza,
                    porcentaje,
                    prediccion,
                )

            if intencion == "buscar_medicamento":
                nombre = self._extraer_busqueda_general(
                    mensaje
                )

                return self._buscar_medicamento(
                    mensaje,
                    nombre,
                    confianza,
                    porcentaje,
                    prediccion,
                )

            if intencion == "buscar_por_categoria":
                categoria = self._extraer_categoria(mensaje)

                return self._buscar_por_categoria(
                    mensaje,
                    categoria,
                )

            if intencion == "buscar_por_proveedor":
                proveedor = self._extraer_proveedor(mensaje)

                return self._buscar_por_proveedor(
                    mensaje,
                    proveedor,
                )

            if intencion == "planear_compras":
                suggestion = (
                    purchase_planner_service
                    .generar_sugerencia_automatica(
                        "sesion-general"
                    )
                )

                if suggestion is not None:
                    return self._respuesta(
                        respuesta=suggestion["respuesta"],
                        mensaje=mensaje,
                        intencion="planear_compras",
                        confianza=confianza,
                        porcentaje=porcentaje,
                        datos=[suggestion],
                        predicciones=self._predicciones(
                            prediccion
                        ),
                    )

            if intencion == "predecir_agotamiento":
                return self._respuesta(
                    respuesta=(
                        "Indícame el nombre del medicamento con "
                        "una frase como: cuando se agotará "
                        "Paracetamol."
                    ),
                    mensaje=mensaje,
                    intencion=intencion,
                    confianza=confianza,
                    porcentaje=porcentaje,
                    predicciones=self._predicciones(
                        prediccion
                    ),
                )

            return self._respuesta(
                respuesta=obtener_respuesta(intencion),
                mensaje=mensaje,
                intencion=intencion,
                confianza=confianza,
                porcentaje=porcentaje,
                predicciones=prediccion.get(
                    "predicciones",
                    [],
                ),
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

        if (
            "categoria" in texto
            and any(
                palabra in texto
                for palabra in [
                    "cuantos",
                    "resumen",
                    "estadisticas",
                    "agrupados",
                ]
            )
        ):
            return "resumen_por_categoria"

        if (
            "proveedor" in texto
            and any(
                palabra in texto
                for palabra in [
                    "cuantos",
                    "resumen",
                    "estadisticas",
                    "agrupados",
                ]
            )
        ):
            return "resumen_por_proveedor"

        if any(
            frase in texto
            for frase in [
                "medicamento mas caro",
                "producto mas caro",
                "cual es el mas caro",
            ]
        ):
            return "medicamento_mas_caro"

        if any(
            frase in texto
            for frase in [
                "medicamento mas barato",
                "producto mas barato",
                "cual es el mas barato",
            ]
        ):
            return "medicamento_mas_barato"

        if any(
            frase in texto
            for frase in [
                "medicamento con menos stock",
                "producto con menos stock",
                "menor stock",
            ]
        ):
            return "medicamento_menor_stock"

        if any(
            frase in texto
            for frase in [
                "medicamento con mas stock",
                "producto con mas stock",
                "mayor stock",
            ]
        ):
            return "medicamento_mayor_stock"

        if (
            "proveedor" in texto
            and any(
                palabra in texto
                for palabra in [
                    "caduca",
                    "caducan",
                    "vencer",
                    "vencen",
                    "caducidad",
                ]
            )
        ):
            return "proveedores_con_caducidad"

        if any(
            frase in texto
            for frase in [
                "resumen del inventario",
                "resumen de inventario",
                "estado del inventario",
                "estadisticas del inventario",
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
            ]
        ):
            return "consultar_caducados"

        if (
            any(
                frase in texto
                for frase in [
                    "este mes",
                    "mes actual",
                ]
            )
            and any(
                palabra in texto
                for palabra in [
                    "caduca",
                    "caducan",
                    "vence",
                    "vencen",
                ]
            )
        ):
            return "consultar_caducidad_mes"

        if any(
            frase in texto
            for frase in [
                "por caducar",
                "proximos a caducar",
                "por vencer",
                "proximos a vencer",
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
            ]
        ):
            return "consultar_agotados"

        if any(
            frase in texto
            for frase in [
                "todos los medicamentos",
                "lista de medicamentos",
                "ver inventario",
                "mostrar inventario",
                "inventario detallado",
            ]
        ):
            return "consultar_inventario"

        if (
            "categoria" in texto
            or "categoría" in mensaje.lower()
        ):
            return "buscar_por_categoria"

        if "proveedor" in texto:
            return "buscar_por_proveedor"

        return None

    def _ejecutar_directa(
        self,
        mensaje: str,
        intencion: str,
    ) -> dict[str, Any]:

        if intencion == "buscar_por_categoria":
            categoria = self._extraer_categoria(mensaje)

            return self._buscar_por_categoria(
                mensaje,
                categoria,
            )

        if intencion == "buscar_por_proveedor":
            proveedor = self._extraer_proveedor(mensaje)

            return self._buscar_por_proveedor(
                mensaje,
                proveedor,
            )

        if intencion == "resumen_por_categoria":
            return self._resumen_por_categoria(
                mensaje
            )

        if intencion == "resumen_por_proveedor":
            return self._resumen_por_proveedor(
                mensaje
            )

        if intencion == "medicamento_mas_caro":
            return self._medicamento_extremo(
                mensaje,
                intencion,
            )

        if intencion == "medicamento_mas_barato":
            return self._medicamento_extremo(
                mensaje,
                intencion,
            )

        if intencion == "medicamento_menor_stock":
            return self._medicamento_extremo(
                mensaje,
                intencion,
            )

        if intencion == "medicamento_mayor_stock":
            return self._medicamento_extremo(
                mensaje,
                intencion,
            )

        if intencion == "proveedores_con_caducidad":
            return self._proveedores_con_caducidad(
                mensaje
            )

        if intencion == "resumen_inventario":
            return self._consultar_resumen(
                mensaje
            )

        if intencion == "consultar_caducados":
            return self._consultar_caducados(
                mensaje
            )

        if intencion == "consultar_por_caducar":
            return self._consultar_por_caducar(
                mensaje,
                self._extraer_dias(mensaje),
            )

        if intencion == "consultar_caducidad_mes":
            return self._consultar_caducidad_mes(
                mensaje
            )

        if intencion == "consultar_bajo_stock":
            return self._consultar_bajo_stock(
                mensaje
            )

        if intencion == "consultar_agotados":
            return self._consultar_agotados(
                mensaje
            )

        if intencion == "consultar_inventario":
            return self._consultar_inventario(
                mensaje
            )

        return self._respuesta(
            respuesta="No pude identificar la consulta.",
            mensaje=mensaje,
            intencion="desconocido",
        )

    def _buscar_por_categoria(
        self,
        mensaje: str,
        categoria: str,
    ) -> dict[str, Any]:

        if not categoria:
            return self._respuesta(
                respuesta=(
                    "Indícame el nombre de la categoría "
                    "que deseas consultar."
                ),
                mensaje=mensaje,
                intencion="buscar_por_categoria",
            )

        medicamentos = (
            inventory_service.buscar_por_categoria(
                categoria
            )
        )

        if medicamentos:
            texto = (
                f"Encontré {len(medicamentos)} "
                f"medicamento(s) en la categoría "
                f"'{categoria}': "
                f"{self._obtener_nombres(medicamentos)}."
            )
        else:
            texto = (
                "No encontré medicamentos en la "
                f"categoría '{categoria}'."
            )

        return self._respuesta(
            respuesta=texto,
            mensaje=mensaje,
            intencion="buscar_por_categoria",
            confianza=1,
            porcentaje=100,
            datos=medicamentos,
            entidades={
                "categoria": categoria,
            },
        )

    def _buscar_por_proveedor(
        self,
        mensaje: str,
        proveedor: str,
    ) -> dict[str, Any]:

        if not proveedor:
            return self._respuesta(
                respuesta=(
                    "Indícame el nombre del proveedor "
                    "que deseas consultar."
                ),
                mensaje=mensaje,
                intencion="buscar_por_proveedor",
            )

        medicamentos = (
            inventory_service.buscar_por_proveedor(
                proveedor
            )
        )

        if medicamentos:
            texto = (
                f"Encontré {len(medicamentos)} "
                f"medicamento(s) del proveedor "
                f"'{proveedor}': "
                f"{self._obtener_nombres(medicamentos)}."
            )
        else:
            texto = (
                "No encontré medicamentos relacionados "
                f"con el proveedor '{proveedor}'."
            )

        return self._respuesta(
            respuesta=texto,
            mensaje=mensaje,
            intencion="buscar_por_proveedor",
            confianza=1,
            porcentaje=100,
            datos=medicamentos,
            entidades={
                "proveedor": proveedor,
            },
        )

    def _resumen_por_categoria(
        self,
        mensaje: str,
    ) -> dict[str, Any]:

        resultados = (
            inventory_service
            .obtener_resumen_por_categoria()
        )

        if resultados:
            principal = resultados[0]

            texto = (
                f"Encontré {len(resultados)} categorías. "
                f"La categoría con más medicamentos es "
                f"{principal.get('categoria')} con "
                f"{principal.get('total_medicamentos')} "
                "medicamento(s)."
            )
        else:
            texto = (
                "No fue posible obtener el resumen "
                "por categoría."
            )

        return self._respuesta(
            respuesta=texto,
            mensaje=mensaje,
            intencion="resumen_por_categoria",
            confianza=1,
            porcentaje=100,
            datos=resultados,
        )

    def _resumen_por_proveedor(
        self,
        mensaje: str,
    ) -> dict[str, Any]:

        resultados = (
            inventory_service
            .obtener_resumen_por_proveedor()
        )

        if resultados:
            principal = resultados[0]

            texto = (
                f"Encontré {len(resultados)} proveedores. "
                f"El proveedor con más medicamentos es "
                f"{principal.get('proveedor')} con "
                f"{principal.get('total_medicamentos')} "
                "medicamento(s)."
            )
        else:
            texto = (
                "No fue posible obtener el resumen "
                "por proveedor."
            )

        return self._respuesta(
            respuesta=texto,
            mensaje=mensaje,
            intencion="resumen_por_proveedor",
            confianza=1,
            porcentaje=100,
            datos=resultados,
        )

    def _medicamento_extremo(
        self,
        mensaje: str,
        intencion: str,
    ) -> dict[str, Any]:

        if intencion == "medicamento_mas_caro":
            medicamento = (
                inventory_service
                .obtener_medicamento_mas_caro()
            )

            descripcion = "más caro"

        elif intencion == "medicamento_mas_barato":
            medicamento = (
                inventory_service
                .obtener_medicamento_mas_barato()
            )

            descripcion = "más barato"

        elif intencion == "medicamento_menor_stock":
            medicamento = (
                inventory_service
                .obtener_medicamento_menor_stock()
            )

            descripcion = "con menor stock"

        else:
            medicamento = (
                inventory_service
                .obtener_medicamento_mayor_stock()
            )

            descripcion = "con mayor stock"

        if not medicamento:
            texto = (
                "No hay medicamentos disponibles "
                "para realizar la consulta."
            )

            datos = []
        else:
            precio = float(
                medicamento.get("precio") or 0
            )

            stock = int(
                medicamento.get("stock") or 0
            )

            texto = (
                f"El medicamento {descripcion} es "
                f"{medicamento.get('nombre')}, "
                f"con precio de ${precio:,.2f} "
                f"y stock de {stock} unidad(es)."
            )

            datos = [medicamento]

        return self._respuesta(
            respuesta=texto,
            mensaje=mensaje,
            intencion=intencion,
            confianza=1,
            porcentaje=100,
            datos=datos,
        )

    def _proveedores_con_caducidad(
        self,
        mensaje: str,
    ) -> dict[str, Any]:

        dias = self._extraer_dias(mensaje)

        resultados = (
            inventory_service
            .proveedores_con_caducidad(dias)
        )

        if resultados:
            texto = (
                f"Encontré {len(resultados)} "
                f"proveedor(es) con medicamentos que "
                f"caducan durante los próximos "
                f"{dias} días."
            )
        else:
            texto = (
                "No encontré proveedores con "
                "medicamentos próximos a caducar "
                f"durante los próximos {dias} días."
            )

        return self._respuesta(
            respuesta=texto,
            mensaje=mensaje,
            intencion="proveedores_con_caducidad",
            confianza=1,
            porcentaje=100,
            datos=resultados,
            entidades={
                "dias": dias,
            },
        )

    def _consultar_bajo_stock(
        self,
        mensaje,
        confianza=1,
        porcentaje=100,
        prediccion=None,
    ):
        medicamentos = (
            inventory_service.obtener_bajo_stock()
        )

        texto = (
            f"Encontré {len(medicamentos)} "
            "medicamento(s) con bajo stock."
            if medicamentos
            else "No hay medicamentos con bajo stock."
        )

        return self._respuesta(
            respuesta=texto,
            mensaje=mensaje,
            intencion="consultar_bajo_stock",
            confianza=confianza,
            porcentaje=porcentaje,
            datos=medicamentos,
            predicciones=self._predicciones(
                prediccion
            ),
        )

    def _consultar_agotados(
        self,
        mensaje,
        confianza=1,
        porcentaje=100,
        prediccion=None,
    ):
        medicamentos = (
            inventory_service.obtener_agotados()
        )

        texto = (
            f"Encontré {len(medicamentos)} "
            "medicamento(s) agotado(s)."
            if medicamentos
            else "No hay medicamentos agotados."
        )

        return self._respuesta(
            respuesta=texto,
            mensaje=mensaje,
            intencion="consultar_agotados",
            confianza=confianza,
            porcentaje=porcentaje,
            datos=medicamentos,
            predicciones=self._predicciones(
                prediccion
            ),
        )

    def _consultar_inventario(
        self,
        mensaje,
        confianza=1,
        porcentaje=100,
        prediccion=None,
    ):
        medicamentos = (
            inventory_service
            .obtener_inventario_detallado()
        )

        return self._respuesta(
            respuesta=(
                f"El inventario contiene "
                f"{len(medicamentos)} medicamento(s)."
            ),
            mensaje=mensaje,
            intencion="consultar_inventario",
            confianza=confianza,
            porcentaje=porcentaje,
            datos=medicamentos,
            predicciones=self._predicciones(
                prediccion
            ),
        )

    def _consultar_caducados(self, mensaje):
        medicamentos = (
            inventory_service.obtener_caducados()
        )

        texto = (
            f"Encontré {len(medicamentos)} "
            "medicamento(s) caducado(s)."
            if medicamentos
            else "No encontré medicamentos caducados."
        )

        return self._respuesta(
            respuesta=texto,
            mensaje=mensaje,
            intencion="consultar_caducados",
            confianza=1,
            porcentaje=100,
            datos=medicamentos,
        )

    def _consultar_por_caducar(
        self,
        mensaje,
        dias,
    ):
        medicamentos = (
            inventory_service.obtener_por_caducar(
                dias
            )
        )

        texto = (
            f"Encontré {len(medicamentos)} "
            f"medicamento(s) que caducan durante "
            f"los próximos {dias} días."
            if medicamentos
            else (
                "No hay medicamentos que caduquen "
                f"durante los próximos {dias} días."
            )
        )

        return self._respuesta(
            respuesta=texto,
            mensaje=mensaje,
            intencion="consultar_por_caducar",
            confianza=1,
            porcentaje=100,
            datos=medicamentos,
            entidades={
                "dias": dias,
            },
        )

    def _consultar_caducidad_mes(
        self,
        mensaje,
    ):
        medicamentos = (
            inventory_service
            .obtener_caducidad_mes_actual()
        )

        texto = (
            f"Encontré {len(medicamentos)} "
            "medicamento(s) que caducan este mes."
            if medicamentos
            else (
                "No hay medicamentos que caduquen "
                "durante el mes actual."
            )
        )

        return self._respuesta(
            respuesta=texto,
            mensaje=mensaje,
            intencion="consultar_caducidad_mes",
            confianza=1,
            porcentaje=100,
            datos=medicamentos,
        )

    def _consultar_resumen(self, mensaje):
        resumen = inventory_service.obtener_resumen()

        valor = float(
            resumen.get("valor_inventario") or 0
        )

        texto = (
            "Resumen del inventario: "
            f"{resumen.get('total_medicamentos', 0)} "
            "medicamentos registrados, "
            f"{resumen.get('unidades_totales', 0)} "
            "unidades, "
            f"{resumen.get('bajo_stock', 0)} "
            "con bajo stock, "
            f"{resumen.get('agotados', 0)} agotados, "
            f"{resumen.get('caducados', 0)} caducados, "
            f"{resumen.get('por_caducar', 0)} "
            "próximos a caducar y un valor aproximado "
            f"de inventario de ${valor:,.2f}."
        )

        return self._respuesta(
            respuesta=texto,
            mensaje=mensaje,
            intencion="resumen_inventario",
            confianza=1,
            porcentaje=100,
            datos=[resumen],
        )

    def _buscar_medicamento(
        self,
        mensaje,
        nombre,
        confianza,
        porcentaje,
        prediccion,
    ):
        medicamentos = inventory_service.buscar(
            nombre
        )

        texto = (
            f"Encontré {len(medicamentos)} "
            f"resultado(s) relacionados con '{nombre}'."
            if medicamentos
            else (
                "No encontré medicamentos relacionados "
                f"con '{nombre}'."
            )
        )

        return self._respuesta(
            respuesta=texto,
            mensaje=mensaje,
            intencion="buscar_medicamento",
            confianza=confianza,
            porcentaje=porcentaje,
            datos=medicamentos,
            predicciones=self._predicciones(
                prediccion
            ),
            entidades={
                "medicamento": nombre,
            },
        )

    @classmethod
    def _extraer_categoria(cls, mensaje):
        texto = cls._normalizar_texto(mensaje)

        patrones = [
            r".*categoria\s+",
            r".*categorias\s+",
            r".*de la categoria\s+",
            r".*de categoria\s+",
        ]

        for patron in patrones:
            nuevo = re.sub(
                patron,
                "",
                texto,
            )

            if nuevo != texto:
                texto = nuevo
                break

        texto = cls._limpiar_busqueda(texto)

        return texto

    @classmethod
    def _extraer_proveedor(cls, mensaje):
        texto = cls._normalizar_texto(mensaje)

        patrones = [
            r".*proveedor\s+",
            r".*proveedores\s+",
            r".*del proveedor\s+",
            r".*de proveedor\s+",
        ]

        for patron in patrones:
            nuevo = re.sub(
                patron,
                "",
                texto,
            )

            if nuevo != texto:
                texto = nuevo
                break

        texto = cls._limpiar_busqueda(texto)

        return texto

    @classmethod
    def _extraer_busqueda_general(
        cls,
        mensaje,
    ):
        texto = cls._normalizar_texto(mensaje)

        texto = re.sub(
            r"^(busca|buscar|consulta|consultar|"
            r"muestra|mostrar|encuentra|encontrar)\s+",
            "",
            texto,
        )

        return cls._limpiar_busqueda(texto)

    @staticmethod
    def _limpiar_busqueda(texto):
        ignoradas = {
            "el",
            "la",
            "los",
            "las",
            "un",
            "una",
            "de",
            "del",
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
            if palabra not in ignoradas
        ]

        return " ".join(palabras).strip()

    @classmethod
    def _extraer_dias(cls, mensaje):
        texto = cls._normalizar_texto(mensaje)

        coincidencia = re.search(
            r"\b(\d{1,3})\s*dias?\b",
            texto,
        )

        if not coincidencia:
            return 30

        return max(
            1,
            min(
                int(coincidencia.group(1)),
                365,
            ),
        )

    @staticmethod
    def _obtener_nombres(registros):
        nombres = [
            str(registro.get("nombre")).strip()
            for registro in registros[:8]
            if registro.get("nombre")
        ]

        return ", ".join(nombres)

    @staticmethod
    def _predicciones(prediccion):
        if not isinstance(prediccion, dict):
            return []

        return prediccion.get(
            "predicciones",
            [],
        )

    @staticmethod
    def _normalizar_texto(texto):
        texto = (texto or "").lower().strip()

        texto = unicodedata.normalize(
            "NFD",
            texto,
        )

        texto = "".join(
            caracter
            for caracter in texto
            if unicodedata.category(caracter)
            != "Mn"
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
    def _serializar(valor):
        if isinstance(
            valor,
            (date, datetime),
        ):
            return valor.isoformat()

        if isinstance(valor, Decimal):
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
        respuesta,
        mensaje,
        intencion,
        confianza=0,
        porcentaje=0,
        datos=None,
        predicciones=None,
        entidades=None,
        error=None,
    ):
        datos = datos or []

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
            "predicciones": predicciones or [],
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

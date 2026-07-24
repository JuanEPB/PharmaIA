RESPUESTAS = {
    "saludo": (
        "Hola. Soy Pharma Neural Assistant. "
        "Puedo ayudarte con medicamentos, stock, "
        "productos agotados y caducidades."
    ),
    "consultar_bajo_stock": (
        "Entendí que deseas consultar los medicamentos "
        "con bajo stock."
    ),
    "consultar_agotados": (
        "Entendí que deseas consultar los medicamentos agotados."
    ),
    "consultar_caducidades": (
        "Entendí que deseas revisar los medicamentos "
        "próximos a caducar."
    ),
    "buscar_medicamento": (
        "Entendí que deseas buscar un medicamento."
    ),
    "desconocido": (
        "No pude identificar claramente tu solicitud. "
        "Puedes preguntarme sobre stock, medicamentos agotados, "
        "caducidades o búsqueda de productos."
    ),
}


def obtener_respuesta(intencion: str) -> str:
    return RESPUESTAS.get(
        intencion,
        RESPUESTAS["desconocido"],
    )

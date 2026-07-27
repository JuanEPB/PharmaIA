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
    "consultar_inventario": (
        "Entendí que deseas consultar el inventario."
    ),
    "resumen_inventario": (
        "Entendí que deseas revisar el resumen del inventario."
    ),
    "buscar_por_categoria": (
        "Entendí que deseas buscar medicamentos por categoría."
    ),
    "buscar_por_proveedor": (
        "Entendí que deseas buscar medicamentos por proveedor."
    ),
    "planear_compras": (
        "Entendí que deseas generar una sugerencia de compras."
    ),
    "predecir_agotamiento": (
        "Entendí que deseas predecir el agotamiento de un medicamento."
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

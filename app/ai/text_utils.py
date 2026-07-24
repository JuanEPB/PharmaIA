import re
import unicodedata


def limpiar_texto(texto: str) -> str:
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
        r"[^a-z0-9ñ\s]",
        "",
        texto,
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto,
    )

    return texto


def tokenizar(texto: str) -> list[str]:
    return limpiar_texto(texto).split()

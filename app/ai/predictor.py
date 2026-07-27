import pickle
import re
import unicodedata
import logging
from copy import deepcopy
from functools import lru_cache
from pathlib import Path

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)

# =========================================================
# RUTAS DEL PROYECTO
# =========================================================

# predictor.py está en:
# pharma-neural/app/ai/predictor.py
#
# parents[0] = app/ai
# parents[1] = app
# parents[2] = pharma-neural
PROJECT_DIR = Path(__file__).resolve().parents[2]

MODEL_DIR = PROJECT_DIR / "model"

MODEL_PATH = MODEL_DIR / "pharma_neural.pth"
VOCAB_PATH = MODEL_DIR / "vocabulario.pkl"
ENCODER_PATH = MODEL_DIR / "label_encoder.pkl"


# =========================================================
# MODELO DE CLASIFICACIÓN
# =========================================================

class IntentClassifier(nn.Module):
    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int,
        hidden_dim: int,
        num_classes: int,
    ):
        super().__init__()

        self.embedding = nn.Embedding(
            num_embeddings=vocab_size,
            embedding_dim=embedding_dim,
            padding_idx=0,
        )

        self.hidden = nn.Linear(
            embedding_dim,
            hidden_dim,
        )

        self.dropout = nn.Dropout(0.30)

        self.output = nn.Linear(
            hidden_dim,
            num_classes,
        )

    def forward(
        self,
        entrada: torch.Tensor,
    ) -> torch.Tensor:
        embeddings = self.embedding(entrada)

        mascara = (entrada != 0).unsqueeze(-1)

        embeddings = embeddings * mascara

        suma_embeddings = embeddings.sum(dim=1)

        cantidad_tokens = mascara.sum(dim=1).clamp(min=1)

        promedio_embeddings = (
            suma_embeddings / cantidad_tokens
        )

        salida_oculta = torch.relu(
            self.hidden(promedio_embeddings)
        )

        salida_oculta = self.dropout(
            salida_oculta
        )

        return self.output(salida_oculta)


# =========================================================
# PREDICTOR
# =========================================================

class PharmaPredictor:
    def __init__(self) -> None:
        self._validar_archivos()

        checkpoint = torch.load(
            MODEL_PATH,
            map_location=torch.device("cpu"),
            weights_only=False,
        )

        with open(VOCAB_PATH, "rb") as archivo:
            self.vocabulario = pickle.load(archivo)

        with open(ENCODER_PATH, "rb") as archivo:
            self.label_encoder = pickle.load(archivo)

        self.labels = list(self.label_encoder.classes_)

        self.max_length = checkpoint["max_length"]

        self.modelo = IntentClassifier(
            vocab_size=checkpoint["vocab_size"],
            embedding_dim=checkpoint["embedding_dim"],
            hidden_dim=checkpoint["hidden_dim"],
            num_classes=checkpoint["num_classes"],
        )

        self.modelo.load_state_dict(
            checkpoint["model_state_dict"]
        )

        self.modelo.eval()
        torch.set_num_threads(1)

        logger.info(
            "Modelo Pharma Neural cargado correctamente desde %s",
            MODEL_PATH,
        )

    def _validar_archivos(self) -> None:
        archivos_requeridos = [
            MODEL_PATH,
            VOCAB_PATH,
            ENCODER_PATH,
        ]

        archivos_faltantes = [
            archivo
            for archivo in archivos_requeridos
            if not archivo.exists()
        ]

        if archivos_faltantes:
            detalle = "\n".join(
                f"- {archivo}"
                for archivo in archivos_faltantes
            )

            raise FileNotFoundError(
                "\nNo se encontraron los archivos del modelo:\n"
                f"{detalle}\n\n"
                "Verifica que la carpeta model contenga:\n"
                "- pharma_neural.pth\n"
                "- vocabulario.pkl\n"
                "- label_encoder.pkl\n"
            )

    def limpiar_texto(
        self,
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
            r"[^a-z0-9ñ\s]",
            "",
            texto,
        )

        texto = re.sub(
            r"\s+",
            " ",
            texto,
        )

        return texto.strip()

    def texto_a_tensor(
        self,
        texto: str,
    ) -> torch.Tensor:
        texto_limpio = self.limpiar_texto(texto)

        palabras = texto_limpio.split()

        indice_desconocido = self.vocabulario.get(
            "<UNK>",
            1,
        )

        indice_padding = self.vocabulario.get(
            "<PAD>",
            0,
        )

        secuencia = [
            self.vocabulario.get(
                palabra,
                indice_desconocido,
            )
            for palabra in palabras
        ]

        secuencia = secuencia[:self.max_length]

        while len(secuencia) < self.max_length:
            secuencia.append(indice_padding)

        return torch.tensor(
            [secuencia],
            dtype=torch.long,
        )

    def predecir(
        self,
        texto: str,
        umbral: float = 0.55,
    ) -> dict:
        if not texto or not texto.strip():
            return {
                "mensaje": texto,
                "intencion": "desconocido",
                "confianza": 0.0,
                "porcentaje": 0.0,
                "predicciones": [],
            }

        cache_key = self.limpiar_texto(texto)

        result = deepcopy(
            self._predecir_normalizado(
                cache_key,
                umbral,
            )
        )

        result["mensaje"] = texto

        return result

    @lru_cache(maxsize=512)
    def _predecir_normalizado(
        self,
        texto_limpio: str,
        umbral: float,
    ) -> dict:
        entrada = self.texto_limpio_a_tensor(texto_limpio)

        with torch.inference_mode():
            salida = self.modelo(entrada)

            probabilidades = torch.softmax(
                salida,
                dim=1,
            )

        confianza_tensor, indice_tensor = torch.max(
            probabilidades,
            dim=1,
        )

        confianza = confianza_tensor.item()
        indice = indice_tensor.item()

        intencion_detectada = self.labels[indice]

        if confianza < umbral:
            intencion_final = "desconocido"
        else:
            intencion_final = intencion_detectada

        predicciones = []

        for posicion, probabilidad in enumerate(
            probabilidades[0].tolist()
        ):
            etiqueta = self.labels[posicion]

            predicciones.append(
                {
                    "intencion": etiqueta,
                    "confianza": round(
                        probabilidad,
                        4,
                    ),
                    "porcentaje": round(
                        probabilidad * 100,
                        2,
                    ),
                }
            )

        predicciones.sort(
            key=lambda elemento: elemento["confianza"],
            reverse=True,
        )

        return {
            "mensaje": texto_limpio,
            "intencion": intencion_final,
            "intencion_detectada": intencion_detectada,
            "confianza": round(
                confianza,
                4,
            ),
            "porcentaje": round(
                confianza * 100,
                2,
            ),
            "predicciones": predicciones[:3],
        }

    def predict(
        self,
        texto: str,
        umbral: float = 0.55,
    ) -> dict:
        return self.predecir(
            texto=texto,
            umbral=umbral,
        )

    def texto_limpio_a_tensor(
        self,
        texto_limpio: str,
    ) -> torch.Tensor:
        palabras = texto_limpio.split()

        indice_desconocido = self.vocabulario.get(
            "<UNK>",
            1,
        )

        indice_padding = self.vocabulario.get(
            "<PAD>",
            0,
        )

        secuencia = [
            self.vocabulario.get(
                palabra,
                indice_desconocido,
            )
            for palabra in palabras
        ]

        secuencia = secuencia[:self.max_length]

        while len(secuencia) < self.max_length:
            secuencia.append(indice_padding)

        return torch.tensor(
            [secuencia],
            dtype=torch.long,
        )


# =========================================================
# INSTANCIA GLOBAL
# =========================================================

predictor = PharmaPredictor()


# =========================================================
# PRUEBA DIRECTA
# =========================================================

if __name__ == "__main__":
    print("\nPharma Neural Assistant")
    print("Escribe 'salir' para terminar.\n")

    while True:
        mensaje = input("Tú: ").strip()

        if mensaje.lower() in {
            "salir",
            "exit",
            "cerrar",
        }:
            print("Asistente finalizado.")
            break

        resultado = predictor.predecir(mensaje)

        print(
            f"Intención: {resultado['intencion']}"
        )

        print(
            f"Confianza: {resultado['porcentaje']}%"
        )

        print("Predicciones:")

        for prediccion in resultado["predicciones"]:
            print(
                f"- {prediccion['intencion']}: "
                f"{prediccion['porcentaje']}%"
            )

        print()

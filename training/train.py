import json
import pickle
import random
import re
import unicodedata
from collections import Counter
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import LabelEncoder
from torch.utils.data import DataLoader, Dataset


BASE_DIR = Path(__file__).resolve().parents[1]
INTENTS_PATH = BASE_DIR / "training" / "intents.json"
MODEL_DIR = BASE_DIR / "model"

MODEL_DIR.mkdir(parents=True, exist_ok=True)

MAX_LENGTH = 20
EMBEDDING_DIM = 64
HIDDEN_DIM = 64
EPOCHS = 250
BATCH_SIZE = 8
LEARNING_RATE = 0.001


def limpiar_texto(texto: str) -> str:
    texto = texto.lower().strip()

    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )

    texto = re.sub(r"[^a-z0-9ñ\s]", "", texto)
    texto = re.sub(r"\s+", " ", texto)

    return texto


def tokenizar(texto: str) -> list[str]:
    return limpiar_texto(texto).split()


def cargar_intenciones():
    if not INTENTS_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {INTENTS_PATH}"
        )

    with open(INTENTS_PATH, "r", encoding="utf-8") as archivo:
        datos = json.load(archivo)

    frases = []
    etiquetas = []

    for intent in datos["intents"]:
        tag = intent["tag"]

        for patron in intent["patterns"]:
            frases.append(patron)
            etiquetas.append(tag)

    return frases, etiquetas


def crear_vocabulario(frases: list[str]) -> dict[str, int]:
    contador = Counter()

    for frase in frases:
        contador.update(tokenizar(frase))

    vocabulario = {
        "<PAD>": 0,
        "<UNK>": 1,
    }

    for palabra in sorted(contador.keys()):
        vocabulario[palabra] = len(vocabulario)

    return vocabulario


def texto_a_secuencia(
    texto: str,
    vocabulario: dict[str, int],
) -> list[int]:
    tokens = tokenizar(texto)

    secuencia = [
        vocabulario.get(token, vocabulario["<UNK>"])
        for token in tokens
    ]

    secuencia = secuencia[:MAX_LENGTH]

    while len(secuencia) < MAX_LENGTH:
        secuencia.append(vocabulario["<PAD>"])

    return secuencia


class IntentDataset(Dataset):
    def __init__(self, entradas, etiquetas):
        self.entradas = torch.tensor(
            entradas,
            dtype=torch.long,
        )

        self.etiquetas = torch.tensor(
            etiquetas,
            dtype=torch.long,
        )

    def __len__(self):
        return len(self.entradas)

    def __getitem__(self, indice):
        return self.entradas[indice], self.etiquetas[indice]


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
            vocab_size,
            embedding_dim,
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

    def forward(self, entrada):
        embeddings = self.embedding(entrada)

        mascara = (entrada != 0).unsqueeze(-1)
        embeddings = embeddings * mascara

        suma = embeddings.sum(dim=1)
        cantidad = mascara.sum(dim=1).clamp(min=1)

        promedio = suma / cantidad

        salida = torch.relu(self.hidden(promedio))
        salida = self.dropout(salida)

        return self.output(salida)


def establecer_semilla(semilla: int = 42):
    random.seed(semilla)
    np.random.seed(semilla)
    torch.manual_seed(semilla)


def entrenar():
    establecer_semilla()

    print("Cargando datos de entrenamiento...")

    frases, etiquetas = cargar_intenciones()

    print(f"Frases encontradas: {len(frases)}")
    print(f"Intenciones encontradas: {len(set(etiquetas))}")

    vocabulario = crear_vocabulario(frases)

    codificador = LabelEncoder()
    etiquetas_codificadas = codificador.fit_transform(etiquetas)

    entradas = [
        texto_a_secuencia(frase, vocabulario)
        for frase in frases
    ]

    dataset = IntentDataset(
        entradas,
        etiquetas_codificadas,
    )

    dataloader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
    )

    modelo = IntentClassifier(
        vocab_size=len(vocabulario),
        embedding_dim=EMBEDDING_DIM,
        hidden_dim=HIDDEN_DIM,
        num_classes=len(codificador.classes_),
    )

    criterio = nn.CrossEntropyLoss()

    optimizador = torch.optim.Adam(
        modelo.parameters(),
        lr=LEARNING_RATE,
    )

    print("\nIniciando entrenamiento...\n")

    for epoch in range(EPOCHS):
        modelo.train()

        perdida_total = 0
        aciertos = 0
        total = 0

        for entradas_batch, etiquetas_batch in dataloader:
            optimizador.zero_grad()

            predicciones = modelo(entradas_batch)

            perdida = criterio(
                predicciones,
                etiquetas_batch,
            )

            perdida.backward()
            optimizador.step()

            perdida_total += perdida.item()

            clases_predichas = predicciones.argmax(dim=1)

            aciertos += (
                clases_predichas == etiquetas_batch
            ).sum().item()

            total += etiquetas_batch.size(0)

        precision = aciertos / total
        perdida_promedio = perdida_total / len(dataloader)

        if epoch == 0 or (epoch + 1) % 25 == 0:
            print(
                f"Época {epoch + 1:03d}/{EPOCHS} | "
                f"Pérdida: {perdida_promedio:.4f} | "
                f"Precisión: {precision * 100:.2f}%"
            )

    ruta_modelo = MODEL_DIR / "pharma_neural.pth"

    torch.save(
        {
            "model_state_dict": modelo.state_dict(),
            "vocab_size": len(vocabulario),
            "embedding_dim": EMBEDDING_DIM,
            "hidden_dim": HIDDEN_DIM,
            "num_classes": len(codificador.classes_),
            "max_length": MAX_LENGTH,
        },
        ruta_modelo,
    )

    with open(
        MODEL_DIR / "vocabulario.pkl",
        "wb",
    ) as archivo:
        pickle.dump(vocabulario, archivo)

    with open(
        MODEL_DIR / "label_encoder.pkl",
        "wb",
    ) as archivo:
        pickle.dump(codificador, archivo)

    configuracion = {
        "max_length": MAX_LENGTH,
        "embedding_dim": EMBEDDING_DIM,
        "hidden_dim": HIDDEN_DIM,
        "clases": codificador.classes_.tolist(),
    }

    with open(
        MODEL_DIR / "config.json",
        "w",
        encoding="utf-8",
    ) as archivo:
        json.dump(
            configuracion,
            archivo,
            ensure_ascii=False,
            indent=4,
        )

    print("\nEntrenamiento finalizado correctamente.")
    print(f"Modelo guardado en: {ruta_modelo}")


if __name__ == "__main__":
    entrenar()

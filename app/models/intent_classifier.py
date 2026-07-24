import torch
import torch.nn as nn


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

    def forward(self, entrada: torch.Tensor) -> torch.Tensor:
        embeddings = self.embedding(entrada)

        mascara = (entrada != 0).unsqueeze(-1)
        embeddings = embeddings * mascara

        suma = embeddings.sum(dim=1)
        cantidad = mascara.sum(dim=1).clamp(min=1)

        promedio = suma / cantidad

        salida = torch.relu(
            self.hidden(promedio)
        )

        salida = self.dropout(salida)

        return self.output(salida)

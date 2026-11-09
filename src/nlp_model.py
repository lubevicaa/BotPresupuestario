"""Clasificador híbrido: embeddings de palabra + rasgos TF-IDF léxicos + MLP."""
from __future__ import annotations
import re
from pathlib import Path
from typing import Iterable

import numpy as np
import torch
from torch import nn

TOKEN_RE = re.compile(r"[a-záéíóúüñ0-9]+", re.IGNORECASE)
PAD, UNK = "<PAD>", "<UNK>"


def normalize(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"https?://\S+", " ", text)
    return " ".join(TOKEN_RE.findall(text))


class IntentMLP(nn.Module):
    def __init__(self, vocab_size: int, n_classes: int, dim: int = 32,
                 hidden: int = 64, semantic_dim: int = 384):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, dim, padding_idx=0)
        self.semantic_projection = nn.Linear(semantic_dim, 48)
        self.linear_skip = nn.Linear(semantic_dim, n_classes)
        self.network = nn.Sequential(
            nn.Linear(dim + 48, hidden), nn.ReLU(), nn.Dropout(0.10),
            nn.Linear(hidden, n_classes)
        )

    def forward(self, tokens: torch.Tensor, mask: torch.Tensor, semantic: torch.Tensor) -> torch.Tensor:
        embedded = self.embedding(tokens)
        pooled = (embedded * mask.unsqueeze(-1)).sum(1) / mask.sum(1, keepdim=True).clamp_min(1)
        semantic_raw = semantic
        semantic = torch.relu(self.semantic_projection(semantic))
        residual = self.network(torch.cat([pooled, semantic], dim=1))
        return self.linear_skip(semantic_raw) + residual


class IntentClassifier:
    def __init__(self, model: IntentMLP, vocab: dict[str, int], labels: list[str],
                 feature_pipeline=None, max_len: int = 24,
                 threshold: float = 0.55, margin: float = 0.08):
        self.model = model
        self.vocab = vocab
        self.labels = labels
        self.feature_pipeline = feature_pipeline
        self.max_len = max_len
        self.threshold = threshold
        self.margin = margin
        self.model.eval()

    def semantic_features(self, texts: list[str]) -> torch.Tensor:
        if self.feature_pipeline is None:
            raise ValueError("Falta el transformador de embeddings LSA")
        matrix = self.feature_pipeline.transform(texts)
        return torch.tensor(matrix.toarray(), dtype=torch.float32)

    def encode(self, texts: Iterable[str]) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        texts = list(texts)
        rows, masks = [], []
        for text in texts:
            ids = [self.vocab.get(t, self.vocab[UNK]) for t in normalize(text).split()]
            ids = ids[:self.max_len]
            mask = [1] * len(ids)
            ids += [0] * (self.max_len - len(ids))
            mask += [0] * (self.max_len - len(mask))
            rows.append(ids); masks.append(mask)
        return (torch.tensor(rows, dtype=torch.long), torch.tensor(masks, dtype=torch.float32),
                self.semantic_features(texts))

    @torch.no_grad()
    def predict(self, text: str) -> dict:
        tokens, mask, semantic = self.encode([text])
        probabilities = torch.softmax(self.model(tokens, mask, semantic), dim=1)[0]
        top_values, top_indices = probabilities.topk(2)
        confidence = float(top_values[0])
        predicted = self.labels[int(top_indices[0])]
        tokens_normalized = normalize(text).split()
        all_unknown = bool(tokens_normalized) and all(token not in self.vocab for token in tokens_normalized)
        if not tokens_normalized or all_unknown or confidence < self.threshold or float(top_values[0] - top_values[1]) < self.margin:
            predicted = "fuera_alcance"
        return {"intent": predicted, "raw_intent": self.labels[int(top_indices[0])],
                "confidence": round(confidence, 4),
                "margin": round(float(top_values[0] - top_values[1]), 4),
                "probabilities": {label: round(float(probabilities[i]), 4) for i, label in enumerate(self.labels)}}

    def save(self, path: str | Path, metadata: dict | None = None) -> None:
        path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"state_dict": self.model.state_dict(), "vocab": self.vocab,
                    "labels": self.labels, "feature_pipeline": self.feature_pipeline,
                    "semantic_dim": self.model.linear_skip.in_features,
                    "max_len": self.max_len, "threshold": self.threshold,
                    "margin": self.margin, "metadata": metadata or {}}, path)

    @classmethod
    def load(cls, path: str | Path) -> "IntentClassifier":
        bundle = torch.load(path, map_location="cpu", weights_only=False)
        semantic_dim = bundle["semantic_dim"]
        model = IntentMLP(len(bundle["vocab"]), len(bundle["labels"]), semantic_dim=semantic_dim)
        model.load_state_dict(bundle["state_dict"])
        return cls(model, bundle["vocab"], bundle["labels"], bundle["feature_pipeline"],
                   bundle["max_len"], bundle["threshold"], bundle["margin"])

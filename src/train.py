"""Entrena y evalúa PresupuestoBot. Uso: python3 src/train.py"""
from __future__ import annotations
import json
import random
import time
from pathlib import Path

import numpy as np
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import Normalizer
from torch import nn

from nlp_model import IntentClassifier, IntentMLP, PAD, UNK, normalize

ROOT = Path(__file__).resolve().parents[1]
SEED = 42
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)


def load_corpus():
    corpus = json.loads((ROOT / "data/corpus.json").read_text(encoding="utf-8"))
    train, val, test = [], [], []
    for label, groups in corpus.items():
        rows = groups["train"]
        train.extend((text, label) for text in rows[:17])
        val.extend((text, label) for text in rows[17:])
        test.extend((text, label) for text in groups["test"])
    return corpus, train, val, test


def evaluate(classifier, rows):
    predictions = [classifier.predict(text) for text, _ in rows]
    y_true = [label for _, label in rows]
    y_pred = [item["intent"] for item in predictions]
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "macro_f1": f1_score(y_true, y_pred, average="macro", zero_division=0),
        "weighted_f1": f1_score(y_true, y_pred, average="weighted", zero_division=0),
        "y_true": y_true, "y_pred": y_pred,
        "details": [{"text": text, "expected": label, **pred}
                    for (text, label), pred in zip(rows, predictions)]
    }


def main():
    corpus, train_rows, val_rows, test_rows = load_corpus()
    labels = sorted(corpus)
    vocab = {PAD: 0, UNK: 1}
    for text, _ in train_rows:
        for token in normalize(text).split():
            if token not in vocab:
                vocab[token] = len(vocab)

    # Proyección densa de subpalabras: el vocabulario se ajusta solo con entrenamiento.
    feature_pipeline = FeatureUnion([("word", TfidfVectorizer(analyzer="word", ngram_range=(1, 2), max_features=2000)), ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), max_features=3000))])
    feature_pipeline.fit([text for text, _ in train_rows])

    # Ruta lineal inicializada con una línea base; el MLP aprende solo el residual.
    linear_teacher = LogisticRegression(max_iter=1000, random_state=SEED)
    linear_teacher.fit(feature_pipeline.transform([text for text, _ in train_rows]),
                       [label for _, label in train_rows])
    model = IntentMLP(len(vocab), len(labels), semantic_dim=feature_pipeline.transform([train_rows[0][0]]).shape[1])
    with torch.no_grad():
        model.linear_skip.weight.copy_(torch.tensor(linear_teacher.coef_, dtype=torch.float32))
        model.linear_skip.bias.copy_(torch.tensor(linear_teacher.intercept_, dtype=torch.float32))
        model.network[-1].weight.zero_(); model.network[-1].bias.zero_()
    model.linear_skip.weight.requires_grad_(False); model.linear_skip.bias.requires_grad_(False)
    classifier = IntentClassifier(model, vocab, labels, feature_pipeline, threshold=0.0, margin=0.0)
    x_train, m_train, s_train = classifier.encode([text for text, _ in train_rows])
    x_val, m_val, s_val = classifier.encode([text for text, _ in val_rows])
    y_train = torch.tensor([labels.index(label) for _, label in train_rows])
    y_val = torch.tensor([labels.index(label) for _, label in val_rows])
    optimizer = torch.optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=0.0003, weight_decay=0.005)
    loss_fn = nn.CrossEntropyLoss(label_smoothing=0.04)
    history, best_state, best_score = [], None, -1.0

    for epoch in range(1, 101):
        model.train()
        optimizer.zero_grad()
        logits = model(x_train, m_train, s_train)
        loss = loss_fn(logits, y_train)
        loss.backward(); optimizer.step()
        if epoch % 10 == 0 or epoch == 1:
            model.eval()
            with torch.no_grad():
                train_loss = float(loss)
                val_loss = float(loss_fn(model(x_val, m_val, s_val), y_val))
                val_acc = float((model(x_val, m_val, s_val).argmax(1) == y_val).float().mean())
            history.append({"epoch": epoch, "train_loss": train_loss,
                            "val_loss": val_loss, "val_accuracy": val_acc})
            if val_acc > best_score:
                best_score = val_acc
                best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)

    # Selección de umbrales exclusivamente con validación.
    best_thresholds, best_val_score = (0.55, 0.08), -1.0
    for threshold in [0.0, 0.20, 0.30, 0.40, 0.50, 0.60]:
        for margin in [0.0, 0.02, 0.05, 0.08, 0.12]:
            candidate = IntentClassifier(model, vocab, labels, feature_pipeline, threshold=threshold, margin=margin)
            score = evaluate(candidate, val_rows)["macro_f1"]
            if score > best_val_score:
                best_val_score, best_thresholds = score, (threshold, margin)
    classifier.threshold, classifier.margin = best_thresholds
    val_result = evaluate(classifier, val_rows)
    test_result = evaluate(classifier, test_rows)

    # Línea base tradicional, sin redes neuronales.
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True)
    tfidf_train = vectorizer.fit_transform([text for text, _ in train_rows])
    baseline = LogisticRegression(max_iter=1000, random_state=SEED)
    baseline.fit(tfidf_train, [label for _, label in train_rows])
    baseline_pred = baseline.predict(vectorizer.transform([text for text, _ in test_rows]))
    baseline_metrics = {
        "accuracy": accuracy_score([label for _, label in test_rows], baseline_pred),
        "macro_f1": f1_score([label for _, label in test_rows], baseline_pred, average="macro")
    }

    start = time.perf_counter()
    for text, _ in test_rows * 5:
        classifier.predict(text)
    latency_ms = (time.perf_counter() - start) * 1000 / (len(test_rows) * 5)

    metadata = {"seed": SEED, "word_embedding_dim": 32,
                "lexical_tfidf_dim": feature_pipeline.transform([train_rows[0][0]]).shape[1],
                "learned_dense_projection_dim": 48, "hidden_dim": 64,
                "representation": "trainable word embeddings + word/char TF-IDF projection + residual MLP + frozen linear skip",
                "max_len": 24, "epochs": 100, "train_size": len(train_rows),
                "validation_size": len(val_rows), "test_size": len(test_rows),
                "parameters": sum(p.numel() for p in model.parameters()),
                "vocabulary_size": len(vocab), "latency_ms_mean_cpu": latency_ms}
    classifier.save(ROOT / "models/intent_model.pt", metadata)
    report = {
        "metadata": metadata,
        "validation": {k: v for k, v in val_result.items() if k not in ["y_true", "y_pred"]},
        "test": {k: v for k, v in test_result.items() if k not in ["y_true", "y_pred"]},
        "baseline_tfidf_logistic": baseline_metrics,
        "classification_report_test": classification_report(
            test_result["y_true"], test_result["y_pred"], labels=labels,
            zero_division=0, output_dict=True),
        "confusion_matrix_test": {"labels": labels,
            "matrix": confusion_matrix(test_result["y_true"], test_result["y_pred"], labels=labels).tolist()},
        "history": history
    }
    (ROOT / "resultados/metricas_nlp.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "resultados/predicciones_test.json").write_text(
        json.dumps(test_result["details"], ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"metadata": metadata, "validation_accuracy": val_result["accuracy"],
                      "test_accuracy": test_result["accuracy"], "test_macro_f1": test_result["macro_f1"],
                      "baseline": baseline_metrics}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

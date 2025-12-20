"""
Linguistic feature extraction for MMSE regression (ADReSS-style).

Implements user-specified formulas:
- Lexical richness (TTR)
- Mean length of utterance (MLU)
- POS noun ratio
- Disfluency rate (uh/um + pauses tokens)
- N-gram probability (simple bigram LM with add-1 smoothing on transcript)
- BERT [CLS] embedding (768 dim) using transformers

Dependencies: spaCy, transformers, torch. The code degrades gracefully if a model
is missing by raising a clear ImportError with guidance.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import List, Tuple

import numpy as np


def _ensure_spacy(model_name: str = "en_core_web_sm"):
    import spacy

    try:
        nlp = spacy.load(model_name)
    except OSError:
        # Provide a helpful error instead of silent failure
        raise ImportError(
            f"spaCy model '{model_name}' not found. "
            f"Install with: python -m spacy download {model_name}"
        )
    return nlp


def _ensure_bert(model_name: str = "bert-base-uncased"):
    from transformers import AutoModel, AutoTokenizer
    import torch

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()
    return tokenizer, model


def _tokenize_words(text: str) -> List[str]:
    return [w for w in text.strip().split() if w]


def lexical_richness_ttr(words: List[str]) -> float:
    if not words:
        return 0.0
    return len(set(words)) / len(words)


def mean_length_of_utterance(words: List[str], n_utterances: int) -> float:
    if n_utterances <= 0:
        return 0.0
    return len(words) / n_utterances


def pos_noun_ratio(doc) -> float:
    tokens = [t for t in doc if not t.is_punct and not t.is_space]
    if not tokens:
        return 0.0
    noun_count = sum(1 for t in tokens if t.pos_ == "NOUN")
    return noun_count / len(tokens)


def disfluency_rate(words: List[str]) -> float:
    if not words:
        return 0.0
    fillers = {"uh", "um", "ờ", "ừ", "à", "à...", "uhm", "erm"}
    pauses = {"...", "..", "pause"}
    disfl_count = sum(1 for w in words if w.lower() in fillers or w in pauses)
    return disfl_count / len(words)


def bigram_logprob(words: List[str]) -> float:
    """Compute average log probability using add-1 smoothed bigrams over the transcript itself."""
    if len(words) < 2:
        return 0.0
    bigrams = [(words[i], words[i + 1]) for i in range(len(words) - 1)]
    unigram_counts = Counter(words)
    bigram_counts = Counter(bigrams)
    vocab = len(unigram_counts)
    total_logprob = 0.0
    for bg in bigrams:
        w1, w2 = bg
        count_bg = bigram_counts[bg]
        count_w1 = unigram_counts[w1]
        # Add-1 smoothing
        prob = (count_bg + 1) / (count_w1 + vocab)
        total_logprob += math.log(prob)
    return total_logprob / max(len(bigrams), 1)


def bert_cls_embedding(text: str, model_name: str = "bert-base-uncased") -> np.ndarray:
    tokenizer, model = _ensure_bert(model_name)
    import torch

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=256,
        padding="max_length",
    )
    with torch.no_grad():
        outputs = model(**inputs)
    cls_emb = outputs.last_hidden_state[:, 0, :].squeeze(0).cpu().numpy()
    return cls_emb


def extract_linguistic_features(
    transcript: str,
    language_model: str = "en_core_web_sm",
    bert_model: str = "bert-base-uncased",
) -> dict:
    """
    Extract linguistic features per user spec.

    Returns:
        dict with scalar linguistic features and 768-d BERT CLS embedding.
    """
    text = transcript.strip()
    words = _tokenize_words(text)

    # spaCy parsing
    nlp = _ensure_spacy(language_model)
    doc = nlp(text)
    # Use sentence boundaries from spaCy for utterance count
    n_utts = max(1, len(list(doc.sents)))

    features = {
        "TTR": lexical_richness_ttr(words),
        "MLU": mean_length_of_utterance(words, n_utts),
        "POS_noun_ratio": pos_noun_ratio(doc),
        "DisfluencyRate": disfluency_rate(words),
        "bigram_logprob": bigram_logprob(words),
    }

    # BERT [CLS] embedding
    cls_vec = bert_cls_embedding(text, model_name=bert_model)
    for i, v in enumerate(cls_vec):
        features[f"BERT_CLS_{i}"] = float(v)

    return features

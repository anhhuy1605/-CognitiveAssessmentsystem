from __future__ import annotations

from typing import List

import numpy as np

try:
    from transformers import AutoModel, AutoTokenizer
    import torch
except Exception:  # pragma: no cover
    AutoModel = None
    AutoTokenizer = None
    torch = None


class SemanticCoherenceAnalyzer:
    """Compute semantic coherence via sentence embeddings (PhoBERT or fallback)."""

    def __init__(self, model_name: str = "vinai/phobert-base"):
        self.model_name = model_name
        self.available = False
        self.device = "cpu"
        if AutoModel is not None and AutoTokenizer is not None:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModel.from_pretrained(model_name)
                self.model.eval()
                if torch and torch.cuda.is_available():
                    self.model.to("cuda")
                    self.device = "cuda"
                self.available = True
            except Exception:
                self.available = False

    def _embed_sentences(self, sentences: List[str]) -> np.ndarray:
        if not self.available:
            # fallback: simple bag-of-words hashing embedding
            vecs = []
            for s in sentences:
                h = hash(s) % (10_000)
                v = np.zeros(64)
                v[h % 64] = 1.0
                vecs.append(v)
            return np.vstack(vecs) if vecs else np.zeros((0, 64))

        import torch

        inputs = self.tokenizer(
            sentences,
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            out = self.model(**inputs)
            # mean pool last hidden state
            emb = out.last_hidden_state.mean(dim=1).cpu().numpy()
        return emb

    def compute_topic_coherence(self, transcript: str) -> float:
        from underthesea import sent_tokenize

        sents = [s.strip() for s in sent_tokenize(transcript or "") if s.strip()]
        if len(sents) < 2:
            return 0.0
        emb = self._embed_sentences(sents)
        if emb.shape[0] < 2:
            return 0.0
        # average cosine similarity of adjacent sentences
        def cos(a, b):
            na = np.linalg.norm(a) + 1e-9
            nb = np.linalg.norm(b) + 1e-9
            return float(np.dot(a, b) / (na * nb))

        sims = [cos(emb[i], emb[i + 1]) for i in range(len(emb) - 1)]
        return float(np.mean(sims)) if sims else 0.0



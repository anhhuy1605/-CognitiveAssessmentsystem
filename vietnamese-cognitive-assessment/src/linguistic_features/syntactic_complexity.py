from __future__ import annotations

from typing import Dict

from underthesea import sent_tokenize, word_tokenize


def compute_syntactic_complexity(transcript: str) -> Dict[str, float]:
    """
    Compute Vietnamese syntactic complexity proxies: MLU and dependent clause ratio.
    """
    sentences = sent_tokenize(transcript or "")
    if not sentences:
        return {"mlu": 0.0, "dependent_clause_ratio": 0.0, "num_sentences": 0}

    total_words = 0
    for s in sentences:
        total_words += len(word_tokenize(s))
    mlu = total_words / len(sentences)

    markers = ["mà", "nếu", "vì", "khi", "tuy", "nhưng", "để"]
    lower = (transcript or "").lower()
    dep_count = sum(lower.count(m) for m in markers)
    dep_ratio = dep_count / len(sentences)

    return {
        "mlu": float(mlu),
        "dependent_clause_ratio": float(dep_ratio),
        "num_sentences": int(len(sentences)),
    }



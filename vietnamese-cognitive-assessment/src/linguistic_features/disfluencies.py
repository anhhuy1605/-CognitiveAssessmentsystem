from __future__ import annotations

from typing import Dict

from underthesea import word_tokenize


def detect_disfluencies_vietnamese(transcript: str) -> Dict[str, float]:
    """
    Detect Vietnamese disfluencies: filled pauses, repetitions, revisions, incomplete phrases.

    Returns
    -------
    dict with keys:
        filled_pause_rate, repetition_rate, revision_count, incomplete_count, total_disfluencies
    """
    text = (transcript or "").strip()
    tokens = word_tokenize(text, format="text").split() if text else []

    filled_set = {"ừ", "à", "ờ", "ể", "hử", "ơ", "ô", "uhm", "ờm", "ừm"}
    filled_count = sum(1 for t in tokens if t.lower() in filled_set)

    repetitions = 0
    for i in range(len(tokens) - 1):
        if tokens[i].lower() == tokens[i + 1].lower():
            repetitions += 1

    revision_markers = ["ý tôi là", "tức là", "hay là", "không không"]
    lower = text.lower()
    revision_count = sum(lower.count(m) for m in revision_markers)

    incomplete_count = text.count("...")

    total_words = max(sum(1 for t in tokens if t.lower() not in filled_set), 1)

    return {
        "filled_pause_rate": filled_count / total_words,
        "repetition_rate": repetitions / total_words,
        "revision_count": int(revision_count),
        "incomplete_count": int(incomplete_count),
        "total_disfluencies": int(filled_count + repetitions + revision_count),
    }



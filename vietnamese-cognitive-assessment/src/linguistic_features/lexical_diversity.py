from __future__ import annotations

from typing import Dict, List

import numpy as np
from underthesea import word_tokenize
import lexicalrichness


class LexicalAnalyzer:
    """
    Analyze lexical diversity for Vietnamese transcripts.
    """

    def __init__(self, language: str = "vietnamese"):
        self.language = language
        self.fillers = ["ừ", "à", "ờ", "ể", "hử", "uhm", "ờm", "ừm", "à à"]

    def tokenize_clean(self, transcript: str) -> List[str]:
        """
        Tokenize transcript and remove filler words; returns list of tokens.
        """
        if not transcript:
            return []
        tokens = word_tokenize(transcript, format="text").split()
        tokens_clean = [t for t in tokens if t.lower() not in self.fillers]
        return tokens_clean

    def compute_lexical_diversity(self, transcript: str) -> Dict[str, float]:
        """
        Compute TTR, MATTR, MTLD, compound ratio and counts.
        """
        tokens_clean = self.tokenize_clean(transcript)
        total = len(tokens_clean)
        types = len(set(tokens_clean))
        ttr = (types / total) if total > 0 else 0.0

        # MATTR
        window = 50
        mattr_scores: List[float] = []
        if total >= window:
            for i in range(0, total - window + 1):
                w = tokens_clean[i : i + window]
                mattr_scores.append(len(set(w)) / window)
            mattr = float(np.mean(mattr_scores))
        else:
            mattr = ttr

        # MTLD via lexicalrichness
        if total > 0:
            lex = lexicalrichness.LexicalRichness(" ".join(tokens_clean))
            try:
                mtld = float(lex.mtld(threshold=0.72))
            except Exception:
                mtld = float("nan")
        else:
            mtld = 0.0

        # Vietnamese-specific: compound words (underscore or space-joined tokens in some pipelines)
        compound_count = sum(1 for t in tokens_clean if ("_" in t))
        compound_ratio = (compound_count / total) if total > 0 else 0.0

        return {
            "ttr": float(ttr),
            "mattr": float(mattr),
            "mtld": float(mtld),
            "compound_ratio": float(compound_ratio),
            "unique_words": int(types),
            "total_words": int(total),
        }



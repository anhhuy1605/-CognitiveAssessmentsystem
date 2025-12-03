from __future__ import annotations

import logging
from typing import List

import pandas as pd

from src.audio_processing.f0_extraction import extract_f0_residual
from src.audio_processing.formants import extract_formants_vietnamese
from src.audio_processing.voice_quality import extract_voice_quality
from src.audio_processing.pause_detection import PauseDetector, calculate_speech_rate
from src.linguistic_features.lexical_diversity import LexicalAnalyzer
from src.linguistic_features.syntactic_complexity import compute_syntactic_complexity
from src.linguistic_features.disfluencies import detect_disfluencies_vietnamese
from src.linguistic_features.semantic_coherence import SemanticCoherenceAnalyzer
from src.quality_control.audio_validation import AudioQualityController, handle_missing_features


class CognitiveAssessmentFeatureExtractor:
    """End-to-end feature extraction pipeline."""

    def __init__(self):
        self.pause_detector = PauseDetector()
        self.lexical_analyzer = LexicalAnalyzer()
        self.quality_controller = AudioQualityController()
        self.semantic = SemanticCoherenceAnalyzer()
        self.logger = logging.getLogger(__name__)

    def extract_all_features(
        self, audio_path: str, transcript: str, participant_id: str
    ) -> pd.DataFrame:
        # 1) Quality control
        qc = self.quality_controller.validate_audio(audio_path)
        qc_row = {
            "participant_id": participant_id,
            "qc_status": qc.status,
            "qc_snr": qc.snr,
            "qc_clipping_ratio": qc.clipping_ratio,
            "qc_speech_ratio": qc.speech_ratio,
            "qc_duration": qc.duration,
        }
        if not qc.is_valid():
            return pd.DataFrame([qc_row])

        # 2) Acoustic
        f0_res = extract_f0_residual(audio_path)
        formants = extract_formants_vietnamese(audio_path)
        vq = extract_voice_quality(audio_path)

        # 3) Pause / rate
        pause = self.pause_detector.analyze_pauses(audio_path)
        rate = calculate_speech_rate(audio_path, transcript)

        # 4) Linguistic
        lex = self.lexical_analyzer.compute_lexical_diversity(transcript)
        syn = compute_syntactic_complexity(transcript)
        dis = detect_disfluencies_vietnamese(transcript)
        coh = {"semantic_coherence": self.semantic.compute_topic_coherence(transcript)}

        # Combine
        feats = {
            **qc_row,
            **f0_res,
            **formants,
            **vq,
            **pause,
            **rate,
            **lex,
            **syn,
            **dis,
            **coh,
        }
        feats = handle_missing_features(feats, threshold=0.3)
        return pd.DataFrame([feats])

    def batch_extract(self, audio_files: List[str], transcripts: List[str], output_path: str) -> pd.DataFrame:
        rows = []
        for i, (ap, tr) in enumerate(zip(audio_files, transcripts)):
            pid = f"PT{i+1:03d}"
            df = self.extract_all_features(ap, tr, pid)
            rows.append(df)
        out = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
        if output_path:
            out.to_csv(output_path, index=False)
        return out



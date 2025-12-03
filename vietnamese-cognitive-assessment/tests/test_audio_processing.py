import numpy as np
import soundfile as sf
import os

from src.audio_processing.f0_extraction import extract_f0_raw, extract_f0_residual
from src.audio_processing.formants import extract_formants_vietnamese
from src.audio_processing.voice_quality import extract_voice_quality
from src.feature_pipeline import CognitiveAssessmentFeatureExtractor


def _sine_tone(freq: float, sr: int, dur: float) -> np.ndarray:
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    return 0.1 * np.sin(2 * np.pi * freq * t)


def test_extract_f0_raw_basic(tmp_path):
    sr = 16000
    y = _sine_tone(150.0, sr, 2.0)
    p = tmp_path / "tone.wav"
    sf.write(p.as_posix(), y, sr)
    res = extract_f0_raw(p.as_posix())
    assert "f0" in res and res["f0"].size > 0
    assert np.nanmedian(res["f0"]) > 100 and np.nanmedian(res["f0"]) < 200


def test_extract_f0_residual_handles_short_audio(tmp_path):
    sr = 16000
    y = _sine_tone(120.0, sr, 1.5)
    p = tmp_path / "short.wav"
    sf.write(p.as_posix(), y, sr)
    features = extract_f0_residual(p.as_posix())
    assert set(features.keys()) == {
        'f0_residual_mean', 'f0_residual_std', 'f0_residual_cv', 'f0_residual_range', 'f0_residual_iqr'
    }


def test_formants_and_voice_quality_smoke(tmp_path):
    sr = 16000
    y = _sine_tone(130.0, sr, 2.0)
    p = tmp_path / "formant.wav"
    sf.write(p.as_posix(), y, sr)
    f = extract_formants_vietnamese(p.as_posix())
    vq = extract_voice_quality(p.as_posix())
    assert 'f1_mean' in f and 'hnr_mean' in vq


def test_pipeline_qc_rejects_short(tmp_path):
    sr = 16000
    y = _sine_tone(130.0, sr, 1.0)
    p = tmp_path / "short.wav"
    sf.write(p.as_posix(), y, sr)
    extractor = CognitiveAssessmentFeatureExtractor()
    df = extractor.extract_all_features(p.as_posix(), "tôi đi học", "PTTEST")
    assert df.loc[0, 'qc_status'] == 'REJECT'



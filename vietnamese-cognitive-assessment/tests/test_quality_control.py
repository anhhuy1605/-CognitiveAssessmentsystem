import numpy as np
import soundfile as sf

from src.audio_processing.pause_detection import PauseDetector, calculate_speech_rate
from src.quality_control.audio_validation import AudioQualityController, handle_missing_features, normalize_features
from src.analysis.clinical_validation import ClinicalValidator


def _tone(sr=16000, f=150.0, dur=2.0):
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    return 0.1 * np.sin(2 * np.pi * f * t)


def test_pause_detector_basic(tmp_path):
    sr = 16000
    # 1s tone, 0.5s silence, 1s tone
    y = np.concatenate([_tone(sr, 150, 1.0), np.zeros(int(sr * 0.5)), _tone(sr, 150, 1.0)])
    p = tmp_path / "pauses.wav"
    sf.write(p.as_posix(), y, sr)

    det = PauseDetector(threshold_db=-40, min_pause_duration=0.2)
    info = det.analyze_pauses(p.as_posix())
    assert info["pause_frequency"] > 0
    assert info["pause_mean_duration"] > 0


def test_audio_quality_controller_short(tmp_path):
    sr = 16000
    y = _tone(sr, 150, 1.0)  # 1 second only
    p = tmp_path / "short.wav"
    sf.write(p.as_posix(), y, sr)
    qc = AudioQualityController(min_duration=2.0)
    rep = qc.validate_audio(p.as_posix())
    assert rep.status == 'REJECT'


def test_handle_missing_features():
    feats = {"a": 1.0, "b": float('nan'), "c": None}
    clean = handle_missing_features(feats, threshold=0.5)
    assert clean["b"] == 0.0 and clean["c"] == 0.0


def test_clinical_primary_and_cutoff():
    import numpy as np
    y_true = np.array([0, 0, 1, 1, 1, 0, 1, 0])
    y_prob = np.array([0.1, 0.3, 0.6, 0.8, 0.7, 0.2, 0.9, 0.4])
    cv = ClinicalValidator()
    res = cv.primary_analysis(y_true, y_prob, cutoff=0.5)
    assert 'sensitivity' in res and 'auc' in res
    cut = cv.find_optimal_cutoff(y_true, y_prob)
    assert 0.0 <= cut['optimal_cutoff'] <= 1.0



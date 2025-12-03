from src.linguistic_features.lexical_diversity import LexicalAnalyzer
from src.linguistic_features.syntactic_complexity import compute_syntactic_complexity
from src.linguistic_features.disfluencies import detect_disfluencies_vietnamese
from src.linguistic_features.semantic_coherence import SemanticCoherenceAnalyzer
from src.models.regression_model import MMSEEquivalentPredictor


def test_lexical_diversity_basic():
    la = LexicalAnalyzer()
    res = la.compute_lexical_diversity("Tôi đi học _hôm_nay . Tôi đi làm _ngày_mai .")
    assert set(["ttr", "mattr", "mtld", "compound_ratio", "unique_words", "total_words"]).issubset(res.keys())


def test_syntactic_complexity_basic():
    res = compute_syntactic_complexity("Nếu trời mưa thì tôi ở nhà. Nhưng tôi vẫn đọc sách.")
    assert res["mlu"] > 0 and res["num_sentences"] == 2


def test_disfluencies_basic():
    res = detect_disfluencies_vietnamese("ờ ờ tôi tôi muốn nói... ý tôi là hôm nay")
    assert res["filled_pause_rate"] >= 0
    assert res["total_disfluencies"] >= 1


def test_semantic_coherence_fallback():
    sc = SemanticCoherenceAnalyzer()
    score = sc.compute_topic_coherence("Tôi thích đọc sách. Tôi cũng thích đi bộ.")
    assert isinstance(score, float)


def test_model_init_and_save_load(tmp_path):
    import pandas as pd
    import numpy as np

    X = pd.DataFrame({"a": [0.1, 0.2, 0.3, 0.4], "b": [1.0, 0.9, 1.1, 1.2]})
    y = np.array([25.0, 24.0, 26.0, 23.0])
    model = MMSEEquivalentPredictor("ridge")
    model.train(X, y, optimize_hyperparameters=False)
    preds = model.predict(X)
    assert preds.shape[0] == X.shape[0]
    p = tmp_path / "model.pkl"
    model.save_model(p.as_posix())
    loaded = MMSEEquivalentPredictor.load_model(p.as_posix())
    preds2 = loaded.predict(X)
    assert preds2.shape[0] == X.shape[0]



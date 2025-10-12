import sys
import os
import types

# Stub optional heavy deps to avoid import-time failures for a quick eval
import importlib.machinery

def _stub_module(name: str):
    if name in sys.modules:
        return sys.modules[name]
    mod = types.ModuleType(name)
    mod.__spec__ = importlib.machinery.ModuleSpec(name=name, loader=None)
    sys.modules[name] = mod
    return mod

for mod_name in ["whisper", "underthesea", "jieba", "librosa", "soundfile", "webrtcvad"]:
    _stub_module(mod_name)

# Minimal torch stubs to satisfy imports
torch_mod = _stub_module("torch")
torch_nn = _stub_module("torch.nn")
torch_optim = _stub_module("torch.optim")
torch_utils = _stub_module("torch.utils")
torch_utils_data = _stub_module("torch.utils.data")
torch_nn_functional = _stub_module("torch.nn.functional")

# Provide minimal classes used in imports
class _Dummy:  # generic placeholder
    pass

setattr(torch_nn, "Module", object)
setattr(torch_utils_data, "DataLoader", _Dummy)
setattr(torch_utils_data, "TensorDataset", _Dummy)
setattr(torch_utils_data, "WeightedRandomSampler", _Dummy)

# Fill minimal functions for underthesea and jieba
underthesea = sys.modules.get("underthesea")
if underthesea:
    setattr(underthesea, "word_tokenize", lambda text: text.split())
    setattr(underthesea, "pos_tag", lambda text: [(w, "N") for w in text.split()])
    setattr(underthesea, "sentiment", lambda text: 0)
    setattr(underthesea, "dependency_parse", lambda text: [])

jieba = sys.modules.get("jieba")
if jieba:
    setattr(jieba, "lcut", lambda text: text.split())

import logging
logging.basicConfig(level=logging.INFO)

def main():
    # Import after stubbing
    # Stub transformers to avoid heavy optional imports
    if 'transformers' not in sys.modules:
        import importlib.machinery
        transformers_stub = types.ModuleType('transformers')
        class _Dummy:
            pass
        transformers_stub.AutoTokenizer = _Dummy
        transformers_stub.AutoModel = _Dummy
        transformers_stub.__spec__ = importlib.machinery.ModuleSpec(name='transformers', loader=None)
        sys.modules['transformers'] = transformers_stub

    # Import unified clinical model
    import clinical_ml_models as caml

    # Shrink grids for quick run
    caml.RF_PARAM_GRID = {"n_estimators": [50], "max_depth": [None], "min_samples_split": [2], "min_samples_leaf": [1], "max_features": ["sqrt"]}
    caml.XGB_PARAM_GRID = {"n_estimators": [50], "max_depth": [3], "learning_rate": [0.1], "subsample": [0.9], "colsample_bytree": [0.9], "reg_alpha": [0], "reg_lambda": [1]}
    caml.SVR_PARAM_GRID = {"C": [1.0], "epsilon": [0.1], "kernel": ["rbf"]}

    model = caml.EnhancedMultimodalCognitiveModel(language='vi', random_state=42)
    logging.info("Starting quick synthetic training/evaluation...")

    # Uses internal synthetic dataset path; CSV args are placeholders
    metrics = model.train_from_adress_data('dx-mmse.csv', 'progression.csv', 'eval-data.csv')

    # Save and reload to validate persistence
    out_dir = 'quick_trained_model'
    model.save_model(out_dir)
    model.load_model(out_dir)

    # Simple confirmation of artifacts
    plot_dir = 'plots'
    expected = [
        os.path.join(plot_dir, 'confusion_matrix_stacking.png'),
        os.path.join(plot_dir, 'learning_curve_rf.png'),
        os.path.join(plot_dir, 'learning_curve_xgb.png'),
    ]
    for p in expected:
        logging.info("Artifact %s exists: %s", p, os.path.exists(p))

    # Print key metrics
    clf_metrics = metrics.get('classification', {}) if isinstance(metrics, dict) else {}
    reg_metrics = metrics.get('regression', {}) if isinstance(metrics, dict) else {}
    logging.info("Classification models: %s", list(clf_metrics.keys()))
    logging.info("Regression models: %s", list(reg_metrics.keys()))
    if 'StackingClassifier' in clf_metrics:
        sc = clf_metrics['StackingClassifier']
        logging.info("StackingClassifier: Acc=%.4f F1=%.4f ROC-AUC=%s",
                     sc.get('test_accuracy', float('nan')),
                     sc.get('test_f1', float('nan')),
                     str(sc.get('roc_auc')))
    if 'StackingRegressor' in reg_metrics:
        sr = reg_metrics['StackingRegressor']
        logging.info("StackingRegressor: MSE=%.4f MAE=%.4f R2=%.4f",
                     sr.get('mse', float('nan')),
                     sr.get('mae', float('nan')),
                     sr.get('r2', float('nan')))

if __name__ == "__main__":
    main()



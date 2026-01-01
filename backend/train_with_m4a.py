# -*- coding: utf-8 -*-
"""
Training Script sử dụng các file M4A trong backend để train model trong modules

Script này:
1. Tìm tất cả file .m4a trong thư mục backend
2. Transcribe audio thành text (nếu cần)
3. Trích xuất features bằng modules (acoustic + linguistic)
4. Train model sử dụng modules (MultimodalFusion + MCIPredictor)
5. Lưu model đã train

Author: Cognitive Assessment System
Version: 1.0
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import modules
try:
    from modules.acoustic_analyzer import AcousticAnalyzer
    from modules.linguistic_analyzer import VietnameseLinguisticAnalyzer
    from modules.multimodal_fusion import MultimodalFusion, FusionConfig
    from modules.mci_predictor import MCIPredictor
    MODULES_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    MODULES_AVAILABLE = False

# Import sklearn
try:
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import (
        accuracy_score, roc_auc_score, confusion_matrix, 
        classification_report, mean_squared_error, mean_absolute_error,
        precision_recall_fscore_support
    )
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.error("sklearn not available. Please install: pip install scikit-learn")

# Try to import transcriber for transcription
try:
    from vietnamese_transcriber import RealTimeVietnameseTranscriber
    TRANSCRIBER_AVAILABLE = True
except ImportError:
    TRANSCRIBER_AVAILABLE = False
    logger.warning("Vietnamese transcriber not available. Will use placeholder transcripts.")


def find_m4a_files(backend_dir: str = None) -> List[Path]:
    """
    Tìm tất cả file .m4a trong thư mục backend
    
    Args:
        backend_dir: Đường dẫn thư mục backend (mặc định: thư mục chứa script)
    
    Returns:
        Danh sách đường dẫn đến các file .m4a
    """
    if backend_dir is None:
        backend_dir = Path(__file__).parent
    else:
        backend_dir = Path(backend_dir)
    
    m4a_files = list(backend_dir.glob("*.m4a"))
    logger.info(f"📁 Tìm thấy {len(m4a_files)} file .m4a trong {backend_dir}")
    
    for f in m4a_files:
        logger.info(f"   - {f.name}")
    
    return sorted(m4a_files)


def transcribe_audio_file(audio_path: str, transcriber=None) -> str:
    """
    Transcribe audio file thành text
    
    Args:
        audio_path: Đường dẫn file audio
        transcriber: Transcriber instance (optional)
    
    Returns:
        Transcript text
    """
    if transcriber is None and TRANSCRIBER_AVAILABLE:
        try:
            transcriber = RealTimeVietnameseTranscriber()
        except Exception as e:
            logger.warning(f"Không thể khởi tạo transcriber: {e}")
            transcriber = None
    
    if transcriber:
        try:
            logger.info(f"📝 Đang transcribe: {Path(audio_path).name}")
            result = transcriber.transcribe_audio_file(audio_path, 'vi', False, None)
            if result.get('success') and result.get('transcript'):
                transcript = result['transcript'].strip()
                logger.info(f"✅ Transcript: {transcript[:100]}...")
                return transcript
        except Exception as e:
            logger.warning(f"Transcription failed: {e}")
    
    # Fallback: return placeholder
    logger.warning(f"⚠️  Không thể transcribe {Path(audio_path).name}, sử dụng transcript placeholder")
    return "Transcript placeholder - cần cập nhật"


def create_labels_csv(m4a_files: List[Path], output_path: str, transcriber=None) -> pd.DataFrame:
    """
    Tạo file labels.csv từ danh sách file m4a
    
    Args:
        m4a_files: Danh sách đường dẫn file .m4a
        output_path: Đường dẫn file CSV output
        transcriber: Transcriber instance (optional)
    
    Returns:
        DataFrame chứa labels
    """
    logger.info("="*60)
    logger.info("TẠO FILE LABELS")
    logger.info("="*60)
    
    records = []
    
    for idx, m4a_path in enumerate(m4a_files, 1):
        participant_id = m4a_path.stem  # Tên file không có extension
        
        logger.info(f"\n[{idx}/{len(m4a_files)}] Xử lý: {m4a_path.name}")
        
        # Transcribe audio
        transcript = transcribe_audio_file(str(m4a_path), transcriber)
        
        # Tạo record với giá trị mặc định (người dùng cần cập nhật)
        record = {
            'participant_id': participant_id,
            'mmse_score': 25,  # Giá trị mặc định, cần cập nhật
            'mci_label': 0,    # 0: Normal, 1: MCI, 2: Dementia - cần cập nhật
            'transcript': transcript,
            'task_type': 'spontaneous_speech',  # Có thể là: spontaneous_speech, picture_description, verbal_fluency, qa
            'age': 70,         # Cần cập nhật
            'gender': 'unknown',  # Cần cập nhật
            'education_years': 12  # Cần cập nhật
        }
        
        records.append(record)
    
    # Tạo DataFrame
    df = pd.DataFrame(records)
    
    # Lưu CSV
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    logger.info(f"\n✅ Đã tạo file labels: {output_path}")
    logger.info(f"⚠️  LƯU Ý: Cần cập nhật các giá trị mmse_score, mci_label, age, gender, education_years")
    logger.info(f"   - mci_label: 0=Normal, 1=MCI, 2=Dementia")
    logger.info(f"   - mmse_score: 0-30")
    
    return df


def extract_features_from_m4a_files(m4a_files: List[Path], labels_df: pd.DataFrame,
                                    use_phobert: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Trích xuất features từ các file m4a sử dụng modules
    
    Args:
        m4a_files: Danh sách đường dẫn file .m4a
        labels_df: DataFrame chứa labels (có cột participant_id và transcript)
        use_phobert: Có sử dụng PhoBERT không
    
    Returns:
        Tuple (acoustic_df, linguistic_df)
    """
    logger.info("="*60)
    logger.info("TRÍCH XUẤT FEATURES")
    logger.info("="*60)
    
    # Khởi tạo analyzers
    acoustic_analyzer = AcousticAnalyzer()
    linguistic_analyzer = VietnameseLinguisticAnalyzer(use_phobert=use_phobert)
    
    acoustic_features_list = []
    linguistic_features_list = []
    valid_indices = []
    
    # Tạo mapping từ participant_id đến file path
    id_to_path = {f.stem: f for f in m4a_files}
    id_to_transcript = dict(zip(labels_df['participant_id'], labels_df['transcript']))
    id_to_task = dict(zip(labels_df['participant_id'], labels_df.get('task_type', [None] * len(labels_df))))
    
    for idx, row in labels_df.iterrows():
        participant_id = row['participant_id']
        transcript = id_to_transcript.get(participant_id, '')
        task_type = id_to_task.get(participant_id, None)
        
        if participant_id not in id_to_path:
            logger.warning(f"⚠️  Không tìm thấy file audio cho: {participant_id}")
            continue
        
        audio_path = id_to_path[participant_id]
        
        logger.info(f"\n[{idx+1}/{len(labels_df)}] Xử lý: {participant_id}")
        logger.info(f"   Audio: {audio_path.name}")
        logger.info(f"   Transcript: {transcript[:50]}...")
        
        try:
            # Trích xuất acoustic features (bắt buộc phải thành công)
            logger.info("   🎵 Trích xuất acoustic features...")
            acoustic_feat = acoustic_analyzer.extract_all_features(str(audio_path), transcript)
            
            # Kiểm tra xem acoustic features có rỗng không
            if not acoustic_feat or len(acoustic_feat) == 0:
                logger.warning(f"   ⚠️  Không extract được acoustic features cho {participant_id}, bỏ qua file này")
                continue
            
            # Trích xuất linguistic features (bắt buộc phải thành công)
            logger.info("   📝 Trích xuất linguistic features...")
            linguistic_feat = linguistic_analyzer.extract_all_features(transcript, task_type)
            
            # Kiểm tra xem linguistic features có rỗng không
            if not linguistic_feat or len(linguistic_feat) == 0:
                logger.warning(f"   ⚠️  Không extract được linguistic features cho {participant_id}, bỏ qua file này")
                continue
            
            # Chỉ thêm vào list nếu cả hai đều thành công
            acoustic_features_list.append(acoustic_feat)
            linguistic_features_list.append(linguistic_feat)
            valid_indices.append(idx)
            
            logger.info(f"   ✅ Hoàn thành")
            
        except KeyboardInterrupt:
            logger.warning("\n⚠️  Bị interrupt bởi người dùng. Dừng processing...")
            raise
        except Exception as e:
            logger.error(f"   ❌ Lỗi khi xử lý {participant_id}: {e}")
            logger.error(f"   Type: {type(e).__name__}")
            import traceback
            logger.error(traceback.format_exc())
            logger.warning(f"   ⚠️  Bỏ qua file {participant_id} và tiếp tục với file khác...")
            logger.warning(f"   Chỉ train với các files extract thành công!")
            continue
    
    # Flatten và chỉ giữ numeric values, nhưng giữ lại F0 metrics
    def flatten_features(features_list: List[Dict]) -> List[Dict]:
        """
        Flatten feature dicts, chỉ giữ numeric values
        
        Giữ lại:
        - Tất cả F0 metrics (f0_mean, f0_std, f0_cv, f0_range, etc.) - đã là numeric
        - Tất cả các features numeric khác
        
        Loại bỏ:
        - Nested dicts (như f0_contour chứa f0_values array)
        - Lists và arrays
        """
        flattened = []
        for feat_dict in features_list:
            flat_dict = {}
            for k, v in feat_dict.items():
                # Bỏ qua nested dicts (như f0_contour chứa arrays)
                # Các F0 metrics đã được extract riêng với prefix f0_ nên không cần nested dict
                if isinstance(v, dict):
                    # Có thể có nested dict như f0_contour - skip nó
                    # Các F0 metrics quan trọng đã có sẵn với prefix f0_
                    continue
                # Bỏ qua lists và arrays (như f0_values, timestamps)
                if isinstance(v, (list, np.ndarray)):
                    continue
                # Chỉ giữ numeric types (bao gồm tất cả F0 metrics như f0_mean, f0_std, etc.)
                if isinstance(v, (int, float, np.integer, np.floating)):
                    flat_dict[k] = float(v)
                elif v is None:
                    flat_dict[k] = 0.0
                elif isinstance(v, bool):
                    flat_dict[k] = float(v)  # Convert bool to float
            flattened.append(flat_dict)
        return flattened
    
    # Flatten features trước khi tạo DataFrame
    logger.info("🔄 Flattening features (giữ F0 metrics, loại bỏ nested arrays)...")
    acoustic_features_flat = flatten_features(acoustic_features_list)
    linguistic_features_flat = flatten_features(linguistic_features_list)
    
    # Log số lượng F0 features được giữ lại
    if acoustic_features_flat:
        f0_feature_count = sum(1 for k in acoustic_features_flat[0].keys() if k.startswith('f0_'))
        logger.info(f"   ✅ Giữ lại {f0_feature_count} F0 metrics (f0_mean, f0_std, f0_cv, f0_range, etc.)")
    
    # Tạo DataFrames
    acoustic_df = pd.DataFrame(acoustic_features_flat)
    linguistic_df = pd.DataFrame(linguistic_features_flat)
    
    # Xử lý NaN và inf
    acoustic_df = acoustic_df.replace([np.inf, -np.inf], np.nan)
    acoustic_df = acoustic_df.fillna(0)
    
    linguistic_df = linguistic_df.replace([np.inf, -np.inf], np.nan)
    linguistic_df = linguistic_df.fillna(0)
    
    # Đảm bảo tất cả columns là numeric
    for col in acoustic_df.columns:
        acoustic_df[col] = pd.to_numeric(acoustic_df[col], errors='coerce').fillna(0)
    for col in linguistic_df.columns:
        linguistic_df[col] = pd.to_numeric(linguistic_df[col], errors='coerce').fillna(0)
    
    # Kiểm tra và loại bỏ columns còn non-numeric (phòng hờ)
    acoustic_df = acoustic_df.select_dtypes(include=[np.number])
    linguistic_df = linguistic_df.select_dtypes(include=[np.number])
    
    # Đảm bảo DataFrame không rỗng
    if len(acoustic_df.columns) == 0:
        logger.error("❌ Không có acoustic features hợp lệ sau khi flatten!")
        raise ValueError("No valid acoustic features extracted")
    if len(linguistic_df.columns) == 0:
        logger.error("❌ Không có linguistic features hợp lệ sau khi flatten!")
        raise ValueError("No valid linguistic features extracted")
    
    logger.info(f"\n✅ Trích xuất hoàn tất:")
    logger.info(f"   Số samples hợp lệ (chỉ những files extract thành công): {len(acoustic_df)}")
    logger.info(f"   Acoustic features: {len(acoustic_df.columns)}")
    logger.info(f"   Linguistic features: {len(linguistic_df.columns)}")
    
    if len(acoustic_df) == 0:
        logger.error("\n❌ KHÔNG CÓ FILE NÀO EXTRACT THÀNH CÔNG!")
        logger.error("   Vui lòng kiểm tra:")
        logger.error("   1. File audio có hợp lệ không?")
        logger.error("   2. Có đủ dependencies không? (opensmile, parselmouth, librosa, etc.)")
        logger.error("   3. Xem log errors ở trên để biết chi tiết")
        raise ValueError("Không có samples hợp lệ để train. Tất cả files đều fail.")
    
    if len(acoustic_df) < 3:
        logger.warning(f"\n⚠️  CHỈ CÓ {len(acoustic_df)} SAMPLES THÀNH CÔNG!")
        logger.warning("   Với ít samples như vậy, model có thể không train tốt.")
        logger.warning("   Khuyến nghị tối thiểu 10-20 samples.")
    
    return acoustic_df, linguistic_df


def train_model_with_modules(acoustic_df: pd.DataFrame, 
                             linguistic_df: pd.DataFrame,
                             mmse_labels: np.ndarray,
                             mci_labels: np.ndarray,
                             output_dir: str = 'models',
                             use_rule_based: bool = False) -> Dict[str, Any]:
    """
    Train model sử dụng modules (MultimodalFusion + MCIPredictor)
    
    Args:
        acoustic_df: DataFrame chứa acoustic features
        linguistic_df: DataFrame chứa linguistic features
        mmse_labels: MMSE scores (0-30)
        mci_labels: MCI labels (0=Normal, 1=MCI, 2=Dementia)
        output_dir: Thư mục lưu model
    
    Returns:
        Dictionary chứa kết quả training
    """
    logger.info("="*60)
    logger.info("TRAIN MODEL VỚI MODULES")
    logger.info("="*60)
    
    if not MODULES_AVAILABLE or not SKLEARN_AVAILABLE:
        raise RuntimeError("Modules hoặc sklearn không khả dụng")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Combine features using MultimodalFusion
    logger.info("\n📊 Kết hợp features với MultimodalFusion...")
    fusion_config = FusionConfig(
        fusion_method='early',
        normalize=True,
        use_pca=False
    )
    fusion = MultimodalFusion(config=fusion_config)
    
    # Prepare feature matrices
    acoustic_features = acoustic_df.values
    linguistic_features = linguistic_df.values
    
    # Combine features
    combined_features = np.hstack([acoustic_features, linguistic_features])
    
    logger.info(f"   Combined features shape: {combined_features.shape}")
    
    # Train-test split
    logger.info("\n🔄 Chia train-test split...")
    
    # Với dataset nhỏ, không dùng stratify vì test set quá nhỏ không đủ classes
    n_samples = len(combined_features)
    n_classes = len(np.unique(mci_labels))
    test_size_ratio = 0.2
    min_test_samples = int(np.ceil(n_samples * test_size_ratio))
    
    # Kiểm tra xem có đủ samples để stratify không
    # Test set phải có ít nhất số samples >= số classes để có thể stratify
    can_stratify = min_test_samples >= n_classes and n_samples >= 10
    
    if not can_stratify:
        logger.warning(f"⚠️  Dataset nhỏ ({n_samples} samples, {n_classes} classes), không sử dụng stratify")
        # Với dataset nhỏ, dùng toàn bộ để train (hoặc chia nhỏ test set)
        if n_samples < 5:
            # Quá ít samples, dùng toàn bộ để train
            logger.warning("⚠️  Quá ít samples, sử dụng toàn bộ dataset để train (không chia test)")
            X_train = combined_features
            X_test = combined_features  # Dùng lại để evaluation
            y_mmse_train = mmse_labels
            y_mmse_test = mmse_labels
            y_mci_train = mci_labels
            y_mci_test = mci_labels
        else:
            # Chia không stratify, đảm bảo test set có ít nhất 1 sample
            actual_test_size = max(0.1, min(0.3, 2.0 / n_samples))  # Ít nhất 1-2 samples trong test
            X_train, X_test, y_mmse_train, y_mmse_test, y_mci_train, y_mci_test = train_test_split(
                combined_features, mmse_labels, mci_labels, 
                test_size=actual_test_size, random_state=42, stratify=None
            )
    else:
        # Dataset đủ lớn, dùng stratify
        X_train, X_test, y_mmse_train, y_mmse_test, y_mci_train, y_mci_test = train_test_split(
            combined_features, mmse_labels, mci_labels, 
            test_size=test_size_ratio, random_state=42, stratify=mci_labels
        )
    
    logger.info(f"   Train: {len(X_train)} samples")
    logger.info(f"   Test: {len(X_test)} samples")
    
    # Initialize MCIPredictor
    predictor = MCIPredictor()
    
    if use_rule_based:
        # Sử dụng rule-based model (không train ML)
        logger.info("\n🤖 Sử dụng Rule-Based Model...")
        logger.info("   Rule-based model sử dụng clinical heuristics từ literature")
        logger.info("   Không cần training - dựa trên ngưỡng features đã được nghiên cứu")
        logger.info("   ✅ Rule-based model ready (không train ML)")
        # Không set is_trained = True, để predictor.predict() sẽ dùng _rule_based_predict
    else:
        # Train ML model
        logger.info("\n🤖 Training ML Model với MCIPredictor...")
        
        # Với dataset nhỏ, train trực tiếp không dùng cross-validation
        # (MCIPredictor.train() dùng cv=5, không phù hợp với dataset nhỏ)
        logger.info("   Dataset nhỏ, train trực tiếp (không dùng cross-validation)...")
        
        # Scale features
        X_train_scaled = predictor.scaler.fit_transform(X_train)
        
        # Train classifier
        logger.info("   Training classifier...")
        predictor.classifier.fit(X_train_scaled, y_mci_train)
        
        # Train regressor
        if y_mmse_train is not None and len(y_mmse_train) > 0:
            logger.info("   Training regressor...")
            predictor.regressor.fit(X_train_scaled, y_mmse_train)
        
        predictor.is_trained = True
        logger.info("   ✅ Training complete (skipped CV due to small dataset)")
    
    # Evaluate model
    logger.info("\n📈 Đánh giá model...")
    
    if use_rule_based:
        # Evaluate rule-based predictions
        # Convert test features back to dict format for rule-based prediction
        # Cần tên features từ DataFrame
        acoustic_feature_names = acoustic_df.columns.tolist()
        linguistic_feature_names = linguistic_df.columns.tolist()
        all_feature_names = acoustic_feature_names + linguistic_feature_names
        
        y_pred_class_list = []
        y_pred_proba_list = []
        y_pred_mmse_list = []
        
        for i in range(len(X_test)):
            # Convert array to feature dict
            features_dict = {all_feature_names[j]: X_test[i, j] for j in range(min(len(all_feature_names), X_test.shape[1]))}
            
            # Predict using rule-based
            prediction = predictor.predict(features_dict)
            
            # Convert class string to numeric
            class_map = {'Normal': 0, 'MCI': 1, 'Dementia': 2}
            y_pred_class_list.append(class_map.get(prediction.mci_class, 1))
            
            # Convert probability to probabilities array (simplified)
            if prediction.mci_class == 'Normal':
                probs = [1.0 - prediction.mci_probability, prediction.mci_probability * 0.5, prediction.mci_probability * 0.5]
            elif prediction.mci_class == 'MCI':
                probs = [0.3, prediction.mci_probability, 0.2]
            else:  # Dementia
                probs = [0.2, 0.3, prediction.mci_probability]
            y_pred_proba_list.append(probs)
            
            y_pred_mmse_list.append(prediction.mmse_estimate)
        
        y_pred_class = np.array(y_pred_class_list)
        y_pred_proba = np.array(y_pred_proba_list)
        y_pred_mmse = np.array(y_pred_mmse_list)
    else:
        # Evaluate ML predictions
        # Use internal models for evaluation (faster and more accurate)
        X_test_scaled = predictor.scaler.transform(X_test)
        
        # Classification predictions
        y_pred_class = predictor.classifier.predict(X_test_scaled)
        y_pred_proba = predictor.classifier.predict_proba(X_test_scaled)
        
        # Regression predictions
        y_pred_mmse = predictor.regressor.predict(X_test_scaled)
        y_pred_mmse = np.clip(y_pred_mmse, 0, 30)  # Clamp to valid range
    
    # Classification metrics
    accuracy = accuracy_score(y_mci_test, y_pred_class)
    
    # Calculate AUC (use probabilities, handle binary/multiclass)
    auc = 0.0
    try:
        if len(np.unique(y_mci_test)) > 1:  # Need at least 2 classes
            if len(np.unique(y_mci_test)) == 2:  # Binary classification
                auc = roc_auc_score(y_mci_test, y_pred_proba[:, 1])
            else:  # Multiclass - use macro average
                auc = roc_auc_score(y_mci_test, y_pred_proba, multi_class='ovr', average='macro')
    except Exception as e:
        logger.warning(f"Could not calculate AUC: {e}")
        auc = 0.0
    
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_mci_test, y_pred_class, average='weighted', zero_division=0
    )
    
    # Regression metrics
    rmse = np.sqrt(mean_squared_error(y_mmse_test, y_pred_mmse))
    mae = mean_absolute_error(y_mmse_test, y_pred_mmse)
    
    logger.info(f"\n📊 Kết quả Test Set:")
    logger.info(f"   Classification:")
    logger.info(f"     Accuracy: {accuracy:.3f}")
    logger.info(f"     AUC: {auc:.3f}")
    logger.info(f"     Precision: {precision:.3f}")
    logger.info(f"     Recall: {recall:.3f}")
    logger.info(f"     F1: {f1:.3f}")
    logger.info(f"   Regression:")
    logger.info(f"     RMSE: {rmse:.3f}")
    logger.info(f"     MAE: {mae:.3f}")
    
    # Save model (even if rule-based, save predictor instance)
    model_path = output_dir / 'mci_predictor_model.pkl'
    joblib.dump(predictor, model_path)
    model_type = "Rule-Based" if use_rule_based else "ML"
    logger.info(f"\n✅ Đã lưu {model_type} model: {model_path}")
    
    # Save metrics
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'model_type': 'rule_based' if use_rule_based else 'ml',
        'n_samples': len(combined_features),
        'n_train': len(X_train),
        'n_test': len(X_test),
        'n_acoustic_features': len(acoustic_df.columns),
        'n_linguistic_features': len(linguistic_df.columns),
        'metrics': {
            'classification': {
                'accuracy': float(accuracy),
                'auc': float(auc),
                'precision': float(precision),
                'recall': float(recall),
                'f1': float(f1)
            },
            'regression': {
                'rmse': float(rmse),
                'mae': float(mae)
            }
        }
    }
    
    metrics_path = output_dir / 'training_metrics.json'
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    logger.info(f"✅ Đã lưu metrics: {metrics_path}")
    
    return {
        'predictor': predictor,
        'metrics': metrics,
        'model_path': model_path,
        'metrics_path': metrics_path
    }


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Train MCI Model với file M4A trong backend')
    parser.add_argument('--backend-dir', type=str, default=None,
                        help='Đường dẫn thư mục backend (mặc định: thư mục chứa script)')
    parser.add_argument('--labels-csv', type=str, default='data/training_data/labels_m4a.csv',
                        help='Đường dẫn file labels CSV (sẽ tạo mới nếu chưa có)')
    parser.add_argument('--output-dir', type=str, default='models/m4a_trained',
                        help='Thư mục lưu model đã train')
    parser.add_argument('--skip-transcription', action='store_true',
                        help='Bỏ qua transcription (sử dụng transcript có sẵn trong CSV)')
    parser.add_argument('--skip-features', action='store_true',
                        help='Bỏ qua feature extraction (sử dụng features đã có)')
    parser.add_argument('--no-phobert', action='store_true',
                        help='Không sử dụng PhoBERT (nhanh hơn nhưng kém chính xác)')
    parser.add_argument('--create-labels-only', action='store_true',
                        help='Chỉ tạo file labels CSV, không train')
    parser.add_argument('--rule-based', action='store_true',
                        help='Sử dụng rule-based model thay vì ML model (phù hợp với dataset nhỏ)')
    
    args = parser.parse_args()
    
    if not MODULES_AVAILABLE:
        logger.error("❌ Modules không khả dụng. Vui lòng kiểm tra imports.")
        sys.exit(1)
    
    if not SKLEARN_AVAILABLE:
        logger.error("❌ sklearn không khả dụng. Cài đặt: pip install scikit-learn")
        sys.exit(1)
    
    # Tìm file m4a
    logger.info("🔍 Đang tìm file .m4a...")
    m4a_files = find_m4a_files(args.backend_dir)
    
    if len(m4a_files) == 0:
        logger.error("❌ Không tìm thấy file .m4a nào trong backend!")
        sys.exit(1)
    
    labels_path = Path(args.labels_csv)
    
    # Tạo hoặc load labels CSV
    if not labels_path.exists() or args.create_labels_only:
        logger.info("📝 Tạo file labels CSV...")
        transcriber = None
        if not args.skip_transcription and TRANSCRIBER_AVAILABLE:
            try:
                transcriber = RealTimeVietnameseTranscriber()
            except Exception as e:
                logger.warning(f"Không thể khởi tạo transcriber: {e}")
        
        labels_df = create_labels_csv(m4a_files, str(labels_path), transcriber)
        
        if args.create_labels_only:
            logger.info("✅ Chỉ tạo labels CSV. Vui lòng cập nhật labels và chạy lại để train.")
            return
    else:
        logger.info(f"📂 Đọc file labels: {labels_path}")
        labels_df = pd.read_csv(labels_path, encoding='utf-8-sig')
        logger.info(f"   Đã load {len(labels_df)} records")
    
    # Validate labels
    required_cols = ['participant_id', 'mmse_score', 'mci_label', 'transcript']
    missing = [col for col in required_cols if col not in labels_df.columns]
    if missing:
        logger.error(f"❌ Thiếu các cột bắt buộc: {missing}")
        sys.exit(1)
    
    # Trích xuất features
    if not args.skip_features:
        logger.info("🎵 Trích xuất features từ audio...")
        acoustic_df, linguistic_df = extract_features_from_m4a_files(
            m4a_files, labels_df, use_phobert=not args.no_phobert
        )
        
        if len(acoustic_df) == 0:
            logger.error("❌ Không thể trích xuất features. Kiểm tra lại audio files.")
            sys.exit(1)
    else:
        logger.warning("⚠️  Bỏ qua feature extraction (cần có features đã trích xuất sẵn)")
        # TODO: Load từ file đã có
        raise NotImplementedError("Loading pre-extracted features chưa được implement")
    
    # Train model
    logger.info("🚀 Bắt đầu training...")
    mmse_labels = labels_df['mmse_score'].values[:len(acoustic_df)]
    mci_labels = labels_df['mci_label'].values[:len(acoustic_df)]
    
    results = train_model_with_modules(
        acoustic_df, linguistic_df,
        mmse_labels, mci_labels,
        output_dir=args.output_dir,
        use_rule_based=args.rule_based
    )
    
    # Print summary
    print("\n" + "="*60)
    print("TRAINING HOÀN TẤT!")
    print("="*60)
    print(f"Samples: {results['metrics']['n_samples']}")
    print(f"Train: {results['metrics']['n_train']}, Test: {results['metrics']['n_test']}")
    print(f"\nClassification Metrics:")
    print(f"  Accuracy: {results['metrics']['metrics']['classification']['accuracy']:.1%}")
    print(f"  AUC: {results['metrics']['metrics']['classification']['auc']:.3f}")
    print(f"  F1: {results['metrics']['metrics']['classification']['f1']:.3f}")
    print(f"\nRegression Metrics:")
    print(f"  RMSE: {results['metrics']['metrics']['regression']['rmse']:.2f}")
    print(f"  MAE: {results['metrics']['metrics']['regression']['mae']:.2f}")
    print(f"\nModel saved: {results['model_path']}")
    print(f"Metrics saved: {results['metrics_path']}")


if __name__ == '__main__':
    main()


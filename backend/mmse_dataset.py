#!/usr/bin/env python3
"""
MMSE Dataset for Speech-based Cognitive Assessment
================================================

PyTorch Dataset implementation for MMSE assessment with:
- Audio segmentation per question-item
- Multi-modal feature extraction
- Support for 12-item audio-first configuration
- Robust handling of missing/corrupted data

Author: AI Assistant
Date: September 2025
"""

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
import logging
from typing import Dict, List, Tuple, Optional, Union, Any, Callable
import os
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

from audio_feature_extractor import AudioFeatureExtractor, normalize_features

logger = logging.getLogger(__name__)


class MMSEDataset(Dataset):
    """
    PyTorch Dataset for MMSE assessment with audio segmentation.

    Supports:
    - 12-item audio-first configuration
    - Multi-modal features (audio + text + metadata)
    - Robust missing data handling
    - Audio quality filtering
    """

    # MMSE item configurations (12-item audio-first)
    MMSE_ITEMS = {
        1: {'code': 'T-OR', 'name': 'Orientation_Time', 'max_score': 5, 'type': 'ordinal'},
        2: {'code': 'P-OR', 'name': 'Orientation_Place', 'max_score': 5, 'type': 'ordinal'},
        3: {'code': 'REG1', 'name': 'Registration_Word1', 'max_score': 1, 'type': 'binary'},
        4: {'code': 'REG2', 'name': 'Registration_Word2', 'max_score': 1, 'type': 'binary'},
        5: {'code': 'REG3', 'name': 'Registration_Word3', 'max_score': 1, 'type': 'binary'},
        6: {'code': 'ATT', 'name': 'Attention_Serial7', 'max_score': 5, 'type': 'ordinal'},
        7: {'code': 'REC1', 'name': 'Recall_Word1', 'max_score': 1, 'type': 'binary'},
        8: {'code': 'REC2', 'name': 'Recall_Word2', 'max_score': 1, 'type': 'binary'},
        9: {'code': 'REC3', 'name': 'Recall_Word3', 'max_score': 1, 'type': 'binary'},
        10: {'code': 'NAME', 'name': 'Naming_2Objects', 'max_score': 2, 'type': 'ordinal'},
        11: {'code': 'REP', 'name': 'Repetition_Sentence', 'max_score': 1, 'type': 'binary'},
        12: {'code': 'FLU', 'name': 'Fluency_Semantic', 'max_score': 2, 'type': 'ordinal'}
    }

    # Required columns in input CSV
    REQUIRED_COLUMNS = [
        'subject_id', 'session_id', 'age', 'sex', 'edu_years',
        'device', 'noise_label', 'item_id', 'item_type',
        'audio_file', 'start_s', 'end_s', 'gold_score',
        'gold_total_mmse', 'transcript'
    ]

    def __init__(self,
                 data_path: Union[str, Path],
                 audio_base_dir: Union[str, Path],
                 feature_extractor: AudioFeatureExtractor,
                 feature_stats_path: Optional[Union[str, Path]] = None,
                 transform: Optional[Callable] = None,
                 target_transform: Optional[Callable] = None,
                 min_audio_quality: float = 0.5,
                 max_segment_duration: float = 60.0,
                 cache_features: bool = True):
        """
        Initialize MMSE Dataset.

        Args:
            data_path: Path to CSV file with MMSE data
            audio_base_dir: Base directory for audio files
            feature_extractor: AudioFeatureExtractor instance
            feature_stats_path: Path to feature statistics for normalization
            transform: Optional transform for features
            target_transform: Optional transform for targets
            min_audio_quality: Minimum audio quality score (0-1)
            max_segment_duration: Maximum allowed segment duration in seconds
            cache_features: Whether to cache extracted features
        """
        self.data_path = Path(data_path)
        self.audio_base_dir = Path(audio_base_dir)
        self.feature_extractor = feature_extractor
        self.transform = transform
        self.target_transform = target_transform
        self.min_audio_quality = min_audio_quality
        self.max_segment_duration = max_segment_duration
        self.cache_features = cache_features

        # Load feature statistics for normalization
        self.feature_stats = None
        if feature_stats_path and Path(feature_stats_path).exists():
            with open(feature_stats_path, 'r') as f:
                self.feature_stats = json.load(f)
            logger.info(f"✅ Loaded feature statistics from {feature_stats_path}")

        # Load and validate data
        self.data = self._load_and_validate_data()

        # Cache for extracted features
        self.feature_cache = {} if cache_features else None

        # Pre-compute valid indices (filter out invalid samples)
        self.valid_indices = self._get_valid_indices()

        logger.info(f"✅ MMSE Dataset initialized: {len(self.valid_indices)}/{len(self.data)} valid samples")

    def _load_and_validate_data(self) -> pd.DataFrame:
        """Load and validate input data."""
        try:
            # Load CSV
            data = pd.read_csv(self.data_path)
            logger.info(f"📁 Loaded {len(data)} rows from {self.data_path}")

            # Check required columns
            missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in data.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            # Basic data validation
            data = self._validate_data_types(data)
            data = self._clean_data(data)

            logger.info(f"✅ Data validation passed: {len(data)} samples")
            return data

        except Exception as e:
            logger.error(f"❌ Failed to load data: {e}")
            raise

    def _validate_data_types(self, data: pd.DataFrame) -> pd.DataFrame:
        """Validate and convert data types."""
        # Convert numeric columns
        numeric_cols = ['age', 'edu_years', 'start_s', 'end_s', 'gold_score', 'gold_total_mmse']
        for col in numeric_cols:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')

        # Convert categorical columns
        data['sex'] = data['sex'].astype(str).str.lower()
        data['device'] = data['device'].astype(str).str.lower()
        data['noise_label'] = data['noise_label'].astype(str).str.lower()
        data['item_type'] = data['item_type'].astype(str).str.lower()

        # Ensure item_id is integer
        data['item_id'] = data['item_id'].astype(int)

        return data

    def _clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean and filter data."""
        original_size = len(data)

        # Remove rows with missing critical values
        critical_cols = ['subject_id', 'item_id', 'audio_file', 'gold_score']
        data = data.dropna(subset=critical_cols)

        # Filter valid item_ids
        valid_items = list(self.MMSE_ITEMS.keys())
        data = data[data['item_id'].isin(valid_items)]

        # Filter valid score ranges
        for idx, row in data.iterrows():
            item_id = row['item_id']
            max_score = self.MMSE_ITEMS[item_id]['max_score']
            if row['gold_score'] > max_score:
                data.loc[idx, 'gold_score'] = max_score  # Cap to max

        # Remove invalid durations
        data = data[
            (data['end_s'] > data['start_s']) &
            (data['end_s'] - data['start_s'] <= self.max_segment_duration) &
            (data['end_s'] - data['start_s'] >= 0.1)  # Minimum 100ms
        ]

        cleaned_size = len(data)
        logger.info(f"🧹 Data cleaning: {original_size} → {cleaned_size} samples")

        return data.reset_index(drop=True)

    def _get_valid_indices(self) -> List[int]:
        """Get indices of valid samples based on audio quality and other criteria."""
        valid_indices = []

        for idx in range(len(self.data)):
            try:
                # Check if audio file exists
                audio_path = self.audio_base_dir / self.data.iloc[idx]['audio_file']
                if not audio_path.exists():
                    continue

                # Check audio quality (if we have cached features)
                if self.cache_features and idx in self.feature_cache:
                    quality = self.feature_cache[idx].get('quality', {})
                    snr = quality.get('snr_db', 30)
                    clipping = quality.get('clipping_percentage', 0)

                    # Skip poor quality audio
                    if snr < 10 or clipping > 5:
                        continue

                valid_indices.append(idx)

            except Exception as e:
                logger.warning(f"⚠️ Skipping invalid sample {idx}: {e}")
                continue

        logger.info(f"✅ Found {len(valid_indices)} valid samples")
        return valid_indices

    def __len__(self) -> int:
        """Return number of valid samples."""
        return len(self.valid_indices)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        """Get a sample from the dataset."""
        # Map to actual data index
        data_idx = self.valid_indices[idx]
        row = self.data.iloc[data_idx]

        try:
            # Extract audio segment features
            audio_path = self.audio_base_dir / row['audio_file']
            start_time = row['start_s']
            end_time = row['end_s']

            # Get features (from cache or extract)
            if self.cache_features and data_idx in self.feature_cache:
                features = self.feature_cache[data_idx]
            else:
                # Extract segment features
                segment_features = self.feature_extractor.extract_segment_features(
                    str(audio_path), [(start_time, end_time)]
                )

                if segment_features:
                    features = segment_features[0]
                else:
                    # Fallback: extract from full audio (not recommended)
                    features = self.feature_extractor.extract_all_features(str(audio_path))
                    # Filter to approximate segment
                    features['duration'] = end_time - start_time

                # Cache if enabled
                if self.cache_features:
                    self.feature_cache[data_idx] = features

            # Prepare input features
            input_features = self._prepare_input_features(features, row)

            # Prepare targets
            targets = self._prepare_targets(row)

            # Apply transforms
            if self.transform:
                input_features = self.transform(input_features)
            if self.target_transform:
                targets = self.target_transform(targets)

            sample = {
                'features': input_features,
                'targets': targets,
                'metadata': {
                    'subject_id': row['subject_id'],
                    'session_id': row['session_id'],
                    'item_id': row['item_id'],
                    'item_code': self.MMSE_ITEMS[row['item_id']]['code'],
                    'item_name': self.MMSE_ITEMS[row['item_id']]['name'],
                    'audio_file': row['audio_file'],
                    'start_time': start_time,
                    'end_time': end_time,
                    'gold_score': row['gold_score'],
                    'gold_total_mmse': row['gold_total_mmse']
                }
            }

            return sample

        except Exception as e:
            logger.error(f"❌ Failed to load sample {data_idx}: {e}")
            # Return a dummy sample to avoid crashes
            return self._get_dummy_sample()

    def _prepare_input_features(self, features: Dict[str, Any], row: pd.Series) -> Dict[str, Any]:
        """Prepare input features for model."""
        # Extract relevant feature groups
        egemaps = features.get('egemaps', {})
        temporal = features.get('temporal', {})
        quality = features.get('quality', {})

        # Normalize features if stats available
        if self.feature_stats:
            egemaps = normalize_features(egemaps, self.feature_stats)
            temporal = normalize_features(temporal, self.feature_stats)
            quality = normalize_features(quality, self.feature_stats)

        # Prepare demographic features
        demographics = {
            'age': float(row['age']) / 100.0,  # Normalize age
            'sex': 1.0 if row['sex'].lower() in ['m', 'male'] else 0.0,
            'edu_years': float(row['edu_years']) / 20.0,  # Normalize education
            'device_score': self._device_to_score(row['device']),
            'noise_score': self._noise_to_score(row['noise_label'])
        }

        # Combine all features
        input_features = {
            'egemaps': egemaps,
            'temporal': temporal,
            'quality': quality,
            'demographics': demographics,
            'segment_duration': features.get('duration', 0.0)
        }

        return input_features

    def _prepare_targets(self, row: pd.Series) -> Dict[str, Any]:
        """Prepare target values for training."""
        item_id = row['item_id']
        gold_score = row['gold_score']
        gold_total = row['gold_total_mmse']

        # Item-specific target
        item_target = gold_score / self.MMSE_ITEMS[item_id]['max_score']  # Normalize to 0-1

        # Total MMSE target
        total_target = gold_total / 30.0  # Normalize to 0-1

        # Cognitive level classification (NC/MCI/Dementia)
        if gold_total >= 25:
            cog_class = 0  # Normal cognition
        elif gold_total >= 18:
            cog_class = 1  # MCI
        else:
            cog_class = 2  # Dementia

        targets = {
            'item_score': item_target,
            'total_mmse': total_target,
            'cognitive_class': cog_class,
            'item_max_score': self.MMSE_ITEMS[item_id]['max_score']
        }

        return targets

    def _device_to_score(self, device: str) -> float:
        """Convert device type to quality score."""
        device_scores = {
            'smartphone': 0.8,
            'tablet': 0.9,
            'laptop': 1.0,
            'desktop': 1.0,
            'professional': 1.0
        }
        return device_scores.get(device.lower(), 0.5)

    def _noise_to_score(self, noise_label: str) -> float:
        """Convert noise label to quality score."""
        noise_scores = {
            'quiet': 1.0,
            'low': 0.8,
            'medium': 0.6,
            'high': 0.3,
            'very_high': 0.1
        }
        return noise_scores.get(noise_label.lower(), 0.5)

    def _get_dummy_sample(self) -> Dict[str, Any]:
        """Return a dummy sample for error cases."""
        return {
            'features': {
                'egemaps': {},
                'temporal': {},
                'quality': {},
                'demographics': {'age': 0.5, 'sex': 0.5, 'edu_years': 0.5, 'device_score': 0.5, 'noise_score': 0.5},
                'segment_duration': 1.0
            },
            'targets': {
                'item_score': 0.5,
                'total_mmse': 0.5,
                'cognitive_class': 1,
                'item_max_score': 1
            },
            'metadata': {
                'subject_id': 'dummy',
                'item_id': 1,
                'gold_score': 0.5
            }
        }

    def get_item_distribution(self) -> Dict[int, int]:
        """Get distribution of MMSE items in dataset."""
        return self.data['item_id'].value_counts().to_dict()

    def get_subject_distribution(self) -> Dict[str, int]:
        """Get distribution of subjects."""
        return self.data['subject_id'].value_counts().to_dict()

    def get_score_distribution(self) -> Dict[str, Any]:
        """Get score distributions."""
        return {
            'item_scores': self.data['gold_score'].describe().to_dict(),
            'total_mmse': self.data['gold_total_mmse'].describe().to_dict(),
            'age': self.data['age'].describe().to_dict(),
            'education': self.data['edu_years'].describe().to_dict()
        }

    def cache_all_features(self, batch_size: int = 32) -> None:
        """Pre-cache all features for faster training."""
        if not self.cache_features:
            logger.info("ℹ️ Feature caching disabled")
            return

        logger.info("🔄 Caching all features...")

        for i in range(0, len(self.valid_indices), batch_size):
            batch_indices = self.valid_indices[i:i + batch_size]

            for idx in batch_indices:
                if idx not in self.feature_cache:
                    try:
                        row = self.data.iloc[idx]
                        audio_path = self.audio_base_dir / row['audio_file']
                        start_time = row['start_s']
                        end_time = row['end_s']

                        segment_features = self.feature_extractor.extract_segment_features(
                            str(audio_path), [(start_time, end_time)]
                        )

                        if segment_features:
                            self.feature_cache[idx] = segment_features[0]

                    except Exception as e:
                        logger.warning(f"⚠️ Failed to cache features for sample {idx}: {e}")
                        continue

            logger.info(f"📦 Cached features for batch {i//batch_size + 1}/{(len(self.valid_indices) + batch_size - 1)//batch_size}")

        logger.info(f"✅ Cached features for {len(self.feature_cache)} samples")

    def save_feature_cache(self, cache_path: Union[str, Path]) -> None:
        """Save feature cache to disk."""
        if not self.feature_cache:
            logger.warning("⚠️ No feature cache to save")
            return

        cache_path = Path(cache_path)
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        with open(cache_path, 'w') as f:
            json.dump(self.feature_cache, f, indent=2)

        logger.info(f"💾 Saved feature cache to {cache_path}")

    def load_feature_cache(self, cache_path: Union[str, Path]) -> None:
        """Load feature cache from disk."""
        cache_path = Path(cache_path)

        if not cache_path.exists():
            logger.warning(f"⚠️ Feature cache not found: {cache_path}")
            return

        with open(cache_path, 'r') as f:
            self.feature_cache = json.load(f)

        logger.info(f"📁 Loaded feature cache from {cache_path}")


def create_mmse_dataloader(dataset: MMSEDataset,
                          batch_size: int = 32,
                          shuffle: bool = True,
                          num_workers: int = 4,
                          pin_memory: bool = True) -> DataLoader:
    """
    Create PyTorch DataLoader for MMSE dataset.

    Args:
        dataset: MMSE dataset instance
        batch_size: Batch size
        shuffle: Whether to shuffle data
        num_workers: Number of worker processes
        pin_memory: Whether to pin memory for faster GPU transfer

    Returns:
        Configured DataLoader
    """

    def collate_fn(batch):
        """Custom collate function for variable-length features."""
        # Group features by type
        features_batch = {
            'egemaps': [],
            'temporal': [],
            'quality': [],
            'demographics': [],
            'segment_duration': []
        }

        targets_batch = {
            'item_score': [],
            'total_mmse': [],
            'cognitive_class': [],
            'item_max_score': []
        }

        metadata_batch = []

        for sample in batch:
            # Handle features
            for key in features_batch.keys():
                if key == 'demographics':
                    # Convert dict to tensor
                    demo_features = sample['features'][key]
                    demo_tensor = torch.tensor([
                        demo_features['age'],
                        demo_features['sex'],
                        demo_features['edu_years'],
                        demo_features['device_score'],
                        demo_features['noise_score']
                    ], dtype=torch.float32)
                    features_batch[key].append(demo_tensor)
                elif key == 'segment_duration':
                    features_batch[key].append(torch.tensor(sample['features'][key], dtype=torch.float32))
                else:
                    # Convert dict of features to tensor (assuming fixed size)
                    feature_dict = sample['features'][key]
                    if feature_dict:
                        feature_tensor = torch.tensor(list(feature_dict.values()), dtype=torch.float32)
                        features_batch[key].append(feature_tensor)
                    else:
                        # Empty tensor for missing features
                        features_batch[key].append(torch.zeros(1, dtype=torch.float32))

            # Handle targets
            for key in targets_batch.keys():
                targets_batch[key].append(torch.tensor(sample['targets'][key], dtype=torch.float32))

            # Handle metadata
            metadata_batch.append(sample['metadata'])

        # Stack tensors
        for key in features_batch.keys():
            if features_batch[key]:
                features_batch[key] = torch.stack(features_batch[key])

        for key in targets_batch.keys():
            targets_batch[key] = torch.stack(targets_batch[key])

        return {
            'features': features_batch,
            'targets': targets_batch,
            'metadata': metadata_batch
        }

    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=pin_memory,
        collate_fn=collate_fn
    )

    return dataloader


if __name__ == "__main__":
    # Test the dataset
    print("🧪 Testing MMSE Dataset...")

    # Create mock data
    import tempfile
    import soundfile as sf
    import numpy as np

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create mock CSV data
        mock_data = []
        for subject in ['S001', 'S002']:
            for session in ['sess1', 'sess2']:
                for item_id in [1, 2, 3, 6, 10]:  # Sample items
                    mock_data.append({
                        'subject_id': subject,
                        'session_id': session,
                        'age': 65,
                        'sex': 'female',
                        'edu_years': 12,
                        'device': 'smartphone',
                        'noise_label': 'low',
                        'item_id': item_id,
                        'item_type': 'audio',
                        'audio_file': f'{subject}_{session}_{item_id}.wav',
                        'start_s': 0.0,
                        'end_s': 3.0,
                        'gold_score': np.random.randint(0, MMSEDataset.MMSE_ITEMS[item_id]['max_score'] + 1),
                        'gold_total_mmse': 25,
                        'transcript': f'Test transcript for item {item_id}'
                    })

        df = pd.DataFrame(mock_data)
        csv_path = temp_path / 'mock_mmse_data.csv'
        df.to_csv(csv_path, index=False)

        # Create mock audio files
        sample_rate = 16000
        duration = 3.0
        for _, row in df.iterrows():
            audio_path = temp_path / row['audio_file']

            # Generate simple audio
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            audio = 0.3 * np.sin(2 * np.pi * 100 * t)  # 100Hz tone
            audio += 0.01 * np.random.randn(len(audio))  # Add noise

            sf.write(str(audio_path), audio, sample_rate)

        # Test dataset
        try:
            from audio_feature_extractor import AudioFeatureExtractor

            feature_extractor = AudioFeatureExtractor()
            dataset = MMSEDataset(
                data_path=csv_path,
                audio_base_dir=temp_path,
                feature_extractor=feature_extractor,
                cache_features=True
            )

            print(f"✅ Dataset created: {len(dataset)} samples")
            print(f"📊 Item distribution: {dataset.get_item_distribution()}")
            print(f"👥 Subject distribution: {len(dataset.get_subject_distribution())} subjects")

            # Test sample loading
            if len(dataset) > 0:
                sample = dataset[0]
                print(f"✅ Sample loaded: {sample['metadata']['item_name']}")
                print(f"   Features shape: egemaps={len(sample['features']['egemaps'])}, temporal={len(sample['features']['temporal'])}")
                print(f"   Target: item_score={sample['targets']['item_score']:.3f}")

            # Test DataLoader
            dataloader = create_mmse_dataloader(dataset, batch_size=2)
            batch = next(iter(dataloader))
            print(f"✅ DataLoader working: batch size={len(batch['metadata'])}")

        except Exception as e:
            print(f"❌ Dataset test failed: {e}")
            import traceback
            traceback.print_exc()

    print("✅ MMSE Dataset test completed!")

#!/usr/bin/env python3
"""
Multi-Task MMSE Model for Speech-based Cognitive Assessment
==========================================================

PyTorch implementation of multi-task learning model for MMSE prediction:
- Audio encoder with Wav2Vec2
- Feature fusion with transformer/MLP
- Multiple output heads for per-item, total MMSE, and cognitive classification
- Optional brain-age regression

Author: AI Assistant
Date: September 2025
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn import TransformerEncoder, TransformerEncoderLayer
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Union, Any
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class AudioEncoder(nn.Module):
    """
    Audio encoder using pretrained Wav2Vec2 with optional fine-tuning.
    """

    def __init__(self,
                 model_name: str = "facebook/wav2vec2-base-960h",
                 freeze_encoder: bool = True,
                 use_lora: bool = False):
        """
        Initialize audio encoder.

        Args:
            model_name: HuggingFace Wav2Vec2 model name
            freeze_encoder: Whether to freeze the encoder weights
            use_lora: Whether to use LoRA for efficient fine-tuning
        """
        super().__init__()

        try:
            from transformers import Wav2Vec2Model
            self.wav2vec = Wav2Vec2Model.from_pretrained(model_name)
            self.hidden_size = self.wav2vec.config.hidden_size

            if freeze_encoder:
                for param in self.wav2vec.parameters():
                    param.requires_grad = False
                logger.info("✅ Wav2Vec2 encoder frozen")

            # Pooling layers
            self.attention_pool = nn.Sequential(
                nn.Linear(self.hidden_size, self.hidden_size // 2),
                nn.Tanh(),
                nn.Linear(self.hidden_size // 2, 1)
            )

            self.dropout = nn.Dropout(0.1)

        except ImportError:
            logger.warning("⚠️ Transformers not available, using dummy encoder")
            self.hidden_size = 768
            self.wav2vec = None
            self.attention_pool = nn.Linear(self.hidden_size, 1)
            self.dropout = nn.Dropout(0.1)

    def forward(self, input_values: torch.Tensor, attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass through audio encoder.

        Args:
            input_values: Audio input values [batch_size, seq_len]
            attention_mask: Attention mask [batch_size, seq_len]

        Returns:
            Encoded audio features [batch_size, hidden_size]
        """
        if self.wav2vec is None:
            # Dummy encoding for testing
            batch_size = input_values.size(0)
            return torch.randn(batch_size, self.hidden_size)

        # Get Wav2Vec2 features
        outputs = self.wav2vec(input_values, attention_mask=attention_mask)
        hidden_states = outputs.last_hidden_state  # [batch_size, seq_len, hidden_size]

        # Attention pooling
        attention_weights = self.attention_pool(hidden_states)  # [batch_size, seq_len, 1]
        attention_weights = torch.softmax(attention_weights.squeeze(-1), dim=1)  # [batch_size, seq_len]

        # Weighted sum
        pooled = torch.sum(hidden_states * attention_weights.unsqueeze(-1), dim=1)  # [batch_size, hidden_size]

        return self.dropout(pooled)


class FeatureFusion(nn.Module):
    """
    Feature fusion layer combining multiple modalities.
    """

    def __init__(self,
                 audio_dim: int = 768,
                 egemaps_dim: int = 50,
                 temporal_dim: int = 20,
                 quality_dim: int = 10,
                 demo_dim: int = 5,
                 text_dim: int = 768,
                 fusion_dim: int = 512,
                 use_transformer: bool = False,
                 n_heads: int = 8,
                 n_layers: int = 2):
        """
        Initialize feature fusion.

        Args:
            audio_dim: Audio feature dimension
            egemaps_dim: eGeMAPS feature dimension
            temporal_dim: Temporal feature dimension
            quality_dim: Audio quality feature dimension
            demo_dim: Demographic feature dimension
            text_dim: Text feature dimension
            fusion_dim: Hidden dimension for fusion
            use_transformer: Whether to use transformer for fusion
            n_heads: Number of attention heads
            n_layers: Number of transformer layers
        """
        super().__init__()

        self.use_transformer = use_transformer
        self.fusion_dim = fusion_dim

        # Feature projection layers
        self.audio_proj = nn.Linear(audio_dim, fusion_dim // 2)
        self.egemaps_proj = nn.Linear(egemaps_dim, fusion_dim // 4)
        self.temporal_proj = nn.Linear(temporal_dim, fusion_dim // 4)
        self.quality_proj = nn.Linear(quality_dim, fusion_dim // 4)
        self.demo_proj = nn.Linear(demo_dim, fusion_dim // 4)
        self.text_proj = nn.Linear(text_dim, fusion_dim // 2) if text_dim > 0 else None

        # Calculate total input dimension dynamically
        proj_dims = [
            fusion_dim // 2,  # audio
            fusion_dim // 4,  # egemaps
            fusion_dim // 4,  # temporal
            fusion_dim // 4,  # quality
            fusion_dim // 4   # demo
        ]
        total_dim = sum(proj_dims)
        if self.text_proj is not None:
            total_dim += fusion_dim // 2

        # Fusion layer
        if use_transformer:
            encoder_layer = TransformerEncoderLayer(
                d_model=fusion_dim,
                nhead=n_heads,
                dim_feedforward=fusion_dim * 4,
                dropout=0.1,
                batch_first=True
            )
            self.fusion_encoder = TransformerEncoder(encoder_layer, num_layers=n_layers)
            self.fusion_proj = nn.Linear(fusion_dim, fusion_dim)
        else:
            # MLP fusion
            self.fusion_mlp = nn.Sequential(
                nn.Linear(total_dim, fusion_dim),
                nn.ReLU(),
                nn.Dropout(0.1),
                nn.Linear(fusion_dim, fusion_dim),
                nn.ReLU(),
                nn.Dropout(0.1)
            )

        self.layer_norm = nn.LayerNorm(fusion_dim)
        self.dropout = nn.Dropout(0.1)

    def forward(self,
                audio_features: torch.Tensor,
                egemaps_features: Dict[str, float],
                temporal_features: Dict[str, float],
                quality_features: Dict[str, float],
                demo_features: Dict[str, float],
                text_features: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Fuse multiple feature modalities.

        Args:
            audio_features: Audio embeddings [batch_size, audio_dim]
            egemaps_features: eGeMAPS features dict
            temporal_features: Temporal features dict
            quality_features: Quality features dict
            demo_features: Demographic features dict
            text_features: Text embeddings [batch_size, text_dim]

        Returns:
            Fused features [batch_size, fusion_dim]
        """
        # Project each feature group
        audio_proj = self.audio_proj(audio_features)

        # Handle variable-length feature dictionaries by padding/truncating
        def dict_to_tensor(feature_dict, expected_dim, device):
            values = list(feature_dict.values()) if feature_dict else [0.0] * expected_dim
            # Pad or truncate to expected dimension
            if len(values) < expected_dim:
                values.extend([0.0] * (expected_dim - len(values)))
            elif len(values) > expected_dim:
                values = values[:expected_dim]
            tensor = torch.tensor(values, dtype=torch.float32, device=device)
            return tensor.unsqueeze(0).expand(audio_features.size(0), -1)

        egemaps_tensor = dict_to_tensor(egemaps_features, self.egemaps_proj.in_features, audio_features.device)
        egemaps_proj = self.egemaps_proj(egemaps_tensor)

        temporal_tensor = dict_to_tensor(temporal_features, self.temporal_proj.in_features, audio_features.device)
        temporal_proj = self.temporal_proj(temporal_tensor)

        quality_tensor = dict_to_tensor(quality_features, self.quality_proj.in_features, audio_features.device)
        quality_proj = self.quality_proj(quality_tensor)

        demo_tensor = dict_to_tensor(demo_features, self.demo_proj.in_features, audio_features.device)
        demo_proj = self.demo_proj(demo_tensor)

        # Concatenate all features
        feature_list = [audio_proj, egemaps_proj, temporal_proj, quality_proj, demo_proj]

        if text_features is not None and self.text_proj is not None:
            text_proj = self.text_proj(text_features)
            feature_list.append(text_proj)

        fused = torch.cat(feature_list, dim=1)

        # Apply fusion
        if self.use_transformer:
            # Add batch dimension for transformer
            fused = fused.unsqueeze(1)  # [batch_size, 1, total_dim]
            fused = self.fusion_encoder(fused)
            fused = fused.squeeze(1)  # [batch_size, fusion_dim]
            fused = self.fusion_proj(fused)
        else:
            fused = self.fusion_mlp(fused)

        # Final processing
        fused = self.layer_norm(fused)
        fused = self.dropout(fused)

        return fused


class MMSEOutputHeads(nn.Module):
    """
    Multiple output heads for MMSE prediction tasks.
    """

    def __init__(self,
                 input_dim: int = 512,
                 num_items: int = 12,
                 hidden_dim: int = 256,
                 use_brain_age: bool = False):
        """
        Initialize output heads.

        Args:
            input_dim: Input feature dimension
            num_items: Number of MMSE items (12)
            hidden_dim: Hidden dimension for heads
            use_brain_age: Whether to include brain-age regression
        """
        super().__init__()

        self.num_items = num_items
        self.use_brain_age = use_brain_age

        # Per-item score prediction heads (12 parallel MLPs)
        self.item_heads = nn.ModuleList([
            nn.Sequential(
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.1),
                nn.Linear(hidden_dim, 1),  # Single score output
                nn.Sigmoid()  # Output between 0-1
            ) for _ in range(num_items)
        ])

        # Total MMSE prediction head
        self.total_mmse_head = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()  # Output between 0-1 (will be scaled to 0-30)
        )

        # Cognitive classification head (NC/MCI/Dementia)
        self.cognitive_class_head = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 3)  # 3 classes
        )

        # Optional brain-age regression head
        if use_brain_age:
            self.brain_age_head = nn.Sequential(
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.1),
                nn.Linear(hidden_dim, 1)
            )

    def forward(self, features: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Forward pass through all output heads.

        Args:
            features: Input features [batch_size, input_dim]

        Returns:
            Dictionary with all predictions
        """
        outputs = {}

        # Per-item predictions
        item_predictions = []
        for i, head in enumerate(self.item_heads):
            pred = head(features).squeeze(-1)  # [batch_size]
            item_predictions.append(pred)
        outputs['item_scores'] = torch.stack(item_predictions, dim=1)  # [batch_size, num_items]

        # Total MMSE prediction
        outputs['total_mmse'] = self.total_mmse_head(features).squeeze(-1)  # [batch_size]

        # Cognitive classification
        outputs['cognitive_logits'] = self.cognitive_class_head(features)  # [batch_size, 3]
        outputs['cognitive_probs'] = F.softmax(outputs['cognitive_logits'], dim=1)

        # Brain age prediction (if enabled)
        if self.use_brain_age:
            outputs['brain_age'] = self.brain_age_head(features).squeeze(-1)

        return outputs


class MultiTaskMMSEModel(nn.Module):
    """
    Complete multi-task MMSE model for speech-based cognitive assessment.
    """

    def __init__(self,
                 # Audio encoder config
                 wav2vec_model: str = "facebook/wav2vec2-base-960h",
                 freeze_audio_encoder: bool = True,

                 # Fusion config
                 fusion_dim: int = 512,
                 use_transformer_fusion: bool = False,

                 # Output config
                 num_items: int = 12,
                 use_brain_age: bool = False,

                 # Feature dimensions (keyword arguments)
                 **feature_dims):
        """
        Initialize multi-task MMSE model.

        Args:
            wav2vec_model: Wav2Vec2 model name
            freeze_audio_encoder: Whether to freeze audio encoder
            fusion_dim: Fusion layer hidden dimension
            use_transformer_fusion: Use transformer for fusion
            num_items: Number of MMSE items
            use_brain_age: Include brain-age prediction
            egemaps_dim: eGeMAPS feature dimension
            temporal_dim: Temporal feature dimension
            quality_dim: Audio quality dimension
            demo_dim: Demographic feature dimension
            text_dim: Text feature dimension
        """
        super().__init__()

        # Audio encoder
        self.audio_encoder = AudioEncoder(
            model_name=wav2vec_model,
            freeze_encoder=freeze_audio_encoder
        )

        # Extract feature dimensions with defaults
        egemaps_dim = feature_dims.get('egemaps', 50)
        temporal_dim = feature_dims.get('temporal', 20)
        quality_dim = feature_dims.get('quality', 10)
        demo_dim = feature_dims.get('demo', 5)
        text_dim = feature_dims.get('text', 0)  # Default to 0 to disable text

        # Feature fusion
        self.feature_fusion = FeatureFusion(
            audio_dim=self.audio_encoder.hidden_size,
            egemaps_dim=egemaps_dim,
            temporal_dim=temporal_dim,
            quality_dim=quality_dim,
            demo_dim=demo_dim,
            text_dim=text_dim,
            fusion_dim=fusion_dim,
            use_transformer=use_transformer_fusion
        )

        # Output heads
        self.output_heads = MMSEOutputHeads(
            input_dim=fusion_dim,
            num_items=num_items,
            use_brain_age=use_brain_age
        )

        # Model configuration
        self.config = {
            'wav2vec_model': wav2vec_model,
            'freeze_audio_encoder': freeze_audio_encoder,
            'fusion_dim': fusion_dim,
            'use_transformer_fusion': use_transformer_fusion,
            'num_items': num_items,
            'use_brain_age': use_brain_age,
            'feature_dims': feature_dims.copy()
        }

        logger.info("✅ Multi-task MMSE model initialized")
        logger.info(f"   Audio encoder: {wav2vec_model}")
        logger.info(f"   Fusion: {'Transformer' if use_transformer_fusion else 'MLP'} ({fusion_dim} dim)")
        logger.info(f"   Tasks: {num_items} items + total MMSE + cognitive class")

    def forward(self,
                audio_input: Optional[torch.Tensor] = None,
                egemaps_features: Optional[Dict[str, float]] = None,
                temporal_features: Optional[Dict[str, float]] = None,
                quality_features: Optional[Dict[str, float]] = None,
                demo_features: Optional[Dict[str, float]] = None,
                text_features: Optional[torch.Tensor] = None,
                return_features: bool = False) -> Dict[str, torch.Tensor]:
        """
        Forward pass through the complete model.

        Args:
            audio_input: Raw audio input [batch_size, seq_len]
            egemaps_features: eGeMAPS features
            temporal_features: Temporal features
            quality_features: Audio quality features
            demo_features: Demographic features
            text_features: Text embeddings [batch_size, text_dim]
            return_features: Whether to return intermediate features

        Returns:
            Dictionary with all predictions
        """
        # Default empty features
        if egemaps_features is None:
            egemaps_features = {}
        if temporal_features is None:
            temporal_features = {}
        if quality_features is None:
            quality_features = {}
        if demo_features is None:
            demo_features = {}

        # Encode audio if provided
        if audio_input is not None:
            audio_features = self.audio_encoder(audio_input)
        else:
            # Use dummy audio features for testing
            batch_size = 1
            audio_features = torch.randn(batch_size, self.audio_encoder.hidden_size, device=next(self.parameters()).device)

        # Fuse all features
        fused_features = self.feature_fusion(
            audio_features=audio_features,
            egemaps_features=egemaps_features,
            temporal_features=temporal_features,
            quality_features=quality_features,
            demo_features=demo_features,
            text_features=text_features
        )

        # Get predictions from all heads
        outputs = self.output_heads(fused_features)

        if return_features:
            outputs['fused_features'] = fused_features
            outputs['audio_features'] = audio_features

        return outputs

    def predict_mmse_total(self,
                          audio_input: Optional[torch.Tensor] = None,
                          **feature_dicts) -> torch.Tensor:
        """
        Predict total MMSE score only.

        Args:
            audio_input: Raw audio input
            feature_dicts: Feature dictionaries

        Returns:
            Total MMSE predictions [batch_size] (scaled 0-30)
        """
        outputs = self.forward(audio_input, **feature_dicts)
        return outputs['total_mmse'] * 30.0  # Scale to 0-30

    def predict_item_scores(self,
                           audio_input: Optional[torch.Tensor] = None,
                           **feature_dicts) -> torch.Tensor:
        """
        Predict per-item scores.

        Args:
            audio_input: Raw audio input
            feature_dicts: Feature dictionaries

        Returns:
            Item score predictions [batch_size, num_items]
        """
        outputs = self.forward(audio_input, **feature_dicts)
        return outputs['item_scores']

    def predict_cognitive_class(self,
                               audio_input: Optional[torch.Tensor] = None,
                               **feature_dicts) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Predict cognitive classification.

        Args:
            audio_input: Raw audio input
            feature_dicts: Feature dictionaries

        Returns:
            Tuple of (predicted_classes, probabilities)
        """
        outputs = self.forward(audio_input, **feature_dicts)
        pred_classes = torch.argmax(outputs['cognitive_logits'], dim=1)
        return pred_classes, outputs['cognitive_probs']

    def get_model_info(self) -> Dict[str, Any]:
        """Get model configuration and statistics."""
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)

        return {
            'config': self.config,
            'total_parameters': total_params,
            'trainable_parameters': trainable_params,
            'frozen_parameters': total_params - trainable_params,
            'model_size_mb': total_params * 4 / (1024 * 1024)  # Rough estimate
        }


def create_mmse_model(config_path: Optional[str] = None) -> MultiTaskMMSEModel:
    """
    Factory function to create MMSE model with default or custom config.

    Args:
        config_path: Path to JSON config file

    Returns:
        Configured MultiTaskMMSEModel
    """
    # Default configuration
    default_config = {
        'wav2vec_model': 'facebook/wav2vec2-base-960h',
        'freeze_audio_encoder': True,
        'fusion_dim': 512,
        'use_transformer_fusion': False,
        'num_items': 12,
        'use_brain_age': False,
        'feature_dims': {
            'egemaps': 50,
            'temporal': 20,
            'quality': 10,
            'demo': 5,
            'text': 0  # Disable text by default
        }
    }

    # Load custom config if provided
    if config_path:
        import json
        with open(config_path, 'r') as f:
            custom_config = json.load(f)
        default_config.update(custom_config)

    # Extract feature dimensions and ensure text is disabled by default
    feature_dims = default_config.pop('feature_dims', {})
    feature_dims['text'] = feature_dims.get('text', 0)  # Force text_dim=0 by default
    model = MultiTaskMMSEModel(**default_config, **feature_dims)

    return model


if __name__ == "__main__":
    # Test the model
    print("🧪 Testing Multi-Task MMSE Model...")

    try:
        # Create model
        model = create_mmse_model()

        # Get model info
        info = model.get_model_info()
        print(f"✅ Model created: {info['total_parameters']} parameters")
        print(f"   Trainable: {info['trainable_parameters']}")
        print(f"   Frozen: {info['frozen_parameters']}")

            # Force recreate model to avoid cached instances
        model = create_mmse_model()

        # Test forward pass with dummy data
        batch_size = 2

        # Dummy features (expand to match expected dimensions)
        egemaps = {f'feat_{i}': float(i) for i in range(50)}  # 50 features as expected
        temporal = {f'temp_{i}': float(i) for i in range(20)}  # 20 features as expected
        quality = {f'qual_{i}': float(i) for i in range(10)}   # 10 features as expected
        demo = {f'demo_{i}': float(i) for i in range(5)}       # 5 features as expected

        # Forward pass
        with torch.no_grad():
            outputs = model.forward(
                audio_input=None,  # Use dummy audio
                egemaps_features=egemaps,
                temporal_features=temporal,
                quality_features=quality,
                demo_features=demo
            )

        print("✅ Forward pass successful!")
        print(f"   Item scores shape: {outputs['item_scores'].shape}")
        print(f"   Total MMSE shape: {outputs['total_mmse'].shape}")
        print(f"   Cognitive probs shape: {outputs['cognitive_probs'].shape}")

        # Test specific prediction methods
        total_pred = model.predict_mmse_total(None, egemaps_features=egemaps, temporal_features=temporal,
                                            quality_features=quality, demo_features=demo)
        print(f"   Total MMSE prediction: {total_pred.item():.1f}")

        class_pred, class_probs = model.predict_cognitive_class(None, egemaps_features=egemaps,
                                                              temporal_features=temporal,
                                                              quality_features=quality, demo_features=demo)
        print(f"   Cognitive class prediction: {class_pred.item()} (prob: {class_probs[0][class_pred].item():.3f})")

    except Exception as e:
        print(f"❌ Model test failed: {e}")
        import traceback
        traceback.print_exc()

    print("✅ Multi-Task MMSE Model test completed!")

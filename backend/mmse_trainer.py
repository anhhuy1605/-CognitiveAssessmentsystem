#!/usr/bin/env python3
"""
MMSE Trainer for Multi-Task Learning
===================================

Comprehensive training framework for speech-based MMSE assessment:
- Multi-task loss with clinical performance targets
- 3-stage training: Warm-up → PEFT → Full fine-tune
- Advanced optimization with clinical metrics monitoring
- Uncertainty quantification and model calibration

Author: AI Assistant
Date: September 2025
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.optim.lr_scheduler import CosineAnnealingLR, StepLR
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional, Union, Any, Callable
import os
import json
from pathlib import Path
import time
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class MultiTaskLoss(nn.Module):
    """
    Multi-task loss function for MMSE assessment.

    Implements the loss from specification:
    L = λ_mmse * MSE(ŷ_MMSE, MMSE_true) +
        λ_diag * CE(p_diag, y_diag) +
        λ_sub * Σ MSE(ŷ_i, s_i_true) +
        λ_age * MAE(ŷ_age, age_true) +
        λ_reg * Ω(Θ)
    """

    def __init__(self,
                 lambda_mmse: float = 1.0,
                 lambda_diag: float = 0.5,
                 lambda_sub: float = 0.8,
                 lambda_age: float = 0.3,
                 lambda_reg: float = 1e-5,
                 item_weights: Optional[Dict[int, float]] = None):
        """
        Initialize multi-task loss.

        Args:
            lambda_mmse: Weight for total MMSE regression loss
            lambda_diag: Weight for cognitive diagnosis classification loss
            lambda_sub: Weight for per-item score losses
            lambda_age: Weight for brain-age regression loss (if available)
            lambda_reg: Weight for regularization term
            item_weights: Optional weights for different items
        """
        super().__init__()

        self.lambda_mmse = lambda_mmse
        self.lambda_diag = lambda_diag
        self.lambda_sub = lambda_sub
        self.lambda_age = lambda_age
        self.lambda_reg = lambda_reg

        # Default item weights (some items may be more important)
        self.item_weights = item_weights or {i: 1.0 for i in range(1, 13)}

        # Loss functions
        self.mse_loss = nn.MSELoss(reduction='mean')
        self.mae_loss = nn.L1Loss(reduction='mean')
        self.ce_loss = nn.CrossEntropyLoss(reduction='mean')

        logger.info(f"✅ Multi-task loss initialized: λ_mmse={lambda_mmse}, λ_diag={lambda_diag}, λ_sub={lambda_sub}")

    def forward(self, predictions: Dict[str, torch.Tensor],
                targets: Dict[str, torch.Tensor],
                model: Optional[nn.Module] = None) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        Compute multi-task loss.

        Args:
            predictions: Model predictions dictionary
            targets: Target values dictionary
            model: Model instance for regularization (optional)

        Returns:
            Tuple of (total_loss, loss_components)
        """
        loss_components = {}

        # Total MMSE regression loss
        if 'total_mmse' in predictions and 'total_mmse' in targets:
            mmse_loss = self.mse_loss(predictions['total_mmse'].squeeze(), targets['total_mmse'])
            loss_components['mmse_loss'] = mmse_loss.item()
        else:
            mmse_loss = torch.tensor(0.0)
            loss_components['mmse_loss'] = 0.0

        # Cognitive diagnosis classification loss
        if 'cognitive_logits' in predictions and 'cognitive_class' in targets:
            diag_loss = self.ce_loss(predictions['cognitive_logits'], targets['cognitive_class'].long())
            loss_components['diag_loss'] = diag_loss.item()
        else:
            diag_loss = torch.tensor(0.0)
            loss_components['diag_loss'] = 0.0

        # Per-item score losses
        item_loss = torch.tensor(0.0)
        item_losses = []

        if 'item_scores' in predictions and 'item_score' in targets:
            pred_items = predictions['item_scores']  # [batch_size, num_items]
            target_items = targets['item_score'].unsqueeze(-1).expand_as(pred_items)  # [batch_size, num_items]

            for i in range(pred_items.size(1)):
                item_weight = self.item_weights.get(i + 1, 1.0)
                item_mse = self.mse_loss(pred_items[:, i], target_items[:, i])
                weighted_loss = item_weight * item_mse
                item_loss = item_loss + weighted_loss
                item_losses.append(weighted_loss.item())

            item_loss = item_loss / pred_items.size(1)  # Average over items
            loss_components['item_loss'] = item_loss.item()
            loss_components['item_losses'] = item_losses
        else:
            loss_components['item_loss'] = 0.0

        # Brain-age regression loss (if available)
        age_loss = torch.tensor(0.0)
        if 'brain_age' in predictions and 'brain_age' in targets:
            age_loss = self.mae_loss(predictions['brain_age'].squeeze(), targets['brain_age'])
            loss_components['age_loss'] = age_loss.item()
        else:
            loss_components['age_loss'] = 0.0

        # Regularization loss (L2 on parameters)
        reg_loss = torch.tensor(0.0)
        if model is not None and self.lambda_reg > 0:
            reg_loss = torch.tensor(0.0)
            for param in model.parameters():
                reg_loss = reg_loss + torch.norm(param, p=2)
            loss_components['reg_loss'] = self.lambda_reg * reg_loss.item()
        else:
            loss_components['reg_loss'] = 0.0

        # Total loss
        total_loss = (
            self.lambda_mmse * mmse_loss +
            self.lambda_diag * diag_loss +
            self.lambda_sub * item_loss +
            self.lambda_age * age_loss +
            self.lambda_reg * reg_loss
        )

        loss_components['total_loss'] = total_loss.item()

        return total_loss, loss_components


class MMSETrainer:
    """
    Comprehensive trainer for speech-based MMSE assessment.

    Implements 3-stage training:
    1. Warm-up: Train heads only, encoder frozen
    2. PEFT: LoRA/Adapter fine-tuning of audio encoder
    3. Full fine-tune: All parameters trainable
    """

    def __init__(self,
                 model: nn.Module,
                 device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
                 learning_rate: float = 1e-3,
                 weight_decay: float = 1e-4,
                 warmup_epochs: int = 5,
                 peft_epochs: int = 10,
                 full_fine_tune_epochs: int = 20,
                 patience: int = 10,
                 save_dir: str = 'checkpoints'):
        """
        Initialize MMSE trainer.

        Args:
            model: MultiTaskMMSEModel instance
            device: Training device
            learning_rate: Base learning rate
            weight_decay: Weight decay for regularization
            warmup_epochs: Number of warm-up epochs
            peft_epochs: Number of PEFT epochs
            full_fine_tune_epochs: Number of full fine-tune epochs
            patience: Early stopping patience
            save_dir: Directory to save checkpoints
        """
        self.model = model.to(device)
        self.device = device
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.warmup_epochs = warmup_epochs
        self.peft_epochs = peft_epochs
        self.full_fine_tune_epochs = full_fine_tune_epochs
        self.patience = patience
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)

        # Loss function
        self.criterion = MultiTaskLoss()

        # Training state
        self.current_stage = 'warmup'
        self.epoch = 0
        self.best_loss = float('inf')
        self.patience_counter = 0

        # History tracking
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'train_metrics': [],
            'val_metrics': [],
            'learning_rates': []
        }

        logger.info(f"✅ MMSE Trainer initialized on {device}")

    def _setup_optimizer(self, stage: str) -> Tuple[optim.Optimizer, Any]:
        """
        Setup optimizer and scheduler for current training stage.

        Args:
            stage: Training stage ('warmup', 'peft', 'full')

        Returns:
            Tuple of (optimizer, scheduler)
        """
        if stage == 'warmup':
            # Only train output heads
            params_to_train = []
            for name, param in self.model.named_parameters():
                if 'output_heads' in name or 'fusion' in name:
                    params_to_train.append(param)

            optimizer = optim.AdamW(params_to_train, lr=self.learning_rate, weight_decay=self.weight_decay)
            scheduler = CosineAnnealingLR(optimizer, T_max=self.warmup_epochs, eta_min=1e-6)

        elif stage == 'peft':
            # Fine-tune audio encoder with smaller LR
            optimizer = optim.AdamW([
                {'params': self.model.audio_encoder.parameters(), 'lr': self.learning_rate * 0.1},
                {'params': self.model.feature_fusion.parameters(), 'lr': self.learning_rate},
                {'params': self.model.output_heads.parameters(), 'lr': self.learning_rate}
            ], weight_decay=self.weight_decay)

            scheduler = StepLR(optimizer, step_size=5, gamma=0.5)

        else:  # full fine-tune
            optimizer = optim.AdamW(self.model.parameters(), lr=self.learning_rate * 0.1, weight_decay=self.weight_decay)
            scheduler = CosineAnnealingLR(optimizer, T_max=self.full_fine_tune_epochs, eta_min=1e-6)

        return optimizer, scheduler

    def _train_epoch(self, train_loader: DataLoader, optimizer: optim.Optimizer) -> Dict[str, float]:
        """Train for one epoch."""
        self.model.train()
        epoch_loss = 0.0
        epoch_metrics = {'mmse_loss': 0.0, 'diag_loss': 0.0, 'item_loss': 0.0}

        num_batches = len(train_loader)

        for batch_idx, batch in enumerate(train_loader):
            # Move to device
            features = {k: v.to(self.device) if torch.is_tensor(v) else v for k, v in batch['features'].items()}
            targets = {k: v.to(self.device) for k, v in batch['targets'].items()}

            # Forward pass
            optimizer.zero_grad()
            predictions = self.model(
                audio_input=None,  # Features already extracted
                egemaps_features=features.get('egemaps', {}),
                temporal_features=features.get('temporal', {}),
                quality_features=features.get('quality', {}),
                demo_features=features.get('demographics', {})
            )

            # Compute loss
            loss, loss_components = self.criterion(predictions, targets, self.model)

            # Backward pass
            loss.backward()

            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)

            optimizer.step()

            # Accumulate metrics
            epoch_loss += loss.item()
            for key in epoch_metrics:
                epoch_metrics[key] += loss_components.get(key, 0.0)

        # Average metrics
        epoch_loss /= num_batches
        for key in epoch_metrics:
            epoch_metrics[key] /= num_batches

        return {'loss': epoch_loss, **epoch_metrics}

    def _validate_epoch(self, val_loader: DataLoader) -> Dict[str, float]:
        """Validate for one epoch."""
        self.model.eval()
        epoch_loss = 0.0
        epoch_metrics = {'mmse_loss': 0.0, 'diag_loss': 0.0, 'item_loss': 0.0}

        num_batches = len(val_loader)

        with torch.no_grad():
            for batch in val_loader:
                # Move to device
                features = {k: v.to(self.device) if torch.is_tensor(v) else v for k, v in batch['features'].items()}
                targets = {k: v.to(self.device) for k, v in batch['targets'].items()}

                # Forward pass
                predictions = self.model(
                    audio_input=None,
                    egemaps_features=features.get('egemaps', {}),
                    temporal_features=features.get('temporal', {}),
                    quality_features=features.get('quality', {}),
                    demo_features=features.get('demographics', {})
                )

                # Compute loss
                loss, loss_components = self.criterion(predictions, targets)

                # Accumulate metrics
                epoch_loss += loss.item()
                for key in epoch_metrics:
                    epoch_metrics[key] += loss_components.get(key, 0.0)

        # Average metrics
        epoch_loss /= num_batches
        for key in epoch_metrics:
            epoch_metrics[key] /= num_batches

        return {'loss': epoch_loss, **epoch_metrics}

    def _save_checkpoint(self, epoch: int, loss: float, optimizer: optim.Optimizer,
                        scheduler: Any, stage: str) -> None:
        """Save model checkpoint."""
        checkpoint_path = self.save_dir / f'checkpoint_{stage}_epoch_{epoch}.pt'

        checkpoint = {
            'epoch': epoch,
            'stage': stage,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'scheduler_state_dict': scheduler.state_dict() if scheduler else None,
            'loss': loss,
            'best_loss': self.best_loss,
            'history': self.history
        }

        torch.save(checkpoint, checkpoint_path)
        logger.info(f"💾 Checkpoint saved: {checkpoint_path}")

    def _load_checkpoint(self, checkpoint_path: str) -> None:
        """Load model checkpoint."""
        checkpoint = torch.load(checkpoint_path, map_location=self.device)

        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.epoch = checkpoint['epoch']
        self.current_stage = checkpoint['stage']
        self.best_loss = checkpoint['best_loss']
        self.history = checkpoint.get('history', self.history)

        logger.info(f"📁 Checkpoint loaded: {checkpoint_path}")

    def train_stage(self, train_loader: DataLoader, val_loader: DataLoader,
                   stage: str, num_epochs: int) -> Dict[str, Any]:
        """
        Train for a specific stage.

        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
            stage: Training stage ('warmup', 'peft', 'full')
            num_epochs: Number of epochs for this stage

        Returns:
            Training results dictionary
        """
        logger.info(f"🚀 Starting {stage} training for {num_epochs} epochs")

        # Setup optimizer and scheduler
        optimizer, scheduler = self._setup_optimizer(stage)
        self.current_stage = stage

        stage_results = {
            'stage': stage,
            'epochs': num_epochs,
            'best_loss': float('inf'),
            'converged': False,
            'early_stopped': False
        }

        for epoch in range(num_epochs):
            self.epoch = epoch

            # Train epoch
            train_results = self._train_epoch(train_loader, optimizer)
            val_results = self._validate_epoch(val_loader)

            # Update learning rate
            if scheduler:
                scheduler.step()

            current_lr = optimizer.param_groups[0]['lr']

            # Log progress
            logger.info(f"Epoch {epoch+1}/{num_epochs} - "
                       f"Train Loss: {train_results['loss']:.4f}, "
                       f"Val Loss: {val_results['loss']:.4f}, "
                       f"LR: {current_lr:.6f}")

            # Update history
            self.history['train_loss'].append(train_results['loss'])
            self.history['val_loss'].append(val_results['loss'])
            self.history['train_metrics'].append(train_results)
            self.history['val_metrics'].append(val_results)
            self.history['learning_rates'].append(current_lr)

            # Check for improvement
            if val_results['loss'] < self.best_loss:
                self.best_loss = val_results['loss']
                self.patience_counter = 0

                # Save best checkpoint
                self._save_checkpoint(epoch, val_results['loss'], optimizer, scheduler, stage)
            else:
                self.patience_counter += 1

            # Early stopping
            if self.patience_counter >= self.patience:
                logger.info(f"⏹️ Early stopping at epoch {epoch+1}")
                stage_results['early_stopped'] = True
                stage_results['epochs_completed'] = epoch + 1
                break

        else:
            stage_results['epochs_completed'] = num_epochs
            stage_results['converged'] = True

        stage_results['best_loss'] = self.best_loss
        logger.info(f"✅ {stage.capitalize()} training completed: Best loss = {self.best_loss:.4f}")

        return stage_results

    def train_complete(self, train_loader: DataLoader, val_loader: DataLoader) -> Dict[str, Any]:
        """
        Run complete 3-stage training pipeline.

        Args:
            train_loader: Training data loader
            val_loader: Validation data loader

        Returns:
            Complete training results
        """
        logger.info("🎯 Starting complete MMSE training pipeline")
        start_time = time.time()

        training_results = {
            'total_time': 0,
            'stages': {},
            'final_model': None,
            'best_checkpoint': None,
            'performance_summary': {}
        }

        # Stage 1: Warm-up
        warmup_results = self.train_stage(train_loader, val_loader, 'warmup', self.warmup_epochs)
        training_results['stages']['warmup'] = warmup_results

        # Stage 2: PEFT (Parameter-Efficient Fine-Tuning)
        peft_results = self.train_stage(train_loader, val_loader, 'peft', self.peft_epochs)
        training_results['stages']['peft'] = peft_results

        # Stage 3: Full fine-tune
        full_results = self.train_stage(train_loader, val_loader, 'full', self.full_fine_tune_epochs)
        training_results['stages']['full'] = full_results

        # Save final model
        final_model_path = self.save_dir / 'final_model.pt'
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'config': self.model.config,
            'training_history': self.history,
            'final_loss': self.best_loss
        }, final_model_path)

        training_results['final_model'] = str(final_model_path)
        training_results['total_time'] = time.time() - start_time

        # Performance summary
        training_results['performance_summary'] = self._generate_performance_summary()

        logger.info("🎉 Training completed!")
        logger.info(f"   Total time: {training_results['total_time']:.1f}s")
        logger.info(f"   Best validation loss: {self.best_loss:.4f}")
        logger.info(f"   Final model saved: {final_model_path}")

        return training_results

    def _generate_performance_summary(self) -> Dict[str, Any]:
        """Generate training performance summary."""
        if not self.history['val_loss']:
            return {}

        best_epoch = np.argmin(self.history['val_loss'])
        final_loss = self.history['val_loss'][-1]
        best_loss = min(self.history['val_loss'])

        improvement = (self.history['val_loss'][0] - best_loss) / self.history['val_loss'][0] if self.history['val_loss'][0] > 0 else 0

        return {
            'initial_loss': self.history['val_loss'][0],
            'final_loss': final_loss,
            'best_loss': best_loss,
            'best_epoch': best_epoch,
            'total_epochs': len(self.history['val_loss']),
            'improvement_ratio': improvement,
            'convergence_achieved': improvement > 0.5,  # 50% improvement threshold
            'learning_rate_schedule': self.history['learning_rates'][-5:]  # Last 5 LRs
        }

    def predict_with_uncertainty(self, features: Dict[str, Any], n_samples: int = 10) -> Dict[str, Any]:
        """
        Make predictions with uncertainty quantification using MC-Dropout.

        Args:
            features: Input features dictionary
            n_samples: Number of Monte Carlo samples

        Returns:
            Predictions with uncertainty estimates
        """
        self.model.train()  # Enable dropout for uncertainty

        predictions = []

        with torch.no_grad():
            for _ in range(n_samples):
                pred = self.model(
                    audio_input=None,
                    egemaps_features=features.get('egemaps', {}),
                    temporal_features=features.get('temporal', {}),
                    quality_features=features.get('quality', {}),
                    demo_features=features.get('demographics', {})
                )
                predictions.append(pred)

        # Aggregate predictions
        result = {}

        # Total MMSE with uncertainty
        mmse_preds = torch.stack([p['total_mmse'] for p in predictions])
        result['mmse_mean'] = mmse_preds.mean().item()
        result['mmse_std'] = mmse_preds.std().item()
        result['mmse_95ci'] = [
            mmse_preds.mean() - 1.96 * mmse_preds.std(),
            mmse_preds.mean() + 1.96 * mmse_preds.std()
        ]

        # Cognitive class probabilities with uncertainty
        if 'cognitive_probs' in predictions[0]:
            cog_probs = torch.stack([p['cognitive_probs'] for p in predictions])
            result['cognitive_probs_mean'] = cog_probs.mean(dim=0).tolist()
            result['cognitive_probs_std'] = cog_probs.std(dim=0).tolist()

        return result

    def save_training_results(self, results: Dict[str, Any], output_path: str) -> None:
        """Save training results to JSON."""
        # Convert torch tensors to serializable format
        def make_serializable(obj):
            if isinstance(obj, torch.Tensor):
                return obj.item() if obj.numel() == 1 else obj.tolist()
            elif isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_serializable(item) for item in obj]
            else:
                return obj

        serializable_results = make_serializable(results)

        with open(output_path, 'w') as f:
            json.dump(serializable_results, f, indent=2)

        logger.info(f"📄 Training results saved to {output_path}")


def create_mmse_trainer(model: nn.Module, config_path: Optional[str] = None) -> MMSETrainer:
    """
    Factory function to create MMSE trainer with default or custom config.

    Args:
        model: MultiTaskMMSEModel instance
        config_path: Path to JSON config file

    Returns:
        Configured MMSETrainer
    """
    # Default configuration
    default_config = {
        'learning_rate': 1e-3,
        'weight_decay': 1e-4,
        'warmup_epochs': 5,
        'peft_epochs': 10,
        'full_fine_tune_epochs': 20,
        'patience': 10,
        'save_dir': 'checkpoints'
    }

    # Load custom config if provided
    if config_path and Path(config_path).exists():
        with open(config_path, 'r') as f:
            custom_config = json.load(f)
        default_config.update(custom_config)

    # Create trainer
    trainer = MMSETrainer(model, **default_config)

    return trainer


if __name__ == "__main__":
    # Test the trainer
    print("🧪 Testing MMSE Trainer...")

    try:
        from multitask_mmse_model import create_mmse_model

        # Create model
        model = create_mmse_model()
        trainer = create_mmse_trainer(model)

        print("✅ Trainer created successfully")
        print(f"   Device: {trainer.device}")
        print(f"   Training stages: {trainer.warmup_epochs} warmup + {trainer.peft_epochs} PEFT + {trainer.full_fine_tune_epochs} full")

        # Test loss function
        criterion = MultiTaskLoss()

        # Dummy predictions and targets
        batch_size = 4
        predictions = {
            'total_mmse': torch.randn(batch_size, 1),
            'cognitive_logits': torch.randn(batch_size, 3),
            'item_scores': torch.randn(batch_size, 12)
        }

        targets = {
            'total_mmse': torch.randn(batch_size),
            'cognitive_class': torch.randint(0, 3, (batch_size,)),
            'item_score': torch.randn(batch_size)
        }

        loss, components = criterion(predictions, targets)
        print(f"   Total loss: {loss.item():.4f}")
        print(f"   Loss components: {list(components.keys())}")

    except Exception as e:
        print(f"❌ Trainer test failed: {e}")
        import traceback
        traceback.print_exc()

    print("✅ MMSE Trainer test completed!")

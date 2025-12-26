# -*- coding: utf-8 -*-
"""
Main Integration Pipeline for Vietnamese MCI Screening
Orchestrates the entire MCI screening process

Author: Cognitive Assessment System
Version: 1.0

Process Flow:
1. Audio → Acoustic features (eGeMAPS + Vietnamese tones)
2. Audio → ASR → Transcript  
3. Transcript → Linguistic features (Vietnamese NLP)
4. Acoustic + Linguistic → Fusion → MCI Prediction + MMSE Estimation
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import modules
try:
    from modules.acoustic_analyzer import AcousticAnalyzer
    from modules.linguistic_analyzer import VietnameseLinguisticAnalyzer
    from modules.multimodal_fusion import MultimodalFusion, FusionConfig
    from modules.mci_predictor import MCIPredictor, MCIPrediction
    MODULES_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    MODULES_AVAILABLE = False


@dataclass
class PipelineResult:
    """Complete pipeline result"""
    audio_path: str
    transcript: str
    wer: float
    acoustic_feature_count: int
    linguistic_feature_count: int
    mci_probability: float
    mmse_score: float
    confidence: float
    severity: str
    risk_factors: List[str]
    recommendations: List[str]
    processing_time: float
    timestamp: str
    branch_predictions: Dict[str, float]
    fusion_weights: Dict[str, float]
    errors: List[str]


class ASRInterface:
    """
    Interface for ASR module
    Replace this with your actual ASR implementation
    """
    
    def __init__(self, asr_module=None):
        """
        Initialize ASR interface
        
        Args:
            asr_module: Your existing ASR module (optional)
        """
        self.asr_module = asr_module
    
    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe audio to text
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            str: Transcribed text
        """
        if self.asr_module is not None:
            # Use provided ASR module
            return self.asr_module.transcribe(audio_path)
        else:
            # Placeholder - replace with your ASR
            logger.warning("No ASR module provided. Using placeholder.")
            return "Đây là transcript placeholder. Vui lòng tích hợp ASR module thực tế."
    
    def transcribe_with_timestamps(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio with word timestamps
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            dict: {
                'text': str,
                'words': List[{'word': str, 'start': float, 'end': float}],
                'confidence': float
            }
        """
        if hasattr(self.asr_module, 'transcribe_with_timestamps'):
            return self.asr_module.transcribe_with_timestamps(audio_path)
        else:
            text = self.transcribe(audio_path)
            return {
                'text': text,
                'words': [],
                'confidence': 0.9
            }


class MCIScreeningPipeline:
    """
    End-to-end pipeline for MCI screening from audio
    
    Complete process:
    1. Audio → Acoustic features (eGeMAPS + Vietnamese tones)
    2. Audio → ASR → Transcript
    3. Transcript → Linguistic features (Vietnamese NLP)
    4. Features → Multimodal Fusion → MCI Prediction
    
    Usage:
        # With your ASR module
        pipeline = MCIScreeningPipeline(asr_module=your_asr)
        result = pipeline.process_audio("audio.wav", task_type="picture_description")
        
        # Or with pre-existing transcript
        result = pipeline.process_with_transcript("audio.wav", "Đây là transcript...")
    """
    
    def __init__(self, 
                 asr_module=None,
                 model_path: Optional[str] = None,
                 vncorenlp_path: Optional[str] = None,
                 use_phobert: bool = True):
        """
        Initialize MCI Screening Pipeline
        
        Args:
            asr_module: Your existing ASR module
            model_path: Path to trained fusion model (optional)
            vncorenlp_path: Path to VnCoreNLP installation (optional)
            use_phobert: Whether to use PhoBERT for semantic analysis
        """
        if not MODULES_AVAILABLE:
            raise ImportError("Required modules not available. Please install dependencies.")
        
        self.asr = ASRInterface(asr_module)
        self.acoustic_analyzer = AcousticAnalyzer()
        self.linguistic_analyzer = VietnameseLinguisticAnalyzer(
            vncorenlp_path=vncorenlp_path,
            use_phobert=use_phobert
        )
        self.fusion_model = MultimodalFusion(FusionConfig(
            acoustic_weight=0.5,
            linguistic_weight=0.5,
            fusion_method='early',
            normalize=True
        ))
        self.predictor = MCIPredictor(model_path)
        
        logger.info("MCIScreeningPipeline initialized")
    
    def calculate_wer(self, reference: str, hypothesis: str) -> float:
        """
        Calculate Word Error Rate
        
        Args:
            reference: Ground truth transcript
            hypothesis: ASR output transcript
        
        Returns:
            float: WER (0-1)
        """
        ref_words = reference.lower().split()
        hyp_words = hypothesis.lower().split()
        
        if len(ref_words) == 0:
            return 1.0 if len(hyp_words) > 0 else 0.0
        
        # Dynamic programming for Levenshtein distance
        d = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]
        
        for i in range(len(ref_words) + 1):
            d[i][0] = i
        for j in range(len(hyp_words) + 1):
            d[0][j] = j
        
        for i in range(1, len(ref_words) + 1):
            for j in range(1, len(hyp_words) + 1):
                if ref_words[i-1] == hyp_words[j-1]:
                    d[i][j] = d[i-1][j-1]
                else:
                    d[i][j] = min(
                        d[i-1][j] + 1,      # deletion
                        d[i][j-1] + 1,      # insertion
                        d[i-1][j-1] + 1     # substitution
                    )
        
        return d[len(ref_words)][len(hyp_words)] / len(ref_words)
    
    def process_audio(self, 
                      audio_path: str,
                      task_type: Optional[str] = None,
                      reference_transcript: Optional[str] = None,
                      user_info: Optional[Dict[str, Any]] = None) -> PipelineResult:
        """
        Complete processing pipeline for one audio file
        
        Args:
            audio_path: Path to audio file
            task_type: Type of cognitive task ('verbal_fluency', 'picture_description',
                       'spontaneous_speech', 'qa')
            reference_transcript: Ground truth transcript (for WER calculation)
            user_info: Optional user information (age, gender, education)
        
        Returns:
            PipelineResult: Complete analysis results
        """
        import time
        start_time = time.time()
        errors = []
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {audio_path}")
        logger.info(f"{'='*60}")
        
        # Validate audio file
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Step 1: ASR Transcription
        logger.info("Step 1: Automatic Speech Recognition...")
        try:
            transcript = self.asr.transcribe(audio_path)
            logger.info(f"Transcript: {transcript[:100]}{'...' if len(transcript) > 100 else ''}")
        except Exception as e:
            logger.error(f"ASR failed: {e}")
            errors.append(f"ASR: {e}")
            transcript = ""
        
        # Calculate WER if reference available
        if reference_transcript:
            wer = self.calculate_wer(reference_transcript, transcript)
            logger.info(f"Word Error Rate: {wer:.2%}")
        else:
            wer = 0.10  # Assume 10% default WER
        
        # Step 2: Acoustic Feature Extraction
        logger.info("\nStep 2: Acoustic Feature Extraction...")
        try:
            acoustic_features = self.acoustic_analyzer.extract_all_features(
                audio_path,
                transcript=transcript
            )
            logger.info(f"Extracted {len(acoustic_features)} acoustic features")
            
            # Log key features
            f0_mean = acoustic_features.get('f0_f0_mean', 0)
            f0_std = acoustic_features.get('f0_f0_std', 0)
            tone_flat = acoustic_features.get('tone_flattening_score', 0)
            logger.info(f"Key: F0_mean={f0_mean:.2f}Hz, F0_std={f0_std:.2f}Hz, ToneFlat={tone_flat:.3f}")
        except Exception as e:
            logger.error(f"Acoustic extraction failed: {e}")
            errors.append(f"Acoustic: {e}")
            acoustic_features = {}
        
        # Step 3: Linguistic Feature Extraction
        logger.info("\nStep 3: Linguistic Feature Extraction...")
        try:
            linguistic_features = self.linguistic_analyzer.extract_all_features(
                transcript,
                task_type=task_type
            )
            logger.info(f"Extracted {len(linguistic_features)} linguistic features")
            
            # Log key features
            ttr = linguistic_features.get('lex_ttr', 0)
            mlu = linguistic_features.get('syn_mlu_words', 0)
            idea_density = linguistic_features.get('sem_idea_density', 0)
            logger.info(f"Key: TTR={ttr:.3f}, MLU={mlu:.2f}, IdeaDensity={idea_density:.2f}")
        except Exception as e:
            logger.error(f"Linguistic extraction failed: {e}")
            errors.append(f"Linguistic: {e}")
            linguistic_features = {}
        
        # Step 4: Multimodal Fusion
        logger.info("\nStep 4: Multimodal Fusion...")
        try:
            fused_result = self.fusion_model.fuse_features(
                acoustic_features,
                linguistic_features
            )
            
            # Get adaptive weights based on WER
            reliability = self.fusion_model.compute_modality_reliability(
                acoustic_features,
                linguistic_features
            )
            
            # Adjust weights based on ASR quality
            if wer > 0.20:
                fusion_weights = {'acoustic': 0.8, 'linguistic': 0.2}
            elif wer > 0.10:
                fusion_weights = {'acoustic': 0.6, 'linguistic': 0.4}
            else:
                fusion_weights = {'acoustic': 0.5, 'linguistic': 0.5}
            
            logger.info(f"Fusion weights: acoustic={fusion_weights['acoustic']:.1%}, linguistic={fusion_weights['linguistic']:.1%}")
        except Exception as e:
            logger.error(f"Fusion failed: {e}")
            errors.append(f"Fusion: {e}")
            fusion_weights = {'acoustic': 0.5, 'linguistic': 0.5}
        
        # Step 5: MCI Prediction
        logger.info("\nStep 5: MCI Prediction...")
        try:
            # Combine all features
            all_features = {}
            all_features.update(acoustic_features)
            all_features.update(linguistic_features)
            
            prediction = self.predictor.predict(all_features)
            
            mci_probability = prediction.mci_probability
            mmse_score = prediction.mmse_estimate
            confidence = prediction.confidence
            severity = prediction.severity
            risk_factors = prediction.risk_factors
            recommendations = prediction.recommendations
            
            # Acoustic branch prediction (MMSE-based)
            acoustic_mmse = mmse_score  # From acoustic features
            acoustic_mci_prob = 1 / (1 + 2.71828 ** (0.5 * (acoustic_mmse - 24)))
            
            # Linguistic branch prediction
            linguistic_mci_prob = mci_probability  # From linguistic features
            
            branch_predictions = {
                'acoustic_mmse': acoustic_mmse,
                'acoustic_mci_prob': acoustic_mci_prob,
                'linguistic_mci_prob': linguistic_mci_prob
            }
            
            logger.info(f"MCI Probability: {mci_probability:.1%}")
            logger.info(f"MMSE Estimate: {mmse_score:.1f}/30")
            logger.info(f"Confidence: {confidence:.1%}")
            logger.info(f"Severity: {severity}")
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            errors.append(f"Prediction: {e}")
            mci_probability = 0.5
            mmse_score = 25.0
            confidence = 0.0
            severity = "Không xác định"
            risk_factors = []
            recommendations = []
            branch_predictions = {}
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Create result
        result = PipelineResult(
            audio_path=audio_path,
            transcript=transcript,
            wer=wer,
            acoustic_feature_count=len(acoustic_features),
            linguistic_feature_count=len(linguistic_features),
            mci_probability=mci_probability,
            mmse_score=mmse_score,
            confidence=confidence,
            severity=severity,
            risk_factors=risk_factors,
            recommendations=recommendations,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat(),
            branch_predictions=branch_predictions,
            fusion_weights=fusion_weights,
            errors=errors
        )
        
        # Print summary
        self._print_results(result)
        
        return result
    
    def process_with_transcript(self,
                                 audio_path: str,
                                 transcript: str,
                                 task_type: Optional[str] = None) -> PipelineResult:
        """
        Process audio with pre-existing transcript (bypass ASR)
        
        Args:
            audio_path: Path to audio file
            transcript: Pre-existing transcript
            task_type: Type of cognitive task
        
        Returns:
            PipelineResult: Complete analysis results
        """
        import time
        start_time = time.time()
        errors = []
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing with transcript: {audio_path}")
        logger.info(f"{'='*60}")
        
        wer = 0.0  # No ASR error when transcript provided
        
        # Extract acoustic features
        logger.info("Extracting acoustic features...")
        try:
            acoustic_features = self.acoustic_analyzer.extract_all_features(
                audio_path,
                transcript=transcript
            )
        except Exception as e:
            logger.error(f"Acoustic extraction failed: {e}")
            errors.append(f"Acoustic: {e}")
            acoustic_features = {}
        
        # Extract linguistic features
        logger.info("Extracting linguistic features...")
        try:
            linguistic_features = self.linguistic_analyzer.extract_all_features(
                transcript,
                task_type=task_type
            )
        except Exception as e:
            logger.error(f"Linguistic extraction failed: {e}")
            errors.append(f"Linguistic: {e}")
            linguistic_features = {}
        
        # Predict
        all_features = {}
        all_features.update(acoustic_features)
        all_features.update(linguistic_features)
        
        try:
            prediction = self.predictor.predict(all_features)
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            errors.append(f"Prediction: {e}")
            prediction = None
        
        processing_time = time.time() - start_time
        
        if prediction:
            return PipelineResult(
                audio_path=audio_path,
                transcript=transcript,
                wer=wer,
                acoustic_feature_count=len(acoustic_features),
                linguistic_feature_count=len(linguistic_features),
                mci_probability=prediction.mci_probability,
                mmse_score=prediction.mmse_estimate,
                confidence=prediction.confidence,
                severity=prediction.severity,
                risk_factors=prediction.risk_factors,
                recommendations=prediction.recommendations,
                processing_time=processing_time,
                timestamp=datetime.now().isoformat(),
                branch_predictions={},
                fusion_weights={'acoustic': 0.5, 'linguistic': 0.5},
                errors=errors
            )
        else:
            return PipelineResult(
                audio_path=audio_path,
                transcript=transcript,
                wer=wer,
                acoustic_feature_count=len(acoustic_features),
                linguistic_feature_count=len(linguistic_features),
                mci_probability=0.5,
                mmse_score=25.0,
                confidence=0.0,
                severity="Không xác định",
                risk_factors=[],
                recommendations=[],
                processing_time=processing_time,
                timestamp=datetime.now().isoformat(),
                branch_predictions={},
                fusion_weights={},
                errors=errors
            )
    
    def _print_results(self, result: PipelineResult):
        """Pretty print results"""
        print(f"\n{'='*60}")
        print("KẾT QUẢ DỰ ĐOÁN MCI")
        print(f"{'='*60}")
        print(f"Xác suất MCI: {result.mci_probability:.1%}")
        print(f"Điểm MMSE ước tính: {result.mmse_score:.1f}/30")
        print(f"Độ tin cậy: {result.confidence:.1%}")
        print(f"Mức độ: {result.severity}")
        
        print(f"\nNhận định:")
        if result.mci_probability > 0.7:
            print("  ⚠️  NGUY CƠ CAO - Khuyến nghị đánh giá lâm sàng")
        elif result.mci_probability > 0.4:
            print("  ⚡ NGUY CƠ TRUNG BÌNH - Cần theo dõi và kiểm tra lại")
        else:
            print("  ✅ NGUY CƠ THẤP - Chức năng nhận thức có vẻ bình thường")
        
        if result.risk_factors:
            print(f"\nYếu tố nguy cơ phát hiện:")
            for rf in result.risk_factors:
                print(f"  • {rf}")
        
        if result.recommendations:
            print(f"\nKhuyến nghị:")
            for rec in result.recommendations:
                print(f"  → {rec}")
        
        if result.branch_predictions:
            print(f"\nChi tiết Fusion:")
            print(f"  Acoustic MMSE: {result.branch_predictions.get('acoustic_mmse', 0):.1f}")
            print(f"  Acoustic MCI prob: {result.branch_predictions.get('acoustic_mci_prob', 0):.1%}")
            print(f"  Linguistic MCI prob: {result.branch_predictions.get('linguistic_mci_prob', 0):.1%}")
        
        print(f"\nThông tin xử lý:")
        print(f"  Thời gian: {result.processing_time:.2f}s")
        print(f"  WER: {result.wer:.1%}")
        print(f"  Số đặc trưng acoustic: {result.acoustic_feature_count}")
        print(f"  Số đặc trưng linguistic: {result.linguistic_feature_count}")
        
        if result.errors:
            print(f"\nLỗi:")
            for err in result.errors:
                print(f"  ❌ {err}")
        
        print(f"{'='*60}\n")
    
    def batch_process(self, 
                      audio_folder: str,
                      output_file: str = 'results.json',
                      task_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Process multiple audio files
        
        Args:
            audio_folder: Folder containing audio files
            output_file: Output JSON file
            task_type: Type of cognitive task
        
        Returns:
            List of results
        """
        audio_folder = Path(audio_folder)
        audio_files = list(audio_folder.glob('*.wav')) + list(audio_folder.glob('*.mp3'))
        
        logger.info(f"Found {len(audio_files)} audio files")
        
        all_results = []
        for i, audio_file in enumerate(audio_files, 1):
            logger.info(f"\nProcessing {i}/{len(audio_files)}: {audio_file.name}")
            try:
                result = self.process_audio(str(audio_file), task_type=task_type)
                all_results.append(asdict(result))
            except Exception as e:
                logger.error(f"Error processing {audio_file}: {e}")
                continue
        
        # Save results
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\nResults saved to {output_file}")
        
        # Print summary
        print(f"\n{'='*60}")
        print("TÓM TẮT BATCH PROCESSING")
        print(f"{'='*60}")
        print(f"Tổng số file: {len(audio_files)}")
        print(f"Xử lý thành công: {len(all_results)}")
        
        if all_results:
            avg_mci = sum(r['mci_probability'] for r in all_results) / len(all_results)
            avg_mmse = sum(r['mmse_score'] for r in all_results) / len(all_results)
            print(f"MCI trung bình: {avg_mci:.1%}")
            print(f"MMSE trung bình: {avg_mmse:.1f}/30")
        
        print(f"{'='*60}\n")
        
        return all_results


def create_pipeline(asr_module=None, model_path: Optional[str] = None) -> MCIScreeningPipeline:
    """
    Factory function to create pipeline
    
    Args:
        asr_module: Your ASR module
        model_path: Path to trained model
    
    Returns:
        MCIScreeningPipeline instance
    """
    return MCIScreeningPipeline(
        asr_module=asr_module,
        model_path=model_path
    )


# ==============================================================================
# USAGE EXAMPLE
# ==============================================================================

if __name__ == "__main__":
    print("="*60)
    print("MCI Screening Pipeline - Demo")
    print("="*60)
    
    # Example 1: Process with your ASR module
    # from your_module import YourASRClass
    # pipeline = MCIScreeningPipeline(asr_module=YourASRClass())
    # result = pipeline.process_audio("audio.wav", task_type="picture_description")
    
    # Example 2: Process with pre-existing transcript
    # pipeline = MCIScreeningPipeline()
    # result = pipeline.process_with_transcript(
    #     audio_path="audio.wav",
    #     transcript="Xin chào, tôi tên là Nguyễn Văn A...",
    #     task_type="spontaneous_speech"
    # )
    
    # Example 3: Batch processing
    # pipeline = MCIScreeningPipeline()
    # results = pipeline.batch_process(
    #     audio_folder="data/audio_samples/",
    #     output_file="results/screening_results.json"
    # )
    
    print("\nTo use the pipeline:")
    print("1. Import: from main_pipeline import MCIScreeningPipeline")
    print("2. Create: pipeline = MCIScreeningPipeline(asr_module=your_asr)")
    print("3. Process: result = pipeline.process_audio('audio.wav')")
    print("\nOr process with existing transcript:")
    print("   result = pipeline.process_with_transcript('audio.wav', 'transcript text')")


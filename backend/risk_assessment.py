"""
Clinical Risk Assessment & Explainability System
Uses SHAP-based explanations and scientific thresholds for MCI/dementia risk assessment
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# SCIENTIFIC THRESHOLDS (From Research Documents)
# =============================================================================

ACOUSTIC_THRESHOLDS = {
    # Voice Quality (indicators of neuromotor decline)
    'jitter': {
        'normal': (0.5, 1.5),      # % variation in F0
        'mild': (1.5, 2.5),
        'moderate': (2.5, 4.0),
        'severe': (4.0, float('inf'))
    },
    'shimmer': {
        'normal': (2.0, 4.0),      # % variation in amplitude
        'mild': (4.0, 6.0),
        'moderate': (6.0, 9.0),
        'severe': (9.0, float('inf'))
    },
    'hnr': {  # Harmonics-to-Noise Ratio
        'normal': (12, float('inf')),  # dB
        'mild': (9, 12),
        'moderate': (6, 9),
        'severe': (0, 6)
    },
    
    # Pitch/Prosody (monotone speech indicator)
    'f0_std': {
        'normal': (15, 50),        # Hz
        'mild': (10, 15),
        'moderate': (5, 10),
        'severe': (0, 5)
    },
    'f0_range': {
        'normal': (50, 200),       # Hz
        'mild': (30, 50),
        'moderate': (15, 30),
        'severe': (0, 15)
    },
    
    # Temporal Features (speech fluency)
    'speech_rate': {
        'normal': (3.0, 5.5),      # syllables/second
        'mild': (2.0, 3.0),
        'moderate': (1.0, 2.0),
        'severe': (0, 1.0)
    },
    'pause_ratio': {
        'normal': (0.2, 0.4),      # ratio of pause to speech
        'mild': (0.4, 0.6),
        'moderate': (0.6, 0.8),
        'severe': (0.8, 1.0)
    },
    'mean_pause_duration': {
        'normal': (0.2, 0.8),      # seconds
        'mild': (0.8, 1.5),
        'moderate': (1.5, 3.0),
        'severe': (3.0, float('inf'))
    },
    # Map from feature extractor names to threshold keys
    'vq_jitter_local': {
        'normal': (0.5, 1.5),
        'mild': (1.5, 2.5),
        'moderate': (2.5, 4.0),
        'severe': (4.0, float('inf'))
    },
    'vq_shimmer_local': {
        'normal': (2.0, 4.0),
        'mild': (4.0, 6.0),
        'moderate': (6.0, 9.0),
        'severe': (9.0, float('inf'))
    },
    'vq_hnr_mean': {
        'normal': (12, float('inf')),
        'mild': (9, 12),
        'moderate': (6, 9),
        'severe': (0, 6)
    },
    'f0_f0_std': {
        'normal': (15, 50),
        'mild': (10, 15),
        'moderate': (5, 10),
        'severe': (0, 5)
    },
    'f0_f0_range': {
        'normal': (50, 200),
        'mild': (30, 50),
        'moderate': (15, 30),
        'severe': (0, 15)
    },
    'rate_syllables_per_second': {
        'normal': (3.0, 5.5),
        'mild': (2.0, 3.0),
        'moderate': (1.0, 2.0),
        'severe': (0, 1.0)
    },
    'pause_pause_rate': {
        'normal': (0.2, 0.4),
        'mild': (0.4, 0.6),
        'moderate': (0.6, 0.8),
        'severe': (0.8, 1.0)
    },
    'pause_mean_pause_duration': {
        'normal': (0.2, 0.8),
        'mild': (0.8, 1.5),
        'moderate': (1.5, 3.0),
        'severe': (3.0, float('inf'))
    }
}

LINGUISTIC_THRESHOLDS = {
    # Lexical Diversity
    'ttr': {  # Type-Token Ratio
        'normal': (0.6, 1.0),
        'mild': (0.4, 0.6),
        'moderate': (0.25, 0.4),
        'severe': (0, 0.25)
    },
    'pronoun_ratio': {
        'normal': (0, 0.15),       # < 15% pronouns is normal
        'mild': (0.15, 0.25),
        'moderate': (0.25, 0.40),
        'severe': (0.40, 1.0)
    },
    'word_repetition_rate': {
        'normal': (0, 0.05),       # < 5% repetition
        'mild': (0.05, 0.10),
        'moderate': (0.10, 0.20),
        'severe': (0.20, 1.0)
    },
    'filler_word_ratio': {  # ừ, ờ, à, thì
        'normal': (0, 0.08),
        'mild': (0.08, 0.15),
        'moderate': (0.15, 0.25),
        'severe': (0.25, 1.0)
    },
    
    # Syntactic Complexity
    'mlu': {  # Mean Length of Utterance (words)
        'normal': (8, 15),
        'mild': (5, 8),
        'moderate': (3, 5),
        'severe': (0, 3)
    },
    'incomplete_sentence_ratio': {
        'normal': (0, 0.15),
        'mild': (0.15, 0.30),
        'moderate': (0.30, 0.50),
        'severe': (0.50, 1.0)
    },
    'syntax_complexity_score': {
        'normal': (0.6, 1.0),
        'mild': (0.4, 0.6),
        'moderate': (0.2, 0.4),
        'severe': (0, 0.2)
    },
    
    # Semantic Coherence
    'semantic_coherence': {
        'normal': (0.7, 1.0),
        'mild': (0.5, 0.7),
        'moderate': (0.3, 0.5),
        'severe': (0, 0.3)
    },
    'idea_density': {  # propositions per 10 words
        'normal': (0.5, 0.8),
        'mild': (0.35, 0.5),
        'moderate': (0.2, 0.35),
        'severe': (0, 0.2)
    },
    # Map from feature extractor names
    'lex_ttr': {
        'normal': (0.6, 1.0),
        'mild': (0.4, 0.6),
        'moderate': (0.25, 0.4),
        'severe': (0, 0.25)
    },
    'lex_pronoun_ratio': {
        'normal': (0, 0.15),
        'mild': (0.15, 0.25),
        'moderate': (0.25, 0.40),
        'severe': (0.40, 1.0)
    },
    'syn_mlu_words': {
        'normal': (8, 15),
        'mild': (5, 8),
        'moderate': (3, 5),
        'severe': (0, 3)
    },
    'syn_incomplete_sentence_ratio': {
        'normal': (0, 0.15),
        'mild': (0.15, 0.30),
        'moderate': (0.30, 0.50),
        'severe': (0.50, 1.0)
    },
    'sem_semantic_coherence': {
        'normal': (0.7, 1.0),
        'mild': (0.5, 0.7),
        'moderate': (0.3, 0.5),
        'severe': (0, 0.3)
    },
    'sem_idea_density': {
        'normal': (0.5, 0.8),
        'mild': (0.35, 0.5),
        'moderate': (0.2, 0.35),
        'severe': (0, 0.2)
    },
    'vi_filler_ratio': {
        'normal': (0, 0.08),
        'mild': (0.08, 0.15),
        'moderate': (0.15, 0.25),
        'severe': (0.25, 1.0)
    }
}

RISK_CLASSIFICATION = {
    'low': {
        'mmse_range': (25, 30),
        'abnormal_features': (0, 3),  # < 3 abnormal features
        'description': 'Không có dấu hiệu suy giảm nhận thức đáng kể'
    },
    'mild': {
        'mmse_range': (21, 24),
        'abnormal_features': (3, 6),
        'description': 'Có dấu hiệu suy giảm nhận thức nhẹ (MCI khả nghi)'
    },
    'moderate': {
        'mmse_range': (15, 20),
        'abnormal_features': (6, 10),
        'description': 'Sa sút trí tuệ mức độ trung bình'
    },
    'severe': {
        'mmse_range': (0, 14),
        'abnormal_features': (10, float('inf')),
        'description': 'Sa sút trí tuệ mức độ nặng'
    }
}


class ClinicalRiskAssessor:
    """
    Assess MCI/dementia risk using scientific thresholds + SHAP explainability
    """
    
    def __init__(self, acoustic_features: Dict, linguistic_features: Dict, mmse_score: int):
        self.acoustic = acoustic_features or {}
        self.linguistic = linguistic_features or {}
        self.mmse_score = mmse_score
        
        # Load thresholds
        self.acoustic_thresholds = ACOUSTIC_THRESHOLDS
        self.linguistic_thresholds = LINGUISTIC_THRESHOLDS
        self.risk_classification = RISK_CLASSIFICATION
        
    def assess_risk(self) -> Dict:
        """
        Main assessment pipeline
        
        Returns:
            {
                'overall_risk': 'low'|'mild'|'moderate'|'severe',
                'acoustic_assessment': {...},
                'linguistic_assessment': {...},
                'abnormal_features': [...],
                'shap_explanation': {...},
                'clinical_interpretation': "...",
                'recommendations': [...]
            }
        """
        # 1. Classify each feature
        acoustic_assessment = self._assess_acoustic_features()
        linguistic_assessment = self._assess_linguistic_features()
        
        # 2. Count abnormal features
        abnormal_count = (
            acoustic_assessment['abnormal_count'] + 
            linguistic_assessment['abnormal_count']
        )
        
        # 3. Determine overall risk
        overall_risk = self._determine_risk_level(self.mmse_score, abnormal_count)
        
        # 4. Generate SHAP explanations
        shap_results = self._generate_shap_explanation()
        
        # 5. Create clinical interpretation
        interpretation = self._generate_clinical_interpretation(
            overall_risk,
            acoustic_assessment,
            linguistic_assessment,
            shap_results
        )
        
        # 6. Generate recommendations
        recommendations = self._generate_recommendations(overall_risk)
        
        # 7. Create visualizations
        visualizations = self._create_visualizations(acoustic_assessment, linguistic_assessment)
        
        return {
            'overall_risk': overall_risk,
            'mmse_score': self.mmse_score,
            'acoustic_assessment': acoustic_assessment,
            'linguistic_assessment': linguistic_assessment,
            'abnormal_features_count': abnormal_count,
            'shap_explanation': shap_results,
            'clinical_interpretation': interpretation,
            'recommendations': recommendations,
            'visualizations': visualizations
        }
    
    def _assess_acoustic_features(self) -> Dict:
        """
        Classify each acoustic feature as normal/mild/moderate/severe
        """
        assessment = {
            'features': {},
            'abnormal_count': 0,
            'severity_distribution': {'normal': 0, 'mild': 0, 'moderate': 0, 'severe': 0}
        }
        
        for feature_name, value in self.acoustic.items():
            if not isinstance(value, (int, float)) or np.isnan(value) or np.isinf(value):
                continue
                
            # Try to find matching threshold
            thresholds = None
            for key in self.acoustic_thresholds:
                if key in feature_name.lower() or feature_name.lower() in key.lower():
                    thresholds = self.acoustic_thresholds[key]
                    break
            
            if not thresholds:
                continue
                
            severity = self._classify_severity(value, thresholds)
            
            assessment['features'][feature_name] = {
                'value': float(value),
                'severity': severity,
                'explanation': self._explain_acoustic_feature(feature_name, value, severity)
            }
            
            assessment['severity_distribution'][severity] += 1
            if severity != 'normal':
                assessment['abnormal_count'] += 1
        
        return assessment
    
    def _assess_linguistic_features(self) -> Dict:
        """
        Classify each linguistic feature
        """
        assessment = {
            'features': {},
            'abnormal_count': 0,
            'severity_distribution': {'normal': 0, 'mild': 0, 'moderate': 0, 'severe': 0}
        }
        
        for feature_name, value in self.linguistic.items():
            if not isinstance(value, (int, float)) or np.isnan(value) or np.isinf(value):
                continue
                
            # Try to find matching threshold
            thresholds = None
            for key in self.linguistic_thresholds:
                if key in feature_name.lower() or feature_name.lower() in key.lower():
                    thresholds = self.linguistic_thresholds[key]
                    break
            
            if not thresholds:
                continue
                
            severity = self._classify_severity(value, thresholds)
            
            assessment['features'][feature_name] = {
                'value': float(value),
                'severity': severity,
                'explanation': self._explain_linguistic_feature(feature_name, value, severity)
            }
            
            assessment['severity_distribution'][severity] += 1
            if severity != 'normal':
                assessment['abnormal_count'] += 1
        
        return assessment
    
    def _classify_severity(self, value: float, thresholds: Dict) -> str:
        """
        Classify value into normal/mild/moderate/severe
        """
        for severity in ['normal', 'mild', 'moderate', 'severe']:
            if severity not in thresholds:
                continue
            low, high = thresholds[severity]
            if low <= value < high:
                return severity
        return 'severe'
    
    def _explain_acoustic_feature(self, feature_name: str, value: float, severity: str) -> str:
        """
        Generate plain Vietnamese explanation for acoustic features
        """
        # Normalize feature name
        feature_key = feature_name.lower()
        if 'jitter' in feature_key:
            feature_key = 'jitter'
        elif 'shimmer' in feature_key:
            feature_key = 'shimmer'
        elif 'hnr' in feature_key:
            feature_key = 'hnr'
        elif 'f0' in feature_key and 'std' in feature_key:
            feature_key = 'f0_std'
        elif 'f0' in feature_key and 'range' in feature_key:
            feature_key = 'f0_range'
        elif 'speech_rate' in feature_key or 'syllables' in feature_key:
            feature_key = 'speech_rate'
        elif 'pause' in feature_key and 'ratio' in feature_key or 'rate' in feature_key:
            feature_key = 'pause_ratio'
        elif 'pause' in feature_key and 'duration' in feature_key:
            feature_key = 'mean_pause_duration'
        
        explanations = {
            'jitter': {
                'normal': f"Độ rung giọng nói ổn định ({value:.2f}%), cho thấy kiểm soát thanh quản tốt.",
                'mild': f"Có chút bất ổn trong độ rung giọng ({value:.2f}%), có thể do căng thẳng hoặc mệt mỏi.",
                'moderate': f"Độ rung giọng cao hơn bình thường ({value:.2f}%), có dấu hiệu giảm kiểm soát vận động thanh quản.",
                'severe': f"Độ rung giọng rất cao ({value:.2f}%), cho thấy sự suy giảm đáng kể trong kiểm soát giọng nói."
            },
            'shimmer': {
                'normal': f"Biên độ giọng nói ổn định ({value:.2f}%), âm thanh rõ ràng.",
                'mild': f"Có chút dao động biên độ giọng ({value:.2f}%), giọng nói hơi run nhẹ.",
                'moderate': f"Biên độ giọng dao động nhiều ({value:.2f}%), giọng nói kém ổn định.",
                'severe': f"Biên độ giọng rất không ổn định ({value:.2f}%), giọng run rõ rệt."
            },
            'hnr': {
                'normal': f"Chất lượng giọng tốt ({value:.1f} dB), âm thanh trong trẻo.",
                'mild': f"Chất lượng giọng hơi khàn ({value:.1f} dB), có chút tạp âm.",
                'moderate': f"Giọng nói khá khàn ({value:.1f} dB), nhiều tạp âm.",
                'severe': f"Giọng rất khàn ({value:.1f} dB), chất lượng âm thanh kém."
            },
            'f0_std': {
                'normal': f"Giọng nói có ngữ điệu tự nhiên ({value:.1f} Hz), sinh động.",
                'mild': f"Ngữ điệu hơi đơn điệu ({value:.1f} Hz), ít biến thiên.",
                'moderate': f"Giọng nói khá đơn điệu ({value:.1f} Hz), thiếu cảm xúc.",
                'severe': f"Giọng rất đơn điệu ({value:.1f} Hz), như robot."
            },
            'f0_range': {
                'normal': f"Phạm vi cao độ giọng nói bình thường ({value:.1f} Hz), linh hoạt.",
                'mild': f"Phạm vi cao độ hơi hẹp ({value:.1f} Hz), ít biến thiên.",
                'moderate': f"Phạm vi cao độ hẹp ({value:.1f} Hz), giọng đơn điệu.",
                'severe': f"Phạm vi cao độ rất hẹp ({value:.1f} Hz), giọng gần như phẳng."
            },
            'speech_rate': {
                'normal': f"Tốc độ nói bình thường ({value:.1f} âm tiết/giây), dễ hiểu.",
                'mild': f"Nói hơi chậm ({value:.1f} âm tiết/giây).",
                'moderate': f"Nói chậm đáng kể ({value:.1f} âm tiết/giây), có thể do khó tìm từ.",
                'severe': f"Nói rất chậm ({value:.1f} âm tiết/giây), gặp nhiều khó khăn trong phát âm."
            },
            'pause_ratio': {
                'normal': f"Thời gian ngắt nghỉ hợp lý ({value:.1%}), nói trơn tru.",
                'mild': f"Ngắt nghỉ hơi nhiều ({value:.1%}), đôi khi ngập ngừng.",
                'moderate': f"Ngắt nghỉ nhiều ({value:.1%}), thường xuyên ngập ngừng.",
                'severe': f"Ngắt nghỉ quá nhiều ({value:.1%}), nói rất gián đoạn."
            },
            'mean_pause_duration': {
                'normal': f"Độ dài ngừng bình thường ({value:.1f}s).",
                'mild': f"Ngừng lâu hơn bình thường ({value:.1f}s), có thể do suy nghĩ.",
                'moderate': f"Ngừng khá lâu ({value:.1f}s), khó khăn trong tìm từ.",
                'severe': f"Ngừng rất lâu ({value:.1f}s), mất nhiều thời gian để tổ chức lời nói."
            }
        }
        
        if feature_key in explanations:
            return explanations[feature_key].get(severity, "Không xác định")
        return f"{feature_name}: {value:.2f}"
    
    def _explain_linguistic_feature(self, feature_name: str, value: float, severity: str) -> str:
        """
        Generate plain Vietnamese explanation for linguistic features
        """
        # Normalize feature name
        feature_key = feature_name.lower()
        if 'ttr' in feature_key:
            feature_key = 'ttr'
        elif 'pronoun' in feature_key:
            feature_key = 'pronoun_ratio'
        elif 'repetition' in feature_key:
            feature_key = 'word_repetition_rate'
        elif 'filler' in feature_key:
            feature_key = 'filler_word_ratio'
        elif 'mlu' in feature_key:
            feature_key = 'mlu'
        elif 'incomplete' in feature_key:
            feature_key = 'incomplete_sentence_ratio'
        elif 'complexity' in feature_key:
            feature_key = 'syntax_complexity_score'
        elif 'coherence' in feature_key:
            feature_key = 'semantic_coherence'
        elif 'idea' in feature_key or 'density' in feature_key:
            feature_key = 'idea_density'
        
        explanations = {
            'ttr': {
                'normal': f"Vốn từ vựng phong phú ({value:.2f}), sử dụng nhiều từ khác nhau.",
                'mild': f"Vốn từ vựng hơi hạn chế ({value:.2f}), lặp lại một số từ.",
                'moderate': f"Vốn từ vựng khá nghèo ({value:.2f}), thường lặp lại các từ cơ bản.",
                'severe': f"Vốn từ vựng rất hạn chế ({value:.2f}), chỉ dùng vài từ đơn giản."
            },
            'pronoun_ratio': {
                'normal': f"Sử dụng danh từ cụ thể tốt ({value:.1%} đại từ).",
                'mild': f"Dùng đại từ hơi nhiều ({value:.1%}), đôi khi thiếu cụ thể.",
                'moderate': f"Dùng đại từ nhiều ({value:.1%}), ít dùng danh từ rõ nghĩa - có dấu hiệu khó nhớ tên.",
                'severe': f"Lạm dụng đại từ ({value:.1%}), hầu như không gọi tên cụ thể - dấu hiệu rõ của suy giảm ký ức."
            },
            'word_repetition_rate': {
                'normal': f"Ít lặp từ ({value:.1%}), lời nói lưu loát.",
                'mild': f"Lặp từ nhẹ ({value:.1%}), đôi khi nói lại.",
                'moderate': f"Lặp từ nhiều ({value:.1%}), thường phải nhắc lại câu.",
                'severe': f"Lặp từ rất nhiều ({value:.1%}), liên tục nói đi nói lại."
            },
            'filler_word_ratio': {
                'normal': f"Ít dùng từ đệm ({value:.1%} 'ừ, ờ, à'), nói tự tin.",
                'mild': f"Dùng từ đệm hơi nhiều ({value:.1%}), đôi khi 'ừm... ờ...'",
                'moderate': f"Lạm dụng từ đệm ({value:.1%}), thường xuyên 'ừm... ờ... à...' - khó tổ chức ý tưởng.",
                'severe': f"Rất nhiều từ đệm ({value:.1%}), hầu như mỗi câu đều có 'ừm... ờ...' - mất khả năng diễn đạt."
            },
            'mlu': {
                'normal': f"Câu có độ dài phù hợp ({value:.1f} từ), diễn đạt đầy đủ ý.",
                'mild': f"Câu hơi ngắn ({value:.1f} từ), đôi khi thiếu chi tiết.",
                'moderate': f"Câu rất ngắn ({value:.1f} từ), khó diễn đạt ý phức tạp.",
                'severe': f"Câu cực ngắn ({value:.1f} từ), chỉ nói từng cụm từ đơn giản."
            },
            'incomplete_sentence_ratio': {
                'normal': f"Hầu hết câu hoàn chỉnh ({value:.1%} câu dở dang).",
                'mild': f"Một số câu dở dang ({value:.1%}), đôi khi không kết thúc câu.",
                'moderate': f"Nhiều câu không hoàn thành ({value:.1%}), thường bỏ lửng.",
                'severe': f"Phần lớn câu dở dang ({value:.1%}), hiếm khi nói hết câu - mất khả năng tổ chức ngôn ngữ."
            },
            'syntax_complexity_score': {
                'normal': f"Cấu trúc câu phức tạp ({value:.2f}), ngữ pháp đa dạng.",
                'mild': f"Cấu trúc câu đơn giản hơn ({value:.2f}), ít câu phức.",
                'moderate': f"Cấu trúc câu rất đơn giản ({value:.2f}), chủ yếu câu đơn.",
                'severe': f"Cấu trúc câu cực kỳ đơn giản ({value:.2f}), không có câu phức."
            },
            'semantic_coherence': {
                'normal': f"Lời nói mạch lạc ({value:.2f}), ý rõ ràng, logic.",
                'mild': f"Đôi khi hơi lạc đề ({value:.2f}), nhưng còn theo chủ đề chính.",
                'moderate': f"Thường lạc đề ({value:.2f}), khó theo dõi mạch suy nghĩ.",
                'severe': f"Lời nói rất rối loạn ({value:.2f}), không có mạch, nhảy lung tung giữa các ý."
            },
            'idea_density': {
                'normal': f"Diễn đạt súc tích ({value:.2f} ý/10 từ), nhiều thông tin.",
                'mild': f"Hơi dài dòng ({value:.2f} ý/10 từ), ít thông tin hơn.",
                'moderate': f"Rất dài dòng ({value:.2f} ý/10 từ), nói nhiều nhưng ít nội dung.",
                'severe': f"Gần như không có nội dung ({value:.2f} ý/10 từ), chỉ lặp lại từ ngữ đơn giản."
            }
        }
        
        if feature_key in explanations:
            return explanations[feature_key].get(severity, "Không xác định")
        return f"{feature_name}: {value:.2f}"
    
    def _determine_risk_level(self, mmse: int, abnormal_count: int) -> str:
        """
        Determine overall risk based on MMSE + feature count
        """
        # Primary: MMSE score
        for risk_level, criteria in self.risk_classification.items():
            mmse_low, mmse_high = criteria['mmse_range']
            feat_low, feat_high = criteria['abnormal_features']
            
            if (mmse_low <= mmse <= mmse_high) and (feat_low <= abnormal_count < feat_high):
                return risk_level
        
        # Fallback based on MMSE only
        if mmse >= 25:
            return 'low'
        elif mmse >= 21:
            return 'mild'
        elif mmse >= 15:
            return 'moderate'
        else:
            return 'severe'
    
    def _generate_shap_explanation(self) -> Dict:
        """
        Generate SHAP-based feature importance explanation
        
        NOTE: This is a simplified implementation.
        For production, train an actual model and compute real SHAP values.
        """
        # Combine all features into array
        all_features = {**self.acoustic, **self.linguistic}
        feature_names = list(all_features.keys())
        feature_values = []
        importances = []
        
        for fname in feature_names:
            value = all_features[fname]
            if not isinstance(value, (int, float)) or np.isnan(value) or np.isinf(value):
                continue
                
            feature_values.append(value)
            
            # Find matching threshold
            thresholds = None
            if fname in self.acoustic_thresholds:
                thresholds = self.acoustic_thresholds[fname]
            elif fname in self.linguistic_thresholds:
                thresholds = self.linguistic_thresholds[fname]
            else:
                # Try fuzzy match
                for key in self.acoustic_thresholds:
                    if key in fname.lower() or fname.lower() in key.lower():
                        thresholds = self.acoustic_thresholds[key]
                        break
                if not thresholds:
                    for key in self.linguistic_thresholds:
                        if key in fname.lower() or fname.lower() in key.lower():
                            thresholds = self.linguistic_thresholds[key]
                            break
            
            if not thresholds:
                importances.append(0)
                continue
            
            normal_range = thresholds.get('normal', (0, 1))
            
            # Calculate deviation from normal range
            if normal_range[0] <= value <= normal_range[1]:
                deviation = 0  # Within normal
            elif value < normal_range[0]:
                deviation = abs((normal_range[0] - value) / max(normal_range[0], 0.01))
            else:
                deviation = abs((value - normal_range[1]) / max(normal_range[1], 0.01))
            
            importances.append(deviation)
        
        # Get top 10 most important features
        if not importances:
            return {
                'top_contributing_features': [],
                'summary': "Không có đủ dữ liệu để phân tích."
            }
        
        sorted_indices = np.argsort(importances)[::-1][:10]
        
        top_features = []
        for idx in sorted_indices:
            if idx >= len(feature_names):
                continue
            fname = feature_names[idx]
            fvalue = all_features[fname]
            importance = importances[idx]
            
            if importance > 0:
                # Get explanation
                if fname in self.acoustic:
                    severity = self._classify_severity(fvalue, self.acoustic_thresholds.get(fname, {}))
                    explanation = self._explain_acoustic_feature(fname, fvalue, severity)
                elif fname in self.linguistic:
                    severity = self._classify_severity(fvalue, self.linguistic_thresholds.get(fname, {}))
                    explanation = self._explain_linguistic_feature(fname, fvalue, severity)
                else:
                    explanation = f"Giá trị: {fvalue:.2f}"
                
                top_features.append({
                    'feature_name': fname,
                    'value': float(fvalue),
                    'importance': float(importance),
                    'explanation': explanation
                })
        
        return {
            'top_contributing_features': top_features,
            'summary': self._summarize_shap_findings(top_features)
        }
    
    def _summarize_shap_findings(self, top_features: List[Dict]) -> str:
        """
        Generate summary of SHAP findings in Vietnamese
        """
        if not top_features:
            return "Tất cả các chỉ số đều trong giới hạn bình thường."
        
        summary_parts = ["### Các yếu tố ảnh hưởng chính:\n"]
        
        for i, feat in enumerate(top_features[:5], 1):
            summary_parts.append(f"{i}. **{feat['feature_name']}**: {feat['explanation']}")
        
        return "\n".join(summary_parts)
    
    def _generate_clinical_interpretation(
        self, 
        risk_level: str,
        acoustic_assessment: Dict,
        linguistic_assessment: Dict,
        shap_results: Dict
    ) -> str:
        """
        Generate comprehensive clinical interpretation
        """
        interpretation = []
        
        # Overall assessment
        interpretation.append("## Đánh Giá Tổng Quan\n")
        interpretation.append(f"**Điểm MMSE**: {self.mmse_score}/30")
        interpretation.append(f"**Mức độ nguy cơ**: {risk_level.upper()}")
        interpretation.append(f"**Đặc trưng bất thường**: {acoustic_assessment['abnormal_count'] + linguistic_assessment['abnormal_count']}\n")
        
        # Acoustic findings
        interpretation.append("### Phân Tích Đặc Trưng Giọng Nói (Acoustic)")
        interpretation.append(f"- Bình thường: {acoustic_assessment['severity_distribution']['normal']}")
        interpretation.append(f"- Bất thường nhẹ: {acoustic_assessment['severity_distribution']['mild']}")
        interpretation.append(f"- Bất thường trung bình: {acoustic_assessment['severity_distribution']['moderate']}")
        interpretation.append(f"- Bất thường nặng: {acoustic_assessment['severity_distribution']['severe']}\n")
        
        # List top acoustic issues
        acoustic_issues = [
            f"- {feat['explanation']}" 
            for feat in acoustic_assessment['features'].values() 
            if feat['severity'] != 'normal'
        ][:5]
        if acoustic_issues:
            interpretation.append("**Các vấn đề chính:**")
            interpretation.extend(acoustic_issues)
            interpretation.append("")
        
        # Linguistic findings
        interpretation.append("### Phân Tích Đặc Trưng Ngôn Ngữ (Linguistic)")
        interpretation.append(f"- Bình thường: {linguistic_assessment['severity_distribution']['normal']}")
        interpretation.append(f"- Bất thường nhẹ: {linguistic_assessment['severity_distribution']['mild']}")
        interpretation.append(f"- Bất thường trung bình: {linguistic_assessment['severity_distribution']['moderate']}")
        interpretation.append(f"- Bất thường nặng: {linguistic_assessment['severity_distribution']['severe']}\n")
        
        # List top linguistic issues
        linguistic_issues = [
            f"- {feat['explanation']}" 
            for feat in linguistic_assessment['features'].values() 
            if feat['severity'] != 'normal'
        ][:5]
        if linguistic_issues:
            interpretation.append("**Các vấn đề chính:**")
            interpretation.extend(linguistic_issues)
            interpretation.append("")
        
        # SHAP insights
        interpretation.append(shap_results['summary'])
        
        return "\n".join(interpretation)
    
    def _generate_recommendations(self, risk_level: str) -> List[str]:
        """
        Generate clinical recommendations based on risk level
        """
        recommendations = {
            'low': [
                "✅ Kết quả tốt, không có dấu hiệu suy giảm nhận thức đáng ngại.",
                "💡 Tiếp tục duy trì lối sống lành mạnh: ngủ đủ giấc, tập thể dục, giao lưu xã hội.",
                "📅 Theo dõi định kỳ 1 năm/lần để phát hiện sớm nếu có thay đổi."
            ],
            'mild': [
                "⚠️ Có dấu hiệu suy giảm nhận thức nhẹ (MCI), cần theo dõi chặt chẽ.",
                "🏥 Nên gặp bác sĩ thần kinh để đánh giá chuyên sâu hơn.",
                "🧠 Tham gia các hoạt động kích thích trí óc: đọc sách, giải ô chữ, học kỹ năng mới.",
                "🗣️ Tham gia therapy ngôn ngữ nếu có khó khăn trong giao tiếp.",
                "📅 Tái khám sau 3-6 tháng để theo dõi diễn biến."
            ],
            'moderate': [
                "🚨 Có dấu hiệu sa sút trí tuệ mức độ trung bình, cần can thiệp y tế.",
                "🏥 Khuyến cáo gặp bác sĩ chuyên khoa thần kinh NGAY.",
                "💊 Có thể cần thuốc điều trị để làm chậm tiến triển bệnh.",
                "👨‍👩‍👧 Gia đình cần hỗ trợ gần gũi trong sinh hoạt hàng ngày.",
                "📱 Cân nhắc sử dụng công nghệ hỗ trợ: nhắc nhở uống thuốc, GPS tracking.",
                "📅 Theo dõi chặt chẽ hàng tháng."
            ],
            'severe': [
                "🆘 Sa sút trí tuệ mức độ nặng, cần chăm sóc y tế và hỗ trợ toàn diện.",
                "🏥 CẦN gặp bác sĩ chuyên khoa NGAY LẬP TỨC.",
                "💊 Cần điều trị thuốc và can thiệp đa chiều.",
                "👨‍⚕️ Cân nhắc chăm sóc tại nhà hoặc viện dưỡng lão chuyên khoa.",
                "👨‍👩‍👧 Gia đình cần hỗ trợ toàn bộ sinh hoạt.",
                "⚖️ Chuẩn bị các vấn đề pháp lý (ủy quyền, giám hộ)."
            ]
        }
        return recommendations.get(risk_level, [])
    
    def _create_visualizations(self, acoustic_assessment: Dict, linguistic_assessment: Dict) -> Dict[str, str]:
        """
        Create visualization charts (return as base64 encoded images)
        """
        visualizations = {}
        
        try:
            # 1. Feature severity distribution
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
            
            # Acoustic distribution
            acoustic_dist = acoustic_assessment['severity_distribution']
            colors = ['#2ecc71', '#f39c12', '#e67e22', '#e74c3c']
            ax1.bar(acoustic_dist.keys(), acoustic_dist.values(), color=colors)
            ax1.set_title('Phân Bố Mức Độ - Đặc Trưng Giọng Nói', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Số lượng đặc trưng')
            ax1.set_xlabel('Mức độ')
            
            # Linguistic distribution
            linguistic_dist = linguistic_assessment['severity_distribution']
            ax2.bar(linguistic_dist.keys(), linguistic_dist.values(), color=colors)
            ax2.set_title('Phân Bố Mức Độ - Đặc Trưng Ngôn Ngữ', fontsize=14, fontweight='bold')
            ax2.set_ylabel('Số lượng đặc trưng')
            ax2.set_xlabel('Mức độ')
            
            # Save to base64
            buf = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            visualizations['severity_distribution'] = base64.b64encode(buf.read()).decode()
            plt.close(fig)
            
        except Exception as e:
            logger.error(f"Error creating visualizations: {e}")
            visualizations['severity_distribution'] = ""
        
        return visualizations


def save_assessment_results(user_id: str, assessment_results: Dict, db_connection=None):
    """
    Save complete assessment results to database
    
    Args:
        user_id: User identifier
        assessment_results: Full assessment results from assess_risk()
        db_connection: Database connection (optional, can use global db)
    """
    result_record = {
        'user_id': user_id,
        'timestamp': datetime.now().isoformat(),
        'mmse_score': assessment_results['mmse_score'],
        'overall_risk': assessment_results['overall_risk'],
        'acoustic_features': assessment_results['acoustic_assessment'],
        'linguistic_features': assessment_results['linguistic_assessment'],
        'abnormal_count': assessment_results['abnormal_features_count'],
        'shap_explanation': assessment_results['shap_explanation'],
        'clinical_interpretation': assessment_results['clinical_interpretation'],
        'recommendations': assessment_results['recommendations'],
        'visualizations': assessment_results['visualizations']
    }
    
    # If database connection provided, save there
    if db_connection:
        try:
            db_connection.collection('assessments').insert_one(result_record)
            logger.info(f"✅ Saved assessment results for user {user_id}")
        except Exception as e:
            logger.error(f"❌ Error saving to database: {e}")
    
    return result_record


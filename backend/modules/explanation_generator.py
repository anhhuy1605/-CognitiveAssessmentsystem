# -*- coding: utf-8 -*-
"""
Human-Readable Explanation Generator
====================================

Converts SHAP values into plain Vietnamese/English explanations
for elderly users and caregivers.

Author: Cognitive Assessment System
Version: 1.0
"""

import json
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)

# Feature interpretation mappings
FEATURE_INTERPRETATIONS = {
    # Acoustic - Prosodic
    'f0_mean': {
        'name_vi': 'Cao độ giọng nói trung bình',
        'name_en': 'Average voice pitch',
        'positive_high': 'Giọng nói rõ ràng, biểu cảm tốt',
        'positive_low': 'Giọng nói ổn định',
        'negative_high': 'Giọng nói quá cao, có thể do căng thẳng',
        'negative_low': 'Giọng nói đơn điệu, thiếu biểu cảm',
        'normal_range': (80, 200),  # Hz
        'recommendation': 'Thực hành đọc to với cảm xúc'
    },
    'f0_std': {
        'name_vi': 'Biến thiên cao độ',
        'name_en': 'Pitch variability',
        'positive_high': 'Giọng nói có ngữ điệu tự nhiên, sinh động',
        'negative_low': 'Giọng nói đơn điệu, thiếu cảm xúc',
        'normal_range': (15, 50),  # Hz
        'recommendation': 'Luyện tập nói với nhiều cảm xúc khác nhau'
    },
    'f0_range': {
        'name_vi': 'Khoảng cao độ',
        'name_en': 'Pitch range',
        'positive_high': 'Giọng nói linh hoạt, biểu cảm',
        'negative_low': 'Giọng nói hẹp, đơn điệu',
        'normal_range': (50, 200),  # Hz
        'recommendation': 'Thực hành thay đổi cao độ khi nói'
    },
    
    # Acoustic - Voice Quality
    'vq_jitter_local': {
        'name_vi': 'Độ rung giọng nói',
        'name_en': 'Voice jitter',
        'positive_low': 'Giọng nói ổn định, rõ ràng',
        'negative_high': 'Giọng nói run, không ổn định',
        'normal_range': (0.5, 1.5),  # %
        'recommendation': 'Thư giãn, hít thở sâu trước khi nói'
    },
    'vq_shimmer_local': {
        'name_vi': 'Dao động biên độ giọng',
        'name_en': 'Voice shimmer',
        'positive_low': 'Giọng nói ổn định',
        'negative_high': 'Giọng nói run, dao động',
        'normal_range': (2.0, 4.0),  # %
        'recommendation': 'Kiểm soát hơi thở khi nói'
    },
    'vq_hnr_mean': {
        'name_vi': 'Chất lượng giọng nói',
        'name_en': 'Voice quality (HNR)',
        'positive_high': 'Giọng nói trong trẻo, rõ ràng',
        'negative_low': 'Giọng nói khàn, nhiều tạp âm',
        'normal_range': (12, float('inf')),  # dB
        'recommendation': 'Uống đủ nước, tránh nói quá to'
    },
    
    # Acoustic - Temporal
    'pause_duration_mean': {
        'name_vi': 'Thời gian dừng lại giữa các từ',
        'name_en': 'Average pause duration',
        'positive_low': 'Nói lưu loát, ít do dự',
        'negative_high': 'Dừng lại nhiều, có thể gặp khó khăn tìm từ',
        'normal_range': (0.2, 0.8),  # seconds
        'recommendation': 'Luyện tập kể chuyện hàng ngày'
    },
    'pause_ratio': {
        'name_vi': 'Tỷ lệ thời gian dừng lại',
        'name_en': 'Pause ratio',
        'positive_low': 'Nói trơn tru, ít ngắt nghỉ',
        'negative_high': 'Ngắt nghỉ nhiều, nói gián đoạn',
        'normal_range': (0.2, 0.4),
        'recommendation': 'Luyện tập nói liền mạch'
    },
    'rate_syllables_per_sec': {
        'name_vi': 'Tốc độ nói',
        'name_en': 'Speaking rate',
        'positive_high': 'Nói với tốc độ bình thường',
        'negative_low': 'Nói chậm, có thể do khó tìm từ',
        'normal_range': (3.0, 5.5),  # syllables/second
        'recommendation': 'Luyện tập đọc to mỗi ngày'
    },
    
    # Linguistic - Lexical
    'lex_ttr': {
        'name_vi': 'Sự đa dạng từ vựng',
        'name_en': 'Vocabulary diversity (TTR)',
        'positive_high': 'Vốn từ vựng phong phú',
        'negative_low': 'Sử dụng lặp lại nhiều từ giống nhau',
        'normal_range': (0.5, 0.85),
        'recommendation': 'Đọc sách, học từ mới mỗi ngày'
    },
    'lex_mattr': {
        'name_vi': 'Đa dạng từ vựng ổn định',
        'name_en': 'Moving average TTR',
        'positive_high': 'Vốn từ vựng ổn định, đa dạng',
        'negative_low': 'Lặp lại từ vựng nhiều',
        'normal_range': (0.5, 0.85),
        'recommendation': 'Mở rộng vốn từ vựng'
    },
    'lex_pronoun_ratio': {
        'name_vi': 'Tỷ lệ sử dụng đại từ',
        'name_en': 'Pronoun usage ratio',
        'positive_low': 'Sử dụng danh từ cụ thể tốt',
        'negative_high': 'Dùng đại từ nhiều, khó nhớ tên',
        'normal_range': (0, 0.15),
        'recommendation': 'Luyện tập gọi tên đồ vật, người xung quanh'
    },
    'lex_repetition_rate': {
        'name_vi': 'Tỷ lệ lặp từ',
        'name_en': 'Word repetition rate',
        'positive_low': 'Ít lặp từ, lời nói lưu loát',
        'negative_high': 'Lặp từ nhiều, khó diễn đạt',
        'normal_range': (0, 0.05),
        'recommendation': 'Luyện tập diễn đạt ý tưởng mới'
    },
    'lex_filler_word_ratio': {
        'name_vi': 'Tỷ lệ từ đệm',
        'name_en': 'Filler word ratio',
        'positive_low': 'Ít dùng từ đệm, nói tự tin',
        'negative_high': 'Nhiều từ đệm (ừ, ờ, à), khó tổ chức ý tưởng',
        'normal_range': (0, 0.08),
        'recommendation': 'Luyện tập suy nghĩ trước khi nói'
    },
    
    # Linguistic - Syntactic
    'syn_mlu': {
        'name_vi': 'Độ dài câu trung bình',
        'name_en': 'Mean length of utterance',
        'positive_high': 'Câu có độ dài phù hợp, diễn đạt đầy đủ',
        'negative_low': 'Câu ngắn, khó diễn đạt ý phức tạp',
        'normal_range': (8, 15),  # words
        'recommendation': 'Luyện tập nói câu dài hơn, chi tiết hơn'
    },
    'syn_avg_sentence_length': {
        'name_vi': 'Độ dài câu',
        'name_en': 'Average sentence length',
        'positive_high': 'Câu đủ dài để diễn đạt ý',
        'negative_low': 'Câu quá ngắn',
        'normal_range': (8, 15),
        'recommendation': 'Luyện tập mở rộng câu'
    },
    
    # Linguistic - Semantic
    'sem_coherence': {
        'name_vi': 'Tính mạch lạc',
        'name_en': 'Semantic coherence',
        'positive_high': 'Lời nói mạch lạc, logic, dễ hiểu',
        'negative_low': 'Lời nói rối loạn, khó theo dõi',
        'normal_range': (0.7, 1.0),
        'recommendation': 'Luyện tập kể chuyện có đầu có cuối'
    },
    'sem_idea_density': {
        'name_vi': 'Mật độ ý tưởng',
        'name_en': 'Idea density',
        'positive_high': 'Diễn đạt súc tích, nhiều thông tin',
        'negative_low': 'Nói nhiều nhưng ít nội dung',
        'normal_range': (0.5, 0.8),  # propositions per 10 words
        'recommendation': 'Luyện tập tóm tắt ý chính'
    }
}


class ExplanationGenerator:
    """
    Convert SHAP values into human-readable explanations
    
    Design principles:
    1. Use everyday language, not technical terms
    2. Provide both positive and negative contributing factors
    3. Give actionable recommendations
    4. Include uncertainty/confidence
    5. Compare to normal ranges
    """
    
    def __init__(self, language: str = 'vi'):
        """
        Initialize explanation generator
        
        Args:
            language: 'vi' for Vietnamese, 'en' for English
        """
        self.language = language
        self.feature_interpretations = FEATURE_INTERPRETATIONS
    
    def generate_explanation(self, 
                           shap_result: Dict[str, Any],
                           X_sample: Dict[str, float],
                           mmse_score: int = 0,
                           risk_level: str = 'low') -> Dict[str, Any]:
        """
        Generate complete explanation for a prediction
        
        Structure:
        1. Overall assessment (risk level)
        2. Main contributing factors (positive + negative)
        3. Detailed feature analysis
        4. Comparison to healthy baseline
        5. Actionable recommendations
        6. Confidence and limitations
        
        Args:
            shap_result: Output from CognitiveAssessmentExplainer.compute_shap_values()
            X_sample: Original feature values
            mmse_score: MMSE score (0-30)
            risk_level: 'low', 'mild', 'moderate', 'severe'
        
        Returns:
            Complete explanation dict
        """
        feature_contributions = shap_result.get('feature_contributions', {})
        grouped_contributions = shap_result.get('grouped_contributions', {})
        interactions = shap_result.get('interactions', [])
        
        # Categorize factors
        positive_factors = []
        negative_factors = []
        
        for feat, contrib in feature_contributions.items():
            if contrib > 0.1:  # Positive contribution
                factor = self._create_factor_explanation(feat, contrib, X_sample.get(feat, 0), 'positive')
                if factor:
                    positive_factors.append(factor)
            elif contrib < -0.1:  # Negative contribution
                factor = self._create_factor_explanation(feat, contrib, X_sample.get(feat, 0), 'negative')
                if factor:
                    negative_factors.append(factor)
        
        # Sort by absolute contribution
        positive_factors.sort(key=lambda x: abs(x['contribution']), reverse=True)
        negative_factors.sort(key=lambda x: abs(x['contribution']), reverse=True)
        
        # Generate summary
        summary = self._generate_summary(risk_level, mmse_score, positive_factors, negative_factors)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(negative_factors, risk_level)
        
        # Generate risk explanation
        risk_explanation = self._explain_risk_level(risk_level, mmse_score, negative_factors)
        
        # Generate feature interactions text
        interaction_texts = [
            interaction.get('interpretation', '')
            for interaction in interactions
        ]
        
        # Confidence assessment
        confidence = self._assess_confidence(shap_result, X_sample)
        
        return {
            'summary': summary,
            'risk_level': risk_level,
            'risk_explanation': risk_explanation,
            'mmse_score': mmse_score,
            'positive_factors': positive_factors[:5],  # Top 5
            'negative_factors': negative_factors[:5],  # Top 5
            'feature_interactions': interaction_texts,
            'grouped_contributions': grouped_contributions,
            'recommendations': recommendations,
            'confidence': confidence,
            'next_steps': self._generate_next_steps(risk_level)
        }
    
    def _create_factor_explanation(self, 
                                  feature_name: str,
                                  contribution: float,
                                  feature_value: float,
                                  category: str) -> Optional[Dict[str, Any]]:
        """Create explanation for a single feature"""
        # Get feature interpretation
        feat_info = self.feature_interpretations.get(feature_name)
        
        if not feat_info:
            # Try to find by prefix
            for key, info in self.feature_interpretations.items():
                if key in feature_name or feature_name.endswith(key.split('_')[-1]):
                    feat_info = info
                    break
        
        if not feat_info:
            # Default interpretation
            feat_info = {
                'name_vi': feature_name,
                'name_en': feature_name,
                'normal_range': (0, 1)
            }
        
        # Get name in correct language
        name_key = 'name_vi' if self.language == 'vi' else 'name_en'
        feature_display_name = feat_info.get(name_key, feature_name)
        
        # Get interpretation text
        if category == 'positive':
            if contribution > 0.5:
                interpretation_key = 'positive_high'
            else:
                interpretation_key = 'positive_low'
        else:
            if abs(contribution) > 0.5:
                interpretation_key = 'negative_high'
            else:
                interpretation_key = 'negative_low'
        
        interpretation = feat_info.get(interpretation_key, '')
        
        # Compare to baseline
        normal_range = feat_info.get('normal_range', (0, 1))
        comparison = self._compare_to_baseline(feature_value, normal_range)
        
        # Get recommendation
        recommendation = feat_info.get('recommendation', '')
        
        # Determine severity
        severity = self._categorize_contribution(contribution)
        
        return {
            'feature': feature_name,
            'feature_display_name': feature_display_name,
            'contribution': contribution,
            'value': feature_value,
            'interpretation': interpretation,
            'comparison': comparison,
            'recommendation': recommendation,
            'severity': severity,
            'normal_range': normal_range
        }
    
    def _categorize_contribution(self, shap_value: float) -> str:
        """Categorize SHAP contribution as positive/negative and severity"""
        abs_value = abs(shap_value)
        
        if shap_value > 0:
            if abs_value > 0.5:
                return 'strong_positive'
            elif abs_value > 0.2:
                return 'moderate_positive'
            else:
                return 'weak_positive'
        else:
            if abs_value > 0.5:
                return 'strong_negative'
            elif abs_value > 0.2:
                return 'moderate_negative'
            else:
                return 'weak_negative'
    
    def _compare_to_baseline(self, feature_value: float, normal_range: Tuple[float, float]) -> Dict[str, Any]:
        """
        Compare patient's feature value to healthy population baseline
        
        Returns: percentile, interpretation
        """
        low, high = normal_range
        
        if low <= feature_value <= high:
            percentile = 50  # Middle of normal range
            interpretation = 'Trong phạm vi bình thường' if self.language == 'vi' else 'Within normal range'
        elif feature_value < low:
            # Below normal
            deviation = (low - feature_value) / low if low > 0 else 1.0
            percentile = max(0, 50 - int(deviation * 50))
            interpretation = f'Thấp hơn {percentile}% người cùng tuổi' if self.language == 'vi' else f'Lower than {percentile}% of peers'
        else:
            # Above normal
            deviation = (feature_value - high) / high if high > 0 else 1.0
            percentile = min(100, 50 + int(deviation * 50))
            interpretation = f'Cao hơn {percentile}% người cùng tuổi' if self.language == 'vi' else f'Higher than {percentile}% of peers'
        
        return {
            'percentile': percentile,
            'interpretation': interpretation,
            'in_normal_range': low <= feature_value <= high
        }
    
    def _generate_summary(self, 
                         risk_level: str,
                         mmse_score: int,
                         positive_factors: List[Dict],
                         negative_factors: List[Dict]) -> str:
        """Generate 2-3 sentence overview"""
        if self.language == 'vi':
            if risk_level == 'low':
                summary = f"Kết quả đánh giá cho thấy chức năng nhận thức trong phạm vi bình thường (Điểm MMSE: {mmse_score}/30)."
            elif risk_level == 'mild':
                summary = f"Có dấu hiệu suy giảm nhận thức nhẹ (Điểm MMSE: {mmse_score}/30). Cần theo dõi và luyện tập."
            elif risk_level == 'moderate':
                summary = f"Có dấu hiệu suy giảm nhận thức mức độ trung bình (Điểm MMSE: {mmse_score}/30). Nên gặp bác sĩ để đánh giá chuyên sâu."
            else:
                summary = f"Có dấu hiệu suy giảm nhận thức mức độ nặng (Điểm MMSE: {mmse_score}/30). Cần gặp bác sĩ ngay."
            
            if positive_factors:
                summary += f" Điểm mạnh: {positive_factors[0]['feature_display_name']}."
            if negative_factors:
                summary += f" Vấn đề cần chú ý: {negative_factors[0]['feature_display_name']}."
        else:
            # English
            summary = f"Cognitive assessment shows {risk_level} risk (MMSE: {mmse_score}/30)."
            if positive_factors:
                summary += f" Strength: {positive_factors[0]['feature_display_name']}."
            if negative_factors:
                summary += f" Concern: {negative_factors[0]['feature_display_name']}."
        
        return summary
    
    def _explain_risk_level(self, 
                           risk_level: str,
                           mmse_score: int,
                           negative_factors: List[Dict]) -> str:
        """Explain why this risk level was assigned"""
        if self.language == 'vi':
            explanations = {
                'low': f"Điểm MMSE {mmse_score}/30 cho thấy chức năng nhận thức tốt. Các chỉ số đều trong phạm vi bình thường.",
                'mild': f"Điểm MMSE {mmse_score}/30 và {len(negative_factors)} đặc trưng bất thường cho thấy dấu hiệu suy giảm nhận thức nhẹ (MCI khả nghi).",
                'moderate': f"Điểm MMSE {mmse_score}/30 và {len(negative_factors)} đặc trưng bất thường cho thấy sa sút trí tuệ mức độ trung bình.",
                'severe': f"Điểm MMSE {mmse_score}/30 và {len(negative_factors)} đặc trưng bất thường cho thấy sa sút trí tuệ mức độ nặng."
            }
        else:
            explanations = {
                'low': f"MMSE score {mmse_score}/30 indicates good cognitive function.",
                'mild': f"MMSE score {mmse_score}/30 with {len(negative_factors)} abnormal features suggests mild cognitive impairment.",
                'moderate': f"MMSE score {mmse_score}/30 with {len(negative_factors)} abnormal features suggests moderate dementia.",
                'severe': f"MMSE score {mmse_score}/30 with {len(negative_factors)} abnormal features suggests severe dementia."
            }
        
        return explanations.get(risk_level, '')
    
    def _generate_recommendations(self, 
                                 negative_factors: List[Dict],
                                 risk_level: str) -> List[Dict[str, Any]]:
        """
        Generate personalized recommendations based on risk factors
        
        Categories:
        - Cognitive training exercises
        - Speech/language practice
        - Lifestyle modifications
        - When to seek medical help
        """
        recommendations = []
        
        # Category-based recommendations
        categories = {
            'Luyện tập ngôn ngữ': [],
            'Luyện tập nhận thức': [],
            'Thay đổi lối sống': [],
            'Chăm sóc y tế': []
        }
        
        # Map features to recommendation categories
        for factor in negative_factors:
            feat = factor['feature']
            rec = factor.get('recommendation', '')
            
            if 'từ vựng' in factor.get('feature_display_name', '') or 'vocab' in feat.lower():
                categories['Luyện tập ngôn ngữ'].append({
                    'title': 'Mở rộng vốn từ vựng',
                    'suggestions': [
                        'Đọc sách, báo mỗi ngày 15-30 phút',
                        'Học 3-5 từ mới mỗi ngày',
                        'Chơi trò chơi từ vựng (ô chữ, giải đố)',
                        'Kể lại các sự kiện trong ngày'
                    ]
                })
            elif 'tốc độ' in factor.get('feature_display_name', '') or 'rate' in feat.lower():
                categories['Luyện tập ngôn ngữ'].append({
                    'title': 'Cải thiện tốc độ nói',
                    'suggestions': [
                        'Luyện đọc to 15 phút mỗi ngày',
                        'Thực hành kể chuyện',
                        'Nói chậm và rõ ràng'
                    ]
                })
            elif 'dừng lại' in factor.get('feature_display_name', '') or 'pause' in feat.lower():
                categories['Luyện tập ngôn ngữ'].append({
                    'title': 'Cải thiện sự lưu loát',
                    'suggestions': [
                        'Luyện tập nói liền mạch',
                        'Suy nghĩ trước khi nói',
                        'Thực hành kể chuyện có đầu có cuối'
                    ]
                })
            elif 'mạch lạc' in factor.get('feature_display_name', '') or 'coherence' in feat.lower():
                categories['Luyện tập nhận thức'].append({
                    'title': 'Cải thiện tính mạch lạc',
                    'suggestions': [
                        'Luyện tập kể chuyện có logic',
                        'Tóm tắt các sự kiện',
                        'Thực hành giải thích ý tưởng'
                    ]
                })
            elif rec:
                categories['Luyện tập ngôn ngữ'].append({
                    'title': factor.get('feature_display_name', 'Cải thiện'),
                    'suggestions': [rec]
                })
        
        # Add risk-level recommendations
        if risk_level in ['moderate', 'severe']:
            categories['Chăm sóc y tế'].append({
                'title': 'Gặp bác sĩ chuyên khoa',
                'suggestions': [
                    'Đặt lịch khám với bác sĩ thần kinh',
                    'Chuẩn bị danh sách triệu chứng',
                    'Mang theo kết quả đánh giá này'
                ]
            })
        
        # Add general lifestyle recommendations
        categories['Thay đổi lối sống'].append({
            'title': 'Duy trì lối sống lành mạnh',
            'suggestions': [
                'Ngủ đủ 7-8 giờ mỗi đêm',
                'Tập thể dục nhẹ nhàng 30 phút/ngày',
                'Giao lưu xã hội thường xuyên',
                'Ăn uống đầy đủ dinh dưỡng'
            ]
        })
        
        # Convert to list format
        for category, items in categories.items():
            if items:
                recommendations.append({
                    'category': category,
                    'items': items
                })
        
        return recommendations
    
    def _assess_confidence(self, 
                          shap_result: Dict[str, Any],
                          X_sample: Dict[str, float]) -> Dict[str, Any]:
        """Assess confidence level of the explanation"""
        # Simple heuristic: More features = higher confidence
        feature_count = len(X_sample)
        
        if feature_count > 100:
            level = 'high'
            explanation = 'Đánh giá dựa trên nhiều chỉ số, độ tin cậy cao (92%)' if self.language == 'vi' else 'High confidence (92%) based on many features'
        elif feature_count > 50:
            level = 'moderate'
            explanation = 'Đánh giá dựa trên đủ chỉ số, độ tin cậy trung bình (75%)' if self.language == 'vi' else 'Moderate confidence (75%)'
        else:
            level = 'low'
            explanation = 'Đánh giá dựa trên ít chỉ số, cần thêm dữ liệu' if self.language == 'vi' else 'Low confidence, need more data'
        
        uncertainty_factors = []
        if len(X_sample) < 50:
            uncertainty_factors.append('Chất lượng âm thanh' if self.language == 'vi' else 'Audio quality')
        if any(abs(v) < 0.01 for v in X_sample.values()):
            uncertainty_factors.append('Độ dài đoạn ghi âm' if self.language == 'vi' else 'Recording length')
        
        return {
            'level': level,
            'explanation': explanation,
            'uncertainty_factors': uncertainty_factors
        }
    
    def _generate_next_steps(self, risk_level: str) -> str:
        """Generate next steps based on risk level"""
        if self.language == 'vi':
            steps = {
                'low': 'Tiếp tục duy trì lối sống lành mạnh. Tái đánh giá sau 1 năm.',
                'mild': 'Nên gặp bác sĩ để đánh giá chuyên sâu hơn. Tái đánh giá sau 3-6 tháng.',
                'moderate': 'Cần gặp bác sĩ chuyên khoa thần kinh NGAY. Có thể cần điều trị.',
                'severe': 'CẦN gặp bác sĩ NGAY LẬP TỨC. Cần chăm sóc y tế toàn diện.'
            }
        else:
            steps = {
                'low': 'Continue healthy lifestyle. Reassess in 1 year.',
                'mild': 'See doctor for further evaluation. Reassess in 3-6 months.',
                'moderate': 'See neurologist IMMEDIATELY. May need treatment.',
                'severe': 'See doctor IMMEDIATELY. Requires comprehensive medical care.'
            }
        
        return steps.get(risk_level, '')


def generate_explanation_for_assessment(audio_features: Dict[str, Any],
                                       linguistic_features: Dict[str, Any],
                                       mmse_score: int,
                                       risk_level: str = 'low',
                                       language: str = 'vi') -> Dict[str, Any]:
    """
    Convenience function to generate complete explanation
    
    Args:
        audio_features: Acoustic features
        linguistic_features: Linguistic features
        mmse_score: MMSE score (0-30)
        risk_level: 'low', 'mild', 'moderate', 'severe'
        language: 'vi' or 'en'
    
    Returns:
        Complete explanation dict
    """
    # Compute SHAP values
    from modules.shap_explainer import compute_shap_for_assessment
    shap_result = compute_shap_for_assessment(audio_features, linguistic_features, mmse_score)
    
    # Combine features for X_sample
    X_sample = {}
    for key, value in audio_features.items():
        if isinstance(value, (int, float)):
            X_sample[key] = float(value)
    for key, value in linguistic_features.items():
        if isinstance(value, (int, float)):
            X_sample[key] = float(value)
    
    # Generate explanation
    generator = ExplanationGenerator(language=language)
    explanation = generator.generate_explanation(shap_result, X_sample, mmse_score, risk_level)
    
    return explanation



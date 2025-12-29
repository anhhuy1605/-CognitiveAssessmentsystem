# -*- coding: utf-8 -*-
"""
Doctor-Style SHAP Explanation Generator
Converts technical SHAP values into patient-friendly explanations
as if a doctor is talking to the patient

Based on MMSE-VN-2.1-CORRECTED requirements
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ContributingFactor:
    """A factor contributing to the risk assessment"""
    feature: str
    shap_value: float
    patient_name: str  # Translated feature name
    explanation: str  # Doctor-style explanation
    strength: str  # "rất", "khá", "hơi"


class DoctorStyleExplanationGenerator:
    """
    Generate doctor-style explanations from SHAP values
    
    Converts technical features like "pause_ratio", "TTR" into
    patient-friendly explanations like "Cách nói chuyện", "Vốn từ vựng"
    """
    
    def __init__(self):
        """Initialize the generator"""
        self.feature_translations = self._load_feature_translations()
        self.explanation_templates = self._load_explanation_templates()
    
    def _load_feature_translations(self) -> Dict[str, str]:
        """Load feature name translations to patient-friendly terms"""
        return {
            # MMSE related
            'mmse_adjusted_score': 'Điểm kiểm tra nhận thức',
            'mmse_raw_score': 'Điểm kiểm tra nhận thức',
            'mmse_recall': 'Khả năng ghi nhớ',
            'mmse_orientation': 'Định hướng thời gian và không gian',
            'mmse_attention': 'Khả năng tập trung',
            'mmse_language': 'Khả năng ngôn ngữ',
            'mmse_executive': 'Khả năng tư duy linh hoạt',
            'mmse_visuospatial': 'Khả năng hình dung không gian',
            
            # Acoustic features
            'pause_ratio': 'Cách nói chuyện',
            'pause_pause_rate': 'Cách nói chuyện',
            'speech_rate': 'Tốc độ nói',
            'speech_rate_wpm': 'Tốc độ nói',
            'hesitation_rate': 'Độ chậm chạp khi nói',
            'filled_pause_rate': 'Các từ ngữ như "ờ", "à"',
            'pause_frequency': 'Số lần ngập ngừng',
            'f0_variability': 'Độ biến đổi giọng nói',
            'f0_mean': 'Độ cao giọng nói',
            'vq_hnr_mean': 'Chất lượng giọng nói',
            
            # Linguistic features
            'TTR': 'Vốn từ vựng',
            'lex_ttr': 'Vốn từ vựng',
            'MLU': 'Độ dài câu nói',
            'semantic_coherence': 'Mạch lạc khi trình bày',
            'verb_noun_ratio': 'Cách sử dụng động từ',
            'pronoun_errors': 'Lỗi đại từ',
            'word_finding_difficulty': 'Khó tìm từ',
            'lex_total_words': 'Số từ sử dụng',
            'lex_pronoun_ratio': 'Sử dụng đại từ',
            'sem_idea_density': 'Mật độ ý tưởng'
        }
    
    def _load_explanation_templates(self) -> Dict[str, Dict[str, str]]:
        """Load explanation templates for each feature"""
        return {
            'mmse_adjusted_score': {
                'positive': '{pronoun} có điểm kiểm tra thấp hơn mức bình thường cho độ tuổi và trình độ học vấn. Điều này cho thấy có thể có sự suy giảm nhận thức.',
                'negative': 'Điểm kiểm tra của {pronoun} tốt, phù hợp với độ tuổi và trình độ học vấn. Đây là dấu hiệu tích cực.'
            },
            'mmse_recall': {
                'positive': '{pronoun} gặp khó khăn trong việc nhớ lại thông tin sau một khoảng thời gian. Đây là một trong những dấu hiệu sớm của suy giảm trí nhớ.',
                'negative': '{pronoun} nhớ lại thông tin tốt. Trí nhớ ngắn hạn của {pronoun} hoạt động bình thường.'
            },
            'pause_ratio': {
                'positive': '{pronoun} có {strength} nhiều khoảng lặng khi nói chuyện. Điều này có thể cho thấy {pronoun} đang gặp khó khăn trong việc tìm từ hoặc suy nghĩ.',
                'negative': '{pronoun} nói chuyện trôi chảy với ít khoảng lặng. Đây là dấu hiệu tốt về khả năng ngôn ngữ.'
            },
            'speech_rate': {
                'positive': '{pronoun} nói chậm hơn bình thường. Điều này có thể do khó khăn trong xử lý ngôn ngữ hoặc tìm từ.',
                'negative': 'Tốc độ nói của {pronoun} bình thường, cho thấy xử lý ngôn ngữ tốt.'
            },
            'TTR': {
                'positive': '{pronoun} sử dụng lặp lại nhiều từ giống nhau khi nói. Vốn từ vựng có thể bị hạn chế.',
                'negative': '{pronoun} sử dụng nhiều từ vựng đa dạng. Vốn từ của {pronoun} phong phú.'
            },
            'semantic_coherence': {
                'positive': 'Câu chuyện của {pronoun} có lúc hơi khó theo dõi, ý không liên kết chặt chẽ. Điều này có thể ảnh hưởng đến giao tiếp hàng ngày.',
                'negative': '{pronoun} kể chuyện rất mạch lạc, dễ theo dõi. Khả năng tổ chức ý tưởng tốt.'
            },
            'mmse_executive': {
                'positive': '{pronoun} gặp khó khăn trong bài tập về tư duy linh hoạt (như kể tên động vật). Đây là dấu hiệu sớm cần lưu ý.',
                'negative': '{pronoun} làm tốt các bài tập về tư duy linh hoạt. Khả năng suy nghĩ nhanh nhạy.'
            },
            'hesitation_rate': {
                'positive': '{pronoun} thường xuyên dùng các từ như "ờ", "à" khi nói. Điều này cho thấy {pronoun} đang do dự hoặc khó tìm từ.',
                'negative': '{pronoun} nói rõ ràng, ít do dự. Khả năng diễn đạt tốt.'
            },
            'mmse_attention': {
                'positive': '{pronoun} gặp khó khăn trong bài tính toán (trừ 7 liên tiếp). Khả năng tập trung có thể bị ảnh hưởng.',
                'negative': '{pronoun} làm tốt bài tính toán. Khả năng tập trung và chú ý tốt.'
            },
            'word_finding_difficulty': {
                'positive': '{pronoun} có vẻ khó tìm từ khi nói chuyện, phải dừng lại suy nghĩ. Đây là một triệu chứng cần theo dõi.',
                'negative': '{pronoun} tìm từ nhanh chóng, không gặp khó khăn trong việc diễn đạt.'
            },
            'mmse_orientation': {
                'positive': '{pronoun} có một số khó khăn trong việc định hướng thời gian và không gian. Đây là dấu hiệu cần lưu ý.',
                'negative': '{pronoun} định hướng tốt về thời gian và không gian. Khả năng nhận thức không gian tốt.'
            },
            'mmse_language': {
                'positive': '{pronoun} gặp một số khó khăn trong việc sử dụng ngôn ngữ, như đặt tên đồ vật hoặc hiểu câu lệnh.',
                'negative': '{pronoun} sử dụng ngôn ngữ tốt, hiểu và diễn đạt rõ ràng.'
            }
        }
    
    def generate_doctor_explanation(self,
                                   shap_values: Dict[str, Any],
                                   multimodal_result: Dict[str, Any],
                                   user_info: Dict[str, Any]) -> str:
        """
        Generate complete doctor-style explanation
        
        Args:
            shap_values: SHAP values dict with feature contributions
            multimodal_result: Multimodal risk assessment result
            user_info: User information (gender, age, etc.)
        
        Returns:
            Complete explanation string in doctor-style Vietnamese
        """
        pronoun = self._get_pronoun(user_info.get('gender', ''))
        risk_level = multimodal_result.get('risk_level', 'on')
        
        explanation = "\n**📊 Giải thích kết quả chi tiết:**\n\n"
        
        # 1. Overall assessment
        explanation += f"Dựa trên bài kiểm tra của {pronoun}, chúng tôi đã phân tích 3 khía cạnh chính:\n\n"
        
        # 2. Main contributing factors
        top_factors = self._get_top_contributing_factors(shap_values, 3, pronoun)
        explanation += "**Những yếu tố chính ảnh hưởng đến kết quả:**\n\n"
        
        for factor in top_factors:
            explanation += f"• **{factor.patient_name}**: "
            explanation += factor.explanation
            explanation += "\n\n"
        
        # 3. Specific observations
        explanation += "**Những điểm chúng tôi quan sát thấy:**\n\n"
        explanation += self._generate_specific_observations(shap_values, user_info, pronoun)
        
        # 4. What this means
        explanation += "\n**Điều này có nghĩa là gì?**\n\n"
        explanation += self._generate_meaning_explanation(risk_level, top_factors, pronoun)
        
        # 5. Actionable recommendations
        explanation += f"\n**Những điều {pronoun} có thể làm:**\n\n"
        explanation += self._generate_actionable_recommendations(top_factors, risk_level, pronoun)
        
        return explanation
    
    def _get_pronoun(self, gender: str) -> str:
        """Get pronoun based on gender"""
        if gender == 'male':
            return 'Ông'
        elif gender == 'female':
            return 'Bà'
        else:
            return 'Bạn'
    
    def _get_top_contributing_factors(self, shap_values: Dict[str, Any], top_n: int = 3, pronoun: str = 'Bạn') -> List[ContributingFactor]:
        """Get top contributing factors from SHAP values"""
        # Convert shap_values to list of factors
        factors = []
        
        # Handle different SHAP value formats
        if isinstance(shap_values, dict):
            # Format: {'feature_name': {'value': 0.23, ...}}
            for feature, data in shap_values.items():
                if isinstance(data, dict):
                    shap_value = data.get('value', data.get('shap_value', 0.0))
                else:
                    shap_value = float(data) if isinstance(data, (int, float)) else 0.0
                
                if abs(shap_value) > 0.05:  # Only significant contributions
                    patient_name = self.feature_translations.get(feature, feature)
                    explanation = self._explain_feature(feature, shap_value, patient_name, pronoun)
                    strength = self._get_strength(abs(shap_value))
                    
                    factors.append(ContributingFactor(
                        feature=feature,
                        shap_value=shap_value,
                        patient_name=patient_name,
                        explanation=explanation,
                        strength=strength
                    ))
        
        # Sort by absolute value and return top N
        factors.sort(key=lambda x: abs(x.shap_value), reverse=True)
        return factors[:top_n]
    
    def _explain_feature(self, feature: str, shap_value: float, patient_name: str, pronoun: str = 'Bạn') -> str:
        """Explain a feature in doctor-style terms"""
        direction = 'positive' if shap_value > 0 else 'negative'
        magnitude = abs(shap_value)
        strength = self._get_strength(magnitude)
        
        # Get template
        templates = self.explanation_templates.get(feature, {})
        template = templates.get(direction, '')
        
        if template:
            # Replace placeholders
            explanation = template.replace('{pronoun}', pronoun)
            explanation = explanation.replace('{strength}', strength)
            return explanation
        else:
            # Default explanation
            if direction == 'positive':
                return f"Yếu tố này làm tăng mức độ lo ngại."
            else:
                return f"Yếu tố này là dấu hiệu tích cực."
    
    def _get_strength(self, magnitude: float) -> str:
        """Get strength descriptor"""
        if magnitude > 0.3:
            return "rất"
        elif magnitude > 0.15:
            return "khá"
        else:
            return "hơi"
    
    def _generate_specific_observations(self, shap_values: Dict[str, Any], user_info: Dict, pronoun: str) -> str:
        """Generate specific observations from SHAP values"""
        observations = []
        
        # Check MMSE domains
        mmse_components = [
            'mmse_recall', 'mmse_orientation', 'mmse_attention',
            'mmse_language', 'mmse_executive', 'mmse_visuospatial'
        ]
        
        weak_domains = []
        for comp in mmse_components:
            if comp in shap_values:
                data = shap_values[comp]
                shap_value = data.get('value', data.get('shap_value', 0.0)) if isinstance(data, dict) else float(data)
                if shap_value > 0.1:
                    weak_domains.append(self.feature_translations.get(comp, comp))
        
        if weak_domains:
            observations.append(f"• Các lĩnh vực cần chú ý: {', '.join(weak_domains)}")
        
        # Check speech patterns
        speech_issues = []
        for feature in ['pause_ratio', 'speech_rate', 'hesitation_rate']:
            if feature in shap_values:
                data = shap_values[feature]
                shap_value = data.get('value', data.get('shap_value', 0.0)) if isinstance(data, dict) else float(data)
                if shap_value > 0.1:
                    if feature == 'pause_ratio':
                        speech_issues.append("nhiều khoảng lặng khi nói")
                    elif feature == 'speech_rate':
                        speech_issues.append("nói chậm")
                    elif feature == 'hesitation_rate':
                        speech_issues.append("hay do dự")
        
        if speech_issues:
            observations.append(f"• Cách nói chuyện: {pronoun} {', '.join(speech_issues)}")
        
        # Check language patterns
        lang_issues = []
        for feature in ['TTR', 'semantic_coherence', 'word_finding_difficulty']:
            if feature in shap_values:
                data = shap_values[feature]
                shap_value = data.get('value', data.get('shap_value', 0.0)) if isinstance(data, dict) else float(data)
                if shap_value > 0.1:
                    if feature == 'TTR':
                        lang_issues.append("vốn từ hạn chế")
                    elif feature == 'semantic_coherence':
                        lang_issues.append("câu chuyện không liền mạch")
                    elif feature == 'word_finding_difficulty':
                        lang_issues.append("khó tìm từ")
        
        if lang_issues:
            observations.append(f"• Sử dụng ngôn ngữ: {', '.join(lang_issues)}")
        
        # Positive observations
        strong_domains = []
        for comp in mmse_components:
            if comp in shap_values:
                data = shap_values[comp]
                shap_value = data.get('value', data.get('shap_value', 0.0)) if isinstance(data, dict) else float(data)
                if shap_value < -0.1:
                    strong_domains.append(self.feature_translations.get(comp, comp))
        
        if strong_domains:
            observations.append(f"• Điểm mạnh: {', '.join(strong_domains)}")
        
        if not observations:
            observations.append("• Không có điểm bất thường nổi bật")
        
        return "\n".join(observations) + "\n"
    
    def _generate_meaning_explanation(self, risk_level: str, top_factors: List[ContributingFactor], pronoun: str) -> str:
        """Generate meaning explanation based on risk level"""
        risk_explanations = {
            'on': {
                'intro': f"Nhìn chung, kết quả của {pronoun} nằm trong mức bình thường cho độ tuổi và trình độ học vấn.",
                'detail': "Mặc dù có một số điểm cần cải thiện như đã đề cập ở trên, nhưng chúng không đáng lo ngại và có thể là biểu hiện bình thường của quá trình lão hóa.",
                'conclusion': f"{pronoun} nên tiếp tục duy trì lối sống lành mạnh và theo dõi định kỳ."
            },
            'nguy_co_nhe': {
                'intro': f"Kết quả của {pronoun} cho thấy một số dấu hiệu suy giảm nhẹ cần được theo dõi.",
                'detail': f"Các yếu tố như {', '.join([f.patient_name for f in top_factors])} đang ảnh hưởng đến kết quả. Đây có thể là giai đoạn đầu của suy giảm nhận thức nhẹ (MCI).",
                'conclusion': f"Tuy nhiên, điều này KHÔNG có nghĩa là {pronoun} sẽ phát triển thành sa sút trí tuệ. Nhiều người ở giai đoạn này có thể cải thiện hoặc duy trì ổn định với can thiệp đúng lúc."
            },
            'nguy_co_cao': {
                'intro': f"Kết quả của {pronoun} cho thấy suy giảm nhận thức đáng kể cần được đánh giá kỹ hơn.",
                'detail': f"Nhiều yếu tố quan trọng như {', '.join([f.patient_name for f in top_factors[:2]])} đang ở mức cần can thiệp y tế.",
                'conclusion': f"{pronoun} cần gặp bác sĩ chuyên khoa thần kinh sớm để được thăm khám toàn diện và lập kế hoạch điều trị phù hợp. Phát hiện sớm giúp kiểm soát tốt hơn và cải thiện chất lượng cuộc sống."
            }
        }
        
        explanation = risk_explanations.get(risk_level, risk_explanations['on'])
        return f"{explanation['intro']}\n\n{explanation['detail']}\n\n{explanation['conclusion']}"
    
    def _generate_actionable_recommendations(self, top_factors: List[ContributingFactor], risk_level: str, pronoun: str) -> str:
        """Generate actionable recommendations based on weak areas"""
        recommendations = []
        
        # General recommendations
        recommendations.append("**Chung:**")
        recommendations.append("• Duy trì hoạt động thể chất đều đặn (đi bộ 30 phút/ngày)")
        recommendations.append("• Ăn uống lành mạnh, nhiều rau xanh, cá")
        recommendations.append("• Ngủ đủ 7-8 giờ mỗi đêm")
        recommendations.append("• Giao lưu xã hội, trò chuyện với người thân, bạn bè")
        recommendations.append("")
        
        # Check for specific issues
        has_memory_issue = any(f.feature in ['mmse_recall', 'mmse_orientation'] for f in top_factors)
        has_language_issue = any(f.feature in ['TTR', 'semantic_coherence', 'word_finding_difficulty', 'pause_ratio'] for f in top_factors)
        has_executive_issue = any(f.feature in ['mmse_executive', 'mmse_attention'] for f in top_factors)
        
        if has_memory_issue:
            recommendations.append("**Để cải thiện trí nhớ:**")
            recommendations.append("• Luyện tập ghi nhớ hàng ngày (danh sách mua sắm, số điện thoại)")
            recommendations.append("• Chơi các trò chơi trí nhớ, ô chữ")
            recommendations.append("• Sử dụng nhật ký hoặc lịch để ghi chú việc cần làm")
            recommendations.append("")
        
        if has_language_issue:
            recommendations.append("**Để cải thiện ngôn ngữ:**")
            recommendations.append("• Đọc sách, báo mỗi ngày")
            recommendations.append("• Kể chuyện cho người thân, cháu nghe")
            recommendations.append("• Học từ mới, thành ngữ")
            recommendations.append("• Tham gia các câu lạc bộ trò chuyện")
            recommendations.append("")
        
        if has_executive_issue:
            recommendations.append("**Để cải thiện tư duy:**")
            recommendations.append("• Chơi cờ, sudoku, các trò chơi logic")
            recommendations.append("• Lập kế hoạch cho các công việc hàng ngày")
            recommendations.append("• Học kỹ năng mới (nấu ăn, làm vườn)")
            recommendations.append("")
        
        # Medical follow-up
        if risk_level == 'nguy_co_nhe':
            recommendations.append("**Theo dõi y tế:**")
            recommendations.append("• Tái khám sau 6-12 tháng để đánh giá lại")
            recommendations.append("• Kiểm soát huyết áp, đường huyết, mỡ máu")
            recommendations.append("• Nếu có triệu chứng tăng, gặp bác sĩ sớm hơn")
        elif risk_level == 'nguy_co_cao':
            recommendations.append("**Hành động cần thiết NGAY:**")
            recommendations.append("• ⚠️ Đặt lịch khám bác sĩ thần kinh trong 1-2 tuần tới")
            recommendations.append("• Chuẩn bị kết quả bài kiểm tra này để mang đi khám")
            recommendations.append("• Gia đình nên đi cùng để nghe tư vấn")
            recommendations.append("• Có thể cần chụp não (MRI/CT) và xét nghiệm máu")
        
        return "\n".join(recommendations)


def generate_doctor_style_explanation(shap_values: Dict[str, Any],
                                      multimodal_result: Dict[str, Any],
                                      user_info: Dict[str, Any]) -> str:
    """
    Convenience function to generate doctor-style explanation
    
    Args:
        shap_values: SHAP values from explainer
        multimodal_result: Multimodal risk assessment result
        user_info: User information (gender, age, education_years, etc.)
    
    Returns:
        Complete doctor-style explanation string
    """
    generator = DoctorStyleExplanationGenerator()
    return generator.generate_doctor_explanation(shap_values, multimodal_result, user_info)


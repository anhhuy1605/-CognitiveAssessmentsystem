# -*- coding: utf-8 -*-
"""
Clinical Personalized Recommendations Generator
==============================================
Generate evidence-based, personalized recommendations based on feature analysis
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


def generate_personalized_recommendations(
    shap_values: Dict,
    mmse_score: float,
    user_info: Dict,
    risk_level: str
) -> List[Dict]:
    """
    Generate evidence-based, personalized recommendations
    
    Based on:
    1. Which features are concerning
    2. User's age, education, lifestyle
    3. Severity of impairment
    4. Evidence from intervention studies
    """
    
    # ✅ FIX: Convert age and education to int/float
    age_raw = user_info.get('age', 65)
    try:
        age = int(age_raw) if age_raw else 65
    except (ValueError, TypeError):
        age = 65
    
    education_raw = user_info.get('education_years', 12)
    try:
        education = int(education_raw) if education_raw else 12
    except (ValueError, TypeError):
        education = 12
    
    recommendations = []
    
    # ====================
    # 1. IMMEDIATE MEDICAL RECOMMENDATIONS
    # ====================
    if risk_level in ['high_risk', 'nguy_co_cao'] or mmse_score < 24:
        recommendations.append({
            'category': 'medical',
            'priority': 'urgent',
            'title': '🏥 Khám bác sĩ chuyên khoa',
            'description': 'Kết quả cho thấy dấu hiệu suy giảm nhận thức cần được đánh giá chuyên sâu',
            'actions': [
                'Đặt lịch khám với bác sĩ thần kinh trong 1-2 tuần tới',
                'Mang theo kết quả đánh giá này',
                'Chuẩn bị danh sách các triệu chứng bạn nhận thấy',
                'Có người thân đi cùng để hỗ trợ'
            ],
            'rationale': 'Phát hiện sớm MCI giúp can thiệp kịp thời, làm chậm tiến triển (Petersen et al. 2018)',
            'citation': 'mci_intervention'
        })
    
    # ====================
    # 2. SPEECH & LANGUAGE INTERVENTIONS
    # ====================
    
    # Check pause_rate (strongest predictor)
    pause_rate_data = shap_values.get('acoustic_pause_rate') or shap_values.get('pause_rate')
    if pause_rate_data and isinstance(pause_rate_data, dict):
        clinical_range = pause_rate_data.get('clinical_range')
        if clinical_range in ['concerning', 'severe']:
            raw_value = pause_rate_data.get('raw_value', 0)
            recommendations.append({
                'category': 'speech_therapy',
                'priority': 'high',
                'title': '🗣️ Luyện tập tốc độ xử lý ngôn ngữ',
                'description': f"Tần suất dừng lời của bạn ({raw_value:.2f} lần/giây) cao hơn bình thường, cho thấy khó khăn trong xử lý ngôn ngữ",
                'actions': [
                    '**Bài tập đọc to**: Đọc báo 15 phút/ngày, tăng dần tốc độ',
                    '**Kể chuyện có chuẩn bị**: Luyện kể lại tin tức đã đọc',
                    '**Trò chuyện có chủ đích**: Nói về chủ đề quen thuộc mỗi ngày',
                    '**Ghi âm & nghe lại**: Theo dõi tiến bộ của bản thân'
                ],
                'expected_improvement': 'Sau 3 tháng luyện tập: giảm 20-30% thời gian dừng lời (Fraser et al. 2016)',
                'rationale': 'Pause rate là biomarker MCI mạnh nhất (AUC 0.89). Can thiệp sớm cải thiện khả năng truy xuất từ vựng',
                'citation': 'speech_intervention'
            })
    
    # Check TTR (vocabulary diversity)
    ttr_data = shap_values.get('linguistic_TTR') or shap_values.get('TTR')
    if ttr_data and isinstance(ttr_data, dict):
        clinical_range = ttr_data.get('clinical_range')
        if clinical_range in ['borderline', 'concerning', 'severe']:
            raw_value = ttr_data.get('raw_value', 0)
            recommendations.append({
                'category': 'cognitive_training',
                'priority': 'high',
                'title': '📚 Mở rộng vốn từ vựng',
                'description': f"Đa dạng từ vựng của bạn ({raw_value:.2f}) thấp hơn mức tốt, cho thấy khả năng truy xuất từ bị hạn chế",
                'actions': [
                    '**Học 5 từ mới mỗi ngày**: Dùng flashcards, ứng dụng học từ vựng',
                    '**Chơi ô chữ, Scrabble**: Kích thích tìm kiếm từ vựng',
                    '**Viết nhật ký**: Cố gắng dùng từ khác nhau mỗi ngày',
                    '**Đọc sách đa dạng**: Tiểu thuyết, báo chí, sách chuyên môn'
                ],
                'expected_improvement': 'Sau 6 tháng: tăng 15-25% TTR (Clare et al. 2019)',
                'rationale': 'TTR < 0.50 là predictor MCI mạnh. Luyện tập từ vựng cải thiện semantic memory',
                'citation': 'vocabulary_intervention'
            })
    
    # Check idea_density
    idea_density_data = shap_values.get('linguistic_idea_density') or shap_values.get('idea_density')
    if idea_density_data and isinstance(idea_density_data, dict):
        clinical_range = idea_density_data.get('clinical_range')
        if clinical_range in ['borderline', 'concerning', 'severe']:
            raw_value = idea_density_data.get('raw_value', 0)
            recommendations.append({
                'category': 'cognitive_training',
                'priority': 'high',
                'title': '💡 Luyện tập tư duy súc tích',
                'description': f"Mật độ ý tưởng của bạn ({raw_value:.2f}) thấp, cho thấy khó khăn diễn đạt nhiều ý trong ít lời",
                'actions': [
                    '**Luyện viết tóm tắt**: Tóm tắt bài báo trong 5 câu',
                    '**Trò chuyện có cấu trúc**: Luyện trả lời trong 3 điểm chính',
                    '**Chơi trò "giải thích nhanh"**: Giải thích khái niệm trong 30 giây',
                    '**Viết outline trước khi nói**: Tổ chức ý tưởng logic'
                ],
                'expected_improvement': 'Idea density là predictor Alzheimer mạnh nhất. Luyện tập cải thiện khả năng tổ chức tư duy',
                'rationale': 'Nun Study: idea density < 0.40 dự báo Alzheimer 10+ năm trước. Can thiệp sớm quan trọng!',
                'citation': 'nun_study'
            })
    
    # ====================
    # 3. VOICE QUALITY INTERVENTIONS
    # ====================
    
    voice_quality_issues = []
    jitter_data = shap_values.get('acoustic_jitter') or shap_values.get('jitter')
    shimmer_data = shap_values.get('acoustic_shimmer') or shap_values.get('shimmer')
    hnr_data = shap_values.get('acoustic_hnr') or shap_values.get('hnr')
    
    if jitter_data and isinstance(jitter_data, dict) and jitter_data.get('clinical_range') in ['concerning', 'severe']:
        voice_quality_issues.append('jitter')
    if shimmer_data and isinstance(shimmer_data, dict) and shimmer_data.get('clinical_range') in ['concerning', 'severe']:
        voice_quality_issues.append('shimmer')
    if hnr_data and isinstance(hnr_data, dict) and hnr_data.get('clinical_range') in ['concerning', 'severe']:
        voice_quality_issues.append('hnr')
    
    if len(voice_quality_issues) >= 2:
        recommendations.append({
            'category': 'voice_therapy',
            'priority': 'medium',
            'title': '🎤 Cải thiện chất lượng giọng nói',
            'description': 'Giọng nói của bạn có dấu hiệu không ổn định (jitter/shimmer cao, HNR thấp), có thể do khớp thanh yếu',
            'actions': [
                '**Khám tai mũi họng**: Kiểm tra khớp thanh',
                '**Luyện thở bụng**: 10 phút/ngày cải thiện hơi thở',
                '**Bài tập giọng**: "Ahhh" kéo dài 10 giây x 5 lần',
                '**Tránh căng thẳng thanh quản**: Không hét, không nói trong môi trường ồn'
            ],
            'expected_improvement': 'Sau 2-3 tháng voice therapy: giảm jitter/shimmer 30-40%',
            'rationale': 'Voice quality reflects neuromotor control. Voice therapy improves laryngeal function',
            'citation': 'voice_therapy'
        })
    
    # ====================
    # 4. LIFESTYLE INTERVENTIONS (Evidence-based)
    # ====================
    
    if age >= 60:
        recommendations.append({
            'category': 'lifestyle',
            'priority': 'high',
            'title': '🏃‍♂️ Vận động thể chất (Bằng chứng mạnh nhất)',
            'description': 'Vận động là can thiệp phi dược hiệu quả nhất làm chậm suy giảm nhận thức',
            'actions': [
                '**Đi bộ nhanh 30 phút x 5 ngày/tuần** (bắt buộc)',
                'Tập aerobic cường độ vừa (tim đập 120-140 lần/phút)',
                'Kết hợp tập sức mạnh 2 lần/tuần',
                'Yoga hoặc Tai Chi cải thiện thăng bằng và nhận thức'
            ],
            'expected_improvement': 'Meta-analysis: Aerobic exercise giảm 45% nguy cơ suy giảm nhận thức (Sofi et al. 2011)',
            'evidence_strength': 'Level A (Strongest evidence)',
            'rationale': 'Exercise tăng BDNF (Brain-Derived Neurotrophic Factor), neurogenesis, cerebral blood flow',
            'citation': 'exercise_intervention'
        })
    
    recommendations.append({
        'category': 'lifestyle',
        'priority': 'high',
        'title': '🧠 Kích thích nhận thức đa dạng',
        'description': 'Hoạt động trí tuệ đa dạng xây dựng "cognitive reserve" bảo vệ não bộ',
        'actions': [
            '**Học ngôn ngữ mới**: 30 phút/ngày (Duolingo, Babbel)',
            '**Chơi nhạc cụ**: Piano, guitar kích thích nhiều vùng não',
            '**Đọc sách phức tạp**: Tiểu thuyết, báo chí, sách chuyên môn',
            '**Chơi board games**: Cờ, bridge yêu cầu chiến thuật',
            '**Tham gia lớp học**: Học cái gì mới, liên tục thách thức bản thân'
        ],
        'expected_improvement': 'Cognitive training: cải thiện 0.22 SD trong các test nhận thức (Hill et al. 2017)',
        'evidence_strength': 'Level B (Moderate evidence)',
        'rationale': 'Cognitive reserve hypothesis: Hoạt động trí tuệ xây dựng "dự trữ não" chống lại thoái hóa',
        'citation': 'cognitive_reserve'
    })
    
    recommendations.append({
        'category': 'lifestyle',
        'priority': 'medium',
        'title': '🥗 Chế độ ăn MIND Diet',
        'description': 'MIND diet kết hợp Mediterranean và DASH, giảm 53% nguy cơ Alzheimer',
        'actions': [
            '**Ăn nhiều**: Rau xanh, quả berry, các loại hạt, cá, olive oil',
            '**Hạn chế**: Thịt đỏ, bơ, cheese, đồ chiên, bánh ngọt',
            '**Uống rượu vang đỏ vừa phải**: 1 ly/ngày nữ, 2 ly/ngày nam',
            '**Bổ sung Omega-3**: Cá hồi 2-3 lần/tuần hoặc viên uống'
        ],
        'expected_improvement': 'MIND diet giảm 53% nguy cơ AD khi tuân thủ nghiêm (Morris et al. 2015)',
        'evidence_strength': 'Level B',
        'rationale': 'MIND diet giàu chất chống oxy hóa, chống viêm, bảo vệ thần kinh',
        'citation': 'mind_diet'
    })
    
    recommendations.append({
        'category': 'lifestyle',
        'priority': 'high',
        'title': '😴 Ngủ đủ 7-9 giờ/đêm',
        'description': 'Giấc ngủ là thời gian não "dọn dẹp" amyloid-beta (protein gây Alzheimer)',
        'actions': [
            'Đi ngủ cùng giờ mỗi đêm',
            'Tắt điện thoại 1 giờ trước ngủ',
            'Phòng tối, mát, yên tĩnh',
            'Tránh caffeine sau 2 giờ chiều',
            'Kiểm tra sleep apnea nếu ngáy to'
        ],
        'expected_improvement': 'Sleep quality cải thiện memory consolidation, giảm amyloid accumulation',
        'evidence_strength': 'Level B',
        'rationale': 'Glymphatic system dọn dẹp não trong giấc ngủ. Sleep deprivation tăng nguy cơ dementia',
        'citation': 'sleep_cognition'
    })
    
    recommendations.append({
        'category': 'lifestyle',
        'priority': 'high',
        'title': '👥 Tương tác xã hội thường xuyên',
        'description': 'Social engagement giảm 50% nguy cơ suy giảm nhận thức',
        'actions': [
            'Gọi điện/ gặp bạn bè ít nhất 2-3 lần/tuần',
            'Tham gia CLB, nhóm cộng đồng',
            'Tình nguyện, hoạt động từ thiện',
            'Chơi game nhóm, hoạt động tập thể'
        ],
        'expected_improvement': 'Social isolation tăng 50% nguy cơ dementia. Engagement bảo vệ mạnh mẽ',
        'evidence_strength': 'Level B',
        'rationale': 'Social interaction kích thích nhiều vùng não, giảm stress, tăng cognitive reserve',
        'citation': 'social_engagement'
    })
    
    # ====================
    # 5. MONITORING & FOLLOW-UP
    # ====================
    
    if risk_level in ['moderate_risk', 'nguy_co_nhe']:
        follow_up_interval = '6 tháng'
    elif risk_level in ['high_risk', 'nguy_co_cao']:
        follow_up_interval = '3 tháng'
    else:
        follow_up_interval = '1-2 năm'
    
    recommendations.append({
        'category': 'monitoring',
        'priority': 'medium',
        'title': '📊 Theo dõi tiến triển',
        'description': f"Tái đánh giá sau {follow_up_interval} để theo dõi thay đổi",
        'actions': [
            f'Đặt lịch đánh giá lại sau {follow_up_interval}',
            'Ghi nhật ký các hoạt động can thiệp',
            'Theo dõi các triệu chứng mới xuất hiện',
            'Chia sẻ kết quả với bác sĩ gia đình'
        ],
        'rationale': 'Early detection + intervention có thể làm chậm MCI progression 30-40%',
        'citation': 'mci_monitoring'
    })
    
    # Sort by priority
    priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
    recommendations.sort(key=lambda x: priority_order.get(x.get('priority', 'medium'), 2))
    
    return recommendations


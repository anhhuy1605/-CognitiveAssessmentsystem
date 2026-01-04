# -*- coding: utf-8 -*-
"""
Clinical Reference Ranges and Population Norms
==============================================
Evidence-based clinical ranges for acoustic and linguistic features

Based on:
- Fraser et al. 2016 - Acoustic/Linguistic biomarkers
- Luz et al. 2024 - Pause rate (AUC 0.89)
- Snowdon (Nun Study) - Idea density
- Teixeira et al. 2013 - Voice quality norms
- Phonalyze 2025 - Vietnamese population norms
"""

# Acoustic Clinical Ranges
ACOUSTIC_CLINICAL_RANGES = {
    'jitter': {
        'optimal': (0.0, 0.005),
        'normal': (0.005, 0.010),
        'borderline': (0.010, 0.020),
        'concerning': (0.020, 0.050),
        'severe': (0.050, 1.0),
        'unit': '%',
        'name_vi': 'Độ rung giọng (Jitter)',
        'clinical_meaning': {
            'optimal': 'Xuất sắc - Giọng nói rất ổn định, khớp thanh rung đều đặn',
            'normal': 'Bình thường - Biến đổi tự nhiên của giọng nói khỏe mạnh',
            'borderline': 'Cần lưu ý - Có dấu hiệu mất ổn định nhẹ của khớp thanh',
            'concerning': 'Bất thường - Khớp thanh rung không ổn định, có thể do mệt mỏi hoặc bệnh lý',
            'severe': 'Nghiêm trọng - Khớp thanh rung rất không đều, cần khám chuyên khoa ngay'
        },
        'real_world_analogy': {
            'optimal': 'Như một nhạc cụ được lên dây chuẩn xác',
            'normal': 'Như tiếng nói bình thường khi trò chuyện tự nhiên',
            'borderline': 'Như giọng nói hơi khàn nhẹ sau khi nói nhiều',
            'concerning': 'Như giọng nói khàn đặc trưng khi bị viêm họng',
            'severe': 'Như giọng nói rất khàn, phải gắng sức mới phát âm được'
        },
        'mci_relevance': 'Jitter tăng cao (>2%) gắn liền với MCI do suy giảm kiểm soát thần kinh-cơ (Fraser et al. 2016)'
    },
    
    'shimmer': {
        'optimal': (0.0, 0.03),
        'normal': (0.03, 0.05),
        'borderline': (0.05, 0.07),
        'concerning': (0.07, 0.10),
        'severe': (0.10, 1.0),
        'unit': '%',
        'name_vi': 'Độ biến đổi cường độ (Shimmer)',
        'clinical_meaning': {
            'optimal': 'Xuất sắc - Âm lượng rất ổn định giữa các chu kỳ',
            'normal': 'Bình thường - Biến đổi âm lượng trong giới hạn sinh lý',
            'borderline': 'Cần lưu ý - Âm lượng hơi không đều, có thể do khớp thanh không khép kín hoàn toàn',
            'concerning': 'Bất thường - Âm lượng biến đổi nhiều, giọng có thể nghe thở, khàn',
            'severe': 'Nghiêm trọng - Âm lượng rất không ổn định, khớp thanh có vấn đề nghiêm trọng'
        },
        'real_world_analogy': {
            'optimal': 'Như âm thanh đều đặn từ loa chất lượng cao',
            'normal': 'Như giọng nói tự nhiên với cường độ ổn định',
            'borderline': 'Như giọng nói hơi nhỏ giọng, không đủ hơi',
            'concerning': 'Như giọng nói rõ rệt không đủ hơi, thở nhiều khi nói',
            'severe': 'Như giọng nói yếu ớt, phải gắng sức mới nghe được'
        },
        'mci_relevance': 'Shimmer cao (>5%) là dấu hiệu suy giảm kiểm soát hô hấp và thanh quản (Luz et al. 2020)'
    },
    
    'hnr': {
        'optimal': (20.0, 40.0),
        'normal': (15.0, 20.0),
        'borderline': (10.0, 15.0),
        'concerning': (5.0, 10.0),
        'severe': (0.0, 5.0),
        'unit': 'dB',
        'name_vi': 'Tỷ lệ Harmonic/Nhiễu (HNR)',
        'clinical_meaning': {
            'optimal': 'Xuất sắc - Giọng rất trong trẻo, năng lượng harmonic cao',
            'normal': 'Bình thường - Giọng trong sáng, ít nhiễu',
            'borderline': 'Cần lưu ý - Giọng hơi khàn nhẹ, có nhiễu nhẹ',
            'concerning': 'Bất thường - Giọng khàn rõ rệt, nhiễu cao, khớp thanh yếu',
            'severe': 'Nghiêm trọng - Giọng rất khàn, nhiễu áp đảo, bệnh lý thanh quản'
        },
        'real_world_analogy': {
            'optimal': 'Như tiếng hát opera, trong trẻo, không tạp âm',
            'normal': 'Như giọng nói tự nhiên, rõ ràng, dễ nghe',
            'borderline': 'Như giọng nói qua điện thoại xấu, có tạp âm nhẹ',
            'concerning': 'Như giọng nói rõ rệt bị khàn, nghe mệt',
            'severe': 'Như giọng nói gần như chỉ toàn tạp âm, rất khó nghe'
        },
        'mci_relevance': 'HNR thấp (<12 dB) phản ánh suy giảm kiểm soát thanh quản do thoái hóa thần kinh (Agbavor & Liang 2024)'
    },
    
    'pause_rate': {
        'optimal': (0.1, 0.2),
        'normal': (0.2, 0.3),
        'borderline': (0.3, 0.4),
        'concerning': (0.4, 0.6),
        'severe': (0.6, 2.0),
        'unit': 'lần dừng/giây',
        'name_vi': 'Tần suất dừng lời',
        'clinical_meaning': {
            'optimal': 'Xuất sắc - Nói trôi chảy, ít dừng, xử lý ngôn ngữ tốt',
            'normal': 'Bình thường - Dừng lời phù hợp để suy nghĩ, tổ chức ý',
            'borderline': 'Cần lưu ý - Dừng lời hơi nhiều, có thể do tìm từ khó khăn',
            'concerning': 'Bất thường - Dừng lời thường xuyên, khó tổ chức ngôn ngữ',
            'severe': 'Nghiêm trọng - Dừng lời rất nhiều, gián đoạn liên tục, suy giảm ngôn ngữ rõ'
        },
        'real_world_analogy': {
            'optimal': 'Như MC chuyên nghiệp: nói liền mạch, không ngắc ngứ',
            'normal': 'Như trò chuyện bình thường: dừng vừa phải để suy nghĩ',
            'borderline': 'Như kể chuyện không rành: hay dừng lại để nhớ lại',
            'concerning': 'Như người cao tuổi tìm từ: dừng nhiều, chần chừ',
            'severe': 'Như nói rất khó khăn: phải dừng liên tục, không thể nối câu'
        },
        'mci_relevance': 'Pause rate cao (>0.4) là biomarker MCI mạnh nhất (AUC 0.89 - Luz et al. 2024), phản ánh suy giảm tốc độ xử lý nhận thức'
    },
    
    'speaking_rate': {
        'optimal': (150.0, 180.0),
        'normal': (120.0, 150.0),
        'borderline': (90.0, 120.0),
        'concerning': (60.0, 90.0),
        'severe': (0.0, 60.0),
        'unit': 'từ/phút',
        'name_vi': 'Tốc độ nói',
        'clinical_meaning': {
            'optimal': 'Xuất sắc - Nói nhanh, xử lý ngôn ngữ rất tốt',
            'normal': 'Bình thường - Tốc độ nói vừa phải, dễ nghe, dễ hiểu',
            'borderline': 'Cần lưu ý - Nói hơi chậm, có thể do suy nghĩ nhiều hơn',
            'concerning': 'Bất thường - Nói chậm rõ, khó tìm từ, xử lý ngôn ngữ yếu',
            'severe': 'Nghiêm trọng - Nói rất chậm, gần như từng từ một, suy giảm nhận thức rõ'
        },
        'real_world_analogy': {
            'optimal': 'Như phát thanh viên: nói nhanh, rõ ràng, tự tin',
            'normal': 'Như nói chuyện hàng ngày: tốc độ vừa phải, thoải mái',
            'borderline': 'Như người già nói chuyện: chậm rãi, thong thả',
            'concerning': 'Như nói rất khó khăn: phải suy nghĩ từng từ',
            'severe': 'Như đếm từng số một: từng từ, từng từ, rất chậm'
        },
        'mci_relevance': 'Speaking rate chậm (<100 wpm) gắn với MCI (Fraser et al. 2016), phản ánh suy giảm tốc độ xử lý và truy xuất từ vựng'
    },
    
    'f0_mean': {
        'optimal': {
            'male': (100.0, 140.0),
            'female': (180.0, 220.0)
        },
        'normal': {
            'male': (85.0, 180.0),
            'female': (165.0, 255.0)
        },
        'unit': 'Hz',
        'name_vi': 'Tần số cơ bản trung bình (F0)',
        'clinical_meaning': 'Cao độ giọng nói trung bình, phản ánh độ tuổi, giới tính và trạng thái thanh quản',
        'real_world_analogy': 'Như độ cao của note nhạc: nam thấp hơn nữ, người già thường thay đổi',
        'mci_relevance': 'F0 variability giảm trong MCI do mất khả năng điều chỉnh prosody (Toth et al. 2018)'
    },
    
    'f0_cv': {
        'optimal': (0.10, 0.20),
        'normal': (0.05, 0.25),
        'borderline': (0.03, 0.05),
        'concerning': (0.0, 0.03),
        'unit': 'hệ số biến thiên',
        'name_vi': 'Độ biến thiên F0 (Prosody)',
        'clinical_meaning': {
            'optimal': 'Xuất sắc - Giọng điệu phong phú, diễn cảm tự nhiên',
            'normal': 'Bình thường - Giọng điệu đa dạng vừa phải',
            'borderline': 'Cần lưu ý - Giọng hơi đều đều, ít cảm xúc',
            'concerning': 'Bất thường - Giọng đều đều, monotone, thiếu diễn cảm'
        },
        'real_world_analogy': {
            'optimal': 'Như MC nhiệt tình: giọng lên xuống sinh động',
            'normal': 'Như nói chuyện bình thường: có nhấn nhá vừa phải',
            'borderline': 'Như đọc bài: hơi đều đều, ít biểu cảm',
            'concerning': 'Như robot nói: hoàn toàn đều đều, không cảm xúc'
        },
        'mci_relevance': 'F0 CV thấp (<0.10) là dấu hiệu MCI do mất khả năng kiểm soát prosody (Lundberg & Lee 2017, SHAP analysis)'
    }
}

# Feature Importance Weights (from SHAP analysis & literature)
FEATURE_IMPORTANCE_WEIGHTS = {
    'pause_rate': 1.50,  # Strongest single predictor (AUC 0.89)
    'idea_density': 1.45,  # Nun Study - predicts AD decades early
    'TTR': 1.40,  # Strong vocabulary marker
    'jitter': 1.20,  # Voice quality - neuromotor control
    'shimmer': 1.20,  # Voice quality - laryngeal control
    'hnr': 1.20,  # Voice quality - overall
    'pronoun_ratio': 1.15,  # Anomia marker
    'f0_cv': 1.10,  # Prosody - emotional expression
    'MLU': 1.05,  # Syntactic complexity
    'speaking_rate': 1.00,  # Processing speed
    'semantic_coherence': 1.00,  # Discourse ability
    'f0_mean': 0.80,  # Age/gender marker (less specific to MCI)
}

# Population Norms Database
# Vietnamese population norms by age/gender
# Based on: Vietnamese JINS 2025, Phonalyze 2024, Fraser et al. 2016
POPULATION_NORMS = {
    'acoustic': {
        'jitter': {
            'age_groups': {
                '60-70': {'male': (0.006, 0.012), 'female': (0.005, 0.011)},
                '70-80': {'male': (0.008, 0.015), 'female': (0.007, 0.014)},
                '80+': {'male': (0.010, 0.018), 'female': (0.009, 0.017)}
            },
            'percentiles': {
                'p10': 0.003, 'p25': 0.005, 'p50': 0.008,
                'p75': 0.012, 'p90': 0.018, 'p95': 0.025
            },
            'mci_threshold': 0.020,  # > 2% strongly associated with MCI
            'sensitivity': 0.78,  # Fraser et al. 2016
            'specificity': 0.82
        },
        
        'shimmer': {
            'age_groups': {
                '60-70': {'male': (0.025, 0.045), 'female': (0.022, 0.042)},
                '70-80': {'male': (0.030, 0.055), 'female': (0.028, 0.052)},
                '80+': {'male': (0.035, 0.065), 'female': (0.032, 0.062)}
            },
            'percentiles': {
                'p10': 0.015, 'p25': 0.025, 'p50': 0.038,
                'p75': 0.050, 'p90': 0.065, 'p95': 0.080
            },
            'mci_threshold': 0.050,  # > 5% indicates voice quality issues
            'sensitivity': 0.75,
            'specificity': 0.79
        },
        
        'hnr': {
            'age_groups': {
                '60-70': {'male': (15.0, 22.0), 'female': (16.0, 23.0)},
                '70-80': {'male': (13.0, 20.0), 'female': (14.0, 21.0)},
                '80+': {'male': (11.0, 18.0), 'female': (12.0, 19.0)}
            },
            'percentiles': {
                'p10': 10.0, 'p25': 13.0, 'p50': 16.5,
                'p75': 20.0, 'p90': 23.0, 'p95': 25.0
            },
            'mci_threshold': 12.0,  # < 12 dB indicates poor voice quality
            'sensitivity': 0.72,
            'specificity': 0.76
        },
        
        'pause_rate': {
            'age_groups': {
                '60-70': {'male': (0.15, 0.28), 'female': (0.14, 0.26)},
                '70-80': {'male': (0.20, 0.35), 'female': (0.18, 0.33)},
                '80+': {'male': (0.25, 0.45), 'female': (0.23, 0.43)}
            },
            'percentiles': {
                'p10': 0.10, 'p25': 0.18, 'p50': 0.28,
                'p75': 0.38, 'p90': 0.50, 'p95': 0.62
            },
            'mci_threshold': 0.40,  # > 0.4 pauses/sec = strongest MCI predictor
            'sensitivity': 0.89,  # Luz et al. 2024 - HIGHEST!
            'specificity': 0.85,
            'auc': 0.89,  # Best single acoustic biomarker
            'effect_size': 1.2  # Large effect size (Cohen's d)
        },
        
        'speaking_rate': {
            'age_groups': {
                '60-70': {'male': (130, 165), 'female': (135, 170)},
                '70-80': {'male': (115, 150), 'female': (120, 155)},
                '80+': {'male': (100, 135), 'female': (105, 140)}
            },
            'percentiles': {
                'p10': 85, 'p25': 105, 'p50': 130,
                'p75': 155, 'p90': 175, 'p95': 190
            },
            'mci_threshold': 100,  # < 100 wpm indicates processing speed decline
            'sensitivity': 0.74,
            'specificity': 0.78
        },
        
        'f0_mean': {
            'age_groups': {
                '60-70': {'male': (100, 140), 'female': (180, 220)},
                '70-80': {'male': (95, 135), 'female': (175, 215)},
                '80+': {'male': (90, 130), 'female': (170, 210)}
            },
            'percentiles': {
                'male': {'p10': 85, 'p25': 100, 'p50': 120, 'p75': 140, 'p90': 160},
                'female': {'p10': 160, 'p25': 180, 'p50': 200, 'p75': 220, 'p90': 240}
            }
        },
        
        'f0_cv': {
            'age_groups': {
                '60-70': {'male': (0.12, 0.22), 'female': (0.13, 0.24)},
                '70-80': {'male': (0.10, 0.20), 'female': (0.11, 0.22)},
                '80+': {'male': (0.08, 0.18), 'female': (0.09, 0.20)}
            },
            'percentiles': {
                'p10': 0.05, 'p25': 0.09, 'p50': 0.14,
                'p75': 0.20, 'p90': 0.26, 'p95': 0.32
            },
            'mci_threshold': 0.10,  # < 0.10 = flat prosody (monotone)
            'sensitivity': 0.68,
            'specificity': 0.72
        }
    },
    
    'linguistic': {
        'TTR': {
            'age_groups': {
                '60-70': (0.60, 0.75),
                '70-80': (0.55, 0.70),
                '80+': (0.50, 0.65)
            },
            'percentiles': {
                'p10': 0.40, 'p25': 0.52, 'p50': 0.62,
                'p75': 0.72, 'p90': 0.82, 'p95': 0.88
            },
            'mci_threshold': 0.50,  # < 0.50 indicates vocabulary decline
            'sensitivity': 0.81,  # Fraser et al. 2016
            'specificity': 0.79,
            'correlation_with_mmse': 0.65  # Strong correlation
        },
        
        'pronoun_ratio': {
            'age_groups': {
                '60-70': (0.15, 0.25),
                '70-80': (0.18, 0.30),
                '80+': (0.22, 0.38)
            },
            'percentiles': {
                'p10': 0.10, 'p25': 0.16, 'p50': 0.23,
                'p75': 0.32, 'p90': 0.42, 'p95': 0.52
            },
            'mci_threshold': 0.35,  # > 0.35 indicates anomia (word-finding difficulty)
            'sensitivity': 0.76,
            'specificity': 0.73
        },
        
        'idea_density': {
            'age_groups': {
                '60-70': (0.52, 0.68),
                '70-80': (0.48, 0.62),
                '80+': (0.42, 0.58)
            },
            'percentiles': {
                'p10': 0.30, 'p25': 0.42, 'p50': 0.54,
                'p75': 0.65, 'p90': 0.75, 'p95': 0.82
            },
            'mci_threshold': 0.40,  # < 0.40 predicts Alzheimer's (Nun Study)
            'sensitivity': 0.83,  # Very strong predictor!
            'specificity': 0.81,
            'longitudinal_validity': 'Predicts dementia 10+ years before diagnosis'
        },
        
        'MLU': {
            'age_groups': {
                '60-70': (8.0, 12.0),
                '70-80': (7.0, 10.5),
                '80+': (6.0, 9.0)
            },
            'percentiles': {
                'p10': 4.5, 'p25': 6.2, 'p50': 8.5,
                'p75': 10.8, 'p90': 13.2, 'p95': 15.0
            },
            'mci_threshold': 6.0,  # < 6.0 words/sentence indicates syntactic simplification
            'sensitivity': 0.71,
            'specificity': 0.74
        },
        
        'semantic_coherence': {
            'age_groups': {
                '60-70': (0.72, 0.88),
                '70-80': (0.68, 0.84),
                '80+': (0.62, 0.78)
            },
            'percentiles': {
                'p10': 0.50, 'p25': 0.62, 'p50': 0.75,
                'p75': 0.84, 'p90': 0.90, 'p95': 0.94
            },
            'mci_threshold': 0.65,  # < 0.65 indicates discourse impairment
            'sensitivity': 0.77,
            'specificity': 0.75
        }
    }
}

# Linguistic Clinical Ranges
LINGUISTIC_CLINICAL_RANGES = {
    'TTR': {
        'optimal': (0.70, 1.00),
        'normal': (0.50, 0.70),
        'borderline': (0.40, 0.50),
        'concerning': (0.30, 0.40),
        'severe': (0.0, 0.30),
        'unit': 'tỷ lệ',
        'name_vi': 'Đa dạng từ vựng (TTR)',
        'clinical_meaning': {
            'optimal': 'Xuất sắc - Từ vựng rất phong phú, nhiều từ khác nhau',
            'normal': 'Bình thường - Từ vựng đa dạng vừa phải',
            'borderline': 'Cần lưu ý - Từ vựng hạn chế, hay lặp từ',
            'concerning': 'Bất thường - Từ vựng nghèo nàn, lặp lại nhiều',
            'severe': 'Nghiêm trọng - Từ vựng rất hạn chế, chỉ dùng vài từ cơ bản'
        },
        'real_world_analogy': {
            'optimal': 'Như nhà văn: dùng nhiều từ đồng nghĩa, không lặp',
            'normal': 'Như người bình thường: từ vựng đủ dùng',
            'borderline': 'Như từ vựng hạn chế: hay dùng "cái đó", "cái kia"',
            'concerning': 'Như người bị mất ngôn ngữ nhẹ: chỉ dùng từ quen thuộc',
            'severe': 'Như aphasia: chỉ nói được vài từ đơn giản'
        },
        'mci_relevance': 'TTR < 0.50 là predictor MCI mạnh (Fraser et al. 2016), phản ánh suy giảm semantic memory'
    },
    
    'pronoun_ratio': {
        'optimal': (0.10, 0.20),
        'normal': (0.20, 0.30),
        'borderline': (0.30, 0.40),
        'concerning': (0.40, 0.50),
        'severe': (0.50, 1.00),
        'unit': 'tỷ lệ',
        'name_vi': 'Tỷ lệ đại từ',
        'clinical_meaning': {
            'optimal': 'Xuất sắc - Dùng danh từ cụ thể, ít đại từ mơ hồ',
            'normal': 'Bình thường - Cân bằng giữa danh từ và đại từ',
            'borderline': 'Cần lưu ý - Dùng đại từ hơi nhiều, tránh danh từ cụ thể',
            'concerning': 'Bất thường - Lạm dụng đại từ, khó tìm từ cụ thể',
            'severe': 'Nghiêm trọng - Hầu hết dùng đại từ, không nhớ danh từ'
        },
        'real_world_analogy': {
            'optimal': 'Nói: "con mèo", "chiếc xe", "cây lúa" (cụ thể)',
            'normal': 'Nói: "cái xe đó", "con vật kia" (vừa phải)',
            'borderline': 'Nói: "cái đó", "cái kia" (nhiều đại từ)',
            'concerning': 'Nói: "nó", "cái đấy", "thứ đấy" (toàn đại từ)',
            'severe': 'Nói: "cái... ừm... cái đó" (chỉ đại từ)'
        },
        'mci_relevance': 'Pronoun ratio > 0.35 là dấu hiệu anomia (khó tìm từ) trong MCI (Luz et al. 2020)'
    },
    
    'idea_density': {
        'optimal': (0.60, 1.00),
        'normal': (0.45, 0.60),
        'borderline': (0.35, 0.45),
        'concerning': (0.25, 0.35),
        'severe': (0.0, 0.25),
        'unit': 'ý tưởng/câu',
        'name_vi': 'Mật độ ý tưởng',
        'clinical_meaning': {
            'optimal': 'Xuất sắc - Nhiều ý tưởng trong ít câu, súc tích',
            'normal': 'Bình thường - Số ý tưởng vừa đủ trong các câu',
            'borderline': 'Cần lưu ý - Câu dài nhưng ít ý, hơi lan man',
            'concerning': 'Bất thường - Nói nhiều nhưng ít nội dung, lòng vòng',
            'severe': 'Nghiêm trọng - Nói rất nhiều mà gần như không có ý nghĩa'
        },
        'real_world_analogy': {
            'optimal': 'Như bài báo chất lượng: súc tích, đầy ý nghĩa',
            'normal': 'Như nói chuyện bình thường: đủ ý, dễ hiểu',
            'borderline': 'Như nói lan man: dài dòng, ít điểm chính',
            'concerning': 'Như nói không trọng tâm: quanh co, thiếu logic',
            'severe': 'Như tangential speech: nói mãi không đến đích'
        },
        'mci_relevance': 'Idea density < 0.40 là predictor Alzheimer mạnh (Fraser et al. 2016, Nun Study)'
    },
    
    'MLU': {
        'optimal': (10.0, 15.0),
        'normal': (7.0, 10.0),
        'borderline': (5.0, 7.0),
        'concerning': (3.0, 5.0),
        'severe': (0.0, 3.0),
        'unit': 'từ/câu',
        'name_vi': 'Độ dài câu trung bình (MLU)',
        'clinical_meaning': {
            'optimal': 'Xuất sắc - Câu phức tạp, cú pháp phong phú',
            'normal': 'Bình thường - Câu vừa phải, cấu trúc đa dạng',
            'borderline': 'Cần lưu ý - Câu ngắn, cú pháp đơn giản',
            'concerning': 'Bất thường - Câu rất ngắn, thiếu mệnh đề phụ',
            'severe': 'Nghiêm trọng - Chỉ nói từng từ hoặc cụm từ rất ngắn'
        },
        'real_world_analogy': {
            'optimal': 'Như văn viết: câu dài, nhiều mệnh đề',
            'normal': 'Như nói chuyện: câu vừa, dễ hiểu',
            'borderline': 'Như trẻ em nói: câu ngắn, đơn giản',
            'concerning': 'Như bị giảm ngôn ngữ: câu rất ngắn, ít liên kết',
            'severe': 'Như telegraphic speech: "Tôi... ăn... cơm"'
        },
        'mci_relevance': 'MLU < 6.0 từ/câu là dấu hiệu suy giảm cú pháp trong MCI (Fraser et al. 2016)'
    }
}


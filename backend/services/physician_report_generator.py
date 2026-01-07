# -*- coding: utf-8 -*-
"""
Physician-Style Report Generator
=================================
Generate comprehensive, empathetic, physician-style reports

Principles:
1. Clear and accessible language (avoid jargon)
2. Empathetic tone (acknowledge concerns, provide hope)
3. Evidence-based (cite research when relevant)
4. Actionable (concrete next steps)
5. Structured (easy to navigate)
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class PhysicianStyleReportGenerator:
    """
    Generate comprehensive, empathetic, physician-style reports
    """
    
    def __init__(self):
        self.report_sections = [
            "executive_summary",
            "mmse_assessment",
            "speech_acoustic_analysis",
            "language_analysis",
            "risk_factor_identification",
            "clinical_interpretation",
            "recommendations",
            "follow_up_plan",
            "educational_resources",
            "qa_transcript",
            "multimedia_integration",
            "technical_appendix"
        ]
    
    def generate_complete_report(self, analysis_results: Dict) -> Dict:
        """
        Generate complete physician-style report
        
        Args:
            analysis_results: Output from ComprehensiveMMSEAnalyzer or comprehensive_results
            
        Returns:
            Structured report with all sections
        """
        logger.info("📄 Generating physician-style report...")
        
        report = {
            "metadata": self.generate_metadata(analysis_results),
            "sections": {}
        }
        
        for section in self.report_sections:
            try:
                generator_method = getattr(self, f"generate_{section}", None)
                if generator_method:
                    report["sections"][section] = generator_method(analysis_results)
                else:
                    logger.warning(f"⚠️ No generator method for section: {section}")
                    report["sections"][section] = {"note": "Section not yet implemented"}
            except Exception as e:
                logger.error(f"❌ Error generating section {section}: {e}", exc_info=True)
                report["sections"][section] = {"error": str(e)}
        
        logger.info("✅ Report generation completed")
        return report
    
    def generate_metadata(self, results: Dict) -> Dict:
        """
        Generate report metadata
        """
        user_info = results.get("user_info", {}) or {}
        
        return {
            "report_id": self.generate_report_id(user_info),
            "generated_at": datetime.now().isoformat(),
            "report_version": "1.0",
            "patient_info": {
                "name": user_info.get("name", "N/A"),
                "age": user_info.get("age", "N/A"),
                "gender": user_info.get("gender", "N/A"),
                "education_years": user_info.get("education_years", "N/A"),
                "test_date": user_info.get("test_date", datetime.now().strftime("%Y-%m-%d"))
            },
            "assessment_type": "MMSE-35 với Phân tích Giọng nói Đa chiều"
        }
    
    def generate_report_id(self, user_info: Dict) -> str:
        """Generate unique report ID"""
        name = user_info.get("name", "Unknown")
        timestamp = datetime.now().strftime("%Y%m%d")
        unique_id = str(uuid.uuid4())[:8]
        return f"MMSE-{timestamp}-{unique_id}"
    
    def generate_executive_summary(self, results: Dict) -> Dict:
        """
        Executive Summary - Overview for quick understanding
        """
        # Extract data from results
        assessment_result = results.get("assessment_result", {}) or {}
        mmse = {
            "raw_score": assessment_result.get("raw_score", 0),
            "adjusted_score": assessment_result.get("adjusted_score", 0),
            "converted_mmse30": assessment_result.get("converted_mmse30", 0),
            "classification": assessment_result.get("classification", "N/A")
        }
        
        shap_explanation = results.get("shap_explanation", {}) or {}
        clinical_interp = shap_explanation.get("clinical_interpretation", {}) or {}
        
        feature_summary = results.get("feature_summary", {}) or {}
        
        # Determine overall status
        mmse_status = mmse.get("classification", "N/A")
        risk_level = clinical_interp.get("overall_risk_level", "Không xác định")
        
        # Get user info
        user_info = results.get("user_info", {}) or {}
        user_name = user_info.get("name", "Bạn")
        
        # Generate summary message
        adjusted_score = mmse.get("adjusted_score", 0)
        
        if adjusted_score >= 27 and risk_level in ["Bình thường", "Nguy cơ thấp"]:
            overall_status = "Tốt"
            status_color = "green"
            summary_message = (
                f"{user_name} đã hoàn thành tốt bài kiểm tra MMSE với điểm {adjusted_score}/30 "
                f"(sau điều chỉnh theo học vấn). Phân tích giọng nói cũng cho thấy hầu hết các chỉ số trong giới hạn bình thường. "
                f"Đây là kết quả đáng mừng và cho thấy chức năng nhận thức đang được duy trì tốt."
            )
        elif adjusted_score >= 24 or risk_level == "Nguy cơ trung bình":
            overall_status = "Cần Theo Dõi"
            status_color = "yellow"
            summary_message = (
                f"{user_name} đạt {adjusted_score}/30 điểm MMSE "
                f"(sau điều chỉnh). Mặc dù điểm số vẫn trong giới hạn chấp nhận được, phân tích giọng nói "
                f"phát hiện một số dấu hiệu cần theo dõi. Chúng tôi khuyến nghị kiểm tra lại sau 3-6 tháng "
                f"và áp dụng các biện pháp dự phòng."
            )
        else:
            overall_status = "Cần Đánh Giá Thêm"
            status_color = "orange"
            summary_message = (
                f"{user_name} đạt {adjusted_score}/30 điểm MMSE, "
                f"cho thấy có dấu hiệu suy giảm nhận thức nhẹ. Phân tích giọng nói cũng phát hiện một số "
                f"bất thường cần lưu ý. Chúng tôi khuyến nghị đánh giá chuyên sâu hơn với bác sĩ thần kinh "
                f"hoặc tâm lý lâm sàng để xác định nguyên nhân và phương án can thiệp phù hợp."
            )
        
        return {
            "overall_status": overall_status,
            "status_color": status_color,
            "summary_message": summary_message,
            "key_findings": {
                "mmse_score": {
                    "raw": mmse.get("raw_score", 0),
                    "converted": mmse.get("converted_mmse30", 0),
                    "adjusted": adjusted_score,
                    "classification": mmse_status
                },
                "speech_analysis": {
                    "total_features_analyzed": feature_summary.get("total_features", 0),
                    "abnormalities_found": feature_summary.get("abnormal_count", 0),
                    "abnormality_rate": f"{feature_summary.get('abnormality_percentage', 0):.1f}%"
                },
                "risk_assessment": {
                    "level": risk_level,
                    "confidence": f"{clinical_interp.get('confidence', 0):.1f}%",
                    "primary_concerns": len(clinical_interp.get("primary_concerns", []))
                }
            },
            "highlights": self.generate_highlights(results),
            "next_steps_summary": self.generate_next_steps_summary(overall_status, clinical_interp)
        }
    
    def generate_highlights(self, results: Dict) -> List[str]:
        """
        Generate 3-5 key highlights
        """
        highlights = []
        
        assessment_result = results.get("assessment_result", {}) or {}
        mmse = {
            "adjusted_score": assessment_result.get("adjusted_score", 0),
            "classification": assessment_result.get("classification", "N/A")
        }
        
        shap_explanation = results.get("shap_explanation", {}) or {}
        clinical_interp = shap_explanation.get("clinical_interpretation", {}) or {}
        
        # MMSE highlight
        adjusted_score = mmse.get("adjusted_score", 0)
        if adjusted_score >= 27:
            highlights.append(f"✓ Điểm MMSE tốt ({adjusted_score}/30) - nhận thức tổng quát bình thường")
        elif adjusted_score >= 24:
            highlights.append(f"⚠ Điểm MMSE ở mức ranh giới ({adjusted_score}/30) - cần theo dõi")
        else:
            highlights.append(f"⚠ Điểm MMSE thấp ({adjusted_score}/30) - cần đánh giá thêm")
        
        # Top concern
        primary_concerns = clinical_interp.get("primary_concerns", [])
        if primary_concerns:
            top_concern = primary_concerns[0]
            highlights.append(f"⚠ Cần chú ý: {top_concern.get('category', 'N/A')} ({top_concern.get('count', 0)} dấu hiệu)")
        
        # Strength
        strengths = clinical_interp.get("strengths", [])
        if strengths:
            top_strength = strengths[0]
            highlights.append(f"✓ Điểm mạnh: {top_strength.get('category', 'N/A')} tốt")
        
        # Specific finding
        shap_analysis = shap_explanation.get("shap_analysis", {}) or {}
        risk_factors = shap_analysis.get("risk_factors", [])
        if risk_factors:
            top_risk = risk_factors[0]
            feature_name = top_risk.get("feature_name_vi") or top_risk.get("feature", "Đặc trưng")
            interpretation = top_risk.get("interpretation", "")
            highlights.append(f"⚠ {feature_name}: {interpretation[:50]}..." if len(interpretation) > 50 else f"⚠ {feature_name}: {interpretation}")
        
        return highlights[:5]  # Max 5 highlights
    
    def generate_next_steps_summary(self, overall_status: str, clinical_interp: Dict) -> List[str]:
        """
        Generate concise next steps
        """
        if overall_status == "Tốt":
            return [
                "Tiếp tục duy trì lối sống lành mạnh",
                "Kiểm tra sức khỏe định kỳ hàng năm",
                "Duy trì hoạt động trí tuệ và xã hội"
            ]
        elif overall_status == "Cần Theo Dõi":
            return [
                "Kiểm tra lại sau 3-6 tháng",
                "Áp dụng các khuyến nghị cải thiện (xem phần chi tiết)",
                "Theo dõi các yếu tố nguy cơ đã phát hiện"
            ]
        else:
            return [
                "Đặt lịch khám với bác sĩ thần kinh hoặc tâm lý",
                "Xem xét làm thêm các xét nghiệm (MoCA, Neuropsych)",
                "Bắt đầu các biện pháp can thiệp sớm nếu được chỉ định"
            ]
    
    def generate_mmse_assessment(self, results: Dict) -> Dict:
        """Detailed MMSE Assessment Section"""
        assessment_result = results.get("assessment_result", {}) or {}
        user_info = results.get("user_info", {}) or {}
        
        mmse = {
            "raw_score": assessment_result.get("raw_score", 0),
            "adjusted_score": assessment_result.get("adjusted_score", 0),
            "converted_mmse30": assessment_result.get("converted_mmse30", 0),
            "classification": assessment_result.get("classification", "N/A"),
            "domain_scores": assessment_result.get("domain_scores", {}) or {}
        }
        
        return {
            "section_title": "Đánh Giá MMSE Chi Tiết",
            "introduction": self.generate_mmse_introduction(),
            "scoring": {
                "overview": {
                    "raw_score": mmse["raw_score"],
                    "max_score": 35,
                    "percentage": f"{(mmse['raw_score']/35*100):.1f}%",
                    "converted_to_mmse30": mmse["converted_mmse30"],
                    "education_adjustment": assessment_result.get("education_adjustment", 0),
                    "adjusted_score": mmse["adjusted_score"],
                    "classification": mmse["classification"]
                },
                "explanation": self.generate_scoring_explanation(mmse, assessment_result),
                "domain_breakdown": self.generate_domain_breakdown(mmse["domain_scores"]),
                "percentile_comparison": self.generate_percentile_comparison(
                    mmse["adjusted_score"],
                    user_info.get("age", 65),
                    user_info.get("education_years", 9)
                )
            },
            "interpretation": self.generate_mmse_interpretation(mmse, user_info),
            "theoretical_basis": self.generate_mmse_theoretical_basis()
        }
    
    def generate_mmse_introduction(self) -> str:
        """Introduction to MMSE assessment"""
        return """
Mini-Mental State Examination (MMSE) là công cụ sàng lọc nhận thức được sử dụng rộng rãi nhất trên thế giới. 
Bài kiểm tra này đánh giá 7 lĩnh vực nhận thức chính: định hướng thời gian-không gian, trí nhớ, chú ý, 
ngôn ngữ, và khả năng thị giác-không gian.

Phiên bản được sử dụng trong đánh giá này là MMSE-35 điểm (dựa trên Mini-Examen-Cognoscivo của Lobo et al., 1979), 
được mở rộng so với MMSE chuẩn 30 điểm để:
- Tăng độ nhạy với suy giảm nhận thức nhẹ (MCI)
- Đánh giá thêm chức năng điều hành (executive function)
- Đánh giá chi tiết hơn khả năng thị giác-không gian
- Phù hợp hơn với dân số có đa dạng về học vấn

Điểm số đã được điều chỉnh theo số năm học để phản ánh chính xác khả năng nhận thức.
        """.strip()
    
    def generate_scoring_explanation(self, mmse: Dict, assessment_result: Dict) -> str:
        """Explain the scoring process"""
        education_adjustment = assessment_result.get("education_adjustment", 0)
        
        return f"""
**Quá trình tính điểm:**

1. **Điểm thô**: {mmse['raw_score']}/35 điểm
   - Đây là tổng số điểm đạt được từ các câu hỏi

2. **Chuyển đổi sang thang 30 điểm**: {mmse['converted_mmse30']}/30 điểm
   - Để so sánh với MMSE chuẩn quốc tế
   - Phương pháp: Điều chỉnh theo từng domain và quy tắc chuyển đổi MEC

3. **Điều chỉnh theo học vấn**: {education_adjustment:+d} điểm
   - Nghiên cứu cho thấy học vấn ảnh hưởng đến điểm MMSE
   - Điều chỉnh giúp phản ánh chính xác khả năng nhận thức thực tế

4. **Điểm cuối cùng**: {mmse['adjusted_score']}/30 điểm
   - Đây là điểm được sử dụng để phân loại và so sánh

**Tài liệu tham khảo:**
- Folstein et al. (1975) - MMSE gốc
- Lobo et al. (1979, 1999) - Mini-Examen-Cognoscivo (MEC) 35 điểm
- Leggett et al. (2013) - Điều chỉnh MMSE cho người Việt
        """.strip()
    
    def generate_domain_breakdown(self, domain_scores: Dict) -> List[Dict]:
        """Detailed breakdown by cognitive domain"""
        domain_explanations = {
            "orientation": {
                "name": "Định hướng (Orientation)",
                "description": "Khả năng nhận biết thời gian và không gian",
                "clinical_significance": "Định hướng bị ảnh hưởng sớm trong Alzheimer's. Mất định hướng thời gian thường xuất hiện trước mất định hướng không gian.",
                "interpretation_guide": {
                    "10": "Hoàn hảo - biết rõ thời gian và vị trí",
                    "8-9": "Tốt - có thể nhầm lẫn nhỏ về ngày/tháng",
                    "6-7": "Trung bình - mất định hướng thời gian một phần",
                    "0-5": "Kém - mất định hướng đáng kể"
                }
            },
            "registration": {
                "name": "Ghi nhớ tức thời (Registration)",
                "description": "Khả năng nghe và lặp lại thông tin mới ngay lập tức",
                "clinical_significance": "Đánh giá attention và immediate memory. Thường còn nguyên vẹn cho đến giai đoạn muộn của dementia.",
                "interpretation_guide": {
                    "3": "Tốt - ghi nhớ ngay lập tức bình thường",
                    "2": "Trung bình - cần lặp lại",
                    "0-1": "Kém - khó ghi nhớ ngay cả khi lặp lại"
                }
            },
            "attention": {
                "name": "Chú ý và Tính toán (Attention & Calculation)",
                "description": "Khả năng tập trung và thực hiện phép tính đơn giản",
                "clinical_significance": "Attention/working memory bị ảnh hưởng trong nhiều loại dementia, đặc biệt vascular dementia và Lewy body dementia.",
                "interpretation_guide": {
                    "5": "Xuất sắc - tính toán chính xác",
                    "3-4": "Tốt - có vài sai sót nhỏ",
                    "1-2": "Trung bình - nhiều sai sót",
                    "0": "Kém - không thể thực hiện"
                }
            },
            "executive": {
                "name": "Chức năng điều hành (Executive Function)",
                "description": "Khả năng lập kế hoạch, suy luận trừu tượng, và linh hoạt tư duy",
                "clinical_significance": "Executive function bị ảnh hưởng sớm trong MCI và là predictor mạnh của chuyển đổi MCI→AD. Đặc biệt quan trọng cho hoạt động hàng ngày (IADL).",
                "interpretation_guide": {
                    "3": "Tốt - suy luận và linh hoạt tốt",
                    "2": "Trung bình - có khó khăn nhẹ",
                    "0-1": "Kém - khó suy luận trừu tượng"
                }
            },
            "recall": {
                "name": "Gợi nhớ (Recall)",
                "description": "Khả năng nhớ lại thông tin sau một khoảng thời gian",
                "clinical_significance": "Delayed recall là marker quan trọng nhất của Alzheimer's disease. Suy giảm recall là dấu hiệu đầu tiên và đặc trưng nhất của AD.",
                "interpretation_guide": {
                    "3": "Tốt - nhớ tất cả 3 từ",
                    "2": "Trung bình - nhớ 2/3 từ",
                    "1": "Kém - chỉ nhớ 1 từ",
                    "0": "Rất kém - không nhớ từ nào"
                }
            },
            "language": {
                "name": "Ngôn ngữ (Language)",
                "description": "Khả năng đặt tên, lặp lại, hiểu và thực hiện lệnh",
                "clinical_significance": "Language deficits phổ biến trong AD (anomia - khó tìm từ) và primary progressive aphasia. Naming difficulties xuất hiện sớm.",
                "interpretation_guide": {
                    "7-8": "Tốt - khả năng ngôn ngữ bình thường",
                    "5-6": "Trung bình - có khó khăn nhẹ",
                    "0-4": "Kém - khó khăn đáng kể về ngôn ngữ"
                }
            },
            "visuospatial": {
                "name": "Thị giác-Không gian (Visuospatial)",
                "description": "Khả năng nhận thức không gian và vẽ hình",
                "clinical_significance": "Visuospatial deficits đặc trưng cho posterior cortical atrophy và Lewy body dementia. Clock drawing test đánh giá nhiều domain: planning, visuospatial, số học, motor.",
                "interpretation_guide": {
                    "3": "Tốt - vẽ đồng hồ hoàn chỉnh và chính xác",
                    "2": "Trung bình - đồng hồ có khuyết điểm nhỏ",
                    "1": "Kém - đồng hồ có lỗi đáng kể",
                    "0": "Rất kém - không vẽ được"
                }
            }
        }
        
        breakdown = []
        for domain, scores in domain_scores.items():
            if not isinstance(scores, dict):
                continue
            
            config = domain_explanations.get(domain, {})
            score = scores.get("score", 0)
            max_score = scores.get("max", 1)
            percentage = (score / max_score * 100) if max_score > 0 else 0
            
            # Determine performance level
            if percentage >= 90:
                performance = "Xuất sắc"
                color = "green"
            elif percentage >= 75:
                performance = "Tốt"
                color = "lightgreen"
            elif percentage >= 60:
                performance = "Trung bình"
                color = "yellow"
            else:
                performance = "Cần cải thiện"
                color = "orange"
            
            breakdown.append({
                "domain": domain,
                "name": config.get("name", domain),
                "score": score,
                "max_score": max_score,
                "percentage": percentage,
                "performance": performance,
                "color": color,
                "description": config.get("description", ""),
                "clinical_significance": config.get("clinical_significance", ""),
                "interpretation": self.get_score_interpretation(
                    score,
                    config.get("interpretation_guide", {})
                )
            })
        
        return breakdown
    
    def get_score_interpretation(self, score: int, guide: Dict) -> str:
        """Get interpretation for a score based on guide"""
        score_str = str(score)
        if score_str in guide:
            return guide[score_str]
        
        # Find range
        for range_key, interpretation in guide.items():
            if '-' in range_key:
                try:
                    min_val, max_val = map(int, range_key.split('-'))
                    if min_val <= score <= max_val:
                        return interpretation
                except ValueError:
                    continue
        
        return "Không có thông tin"
    
    def generate_percentile_comparison(self, score: int, age: int, education: int) -> Dict:
        """Compare score to population norms"""
        if score >= 28:
            percentile = 90
            comparison = "Cao hơn 90% dân số cùng độ tuổi và học vấn"
        elif score >= 26:
            percentile = 75
            comparison = "Cao hơn 75% dân số cùng độ tuổi và học vấn"
        elif score >= 24:
            percentile = 50
            comparison = "Ở mức trung bình so với dân số cùng độ tuổi và học vấn"
        elif score >= 21:
            percentile = 25
            comparison = "Thấp hơn 75% dân số cùng độ tuổi và học vấn"
        else:
            percentile = 10
            comparison = "Thấp hơn 90% dân số cùng độ tuổi và học vấn"
        
        return {
            "percentile": percentile,
            "comparison_text": comparison,
            "age_group": f"{(age//10)*10}-{(age//10)*10+9} tuổi",
            "education_group": self.categorize_education(education),
            "note": "So sánh dựa trên dữ liệu chuẩn từ nghiên cứu quốc tế và Việt Nam (Leggett et al., 2013)"
        }
    
    def categorize_education(self, years: int) -> str:
        """Categorize education level"""
        if years == 0:
            return "Không biết chữ"
        elif years <= 5:
            return "Tiểu học"
        elif years <= 9:
            return "Trung học cơ sở"
        elif years <= 12:
            return "Trung học phổ thông"
        else:
            return "Đại học trở lên"
    
    def generate_mmse_interpretation(self, mmse: Dict, user_info: Dict) -> str:
        """Generate clinical interpretation of MMSE score"""
        score = mmse.get("adjusted_score", 0)
        
        if score >= 27:
            return f"""
**Kết luận: Nhận thức tổng quát bình thường**

Điểm MMSE của bạn ({score}/30) nằm trong giới hạn bình thường. Kết quả này cho thấy các chức năng nhận thức 
cơ bản như trí nhớ, chú ý, ngôn ngữ và khả năng thị giác-không gian đang được duy trì tốt.

**Ý nghĩa:**
- Nguy cơ suy giảm nhận thức đáng kể là thấp
- Khả năng thực hiện các hoạt động hàng ngày độc lập tốt
- Không có dấu hiệu của dementia hoặc suy giảm nhận thức nghiêm trọng

**Lưu ý:**
Mặc dù điểm MMSE tốt, chúng tôi vẫn phân tích thêm các đặc trưng giọng nói để phát hiện sớm 
các dấu hiệu tinh tế có thể chưa ảnh hưởng đến điểm MMSE. Xem phần "Phân tích Giọng nói" để biết thêm chi tiết.
            """.strip()
        
        elif score >= 24:
            return f"""
**Kết luận: Nhận thức ở mức ranh giới - Cần theo dõi**

Điểm MMSE của bạn ({score}/30) nằm ở mức ranh giới, có nghĩa là có một số dấu hiệu suy giảm nhẹ 
nhưng chưa đến mức dementia. Đây có thể là:
- Biến đổi bình thường do tuổi tác (Age-Associated Memory Impairment)
- Suy giảm nhận thức nhẹ (Mild Cognitive Impairment - MCI)
- Ảnh hưởng tạm thời từ stress, thiếu ngủ, hoặc thuốc men

**Ý nghĩa:**
- Nguy cơ tiến triển thành dementia: 10-15%/năm (so với 1-2%/năm ở người bình thường)
- Cần theo dõi sát và can thiệp sớm
- Vẫn có thể cải thiện hoặc ổn định với các biện pháp phù hợp

**Khuyến nghị:**
- Kiểm tra lại sau 3-6 tháng để theo dõi xu hướng
- Đánh giá các yếu tố nguy cơ (tim mạch, thiếu vitamin B12, trầm cảm, v.v.)
- Bắt đầu các biện pháp dự phòng (xem phần Khuyến nghị)
            """.strip()
        
        elif score >= 20:
            return f"""
**Kết luận: Suy giảm nhận thức nhẹ - Cần đánh giá chuyên sâu**

Điểm MMSE của bạn ({score}/30) cho thấy có suy giảm nhận thức nhẹ. Kết quả này cần được đánh giá 
kỹ hơn bởi bác sĩ thần kinh hoặc tâm lý lâm sàng để:
- Xác định nguyên nhân (Alzheimer's, vascular dementia, trầm cảm, thiếu vitamin, v.v.)
- Đánh giá mức độ ảnh hưởng đến sinh hoạt hàng ngày
- Lập kế hoạch can thiệp và theo dõi

**Ý nghĩa:**
- Có thể đã ảnh hưởng đến một số hoạt động phức tạp (quản lý tài chính, đi lại xa, v.v.)
- Nguy cơ tiến triển cần được quản lý tích cực
- Can thiệp sớm có thể làm chậm tiến triển

**Hành động cần làm:**
- Đặt lịch khám với bác sĩ thần kinh trong 1-2 tuần
- Chuẩn bị danh sách thuốc đang dùng và tiền sử bệnh
- Xem xét làm thêm xét nghiệm: MoCA, hình ảnh học (CT/MRI), xét nghiệm máu
            """.strip()
        
        else:
            return f"""
**Kết luận: Suy giảm nhận thức trung bình đến nặng - Cần can thiệp khẩn**

Điểm MMSE của bạn ({score}/30) cho thấy suy giảm nhận thức đáng kể. Đây là tình trạng nghiêm trọng 
cần được đánh giá và quản lý bởi đội ngũ y tế chuyên khoa ngay lập tức.

**Ý nghĩa:**
- Có khả năng đã ảnh hưởng đến khả năng sinh hoạt độc lập
- Cần hỗ trợ và giám sát trong các hoạt động hàng ngày
- Nguy cơ tai nạn, lạc đường, và các vấn đề an toàn

**Hành động khẩn cấp:**
- Đặt lịch khám bác sĩ thần kinh NGAY trong tuần này
- Không để người bệnh ở nhà một mình
- Đánh giá an toàn: lái xe, sử dụng bếp ga, quản lý thuốc
- Liên hệ dịch vụ hỗ trợ xã hội và chăm sóc người cao tuổi

**Hỗ trợ gia đình:**
- Tìm hiểu về nhóm hỗ trợ cho người chăm sóc
- Lập kế hoạch chăm sóc dài hạn
- Tìm hiểu quy trình pháp lý (ủy quyền, giám hộ nếu cần)
            """.strip()
    
    def generate_mmse_theoretical_basis(self) -> Dict:
        """Explain theoretical basis of MMSE-35"""
        return {
            "title": "Cơ Sở Lý Thuyết và Khoa Học",
            "why_35_points": """
Tại sao sử dụng thang 35 điểm thay vì 30 điểm chuẩn?
Bài kiểm tra này sử dụng phiên bản mở rộng Mini-Examen-Cognoscivo (MEC) 35 điểm, dựa trên nghiên cứu
của Lobo và cộng sự (1979, 1999) tại Tây Ban Nha. Phiên bản này được thiết kế để:

- Tăng độ nhạy với suy giảm nhẹ: MMSE 30 điểm có hiệu ứng trần (ceiling effect) - nhiều người
bình thường đạt 29-30 điểm, khiến khó phát hiện suy giảm nhẹ. Thang 35 điểm tạo không gian phân biệt tốt hơn.
- Đánh giá chức năng điều hành: Thêm 3 điểm cho executive function (verbal fluency + abstraction) -
chức năng bị ảnh hưởng sớm trong MCI nhưng không được đánh giá trong MMSE 30.
- Đánh giá thị giác-không gian chi tiết: Sử dụng Clock Drawing Test (3 điểm) thay vì chỉ vẽ ngũ giác (1 điểm).
Clock drawing đánh giá đa chiều: planning, visuospatial, number knowledge, motor execution.
- Phù hợp với dân số đa dạng: Đã được xác thực trên nhiều quốc gia với học vấn đa dạng,
bao gồm nghiên cứu trên người Việt (Leggett et al., 2013).
            """.strip(),
            "conversion_methodology": """
Phương pháp chuyển đổi 35 → 30 điểm:
Để so sánh với MMSE chuẩn quốc tế, điểm được chuyển đổi theo quy tắc domain-based conversion:

- Orientation, Registration, Attention, Recall, Language: Giữ nguyên (29 điểm)
- Visuospatial: Clock Drawing 3 điểm → 1 điểm (nếu ≥2 điểm thì tính 1, <2 thì tính 0)
- Executive Function: Loại bỏ (không có trong MMSE 30)

Công thức điều chỉnh học vấn dựa trên nghiên cứu của Leggett et al. (2013) trên người Việt:

- Không biết chữ: +6 điểm
- Tiểu học (1-5 năm): +3 điểm
- Trung học (6-12 năm): Không điều chỉnh
- Đại học (>12 năm): -2 điểm (kỳ vọng cao hơn)
            """.strip(),
            "scientific_validation": """
Bằng chứng khoa học:

**Lobo et al. (1979, 1999)**
- Phát triển và xác thực MEC 35 điểm tại Tây Ban Nha
- Tương quan cao với MMSE 30: r = 0.92
- Độ nhạy tốt hơn 15% trong phát hiện MCI

**Modrego et al. (2005, 2013)**
- Sử dụng MEC dự đoán chuyển từ MCI sang AD
- Độ nhạy 78%, độ đặc hiệu 82% với cut-off 28/35

**Leggett et al. (2013)**
- Nghiên cứu MMSE trên 150 người Việt (75 HC, 75 dementia)
- Xác định ngưỡng điều chỉnh theo học vấn cho dân số Việt
- Khuyến nghị cut-off thấp hơn do ảnh hưởng văn hóa và học vấn

**Tombaugh & McIntyre (1992)**
- Meta-analysis của 166 nghiên cứu MMSE
- Xác định ảnh hưởng của tuổi và học vấn đến điểm số
- Cơ sở cho các điều chỉnh chuẩn hóa
            """.strip(),
            "citations": [
                {
                    "authors": "Folstein MF, Folstein SE, McHugh PR",
                    "year": 1975,
                    "title": "Mini-mental state: A practical method for grading the cognitive state of patients for the clinician",
                    "journal": "Journal of Psychiatric Research",
                    "volume": "12(3)",
                    "pages": "189-198"
                },
                {
                    "authors": "Lobo A, Ezquerra J, Gomez Burgada F, et al.",
                    "year": 1979,
                    "title": "El Mini-Examen Cognoscivo: Un test sencillo, práctico, para detectar alteraciones intelectuales en pacientes médicos",
                    "journal": "Actas Luso-Españolas de Neurología y Psiquiatría",
                    "volume": "7",
                    "pages": "189-202"
                },
                {
                    "authors": "Leggett AN, Zarit SH, Nguyen NH, et al.",
                    "year": 2013,
                    "title": "The effects of social, cultural, and economic factors on the Mini Mental State Examination in Vietnamese dementia patients and their caregivers",
                    "journal": "International Psychogeriatrics",
                    "volume": "25(9)",
                    "pages": "1545-1552"
                }
            ]
        }
    
    def generate_speech_acoustic_analysis(self, results: Dict) -> Dict:
        """Detailed acoustic feature analysis section"""
        detailed_analysis = results.get("detailed_analysis", {}) or {}
        acoustic_features = detailed_analysis.get("acoustic", {}) or {}
        
        if not acoustic_features:
            return {
                "section_title": "Phân Tích Đặc Trưng Âm Thanh Giọng Nói",
                "note": "Không có dữ liệu acoustic features"
            }
        
        # Group by category
        by_category = {}
        all_features = []
        
        for key, feature_data in acoustic_features.items():
            if not isinstance(feature_data, dict):
                continue
            
            category = feature_data.get("category", "Khác")
            if category not in by_category:
                by_category[category] = []
            
            by_category[category].append(feature_data)
            all_features.append(feature_data)
        
        # Count abnormal
        abnormal_count = sum(1 for f in all_features if f.get("severity") not in ["normal", "borderline"])
        
        return {
            "section_title": "Phân Tích Đặc Trưng Âm Thanh Giọng Nói",
            "introduction": self.generate_acoustic_introduction(),
            "summary": {
                "total_features": len(all_features),
                "abnormal_count": abnormal_count,
                "abnormality_rate": f"{(abnormal_count/len(all_features)*100):.1f}%" if all_features else "0%",
                "categories_analyzed": list(by_category.keys())
            },
            "by_category": self.format_acoustic_by_category(by_category),
            "key_findings": self.extract_acoustic_key_findings(all_features),
            "clinical_implications": self.generate_acoustic_clinical_implications(abnormal_count, len(all_features))
        }
    
    def generate_acoustic_introduction(self) -> str:
        """Introduction to acoustic analysis"""
        return """
Phân tích giọng nói là phương pháp tiên tiến để phát hiện sớm suy giảm nhận thức, dựa trên nghiên cứu
cho thấy rằng thay đổi về giọng nói xuất hiện sớm hơn nhiều so với các triệu chứng rõ ràng khác.

**Tại sao phân tích giọng nói quan trọng?**

- **Phát hiện sớm hơn**: Thay đổi giọng nói có thể xuất hiện 5-10 năm trước khi dementia được chẩn đoán.
- **Khách quan và định lượng**: Không phụ thuộc vào cảm nhận chủ quan, sử dụng các chỉ số đo lường chính xác.
- **Không xâm lấn**: Chỉ cần ghi âm lời nói tự nhiên, không cần thiết bị đặc biệt hay can thiệp y tế.
- **Đánh giá đa chiều**: Giọng nói phản ánh nhiều khía cạnh: motor control, breathing, cognition, emotion.

Hệ thống sử dụng bộ đặc trưng eGeMAPS (extended Geneva Minimalistic Acoustic Parameter Set) -
tiêu chuẩn quốc tế cho phân tích giọng nói trong y học, kết hợp với các đặc trưng đặc thù cho tiếng Việt.
        """.strip()
    
    def format_acoustic_by_category(self, by_category: Dict) -> List[Dict]:
        """Format acoustic features grouped by category"""
        formatted_categories = []
        
        category_order = [
            "Đặc trưng thanh điệu",
            "Chất lượng giọng nói",
            "Tốc độ và nhịp điệu",
            "Tạm dừng và lưu loát",
            "Thanh điệu tiếng Việt",
            "Âm lượng"
        ]
        
        for category_name in category_order:
            if category_name not in by_category:
                continue
            
            features = by_category[category_name]
            abnormal_features = [f for f in features if f.get("severity") not in ["normal", "borderline"]]
            
            formatted_categories.append({
                "category_name": category_name,
                "total_features": len(features),
                "abnormal_count": len(abnormal_features),
                "status": "Cần chú ý" if abnormal_features else "Bình thường",
                "color": "orange" if abnormal_features else "green",
                "features": self.format_features_for_display(features),
                "summary": self.summarize_category_acoustic(category_name, features, abnormal_features)
            })
        
        return formatted_categories
    
    def format_features_for_display(self, features: List[Dict]) -> List[Dict]:
        """Format features for user-friendly display"""
        display_features = []
        
        for feature in features:
            # Only show abnormal or borderline features in detail
            if feature.get("severity") == "normal":
                continue
            
            normal_range = feature.get("normal_range", {})
            if isinstance(normal_range, dict):
                range_display = normal_range.get("display", "N/A")
            elif isinstance(normal_range, list) and len(normal_range) == 2:
                range_display = f"{normal_range[0]}-{normal_range[1]}"
            else:
                range_display = str(normal_range) if normal_range else "N/A"
            
            display_features.append({
                "name": feature.get("name_vi") or feature.get("description", "N/A"),
                "value": f"{feature.get('value', 0):.2f} {feature.get('unit', '')}",
                "status": feature.get("status", "N/A"),
                "severity": feature.get("severity", "normal"),
                "normal_range": range_display,
                "deviation": f"{feature.get('deviation_pct', 0):.1f}%",
                "interpretation": feature.get("interpretation", ""),
                "clinical_significance": feature.get("clinical_significance", "")
            })
        
        return display_features
    
    def summarize_category_acoustic(
        self,
        category_name: str,
        all_features: List[Dict],
        abnormal_features: List[Dict]
    ) -> str:
        """Summarize findings for an acoustic category"""
        if not abnormal_features:
            return f"{category_name} trong giới hạn bình thường. Không phát hiện vấn đề đáng kể."
        
        severe_count = len([f for f in abnormal_features if f.get("severity") == "severe"])
        moderate_count = len([f for f in abnormal_features if f.get("severity") == "moderate"])
        mild_count = len([f for f in abnormal_features if f.get("severity") == "mild"])
        
        summary = f"Phát hiện {len(abnormal_features)} bất thường trong {category_name}: "
        
        parts = []
        if severe_count > 0:
            parts.append(f"{severe_count} vấn đề nghiêm trọng")
        if moderate_count > 0:
            parts.append(f"{moderate_count} vấn đề trung bình")
        if mild_count > 0:
            parts.append(f"{mild_count} vấn đề nhẹ")
        
        summary += ", ".join(parts) + ". "
        
        # Add specific features
        top_issues = sorted(
            abnormal_features,
            key=lambda x: {"severe": 3, "moderate": 2, "mild": 1}.get(x.get("severity", "normal"), 0),
            reverse=True
        )[:2]
        
        if top_issues:
            summary += "Đặc biệt chú ý: " + ", ".join([
                f.get("name_vi") or f.get("description", "N/A") for f in top_issues
            ]) + "."
        
        return summary
    
    def extract_acoustic_key_findings(self, all_features: List[Dict]) -> List[Dict]:
        """Extract key findings from acoustic analysis"""
        # Sort by severity and deviation
        sorted_features = sorted(
            all_features,
            key=lambda x: (
                {"severe": 3, "moderate": 2, "mild": 1, "borderline": 0.5, "normal": 0}.get(
                    x.get("severity", "normal"), 0
                ),
                x.get("deviation_pct", 0)
            ),
            reverse=True
        )
        
        key_findings = []
        for feature in sorted_features[:5]:  # Top 5
            if feature.get("severity") == "normal":
                continue
            
            normal_range = feature.get("normal_range", {})
            if isinstance(normal_range, dict):
                range_display = normal_range.get("display", "N/A")
            elif isinstance(normal_range, list) and len(normal_range) == 2:
                range_display = f"{normal_range[0]}-{normal_range[1]}"
            else:
                range_display = str(normal_range) if normal_range else "N/A"
            
            key_findings.append({
                "feature_name": feature.get("name_vi") or feature.get("description", "N/A"),
                "category": feature.get("category", "Khác"),
                "severity": feature.get("severity", "normal"),
                "finding": (
                    f"{feature.get('name_vi', 'N/A')} {self.severity_to_vietnamese(feature.get('severity', 'normal'))}: "
                    f"{feature.get('value', 0):.2f}{feature.get('unit', '')} "
                    f"(Bình thường: {range_display})"
                ),
                "implication": feature.get("interpretation", ""),
                "clinical_relevance": feature.get("clinical_significance", "")
            })
        
        return key_findings
    
    def severity_to_vietnamese(self, severity: str) -> str:
        """Convert severity to Vietnamese"""
        mapping = {
            "severe": "bất thường nghiêm trọng",
            "moderate": "bất thường trung bình",
            "mild": "bất thường nhẹ",
            "borderline": "ở mức ranh giới"
        }
        return mapping.get(severity, severity)
    
    def generate_acoustic_clinical_implications(self, abnormal_count: int, total_count: int) -> str:
        """Generate clinical implications from acoustic findings"""
        abnormal_rate = (abnormal_count / total_count * 100) if total_count > 0 else 0
        
        if abnormal_rate < 10:
            return """
Ý nghĩa lâm sàng: Tích cực
Các đặc trưng giọng nói hầu hết trong giới hạn bình thường, cho thấy không có dấu hiệu rõ ràng
của suy giảm nhận thức từ góc độ âm thanh học. Đây là kết quả tích cực.
            """.strip()
        elif abnormal_rate < 25:
            return f"""
Ý nghĩa lâm sàng: Cần theo dõi
Phát hiện {abnormal_count}/{total_count} ({abnormal_rate:.1f}%) đặc trưng giọng nói bất thường.
Mặc dù tỷ lệ này không cao, nhưng một số thay đổi nhỏ trong giọng nói có thể là dấu hiệu sớm.
Khuyến nghị theo dõi trong các lần kiểm tra tiếp theo để xem xu hướng thay đổi.
            """.strip()
        else:
            return f"""
Ý nghĩa lâm sàng: Cần đánh giá thêm
Phát hiện {abnormal_count}/{total_count} ({abnormal_rate:.1f}%) đặc trưng giọng nói bất thường.
Tỷ lệ này cao và cần được đánh giá kỹ hơn. Thay đổi về giọng nói có thể phản ánh:

- Vấn đề về kiểm soát vận động (motor control)
- Suy giảm chức năng điều hành (executive function)
- Thay đổi về xử lý ngôn ngữ

Khuyến nghị đánh giá toàn diện với bác sĩ thần kinh.
            """.strip()
    
    # Placeholder methods for other sections (will implement in next steps)
    
    def generate_language_analysis(self, results: Dict) -> Dict:
        """Detailed linguistic feature analysis section"""
        detailed_analysis = results.get("detailed_analysis", {}) or {}
        linguistic_features = detailed_analysis.get("linguistic", {}) or {}
        
        if not linguistic_features:
            return {
                "section_title": "Phân Tích Đặc Trưng Ngôn Ngữ",
                "note": "Không có dữ liệu linguistic features"
            }
        
        # Extract features list
        features_list = linguistic_features.get("features", [])
        if not features_list:
            # Try to extract from dict structure
            features_list = []
            for key, value in linguistic_features.items():
                if isinstance(value, dict) and "value" in value:
                    features_list.append(value)
        
        # Group by category
        by_category = linguistic_features.get("by_category", {}) or {}
        if not by_category and features_list:
            # Group manually
            for feature in features_list:
                category = feature.get("category", "Khác")
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(feature)
        
        # Count abnormal
        abnormal_count = sum(
            1 for f in features_list 
            if f.get("severity") not in ["normal", "borderline"]
        )
        
        return {
            "section_title": "Phân Tích Đặc Trưng Ngôn Ngữ",
            "introduction": self.generate_linguistic_introduction(),
            "summary": {
                "total_features": len(features_list),
                "abnormal_count": abnormal_count,
                "abnormality_rate": f"{(abnormal_count/len(features_list)*100):.1f}%" if features_list else "0%",
                "categories_analyzed": list(by_category.keys())
            },
            "by_category": self.format_linguistic_by_category(by_category),
            "key_findings": self.extract_linguistic_key_findings(features_list),
            "clinical_implications": self.generate_linguistic_clinical_implications(abnormal_count, len(features_list)),
            "research_basis": self._generate_linguistic_research_basis()
        }
    
    def generate_linguistic_introduction(self) -> str:
        """Introduction to linguistic analysis"""
        return """
Phân tích ngôn ngữ đánh giá khả năng sử dụng ngôn ngữ của bạn từ nhiều góc độ: từ vựng, cú pháp, 
ngữ nghĩa, và các đặc trưng đặc thù của tiếng Việt. Thay đổi về ngôn ngữ là một trong những dấu hiệu 
sớm nhất của suy giảm nhận thức.

**Tại sao phân tích ngôn ngữ quan trọng?**

- **Phát hiện sớm**: Thay đổi về từ vựng và cú pháp xuất hiện sớm trong MCI và Alzheimer's
- **Đánh giá đa chiều**: Từ vựng (lexical), cú pháp (syntactic), ngữ nghĩa (semantic)
- **Đặc thù tiếng Việt**: Phân tích các đặc trưng riêng như thanh điệu, từ loại, cấu trúc câu
- **Marker lâm sàng**: Một số đặc trưng (như TTR, pronoun ratio) là biomarker đã được xác thực

Hệ thống sử dụng các công cụ NLP tiên tiến (underthesea, PhoBERT) để phân tích chi tiết ngôn ngữ tiếng Việt.
        """.strip()
    
    def format_linguistic_by_category(self, by_category: Dict) -> List[Dict]:
        """Format linguistic features grouped by category with detailed explanations"""
        formatted_categories = []
        
        category_order = [
            "Từ vựng (Lexical)",
            "Cú pháp (Syntactic)",
            "Ngữ nghĩa (Semantic)",
            "Đặc trưng tiếng Việt",
            "Pragmatic/Discourse"
        ]
        
        for category_name in category_order:
            if category_name not in by_category:
                continue
            
            features = by_category[category_name]
            abnormal_features = [f for f in features if f.get("severity") not in ["normal", "borderline"]]
            
            # Get category explanation
            category_explanation = self._get_category_explanation(category_name)
            
            formatted_categories.append({
                "category_name": category_name,
                "what_it_measures": category_explanation.get("what_it_measures", ""),
                "why_important": category_explanation.get("why_important", ""),
                "clinical_markers": category_explanation.get("clinical_markers", []),
                "total_features": len(features),
                "abnormal_count": len(abnormal_features),
                "status": self._determine_category_status(abnormal_features, len(features)),
                "color": self._determine_category_color(abnormal_features, len(features)),
                "features": self.format_linguistic_features_for_display(features),
                "summary": self.summarize_category_linguistic(category_name, features, abnormal_features),
                "recommendations": self._generate_category_recommendations(category_name, abnormal_features)
            })
        
        return formatted_categories
    
    def _get_category_explanation(self, category_name: str) -> Dict:
        """Get detailed explanation for each category"""
        explanations = {
            "Từ vựng (Lexical)": {
                "what_it_measures": "Độ phong phú và đa dạng của từ vựng bạn sử dụng",
                "why_important": "Giảm đa dạng từ vựng (lặp lại nhiều từ) là dấu hiệu sớm nhất của suy giảm semantic memory - lưu trữ kiến thức về từ ngữ và ý nghĩa. Trong Alzheimer's, anomia (khó tìm từ) xuất hiện rất sớm.",
                "clinical_markers": [
                    "TTR (Type-Token Ratio) <0.45: Sử dụng lại từ cũ quá nhiều",
                    "MATTR <0.60: Không duy trì đa dạng từ trong suốt đoạn nói",
                    "Brunet Index <10: Vốn từ rất nghèo nàn"
                ]
            },
            "Cú pháp (Syntactic)": {
                "what_it_measures": "Cấu trúc câu: độ dài, độ phức tạp, tính hoàn chỉnh",
                "why_important": "Syntactic complexity phản ánh executive function và working memory. Người có MCI/AD thường đơn giản hóa câu - dùng câu ngắn, ít mệnh đề phụ, nhiều câu không hoàn chỉnh.",
                "clinical_markers": [
                    "MLU (Mean Length of Utterance) <10 từ: Câu quá ngắn, đơn giản",
                    "Clause Density <1.2: Ít dùng mệnh đề phụ",
                    "Incomplete Sentence Ratio >0.30: Nhiều câu dở dang"
                ]
            },
            "Ngữ nghĩa (Semantic)": {
                "what_it_measures": "Ý nghĩa, mạch lạc, và mật độ thông tin",
                "why_important": "Semantic coherence đo lường khả năng tổ chức tư duy và giữ mạch. Idea density phản ánh khả năng truyền đạt thông tin hiệu quả. Cả hai giảm rõ rệt trong dementia.",
                "clinical_markers": [
                    "Semantic Coherence <0.40: Nội dung rời rạc, không liên kết",
                    "Idea Density <4.5: Nói nhiều nhưng ít nội dung",
                    "Information Entropy thấp: Nội dung lặp lại, không đa dạng"
                ]
            },
            "Đặc trưng tiếng Việt": {
                "what_it_measures": "Sử dụng các yếu tố ngữ pháp đặc trưng tiếng Việt",
                "why_important": "Tiếng Việt có các cấu trúc phức tạp như danh từ đơn vị (con, cái, chiếc), từ láy, trợ từ thời gian. Mất khả năng sử dụng đúng là dấu hiệu suy giảm nhận thức ở người Việt.",
                "clinical_markers": [
                    "Classifier Ratio <0.02: Ít dùng danh từ đơn vị",
                    "Reduplication Ratio <0.08: Ít dùng từ láy (có thể do đơn giản hóa)",
                    "Tense/Aspect Marker giảm: Khó biểu đạt thời gian"
                ]
            }
        }
        return explanations.get(category_name, {
            "what_it_measures": "",
            "why_important": "",
            "clinical_markers": []
        })
    
    def _determine_category_status(self, abnormal_features: List[Dict], total_features: int) -> str:
        """Determine status of a category"""
        if not abnormal_features:
            return "Tốt"
        
        abnormal_rate = len(abnormal_features) / total_features if total_features > 0 else 0
        severe_count = len([f for f in abnormal_features if f.get("severity") == "severe"])
        
        if severe_count > 0 or abnormal_rate > 0.5:
            return "Cần chú ý"
        elif abnormal_rate > 0.3:
            return "Cần theo dõi"
        else:
            return "Bình thường với một vài điểm nhỏ"
    
    def _determine_category_color(self, abnormal_features: List[Dict], total_features: int) -> str:
        """Determine color for category status"""
        if not abnormal_features:
            return "green"
        
        abnormal_rate = len(abnormal_features) / total_features if total_features > 0 else 0
        severe_count = len([f for f in abnormal_features if f.get("severity") == "severe"])
        
        if severe_count > 0 or abnormal_rate > 0.5:
            return "red"
        elif abnormal_rate > 0.3:
            return "orange"
        else:
            return "yellow"
    
    def _generate_category_recommendations(self, category_name: str, abnormal_features: List[Dict]) -> List[str]:
        """Generate specific recommendations for each category"""
        if not abnormal_features:
            return []
        
        recommendations_by_category = {
            "Từ vựng (Lexical)": [
                "📚 Đọc sách đa dạng thể loại (tiểu thuyết, báo, sách chuyên môn)",
                "✍️ Viết nhật ký hàng ngày, cố gắng dùng từ mới",
                "🎮 Chơi trò chơi từ vựng: ô chữ, scrabble, word search",
                "💬 Học 3-5 từ mới mỗi ngày và dùng trong hội thoại"
            ],
            "Cú pháp (Syntactic)": [
                "📖 Luyện đọc to và phân tích cấu trúc câu",
                "✏️ Viết câu phức: dùng 'vì', 'mặc dù', 'khi', 'nếu'",
                "🗣️ Luyện kể chuyện có đầu-giữa-cuối rõ ràng",
                "👂 Nghe và lặp lại câu dài từ radio/podcast"
            ],
            "Ngữ nghĩa (Semantic)": [
                "🎯 Luyện tóm tắt nội dung: phim, tin tức, câu chuyện",
                "🔗 Luyện liên kết ý tưởng: 'điều này liên quan đến...'",
                "📝 Viết outline trước khi nói về chủ đề phức tạp",
                "🧩 Chơi trò chơi logic: sudoku, puzzle, cờ vua"
            ],
            "Đặc trưng tiếng Việt": [
                "🇻🇳 Luyện phân biệt 'con gà', 'cái bàn', 'chiếc xe'",
                "🔄 Luyện từ láy: 'đỏ đỏ', 'nhanh nhanh', 'chầm chậm'",
                "⏰ Luyện diễn đạt thời gian: 'đã', 'đang', 'sẽ', 'vừa mới'",
                "📚 Đọc văn học Việt Nam để giữ cấu trúc ngôn ngữ"
            ]
        }
        
        return recommendations_by_category.get(category_name, [
            "Luyện tập giao tiếp thường xuyên",
            "Tham gia hoạt động xã hội",
            "Đọc sách và viết nhật ký"
        ])
    
    def format_linguistic_features_for_display(self, features: List[Dict]) -> List[Dict]:
        """Format linguistic features for display"""
        display_features = []
        
        for feature in features:
            # Only show abnormal or borderline features in detail
            if feature.get("severity") == "normal":
                continue
            
            normal_range = feature.get("normal_range", {})
            if isinstance(normal_range, dict):
                range_display = normal_range.get("display", "N/A")
            elif isinstance(normal_range, list) and len(normal_range) == 2:
                range_display = f"{normal_range[0]}-{normal_range[1]}"
            else:
                range_display = str(normal_range) if normal_range else "N/A"
            
            display_features.append({
                "name": feature.get("name_vi") or feature.get("description", "N/A"),
                "value": f"{feature.get('value', 0):.3f} {feature.get('unit', '')}",
                "status": feature.get("status", "N/A"),
                "severity": feature.get("severity", "normal"),
                "normal_range": range_display,
                "deviation": f"{feature.get('deviation_pct', 0):.1f}%",
                "interpretation": feature.get("interpretation", ""),
                "clinical_significance": feature.get("clinical_significance", ""),
                "what_this_means": self._explain_feature_to_user(feature),
                "citation": feature.get("citation", "")
            })
        
        return display_features
    
    def summarize_category_linguistic(
        self,
        category_name: str,
        all_features: List[Dict],
        abnormal_features: List[Dict]
    ) -> str:
        """Summarize findings for a linguistic category"""
        if not abnormal_features:
            return f"{category_name} trong giới hạn bình thường. Khả năng ngôn ngữ tốt."
        
        severe_count = len([f for f in abnormal_features if f.get("severity") == "severe"])
        moderate_count = len([f for f in abnormal_features if f.get("severity") == "moderate"])
        mild_count = len([f for f in abnormal_features if f.get("severity") == "mild"])
        
        summary = f"Phát hiện {len(abnormal_features)} bất thường trong {category_name}: "
        
        parts = []
        if severe_count > 0:
            parts.append(f"{severe_count} vấn đề nghiêm trọng")
        if moderate_count > 0:
            parts.append(f"{moderate_count} vấn đề trung bình")
        if mild_count > 0:
            parts.append(f"{mild_count} vấn đề nhẹ")
        
        summary += ", ".join(parts) + ". "
        
        # Add specific features
        top_issues = sorted(
            abnormal_features,
            key=lambda x: {"severe": 3, "moderate": 2, "mild": 1}.get(x.get("severity", "normal"), 0),
            reverse=True
        )[:2]
        
        if top_issues:
            summary += "Đặc biệt chú ý: " + ", ".join([
                f.get("name_vi") or f.get("description", "N/A") for f in top_issues
            ]) + "."
        
        return summary
    
    def extract_linguistic_key_findings(self, all_features: List[Dict]) -> List[Dict]:
        """Extract key findings from linguistic analysis"""
        # Sort by severity and deviation
        sorted_features = sorted(
            all_features,
            key=lambda x: (
                {"severe": 3, "moderate": 2, "mild": 1, "borderline": 0.5, "normal": 0}.get(
                    x.get("severity", "normal"), 0
                ),
                x.get("deviation_pct", 0)
            ),
            reverse=True
        )
        
        key_findings = []
        for feature in sorted_features[:5]:  # Top 5
            if feature.get("severity") == "normal":
                continue
            
            normal_range = feature.get("normal_range", {})
            if isinstance(normal_range, dict):
                range_display = normal_range.get("display", "N/A")
            elif isinstance(normal_range, list) and len(normal_range) == 2:
                range_display = f"{normal_range[0]}-{normal_range[1]}"
            else:
                range_display = str(normal_range) if normal_range else "N/A"
            
            key_findings.append({
                "feature_name": feature.get("name_vi") or feature.get("description", "N/A"),
                "category": feature.get("category", "Khác"),
                "severity": feature.get("severity", "normal"),
                "finding": (
                    f"{feature.get('name_vi', 'N/A')} {self.severity_to_vietnamese(feature.get('severity', 'normal'))}: "
                    f"{feature.get('value', 0):.3f}{feature.get('unit', '')} "
                    f"(Bình thường: {range_display})"
                ),
                "implication": feature.get("interpretation", ""),
                "clinical_relevance": feature.get("clinical_significance", "")
            })
        
        return key_findings
    
    def generate_linguistic_clinical_implications(self, abnormal_count: int, total_count: int) -> str:
        """Generate clinical implications from linguistic findings"""
        abnormal_rate = (abnormal_count / total_count * 100) if total_count > 0 else 0
        
        if abnormal_rate < 10:
            return """
Ý nghĩa lâm sàng: Tích cực
Khả năng ngôn ngữ của bạn hầu hết trong giới hạn bình thường. Từ vựng, cú pháp và ngữ nghĩa 
đều được duy trì tốt. Đây là dấu hiệu tích cực cho thấy chức năng ngôn ngữ chưa bị ảnh hưởng.
            """.strip()
        elif abnormal_rate < 25:
            return f"""
Ý nghĩa lâm sàng: Cần theo dõi
Phát hiện {abnormal_count}/{total_count} ({abnormal_rate:.1f}%) đặc trưng ngôn ngữ bất thường.
Một số thay đổi nhỏ về từ vựng hoặc cú pháp có thể là dấu hiệu sớm. Khuyến nghị theo dõi 
trong các lần kiểm tra tiếp theo để đánh giá xu hướng.
            """.strip()
        else:
            return f"""
Ý nghĩa lâm sàng: Cần đánh giá thêm
Phát hiện {abnormal_count}/{total_count} ({abnormal_rate:.1f}%) đặc trưng ngôn ngữ bất thường.
Tỷ lệ này cao và có thể phản ánh:

- Suy giảm từ vựng (anomia - khó tìm từ)
- Thay đổi về cú pháp (câu ngắn hơn, đơn giản hơn)
- Giảm độ phức tạp ngữ nghĩa
- Có thể liên quan đến Primary Progressive Aphasia hoặc Alzheimer's

Khuyến nghị đánh giá chuyên sâu với bác sĩ thần kinh hoặc chuyên gia ngôn ngữ trị liệu.
            """.strip()
    
    def generate_risk_factor_identification(self, results: Dict) -> Dict:
        """SHAP-based risk and protective factor identification"""
        shap_explanation = results.get("shap_explanation", {}) or {}
        
        if not shap_explanation:
            return {
                "section_title": "Xác Định Yếu Tố Nguy Cơ và Bảo Vệ",
                "note": "Không có dữ liệu SHAP explanation"
            }
        
        risk_factors = shap_explanation.get("top_risk_factors", []) or []
        protective_factors = shap_explanation.get("top_protective_factors", []) or []
        grouped_contributions = shap_explanation.get("grouped_contributions", {}) or {}
        clinical_interp = shap_explanation.get("clinical_interpretation", {}) or {}
        
        return {
            "section_title": "Xác Định Yếu Tố Nguy Cơ và Bảo Vệ",
            "introduction": self.generate_risk_factor_introduction(),
            "summary": {
                "total_risk_factors": len(risk_factors),
                "total_protective_factors": len(protective_factors),
                "overall_risk_level": clinical_interp.get("overall_risk_level", "Không xác định"),
                "confidence": clinical_interp.get("confidence", 0),
                "primary_concerns": len(clinical_interp.get("primary_concerns", [])),
                "strengths": len(clinical_interp.get("strengths", []))
            },
            "risk_factors": self.format_risk_factors(risk_factors),
            "protective_factors": self.format_protective_factors(protective_factors),
            "grouped_analysis": self.format_grouped_contributions(grouped_contributions),
            "clinical_interpretation": self.format_clinical_interpretation_summary(clinical_interp)
        }
    
    def generate_risk_factor_introduction(self) -> str:
        """Introduction to risk factor identification"""
        return """
Phân tích SHAP (SHapley Additive exPlanations) xác định các yếu tố cụ thể góp phần vào nguy cơ 
suy giảm nhận thức hoặc bảo vệ chống lại suy giảm. Phương pháp này dựa trên lý thuyết trò chơi 
để phân bổ "đóng góp" của từng đặc trưng vào kết quả dự đoán.

**Cách đọc kết quả:**

- **Yếu tố nguy cơ** (SHAP > 0): Đặc trưng này làm tăng nguy cơ suy giảm nhận thức
- **Yếu tố bảo vệ** (SHAP < 0): Đặc trưng này giúp giảm nguy cơ, bảo vệ chức năng nhận thức
- **Độ lớn SHAP**: Càng lớn (dương hoặc âm) thì ảnh hưởng càng mạnh

**Ý nghĩa lâm sàng:**

Việc xác định các yếu tố nguy cơ cụ thể giúp:
- Tập trung can thiệp vào các vấn đề quan trọng nhất
- Hiểu rõ nguyên nhân gốc rễ của suy giảm nhận thức
- Phát triển kế hoạch điều trị cá nhân hóa
- Theo dõi hiệu quả can thiệp theo thời gian
        """.strip()
    
    def format_risk_factors(self, risk_factors: List[Dict]) -> List[Dict]:
        """Format risk factors for display"""
        formatted = []
        
        for i, factor in enumerate(risk_factors[:10], 1):  # Top 10
            shap_value = factor.get("shap_value", 0) or factor.get("absolute_importance", 0)
            feature_name = factor.get("feature_name_vi") or factor.get("feature", "N/A")
            
            # Determine severity based on SHAP value
            if abs(shap_value) >= 0.3:
                severity = "Nghiêm trọng"
                priority = "Cao"
            elif abs(shap_value) >= 0.2:
                severity = "Trung bình"
                priority = "Trung bình"
            else:
                severity = "Nhẹ"
                priority = "Thấp"
            
            formatted.append({
                "rank": i,
                "feature_name": feature_name,
                "feature_name_en": factor.get("feature_name_en", ""),
                "shap_value": f"{shap_value:.3f}",
                "severity": severity,
                "priority": priority,
                "current_value": f"{factor.get('value', 0):.3f} {factor.get('unit', '')}",
                "normal_range": self._format_normal_range(factor.get("normal_range")),
                "comparison": factor.get("comparison", "N/A"),
                "interpretation": self._format_interpretation(factor.get("interpretation")),
                "explanation": factor.get("explanation_vi") or factor.get("explanation", ""),
                "recommendation": self._format_recommendation(factor.get("recommendation")),
                "citation": factor.get("citation", "")
            })
        
        return formatted
    
    def format_protective_factors(self, protective_factors: List[Dict]) -> List[Dict]:
        """Format protective factors for display"""
        formatted = []
        
        for i, factor in enumerate(protective_factors[:10], 1):  # Top 10
            shap_value = factor.get("shap_value", 0) or factor.get("absolute_importance", 0)
            feature_name = factor.get("feature_name_vi") or factor.get("feature", "N/A")
            
            # For protective factors, negative SHAP is good
            abs_shap = abs(shap_value)
            
            if abs_shap >= 0.3:
                strength = "Mạnh"
            elif abs_shap >= 0.2:
                strength = "Trung bình"
            else:
                strength = "Nhẹ"
            
            formatted.append({
                "rank": i,
                "feature_name": feature_name,
                "feature_name_en": factor.get("feature_name_en", ""),
                "shap_value": f"{shap_value:.3f}",
                "strength": strength,
                "current_value": f"{factor.get('value', 0):.3f} {factor.get('unit', '')}",
                "normal_range": self._format_normal_range(factor.get("normal_range")),
                "comparison": factor.get("comparison", "N/A"),
                "interpretation": self._format_interpretation(factor.get("interpretation")),
                "explanation": factor.get("explanation_vi") or factor.get("explanation", ""),
                "recommendation": self._format_recommendation(factor.get("recommendation")),
                "citation": factor.get("citation", "")
            })
        
        return formatted
    
    def format_grouped_contributions(self, grouped_contributions: Dict) -> List[Dict]:
        """Format grouped contributions by category"""
        if not grouped_contributions:
            return []
        
        formatted = []
        sorted_groups = sorted(
            grouped_contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        for category, contribution in sorted_groups:
            category_name_vi = {
                "acoustic": "Đặc trưng âm thanh",
                "linguistic": "Đặc trưng ngôn ngữ",
                "mmse": "Điểm MMSE",
                "demographic": "Nhân khẩu học"
            }.get(category.lower(), category)
            
            formatted.append({
                "category": category_name_vi,
                "category_en": category,
                "contribution": f"{contribution:.3f}",
                "percentage": f"{(abs(contribution) / sum(abs(v) for v in grouped_contributions.values()) * 100):.1f}%",
                "type": "Nguy cơ" if contribution > 0 else "Bảo vệ"
            })
        
        return formatted
    
    def format_clinical_interpretation_summary(self, clinical_interp: Dict) -> Dict:
        """Format clinical interpretation summary"""
        if not clinical_interp:
            return {"note": "Không có dữ liệu"}
        
        primary_concerns = clinical_interp.get("primary_concerns", [])
        strengths = clinical_interp.get("strengths", [])
        
        return {
            "overall_risk_level": clinical_interp.get("overall_risk_level", "Không xác định"),
            "confidence": f"{clinical_interp.get('confidence', 0):.1f}%",
            "summary": clinical_interp.get("summary", ""),
            "primary_concerns": [
                {
                    "category": c.get("category", "N/A"),
                    "count": c.get("count", 0),
                    "description": c.get("description", "")
                }
                for c in primary_concerns
            ],
            "strengths": [
                {
                    "category": s.get("category", "N/A"),
                    "count": s.get("count", 0),
                    "description": s.get("description", "")
                }
                for s in strengths
            ],
            "key_recommendations": clinical_interp.get("key_recommendations", [])
        }
    
    def _format_normal_range(self, normal_range: Any) -> str:
        """Format normal range for display"""
        if not normal_range:
            return "N/A"
        
        if isinstance(normal_range, dict):
            return normal_range.get("display", "N/A")
        elif isinstance(normal_range, list) and len(normal_range) == 2:
            return f"{normal_range[0]}-{normal_range[1]}"
        else:
            return str(normal_range)
    
    def _format_interpretation(self, interpretation: Any) -> str:
        """Format interpretation for display"""
        if not interpretation:
            return ""
        
        if isinstance(interpretation, dict):
            return interpretation.get("description", "")
        elif isinstance(interpretation, str):
            return interpretation
        else:
            return str(interpretation)
    
    def _format_recommendation(self, recommendation: Any) -> str:
        """Format recommendation for display"""
        if not recommendation:
            return ""
        
        if isinstance(recommendation, dict):
            return recommendation.get("description", "") or recommendation.get("title", "")
        elif isinstance(recommendation, str):
            return recommendation
        else:
            return str(recommendation)
    
    def generate_clinical_interpretation(self, results: Dict) -> Dict:
        """Synthesize all findings into cohesive clinical interpretation"""
        assessment_result = results.get("assessment_result", {}) or {}
        detailed_analysis = results.get("detailed_analysis", {}) or {}
        acoustic = detailed_analysis.get("acoustic", {}) or {}
        linguistic = detailed_analysis.get("linguistic", {}) or {}
        shap_explanation = results.get("shap_explanation", {}) or {}
        qa_history = results.get("qa_history", []) or []
        
        return {
            "section_title": "Tổng Hợp Đánh Giá Lâm Sàng",
            "introduction": self._generate_clinical_intro(),
            "overall_assessment": self._synthesize_overall_assessment(
                assessment_result, acoustic, linguistic, shap_explanation
            ),
            "cognitive_profile": self._generate_cognitive_profile(assessment_result, qa_history),
            "speech_language_profile": self._generate_speech_language_profile(acoustic, linguistic),
            "risk_stratification": self._generate_risk_stratification(
                assessment_result, acoustic, linguistic, shap_explanation
            ),
            "differential_considerations": self._generate_differential_considerations(results),
            "clinical_recommendations": self._generate_clinical_recommendations_summary(results),
            "prognosis_discussion": self._generate_prognosis_discussion(results)
        }
    
    def _generate_clinical_intro(self) -> str:
        """Introduction to clinical interpretation"""
        return """
**Phần này tổng hợp tất cả các phân tích thành một bức tranh toàn diện về tình trạng nhận thức của bạn.**

Chúng tôi đã đánh giá ba khía cạnh chính:
1. **Hiệu suất MMSE:** Khả năng thực hiện các nhiệm vụ nhận thức cơ bản
2. **Phân tích giọng nói:** Các đặc trưng âm thanh và ngôn ngữ từ lời nói tự nhiên
3. **SHAP Analysis:** Xác định các yếu tố nguy cơ và bảo vệ cụ thể

Việc kết hợp cả ba góc nhìn này cho phép đánh giá chính xác và toàn diện hơn so với chỉ dùng 
một công cụ đơn lẻ. Dưới đây là bức tranh tổng thể về tình trạng nhận thức của bạn.
        """.strip()
    
    def generate_recommendations(self, results: Dict) -> Dict:
        """Comprehensive recommendations section"""
        recommendations = results.get("recommendations", []) or []
        shap_explanation = results.get("shap_explanation", {}) or {}
        assessment_result = results.get("assessment_result", {}) or {}
        user_info = results.get("user_info", {}) or {}
        
        # Categorize recommendations
        categorized = self._categorize_recommendations(recommendations)
        
        # Generate priority-based recommendations
        priority_recs = self._generate_priority_recommendations(
            assessment_result,
            shap_explanation,
            user_info
        )
        
        return {
            "section_title": "Khuyến Nghị và Hành Động",
            "introduction": self.generate_recommendations_introduction(),
            "summary": {
                "total_recommendations": len(recommendations),
                "by_priority": {
                    "urgent": len([r for r in recommendations if isinstance(r, dict) and r.get("priority") == "urgent"]),
                    "high": len([r for r in recommendations if isinstance(r, dict) and r.get("priority") == "high"]),
                    "medium": len([r for r in recommendations if isinstance(r, dict) and r.get("priority") == "medium"]),
                    "low": len([r for r in recommendations if isinstance(r, dict) and r.get("priority") == "low"])
                },
                "by_category": {cat: len(recs) for cat, recs in categorized.items()}
            },
            "priority_recommendations": priority_recs,
            "by_category": self._format_categorized_recommendations(categorized),
            "feature_specific": self._extract_feature_specific_recommendations(shap_explanation),
            "lifestyle_recommendations": self._generate_lifestyle_recommendations(assessment_result)
        }
    
    def generate_recommendations_introduction(self) -> str:
        """Introduction to recommendations section"""
        return """
Các khuyến nghị dưới đây được cá nhân hóa dựa trên kết quả đánh giá của bạn. Chúng được phân loại 
theo mức độ ưu tiên và lĩnh vực để giúp bạn dễ dàng lập kế hoạch hành động.

**Cách sử dụng:**

1. **Ưu tiên cao/khẩn cấp**: Thực hiện ngay trong tuần này
2. **Ưu tiên trung bình**: Thực hiện trong tháng này
3. **Ưu tiên thấp**: Kế hoạch dài hạn, duy trì lối sống

**Lưu ý quan trọng:**

- Các khuyến nghị này bổ sung, không thay thế, lời khuyên của bác sĩ
- Luôn tham khảo ý kiến chuyên gia y tế trước khi thay đổi thuốc hoặc chế độ điều trị
- Theo dõi tiến triển và điều chỉnh kế hoạch theo thời gian
        """.strip()
    
    def _categorize_recommendations(self, recommendations: List) -> Dict[str, List]:
        """Categorize recommendations by type"""
        categorized = {
            "medical": [],
            "lifestyle": [],
            "cognitive": [],
            "monitoring": [],
            "general": []
        }
        
        for rec in recommendations:
            if isinstance(rec, dict):
                category = rec.get("category", "general")
                if category in categorized:
                    categorized[category].append(rec)
                else:
                    categorized["general"].append(rec)
            else:
                categorized["general"].append(rec)
        
        return categorized
    
    def _generate_priority_recommendations(
        self,
        assessment_result: Dict,
        shap_explanation: Dict,
        user_info: Dict
    ) -> Dict[str, List[Dict]]:
        """Generate recommendations by priority level"""
        priority_recs = {
            "urgent": [],
            "high": [],
            "medium": [],
            "low": []
        }
        
        mmse_score = assessment_result.get("adjusted_score", 0) or assessment_result.get("raw_score", 0)
        risk_level = assessment_result.get("risk_level", "normal")
        
        # Urgent recommendations
        if mmse_score < 20:
            priority_recs["urgent"].append({
                "title": "Khám bác sĩ thần kinh ngay lập tức",
                "description": "Điểm MMSE thấp cho thấy cần đánh giá chuyên sâu ngay",
                "actions": [
                    "Đặt lịch khám trong tuần này",
                    "Chuẩn bị danh sách thuốc và tiền sử bệnh",
                    "Mang theo kết quả đánh giá này"
                ],
                "rationale": f"Điểm MMSE {mmse_score}/30 cho thấy suy giảm nhận thức đáng kể"
            })
        
        # High priority
        if mmse_score < 24:
            priority_recs["high"].append({
                "title": "Đánh giá chuyên sâu với bác sĩ",
                "description": "Cần xác định nguyên nhân và lập kế hoạch can thiệp",
                "actions": [
                    "Khám bác sĩ thần kinh trong 2-4 tuần",
                    "Xem xét làm thêm xét nghiệm (MoCA, hình ảnh học)",
                    "Đánh giá các yếu tố có thể điều chỉnh được"
                ],
                "rationale": "Suy giảm nhận thức nhẹ cần được quản lý tích cực"
            })
        
        # Medium priority
        if mmse_score < 27:
            priority_recs["medium"].append({
                "title": "Theo dõi định kỳ",
                "description": "Tái đánh giá sau 3-6 tháng để theo dõi xu hướng",
                "actions": [
                    "Lên lịch tái đánh giá sau 3-6 tháng",
                    "Theo dõi các triệu chứng hàng ngày",
                    "Áp dụng các biện pháp dự phòng"
                ],
                "rationale": "Điểm ở mức ranh giới, cần theo dõi để phát hiện thay đổi"
            })
        
        return priority_recs
    
    def _format_categorized_recommendations(self, categorized: Dict[str, List]) -> List[Dict]:
        """Format categorized recommendations for display"""
        formatted = []
        
        category_names = {
            "medical": "Y tế và Điều trị",
            "lifestyle": "Lối sống",
            "cognitive": "Kích thích Nhận thức",
            "monitoring": "Theo dõi",
            "general": "Chung"
        }
        
        for category, recs in categorized.items():
            if not recs:
                continue
            
            formatted.append({
                "category": category_names.get(category, category),
                "category_en": category,
                "count": len(recs),
                "recommendations": [
                    self._format_single_recommendation(rec) for rec in recs[:5]  # Top 5 per category
                ]
            })
        
        return formatted
    
    def _format_single_recommendation(self, rec: Any) -> Dict:
        """Format a single recommendation"""
        if isinstance(rec, str):
            return {
                "title": rec,
                "type": "simple"
            }
        elif isinstance(rec, dict):
            return {
                "title": rec.get("title", "Khuyến nghị"),
                "description": rec.get("description", ""),
                "priority": rec.get("priority", "medium"),
                "category": rec.get("category", "general"),
                "actions": rec.get("actions", []),
                "rationale": rec.get("rationale", ""),
                "citation": rec.get("citation", ""),
                "type": "structured"
            }
        else:
            return {"title": str(rec), "type": "simple"}
    
    def _extract_feature_specific_recommendations(self, shap_explanation: Dict) -> List[Dict]:
        """Extract feature-specific recommendations from SHAP"""
        recommendations = []
        
        risk_factors = shap_explanation.get("top_risk_factors", [])[:5]
        
        for factor in risk_factors:
            rec = factor.get("recommendation")
            if rec:
                if isinstance(rec, dict):
                    recommendations.append({
                        "feature": factor.get("feature_name_vi", "N/A"),
                        "recommendation": rec
                    })
                elif isinstance(rec, str):
                    recommendations.append({
                        "feature": factor.get("feature_name_vi", "N/A"),
                        "recommendation": {
                            "title": f"Khuyến nghị cho {factor.get('feature_name_vi', 'đặc trưng này')}",
                            "description": rec
                        }
                    })
        
        return recommendations
    
    def _generate_lifestyle_recommendations(self, assessment_result: Dict) -> List[Dict]:
        """Generate lifestyle recommendations"""
        recommendations = []
        
        mmse_score = assessment_result.get("adjusted_score", 0) or assessment_result.get("raw_score", 0)
        
        # Always include general lifestyle recommendations
        recommendations.extend([
            {
                "title": "Hoạt động thể chất thường xuyên",
                "description": "Tập thể dục ít nhất 30 phút/ngày, 5 ngày/tuần",
                "actions": [
                    "Đi bộ nhanh, bơi lội, hoặc đạp xe",
                    "Tập yoga hoặc thái cực quyền",
                    "Hoạt động ngoài trời khi có thể"
                ],
                "rationale": "Tập thể dục cải thiện lưu thông máu não và tăng BDNF (brain-derived neurotrophic factor)"
            },
            {
                "title": "Chế độ ăn uống lành mạnh",
                "description": "Chế độ ăn Địa Trung Hải hoặc MIND diet",
                "actions": [
                    "Tăng cường rau xanh, đặc biệt rau lá xanh đậm",
                    "Ăn cá béo 2-3 lần/tuần (cá hồi, cá thu)",
                    "Hạn chế thực phẩm chế biến sẵn và đường",
                    "Uống đủ nước (1.5-2 lít/ngày)"
                ],
                "rationale": "Chế độ ăn giàu omega-3 và chất chống oxy hóa bảo vệ tế bào thần kinh"
            },
            {
                "title": "Kích thích nhận thức hàng ngày",
                "description": "Giữ cho não hoạt động và học hỏi",
                "actions": [
                    "Đọc sách, báo hàng ngày",
                    "Chơi trò chơi trí tuệ (sudoku, crossword)",
                    "Học kỹ năng mới (ngôn ngữ, nhạc cụ)",
                    "Tham gia hoạt động xã hội"
                ],
                "rationale": "Cognitive reserve giúp bù đắp cho tổn thương não"
            }
        ])
        
        # Add specific recommendations based on score
        if mmse_score < 24:
            recommendations.append({
                "title": "Quản lý stress và giấc ngủ",
                "description": "Stress và thiếu ngủ ảnh hưởng tiêu cực đến nhận thức",
                "actions": [
                    "Ngủ đủ 7-8 giờ/đêm",
                    "Thực hành kỹ thuật thư giãn (thiền, hít thở sâu)",
                    "Tránh căng thẳng không cần thiết"
                ],
                "rationale": "Giấc ngủ là thời gian não phục hồi và củng cố trí nhớ"
            })
        
        return recommendations
    
    def generate_follow_up_plan(self, results: Dict) -> Dict:
        """Comprehensive follow-up plan section"""
        assessment_result = results.get("assessment_result", {}) or {}
        shap_explanation = results.get("shap_explanation", {}) or {}
        user_info = results.get("user_info", {}) or {}
        
        mmse_score = assessment_result.get("adjusted_score", 0) or assessment_result.get("raw_score", 0)
        risk_level = assessment_result.get("risk_level", "normal")
        clinical_interp = shap_explanation.get("clinical_interpretation", {}) or {}
        
        return {
            "section_title": "Kế Hoạch Theo Dõi và Tái Đánh Giá",
            "introduction": self.generate_follow_up_introduction(),
            "immediate_actions": self._generate_immediate_actions(mmse_score, risk_level),
            "short_term_plan": self._generate_short_term_plan(mmse_score, risk_level, clinical_interp),
            "long_term_plan": self._generate_long_term_plan(mmse_score, risk_level),
            "monitoring_schedule": self._generate_monitoring_schedule(mmse_score, risk_level),
            "red_flags": self._generate_red_flags(),
            "support_resources": self._generate_support_resources()
        }
    
    def generate_follow_up_introduction(self) -> str:
        """Introduction to follow-up plan"""
        return """
Kế hoạch theo dõi được thiết kế dựa trên kết quả đánh giá hiện tại của bạn. Mục tiêu là:

- **Phát hiện sớm**: Nhận biết thay đổi ngay khi chúng xuất hiện
- **Can thiệp kịp thời**: Điều chỉnh kế hoạch điều trị khi cần
- **Theo dõi tiến triển**: Đánh giá hiệu quả của các biện pháp can thiệp
- **Hỗ trợ liên tục**: Đảm bảo bạn nhận được sự hỗ trợ cần thiết

**Lưu ý**: Kế hoạch này có thể được điều chỉnh dựa trên tình trạng sức khỏe và lời khuyên của bác sĩ.
        """.strip()
    
    def _generate_immediate_actions(self, mmse_score: float, risk_level: str) -> List[Dict]:
        """Generate immediate actions (next 1-2 weeks)"""
        actions = []
        
        if mmse_score < 20:
            actions.append({
                "timeframe": "Trong tuần này",
                "action": "Khám bác sĩ thần kinh ngay",
                "priority": "Khẩn cấp",
                "details": [
                    "Đặt lịch khám trong 7 ngày",
                    "Chuẩn bị hồ sơ y tế đầy đủ",
                    "Mang theo kết quả đánh giá này"
                ]
            })
        elif mmse_score < 24:
            actions.append({
                "timeframe": "Trong 2 tuần",
                "action": "Đặt lịch khám bác sĩ",
                "priority": "Cao",
                "details": [
                    "Khám bác sĩ thần kinh hoặc tâm lý lâm sàng",
                    "Chuẩn bị danh sách câu hỏi",
                    "Thảo luận về kế hoạch điều trị"
                ]
            })
        
        # Always include baseline documentation
        actions.append({
            "timeframe": "Ngay bây giờ",
            "action": "Ghi lại trạng thái hiện tại",
            "priority": "Trung bình",
            "details": [
                "Lưu giữ kết quả đánh giá này làm baseline",
                "Ghi chú các triệu chứng hiện tại",
                "Theo dõi các hoạt động hàng ngày"
            ]
        })
        
        return actions
    
    def _generate_short_term_plan(self, mmse_score: float, risk_level: str, clinical_interp: Dict) -> Dict:
        """Generate short-term plan (1-6 months)"""
        if mmse_score < 20:
            return {
                "timeframe": "1-3 tháng",
                "objectives": [
                    "Xác định chẩn đoán chính xác",
                    "Bắt đầu điều trị nếu được chỉ định",
                    "Thiết lập hệ thống hỗ trợ"
                ],
                "actions": [
                    "Hoàn thành các xét nghiệm chuyên sâu (nếu cần)",
                    "Bắt đầu thuốc điều trị (theo chỉ định bác sĩ)",
                    "Tham gia các chương trình can thiệp nhận thức",
                    "Thiết lập mạng lưới hỗ trợ gia đình"
                ],
                "milestones": [
                    "Hoàn thành đánh giá chuyên sâu",
                    "Bắt đầu điều trị",
                    "Thiết lập kế hoạch chăm sóc"
                ]
            }
        elif mmse_score < 24:
            return {
                "timeframe": "3-6 tháng",
                "objectives": [
                    "Theo dõi xu hướng thay đổi",
                    "Áp dụng các biện pháp dự phòng",
                    "Tối ưu hóa lối sống"
                ],
                "actions": [
                    "Tái đánh giá sau 3 tháng",
                    "Thực hiện các khuyến nghị về lối sống",
                    "Tham gia hoạt động kích thích nhận thức",
                    "Theo dõi các yếu tố nguy cơ"
                ],
                "milestones": [
                    "Tái đánh giá MMSE",
                    "Đánh giá hiệu quả can thiệp",
                    "Điều chỉnh kế hoạch nếu cần"
                ]
            }
        else:
            return {
                "timeframe": "6 tháng",
                "objectives": [
                    "Duy trì chức năng nhận thức",
                    "Tiếp tục các biện pháp dự phòng",
                    "Theo dõi định kỳ"
                ],
                "actions": [
                    "Tái đánh giá sau 6 tháng",
                    "Duy trì lối sống lành mạnh",
                    "Tiếp tục hoạt động trí tuệ và xã hội"
                ],
                "milestones": [
                    "Tái đánh giá MMSE",
                    "So sánh với baseline",
                    "Xác nhận tình trạng ổn định"
                ]
            }
    
    def _generate_long_term_plan(self, mmse_score: float, risk_level: str) -> Dict:
        """Generate long-term plan (6-12 months and beyond)"""
        return {
            "timeframe": "6-12 tháng và dài hạn",
            "objectives": [
                "Theo dõi tiến triển dài hạn",
                "Điều chỉnh kế hoạch theo nhu cầu",
                "Duy trì chất lượng cuộc sống"
            ],
            "actions": [
                "Tái đánh giá định kỳ mỗi 6-12 tháng",
                "Điều chỉnh thuốc và can thiệp theo chỉ định",
                "Tham gia các chương trình hỗ trợ cộng đồng",
                "Lập kế hoạch chăm sóc dài hạn nếu cần"
            ],
            "considerations": [
                "Đánh giá nhu cầu hỗ trợ tại nhà",
                "Xem xét các dịch vụ chăm sóc chuyên nghiệp",
                "Lập kế hoạch tài chính cho chăm sóc dài hạn",
                "Thảo luận về quyết định y tế với gia đình"
            ]
        }
    
    def _generate_monitoring_schedule(self, mmse_score: float, risk_level: str) -> List[Dict]:
        """Generate monitoring schedule"""
        schedule = []
        
        if mmse_score < 20:
            schedule = [
                {"timeframe": "1 tháng", "assessment": "MMSE + Đánh giá lâm sàng", "provider": "Bác sĩ thần kinh"},
                {"timeframe": "3 tháng", "assessment": "MMSE + Đánh giá chức năng", "provider": "Bác sĩ thần kinh"},
                {"timeframe": "6 tháng", "assessment": "MMSE + Đánh giá toàn diện", "provider": "Bác sĩ thần kinh"},
                {"timeframe": "12 tháng", "assessment": "MMSE + Hình ảnh học (nếu cần)", "provider": "Bác sĩ thần kinh"}
            ]
        elif mmse_score < 24:
            schedule = [
                {"timeframe": "3 tháng", "assessment": "MMSE + Đánh giá lâm sàng", "provider": "Bác sĩ thần kinh"},
                {"timeframe": "6 tháng", "assessment": "MMSE + Đánh giá chức năng", "provider": "Bác sĩ thần kinh"},
                {"timeframe": "12 tháng", "assessment": "MMSE + Đánh giá toàn diện", "provider": "Bác sĩ thần kinh"}
            ]
        else:
            schedule = [
                {"timeframe": "6 tháng", "assessment": "MMSE + Đánh giá nhanh", "provider": "Bác sĩ đa khoa"},
                {"timeframe": "12 tháng", "assessment": "MMSE + Đánh giá toàn diện", "provider": "Bác sĩ thần kinh"}
            ]
        
        return schedule
    
    def _generate_red_flags(self) -> List[Dict]:
        """Generate red flags to watch for"""
        return [
            {
                "symptom": "Suy giảm nhanh điểm MMSE (>3 điểm trong 6 tháng)",
                "action": "Khám bác sĩ ngay lập tức"
            },
            {
                "symptom": "Thay đổi đột ngột về hành vi hoặc tính cách",
                "action": "Liên hệ bác sĩ trong 24-48 giờ"
            },
            {
                "symptom": "Mất khả năng thực hiện các hoạt động hàng ngày cơ bản",
                "action": "Đánh giá an toàn và hỗ trợ ngay"
            },
            {
                "symptom": "Ảo giác, hoang tưởng, hoặc lú lẫn nghiêm trọng",
                "action": "Tìm kiếm chăm sóc y tế khẩn cấp"
            },
            {
                "symptom": "Ngã hoặc tai nạn do mất định hướng",
                "action": "Đánh giá an toàn và điều chỉnh môi trường"
            }
        ]
    
    def _generate_support_resources(self) -> List[Dict]:
        """Generate support resources"""
        return [
            {
                "type": "Nhóm hỗ trợ",
                "description": "Tham gia nhóm hỗ trợ cho người có suy giảm nhận thức và gia đình",
                "resources": [
                    "Hiệp hội Alzheimer Việt Nam",
                    "Nhóm hỗ trợ địa phương",
                    "Cộng đồng trực tuyến"
                ]
            },
            {
                "type": "Dịch vụ chăm sóc",
                "description": "Các dịch vụ hỗ trợ chăm sóc tại nhà và cộng đồng",
                "resources": [
                    "Dịch vụ chăm sóc tại nhà",
                    "Trung tâm chăm sóc ban ngày",
                    "Dịch vụ tư vấn tâm lý"
                ]
            },
            {
                "type": "Tài liệu giáo dục",
                "description": "Tài liệu và nguồn thông tin về suy giảm nhận thức",
                "resources": [
                    "Sách hướng dẫn cho gia đình",
                    "Website y tế uy tín",
                    "Ứng dụng hỗ trợ nhận thức"
                ]
            }
        ]
    
    def generate_educational_resources(self, results: Dict) -> Dict:
        """Educational Resources Section - TODO: Implement"""
        return {"note": "Section implementation in progress"}
    
    def generate_qa_transcript(self, results: Dict) -> Dict:
        """Q&A Transcript Section"""
        qa_history = results.get("qa_history", []) or []
        
        if not qa_history:
            return {
                "section_title": "Lịch Sử Câu Hỏi và Trả Lời",
                "note": "Không có dữ liệu Q&A history"
            }
        
        # Extract clock drawing if present
        clock_drawing_analysis = self._extract_clock_drawing_analysis(qa_history)
        
        # Get assessment result for performance insights
        assessment_result = results.get("assessment_result", {}) or {}
        
        return {
            "section_title": "Lịch Sử Câu Hỏi và Trả Lời",
            "introduction": self.generate_qa_introduction(),
            "summary": {
                "total_questions": len(qa_history),
                "questions_correct": len([q for q in qa_history if q.get("is_correct", False)]),
                "questions_incorrect": len([q for q in qa_history if not q.get("is_correct", True)]),
                "accuracy_rate": f"{len([q for q in qa_history if q.get('is_correct', False)])/len(qa_history)*100:.1f}%" if qa_history else "N/A",
                "domains_covered": self._extract_domains_covered(qa_history),
                "audio_files_available": self._count_audio_files(qa_history)
            },
            "by_domain": self._organize_qa_by_domain(qa_history),
            "detailed_transcript": self._format_qa_history(qa_history),
            "clock_drawing_analysis": clock_drawing_analysis,
            "performance_insights": self._generate_performance_insights(qa_history, assessment_result)
        }
    
    def generate_qa_introduction(self) -> str:
        """Introduction to Q&A transcript"""
        return """
**Phần này ghi lại chi tiết tất cả các câu hỏi trong bài kiểm tra MMSE và câu trả lời của bạn.**

Tại sao chi tiết này quan trọng?
- **Transparency (Minh bạch)**: Bạn có thể xem lại chính xác những gì đã được hỏi và trả lời
- **Learning (Học hỏi)**: Hiểu được điểm mạnh và điểm cần cải thiện
- **Tracking (Theo dõi)**: So sánh với các lần kiểm tra sau để thấy tiến bộ
- **Clinical Review (Xem xét lâm sàng)**: Bác sĩ có thể xem xét chi tiết để đánh giá chính xác hơn

Mỗi câu hỏi bao gồm:
- 🎙️ **Audio câu hỏi**: Nghe lại câu hỏi được đọc
- 💬 **Câu trả lời văn bản**: Transcript của câu trả lời
- 🎧 **Audio câu trả lời**: Nghe lại giọng nói khi trả lời
- ✅/❌ **Đánh giá**: Đúng hay sai, và giải thích
- 📊 **Điểm số**: Số điểm đạt được cho câu này
- 🖼️ **Hình ảnh** (nếu có): Ví dụ câu vẽ đồng hồ
        """.strip()
    
    def _extract_domains_covered(self, qa_history: List[Dict]) -> List[str]:
        """Extract domains covered in Q&A"""
        domains = set()
        
        for qa in qa_history:
            question = qa.get("question", {}) or {}
            domain = question.get("domain") or question.get("category")
            if domain:
                domains.add(domain)
        
        domain_names = {
            "orientation": "Định hướng",
            "registration": "Ghi nhớ tức thời",
            "attention": "Chú ý",
            "recall": "Gợi nhớ",
            "language": "Ngôn ngữ",
            "visuospatial": "Thị giác-Không gian",
            "executive": "Chức năng điều hành"
        }
        
        return [domain_names.get(d, d) for d in sorted(domains)]
    
    def _count_audio_files(self, qa_history: List[Dict]) -> int:
        """Count available audio files"""
        count = 0
        for qa in qa_history:
            if qa.get("audio_file") or qa.get("answer_audio"):
                count += 1
        return count
    
    def _format_qa_history(self, qa_history: List[Dict]) -> List[Dict]:
        """Format Q&A history for display"""
        formatted = []
        
        for i, qa in enumerate(qa_history, 1):
            question = qa.get("question", {}) or {}
            answer = qa.get("answer", "")
            score = qa.get("score", 0)
            max_score = qa.get("max_score", 1)
            
            formatted.append({
                "question_number": i,
                "question_id": question.get("id", ""),
                "question_text": question.get("text", "") or question.get("question", ""),
                "domain": question.get("domain") or question.get("category", "Khác"),
                "answer": answer,
                "score": score,
                "max_score": max_score,
                "score_percentage": f"{(score/max_score*100):.0f}%" if max_score > 0 else "0%",
                "audio_file": qa.get("audio_file") or qa.get("answer_audio"),
                "timestamp": qa.get("timestamp"),
                "notes": qa.get("notes", "")
            })
        
        return formatted
    
    def _generate_domain_summary(self, qa_history: List[Dict]) -> Dict[str, Dict]:
        """Generate summary by domain"""
        domain_summary = {}
        
        for qa in qa_history:
            question = qa.get("question", {}) or {}
            domain = question.get("domain") or question.get("category", "Khác")
            
            if domain not in domain_summary:
                domain_summary[domain] = {
                    "total_questions": 0,
                    "total_score": 0,
                    "max_score": 0,
                    "questions": []
                }
            
            domain_summary[domain]["total_questions"] += 1
            domain_summary[domain]["total_score"] += qa.get("score", 0)
            domain_summary[domain]["max_score"] += qa.get("max_score", 1)
            domain_summary[domain]["questions"].append({
                "question": question.get("text", ""),
                "answer": qa.get("answer", ""),
                "score": qa.get("score", 0)
            })
        
        # Calculate percentages
        for domain, summary in domain_summary.items():
            if summary["max_score"] > 0:
                summary["percentage"] = f"{(summary['total_score']/summary['max_score']*100):.1f}%"
            else:
                summary["percentage"] = "0%"
        
        return domain_summary
    
    def _organize_qa_by_domain(self, qa_history: List[Dict]) -> List[Dict]:
        """Organize Q&A by cognitive domain with detailed stats"""
        domains = {}
        
        for qa in qa_history:
            question = qa.get("question", {}) or {}
            domain = question.get("domain") or question.get("category", "Unknown")
            
            if domain not in domains:
                domains[domain] = {
                    "domain_name": domain,
                    "domain_name_vi": self._translate_domain_name(domain),
                    "questions": [],
                    "total_questions": 0,
                    "correct_count": 0,
                    "points_earned": 0,
                    "points_possible": 0
                }
            
            domains[domain]["questions"].append(qa)
            domains[domain]["total_questions"] += 1
            if qa.get("is_correct", False):
                domains[domain]["correct_count"] += 1
            domains[domain]["points_earned"] += qa.get("score", 0) or qa.get("points_earned", 0)
            domains[domain]["points_possible"] += qa.get("max_score", 1) or qa.get("points_possible", 1)
        
        # Convert to list and add summary
        result = []
        for domain_key, domain_data in domains.items():
            domain_data["accuracy"] = f"{domain_data['correct_count']/domain_data['total_questions']*100:.0f}%" if domain_data["total_questions"] > 0 else "N/A"
            domain_data["score_display"] = f"{domain_data['points_earned']}/{domain_data['points_possible']}"
            result.append(domain_data)
        
        # Sort by standard MMSE order
        domain_order = ["orientation", "registration", "attention", "executive", "recall", "language", "visuospatial"]
        result.sort(key=lambda x: domain_order.index(x["domain_name"]) if x["domain_name"] in domain_order else 99)
        
        return result
    
    def _translate_domain_name(self, domain: str) -> str:
        """Translate domain name to Vietnamese"""
        translations = {
            "orientation": "Định hướng",
            "registration": "Ghi nhớ tức thời",
            "attention": "Chú ý và Tính toán",
            "executive": "Chức năng điều hành",
            "recall": "Gợi nhớ",
            "language": "Ngôn ngữ",
            "visuospatial": "Thị giác-Không gian"
        }
        return translations.get(domain, domain)
    
    def _extract_clock_drawing_analysis(self, qa_history: List[Dict]) -> Optional[Dict]:
        """Extract and analyze clock drawing if present"""
        clock_qa = None
        for qa in qa_history:
            # Check for clock drawing in various possible locations
            special_data = qa.get("special_data", {}) or {}
            clock_data = qa.get("clock_drawing_data") or special_data.get("clock_drawing")
            
            if clock_data or special_data.get("clock_drawing_image_url") or qa.get("question_id", "").lower().find("clock") >= 0:
                clock_qa = qa
                break
        
        if not clock_qa:
            return None
        
        # Extract clock score details
        clock_score_detail = {}
        if isinstance(clock_qa.get("clock_drawing_data"), dict):
            clock_score_detail = clock_qa["clock_drawing_data"].get("score_detail", {}) or {}
        elif isinstance(clock_qa.get("special_data"), dict):
            clock_score_detail = clock_qa["special_data"].get("clock_score_detail", {}) or {}
        
        total_score = clock_qa.get("score", 0) or clock_qa.get("points_earned", 0)
        max_score = clock_qa.get("max_score", 3)
        
        return {
            "title": "Phân Tích Bài Vẽ Đồng Hồ Chi Tiết",
            "image_url": clock_qa.get("special_data", {}).get("clock_drawing_image_url") if isinstance(clock_qa.get("special_data"), dict) else None,
            "total_score": total_score,
            "max_score": max_score,
            "components": {
                "contour": {
                    "score": clock_score_detail.get("contour", 0),
                    "name": "Vẽ vòng tròn",
                    "explanation": "Khả năng vẽ hình tròn hoàn chỉnh, khép kín",
                    "status": "✅ Đạt" if clock_score_detail.get("contour", 0) == 1 else "❌ Chưa đạt",
                    "clinical_note": "Contour phản ánh visuospatial ability và motor planning"
                },
                "numbers": {
                    "score": clock_score_detail.get("numbers", 0),
                    "name": "Ghi số 1-12",
                    "explanation": "Đặt đúng 12 số, đúng vị trí, đúng thứ tự",
                    "status": "✅ Đạt" if clock_score_detail.get("numbers", 0) == 1 else "❌ Chưa đạt",
                    "clinical_note": "Number placement phản ánh spatial organization và working memory"
                },
                "hands": {
                    "score": clock_score_detail.get("hands", 0),
                    "name": "Vẽ kim đúng giờ",
                    "explanation": "Vẽ 2 kim (giờ và phút) đúng vị trí theo yêu cầu",
                    "status": "✅ Đạt" if clock_score_detail.get("hands", 0) == 1 else "❌ Chưa đạt",
                    "clinical_note": "Hand placement phản ánh executive function và comprehension"
                }
            },
            "interpretation": self._interpret_clock_drawing(clock_score_detail, total_score),
            "research_context": """
**Clock Drawing Test (CDT) trong đánh giá nhận thức:**

CDT là một trong những công cụ screening nhanh và hiệu quả nhất vì:
- Đánh giá nhiều cognitive domains cùng lúc
- Nhanh (2-3 phút), dễ thực hiện
- Sensitivity 85% cho dementia khi kết hợp với MMSE

**Điểm số và ý nghĩa:**
- 3/3: Bình thường - visuospatial và executive function tốt
- 2/3: Borderline - có thể có khó khăn nhẹ, cần theo dõi
- 0-1/3: Bất thường - nên đánh giá thêm

**Citations:**
- Shulman (2000) - "Clock-drawing: is it the ideal cognitive screening test?"
- Mainland & Amodeo (2007) - "Qualitative analysis of clock drawing"
            """.strip()
        }
    
    def _interpret_clock_drawing(self, clock_score_detail: Dict, total_score: int) -> str:
        """Interpret clock drawing performance"""
        if total_score == 3:
            return """
**Kết quả: Xuất sắc (3/3 điểm)**

Bài vẽ đồng hồ hoàn chỉnh và chính xác. Điều này cho thấy:
- ✅ Visuospatial ability (khả năng nhận thức không gian) tốt
- ✅ Executive function (lập kế hoạch, tổ chức) tốt
- ✅ Working memory (nhớ yêu cầu trong khi vẽ) tốt
- ✅ Motor control (kiểm soát vận động tay) tốt
- ✅ Comprehension (hiểu nhiệm vụ) tốt

Clock drawing là một trong những tests nhạy với visuospatial deficits - một dấu hiệu 
sớm của posterior cortical atrophy và Lewy body dementia. Kết quả tốt này là tin đáng mừng.
            """.strip()
        elif total_score == 2:
            return """
**Kết quả: Tốt với một điểm nhỏ cần chú ý (2/3 điểm)**

Bài vẽ đồng hồ gần hoàn chỉnh nhưng có khó khăn ở một phần. Điều này có thể do nervousness, 
motor difficulty, hoặc không quen vẽ.

**Khuyến nghị:**
- Luyện vẽ hình đơn giản (tròn, vuông, ngôi sao)
- Luyện đọc đồng hồ kim và vẽ lại
- Nếu kèm dấu hiệu khác, nên đánh giá visuospatial ability chi tiết hơn
            """.strip()
        elif total_score == 1:
            return """
**Kết quả: Cần chú ý (1/3 điểm)**

Bài vẽ đồng hồ có nhiều khó khăn. Điều này có thể phản ánh:
- ⚠️ Visuospatial deficits (khó nhận thức không gian)
- ⚠️ Executive dysfunction (khó lập kế hoạch, tổ chức)
- ⚠️ Working memory problems (khó giữ nhiệm vụ trong đầu)

**Khuyến nghị:**
- Đánh giá chuyên sâu về visuospatial abilities
- Xem xét làm thêm tests: ROCF (Rey-Osterrieth Complex Figure)
- Nếu có thêm dấu hiệu, cần MRI để đánh giá
            """.strip()
        else:
            return """
**Kết quả: Bất thường đáng kể (0/3 điểm)**

Không thể hoàn thành bài vẽ đồng hồ. Đây là dấu hiệu nghiêm trọng và cần đánh giá ngay:
- ⚠️ Severe visuospatial deficits
- ⚠️ Severe executive dysfunction
- ⚠️ Possible apraxia (mất khả năng thực hiện động tác có mục đích)

**Hành động khẩn cấp:**
- ⚠️ Đánh giá bác sĩ thần kinh NGAY
- Cần MRI não để đánh giá cấu trúc
- Đánh giá toàn diện neuropsychological
            """.strip()
    
    def _generate_performance_insights(self, qa_history: List[Dict], assessment_result: Dict) -> Dict:
        """Generate insights from Q&A performance"""
        # Analyze patterns
        correct_by_domain = {}
        for qa in qa_history:
            question = qa.get("question", {}) or {}
            domain = question.get("domain") or question.get("category", "Unknown")
            if domain not in correct_by_domain:
                correct_by_domain[domain] = {"correct": 0, "total": 0}
            correct_by_domain[domain]["total"] += 1
            if qa.get("is_correct", False):
                correct_by_domain[domain]["correct"] += 1
        
        # Find strengths and weaknesses
        strengths = []
        weaknesses = []
        
        for domain, stats in correct_by_domain.items():
            accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
            domain_vi = self._translate_domain_name(domain)
            
            if accuracy >= 0.9:
                strengths.append(f"{domain_vi} ({stats['correct']}/{stats['total']})")
            elif accuracy < 0.5:
                weaknesses.append(f"{domain_vi} ({stats['correct']}/{stats['total']})")
        
        return {
            "strengths": strengths if strengths else ["Cần cải thiện ở nhiều lĩnh vực"],
            "weaknesses": weaknesses if weaknesses else ["Không có lĩnh vực đặc biệt yếu"],
            "pattern_analysis": self._analyze_error_patterns(qa_history),
            "recommendations": self._generate_qa_recommendations(weaknesses, qa_history)
        }
    
    def _analyze_error_patterns(self, qa_history: List[Dict]) -> List[str]:
        """Analyze error patterns"""
        patterns = []
        
        # Check for orientation errors
        orientation_errors = [qa for qa in qa_history 
                            if (qa.get("question", {}).get("domain") == "orientation" or 
                                qa.get("question", {}).get("category") == "orientation") 
                            and not qa.get("is_correct", True)]
        if orientation_errors:
            patterns.append("⚠️ Mất định hướng thời gian - có thể là dấu hiệu sớm của AD")
        
        # Check for recall errors
        recall_errors = [qa for qa in qa_history 
                        if (qa.get("question", {}).get("domain") == "recall" or 
                            qa.get("question", {}).get("category") == "recall") 
                        and not qa.get("is_correct", True)]
        if recall_errors:
            patterns.append("⚠️ Khó khăn với trí nhớ gần (delayed recall) - dấu hiệu đặc trưng của AD")
        
        # Check for attention errors
        attention_errors = [qa for qa in qa_history 
                          if (qa.get("question", {}).get("domain") == "attention" or 
                              qa.get("question", {}).get("category") == "attention") 
                          and not qa.get("is_correct", True)]
        if len(attention_errors) >= 2:
            patterns.append("⚠️ Khó tập trung và làm phép tính - có thể do vấn đề attention/working memory")
        
        if not patterns:
            patterns.append("✅ Không phát hiện pattern lỗi đặc biệt - lỗi rải rác, không tập trung")
        
        return patterns
    
    def _generate_qa_recommendations(self, weaknesses: List[str], qa_history: List[Dict]) -> List[str]:
        """Generate recommendations based on Q&A performance"""
        recommendations = []
        
        # Based on weaknesses
        if any("Định hướng" in w for w in weaknesses):
            recommendations.extend([
                "🗓️ Luyện nhận biết thời gian: mỗi sáng nói to ngày/tháng/năm hiện tại",
                "📍 Luyện định hướng không gian: nhớ địa chỉ, mô tả đường đi",
                "⏰ Dùng lịch và đồng hồ rõ ràng trong nhà"
            ])
        
        if any("Gợi nhớ" in w or "nhớ" in w.lower() for w in weaknesses):
            recommendations.extend([
                "🧠 Luyện trí nhớ với flashcards: học 3-5 từ mỗi ngày",
                "📝 Luyện nhớ lại thông tin: đọc đoạn văn ngắn rồi kể lại",
                "🎯 Dùng kỹ thuật ghi nhớ: visualization, chunking, association"
            ])
        
        if any("Chú ý" in w for w in weaknesses):
            recommendations.extend([
                "🎯 Luyện tập tập trung: meditation, mindfulness",
                "🔢 Luyện tính toán đơn giản hàng ngày",
                "🧩 Chơi các trò chơi yêu cầu attention: sudoku, find differences"
            ])
        
        if not recommendations:
            recommendations = [
                "✅ Hiệu suất tốt - tiếp tục duy trì hoạt động trí tuệ",
                "📖 Đọc sách, làm ô chữ, trò chơi trí tuệ",
                "👥 Giao tiếp xã hội thường xuyên"
            ]
        
        return recommendations
    
    def _explain_feature_to_user(self, feature: Dict) -> str:
        """Generate user-friendly explanation for each feature"""
        feature_key = feature.get("key", "") or feature.get("name_vi", "")
        feature_name = feature.get("name_vi", "") or feature.get("description", "")
        
        explanations = {
            "ttr": "TTR (Type-Token Ratio) đo lường bao nhiêu % từ bạn nói là từ khác nhau. Ví dụ: nếu bạn nói 100 từ mà có 50 từ khác nhau thì TTR = 0.50. TTR cao = đa dạng từ vựng, TTR thấp = lặp lại nhiều từ.",
            "mattr": "MATTR đo đa dạng từ vựng trong suốt đoạn nói. Khác với TTR thường, MATTR không bị ảnh hưởng bởi độ dài đoạn nói, nên chính xác hơn cho đoạn dài.",
            "mlu": "MLU (Mean Length of Utterance) là độ dài trung bình của câu. Câu dài thường phức tạp hơn và yêu cầu working memory tốt hơn. Giảm MLU = đơn giản hóa ngôn ngữ.",
            "coherence": "Coherence đo mức độ liên kết giữa các ý tưởng. Sử dụng AI để phân tích xem các câu có liên quan đến nhau không. Coherence cao = mạch lạc, coherence thấp = rời rạc.",
            "idea_density": "Idea Density đo bao nhiêu ý tưởng/thông tin trong mỗi 10 từ. Ví dụ: 'Tôi đi chợ mua rau' có nhiều ý hơn 'Tôi đi đến chỗ đó'. Mật độ cao = súc tích, mật độ thấp = dài dòng."
        }
        
        # Try to match by key or name
        for key, explanation in explanations.items():
            if key.lower() in feature_key.lower() or key.lower() in feature_name.lower():
                return explanation
        
        return f"Đây là chỉ số đo lường {feature_name}. Giá trị này phản ánh khả năng sử dụng ngôn ngữ của bạn."
    
    def _generate_linguistic_research_basis(self) -> Dict:
        """Generate research basis for linguistic analysis"""
        return {
            "title": "Cơ Sở Nghiên Cứu - Phân Tích Ngôn Ngữ",
            "summary": """
**Tại sao ngôn ngữ thay đổi trong suy giảm nhận thức?**

Ngôn ngữ là chức năng phức tạp nhất của não bộ, yêu cầu sự phối hợp của nhiều vùng:
- Temporal Lobes: Lưu trữ semantic memory, bị tổn thương sớm trong AD → Anomia
- Frontal Lobes: Executive control của ngôn ngữ, suy giảm → Câu ngắn, đơn giản
- Parietal Lobes: Phonological processing, tổn thương → Paraphasia

**Dấu hiệu ngôn ngữ sớm nhất:**
- Anomia (Word-Finding Difficulty) - Xuất hiện sớm nhất (Hodges et al., 1992)
- Giảm Lexical Diversity - TTR giảm 15-20% so với HC (Ahmed et al., 2013)
- Syntactic Simplification - MLU giảm >30% trong AD (Kemper et al., 2001)
- Semantic Coherence giảm - AUC 0.84 cho HC vs AD (Prud'hommeaux & Roark, 2015)
            """.strip(),
            "key_studies": [
                {
                    "title": "Connected speech as a marker of disease progression in autopsy-proven Alzheimer's disease",
                    "authors": "Ahmed S, et al.",
                    "year": 2013,
                    "journal": "Brain",
                    "finding": "TTR, MLU, và idea density là strongest predictors of AD progression"
                },
                {
                    "title": "Linguistic ability in early life and cognitive function and Alzheimer's disease in late life",
                    "authors": "Snowdon DA, et al.",
                    "year": 1996,
                    "journal": "JAMA",
                    "finding": "Low idea density at age 20 predicts AD 50+ years later"
                },
                {
                    "title": "Linguistic features identify Alzheimer's disease in narrative speech",
                    "authors": "Fraser KC, et al.",
                    "year": 2016,
                    "journal": "Journal of Alzheimer's Disease",
                    "finding": "Achieved 81% accuracy using only linguistic features"
                }
            ]
        }
    
    def generate_multimedia_integration(self, results: Dict) -> Dict:
        """Generate multimedia player configuration and audio analysis"""
        qa_history = results.get("qa_history", []) or []
        
        return {
            "section_title": "Tích Hợp Đa Phương Tiện",
            "multimedia_config": self._generate_multimedia_player_config(qa_history),
            "audio_analysis_insights": self._generate_audio_analysis_insights(qa_history)
        }
    
    def _generate_multimedia_player_config(self, qa_history: List[Dict]) -> Dict:
        """Generate configuration for multimedia players in frontend"""
        audio_files = []
        image_files = []
        
        for qa in qa_history:
            question = qa.get("question", {}) or {}
            
            # Question audio
            question_audio = qa.get("question_audio_url") or qa.get("question_audio")
            if question_audio:
                audio_files.append({
                    "type": "question",
                    "question_id": question.get("id", ""),
                    "url": question_audio,
                    "label": f"Câu hỏi: {question.get('text', '')[:50]}...",
                    "duration": qa.get("question_duration", None)
                })
            
            # Answer audio
            answer_audio = qa.get("user_answer_audio_url") or qa.get("answer_audio") or qa.get("audio_file")
            if answer_audio:
                audio_files.append({
                    "type": "answer",
                    "question_id": question.get("id", ""),
                    "url": answer_audio,
                    "label": f"Trả lời: {qa.get('answer', '')[:50]}...",
                    "duration": qa.get("answer_duration", None),
                    "transcript": qa.get("answer", "")
                })
            
            # Clock drawing image
            special_data = qa.get("special_data", {}) or {}
            clock_image = special_data.get("clock_drawing_image_url") or qa.get("clock_drawing_image")
            if clock_image:
                image_files.append({
                    "type": "clock_drawing",
                    "question_id": question.get("id", ""),
                    "url": clock_image,
                    "label": "Bài vẽ đồng hồ",
                    "score": qa.get("score", 0) or qa.get("points_earned", 0),
                    "max_score": qa.get("max_score", 3),
                    "components": special_data.get("clock_score_detail", {})
                })
        
        return {
            "audio_files": audio_files,
            "image_files": image_files,
            "player_settings": {
                "show_waveform": True,
                "show_transcript": True,
                "playback_speed_options": [0.75, 1.0, 1.25, 1.5],
                "default_speed": 1.0
            }
        }
    
    def _generate_audio_analysis_insights(self, qa_history: List[Dict]) -> Optional[Dict]:
        """Generate insights from audio recordings"""
        answer_audios = [qa for qa in qa_history 
                        if qa.get("user_answer_audio_url") or qa.get("answer_audio") or qa.get("audio_file")]
        
        if not answer_audios:
            return None
        
        # Calculate average response time
        durations = [qa.get("answer_duration", 0) for qa in answer_audios if qa.get("answer_duration")]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Calculate words per minute from durations and word counts
        wpm_values = []
        for qa in answer_audios:
            duration = qa.get("answer_duration", 0)
            answer_text = qa.get("answer", "") or ""
            word_count = len(answer_text.split()) if answer_text else 0
            if duration > 0:
                wpm = (word_count / duration) * 60
                wpm_values.append(wpm)
        
        avg_wpm = sum(wpm_values) / len(wpm_values) if wpm_values else 0
        
        return {
            "total_recordings": len(answer_audios),
            "average_response_duration": f"{avg_duration:.1f} giây",
            "average_words_per_minute": f"{avg_wpm:.0f} từ/phút",
            "interpretation": self._interpret_audio_metrics(avg_duration, avg_wpm),
            "note": "Các chỉ số này được tính từ audio recordings và có thể hơi khác so với phân tích acoustic features chi tiết (eGeMAPS)"
        }
    
    def _interpret_audio_metrics(self, avg_duration: float, avg_wpm: float) -> str:
        """Interpret audio metrics"""
        interpretation = []
        
        # Interpret duration
        if avg_duration < 2:
            interpretation.append("✅ Trả lời nhanh - phản xạ nhận thức tốt")
        elif avg_duration < 5:
            interpretation.append("✅ Thời gian trả lời bình thường")
        elif avg_duration < 10:
            interpretation.append("⚠️ Trả lời hơi chậm - có thể cần thời gian suy nghĩ")
        else:
            interpretation.append("⚠️ Trả lời chậm - có thể do khó tìm từ hoặc chậm xử lý")
        
        # Interpret WPM
        if avg_wpm >= 120:
            interpretation.append("✅ Tốc độ nói bình thường đến nhanh")
        elif avg_wpm >= 80:
            interpretation.append("✅ Tốc độ nói bình thường")
        elif avg_wpm >= 60:
            interpretation.append("⚠️ Tốc độ nói hơi chậm - cần theo dõi")
        else:
            interpretation.append("⚠️ Tốc độ nói chậm đáng kể - cần đánh giá thêm")
        
        return " | ".join(interpretation)
    
    def _synthesize_overall_assessment(
        self,
        assessment_result: Dict,
        acoustic: Dict,
        linguistic: Dict,
        shap_explanation: Dict
    ) -> Dict:
        """Synthesize findings from all modalities"""
        mmse_score = assessment_result.get("adjusted_score", 0) or assessment_result.get("raw_score", 0)
        mmse_classification = assessment_result.get("classification", "Unknown")
        
        # Calculate abnormal rates
        acoustic_features = acoustic.get("features", []) or []
        acoustic_abnormal_count = len([f for f in acoustic_features if f.get("severity") not in ["normal", "borderline"]])
        acoustic_abnormal_rate = (acoustic_abnormal_count / len(acoustic_features) * 100) if acoustic_features else 0
        
        linguistic_features = linguistic.get("features", []) or []
        linguistic_abnormal_count = len([f for f in linguistic_features if f.get("severity") not in ["normal", "borderline"]])
        linguistic_abnormal_rate = (linguistic_abnormal_count / len(linguistic_features) * 100) if linguistic_features else 0
        
        clinical_interp = shap_explanation.get("clinical_interpretation", {}) or {}
        risk_level = clinical_interp.get("overall_risk_level", "Không xác định")
        
        # Determine concordance (will implement helper next)
        concordance = self._assess_concordance(
            mmse_score,
            acoustic_abnormal_rate,
            linguistic_abnormal_rate,
            risk_level
        )
        
        # Determine overall status (will implement helper next)
        overall_status = self._determine_overall_status(
            mmse_score,
            acoustic_abnormal_rate,
            linguistic_abnormal_rate,
            risk_level
        )
        
        return {
            "overall_status": overall_status["status"],
            "status_color": overall_status["color"],
            "confidence_level": overall_status["confidence"],
            "summary_statement": self._generate_summary_statement(
                mmse_score,
                mmse_classification,
                acoustic_abnormal_rate,
                linguistic_abnormal_rate,
                risk_level
            ),
            "concordance": concordance,
            "key_findings": self._extract_key_clinical_findings(
                assessment_result, acoustic, linguistic, shap_explanation
            ),
            "comparison_to_norms": self._generate_comparison_to_norms(
                assessment_result, acoustic, linguistic
            )
        }
    
    def _assess_concordance(
        self,
        mmse_score: float,
        acoustic_abnormal_rate: float,
        linguistic_abnormal_rate: float,
        risk_level: str
    ) -> Dict:
        """Assess agreement between different assessment modalities"""
        # Classify each modality
        mmse_status = "normal" if mmse_score >= 27 else "borderline" if mmse_score >= 24 else "impaired"
        acoustic_status = "normal" if acoustic_abnormal_rate < 15 else "borderline" if acoustic_abnormal_rate < 30 else "impaired"
        linguistic_status = "normal" if linguistic_abnormal_rate < 15 else "borderline" if linguistic_abnormal_rate < 30 else "impaired"
        risk_status = "normal" if risk_level in ["Bình thường", "Nguy cơ thấp"] else "borderline" if risk_level == "Nguy cơ trung bình" else "impaired"
        
        statuses = [mmse_status, acoustic_status, linguistic_status, risk_status]
        
        # Check concordance
        unique_statuses = len(set(statuses))
        if unique_statuses == 1:
            concordance_level = "Cao"
            interpretation = f"Tất cả các phương pháp đánh giá đều cho kết quả nhất quán ({mmse_status}). Điều này tăng độ tin cậy của kết luận."
        elif unique_statuses == 2:
            concordance_level = "Trung bình"
            interpretation = "Có một số khác biệt giữa các phương pháp đánh giá. Điều này không bất thường và có thể phản ánh các khía cạnh khác nhau của nhận thức."
        else:
            concordance_level = "Thấp"
            interpretation = "Các phương pháp đánh giá cho kết quả khá khác nhau. Điều này cho thấy profile nhận thức phức tạp và cần đánh giá thêm để làm rõ."
        
        return {
            "level": concordance_level,
            "interpretation": interpretation,
            "details": {
                "mmse": {"status": mmse_status, "metric": f"{mmse_score}/30"},
                "acoustic": {"status": acoustic_status, "metric": f"{acoustic_abnormal_rate:.1f}% bất thường"},
                "linguistic": {"status": linguistic_status, "metric": f"{linguistic_abnormal_rate:.1f}% bất thường"},
                "risk_ai": {"status": risk_status, "metric": risk_level}
            },
            "clinical_note": self._explain_concordance_clinically(unique_statuses, concordance_level)
        }
    
    def _explain_concordance_clinically(self, unique_statuses: int, concordance_level: str) -> str:
        """Explain concordance from clinical perspective"""
        if concordance_level == "Cao":
            return """
**Giải thích lâm sàng:**
Khi tất cả các phương pháp đánh giá cho kết quả nhất quán, đây là bằng chứng mạnh. 
Điều này giảm khả năng false positive (báo sai có vấn đề) hoặc false negative (bỏ sót vấn đề).
            """.strip()
        elif concordance_level == "Trung bình":
            return """
**Giải thích lâm sàng:**
Sự không nhất quán một phần có thể do:
- **Các domain khác nhau bị ảnh hưởng khác nhau:** Ví dụ MMSE tốt nhưng speech analysis phát hiện vấn đề → có thể suy giảm nhẹ chưa ảnh hưởng điểm MMSE
- **Sensitivity khác nhau:** Speech/language analysis thường nhạy hơn với early changes
- **Test conditions:** Nervousness có thể ảnh hưởng speech nhưng không ảnh hưởng MMSE nhiều

Khuyến nghị: Theo dõi sát hơn và kiểm tra lại sau 3-6 tháng để xác nhận xu hướng.
            """.strip()
        else:
            return """
**Giải thích lâm sàng:**
Sự khác biệt lớn giữa các modalities đòi hỏi đánh giá kỹ hơn:
- **Possible MCI with uneven cognitive profile:** Một số domains bị ảnh hưởng, một số còn tốt
- **Test validity concerns:** Có thể có yếu tố confounding (hearing loss, depression, medication)
- **Need for comprehensive evaluation:** Nên làm neuropsychological battery đầy đủ

Khuyến nghị: Đánh giá chuyên sâu với neuropsychologist để làm rõ pattern.
            """.strip()
    
    def _determine_overall_status(
        self,
        mmse_score: float,
        acoustic_abnormal_rate: float,
        linguistic_abnormal_rate: float,
        risk_level: str
    ) -> Dict:
        """Determine overall clinical status"""
        # Weighted scoring
        mmse_weight = 0.4
        acoustic_weight = 0.3
        linguistic_weight = 0.3
        
        # Convert to 0-100 scale
        mmse_score_normalized = (mmse_score / 30) * 100
        acoustic_score_normalized = 100 - acoustic_abnormal_rate
        linguistic_score_normalized = 100 - linguistic_abnormal_rate
        
        # Calculate weighted average
        composite_score = (
            mmse_score_normalized * mmse_weight +
            acoustic_score_normalized * acoustic_weight +
            linguistic_score_normalized * linguistic_weight
        )
        
        # Determine status
        if composite_score >= 85:
            return {
                "status": "Nhận thức bình thường",
                "color": "green",
                "confidence": "Cao",
                "composite_score": composite_score
            }
        elif composite_score >= 75:
            return {
                "status": "Nhận thức tốt với một vài điểm nhỏ",
                "color": "lightgreen",
                "confidence": "Trung bình-Cao",
                "composite_score": composite_score
            }
        elif composite_score >= 65:
            return {
                "status": "Nguy cơ nhẹ - Cần theo dõi",
                "color": "yellow",
                "confidence": "Trung bình",
                "composite_score": composite_score
            }
        elif composite_score >= 50:
            return {
                "status": "Suy giảm nhận thức nhẹ - Cần can thiệp",
                "color": "orange",
                "confidence": "Trung bình-Cao",
                "composite_score": composite_score
            }
        else:
            return {
                "status": "Suy giảm nhận thức đáng kể - Cần đánh giá khẩn",
                "color": "red",
                "confidence": "Cao",
                "composite_score": composite_score
            }
    
    def _generate_summary_statement(
        self,
        mmse_score: float,
        mmse_classification: str,
        acoustic_abnormal_rate: float,
        linguistic_abnormal_rate: float,
        risk_level: str
    ) -> str:
        """Generate physician-style summary statement"""
        # Start with MMSE
        statement = f"Người được đánh giá đạt {mmse_score}/30 điểm MMSE (sau điều chỉnh học vấn), "
        statement += f"được phân loại là **{mmse_classification}**. "
        
        # Add speech/language findings
        if acoustic_abnormal_rate < 15 and linguistic_abnormal_rate < 15:
            statement += "Phân tích giọng nói và ngôn ngữ không phát hiện bất thường đáng kể, hỗ trợ đánh giá nhận thức bình thường. "
        elif acoustic_abnormal_rate >= 30 or linguistic_abnormal_rate >= 30:
            statement += f"Tuy nhiên, phân tích giọng nói phát hiện {acoustic_abnormal_rate:.0f}% đặc trưng âm thanh bất thường và "
            statement += f"{linguistic_abnormal_rate:.0f}% đặc trưng ngôn ngữ bất thường, cho thấy có thể có suy giảm tinh tế chưa phản ánh rõ trong điểm MMSE. "
        else:
            statement += f"Phân tích giọng nói phát hiện một số bất thường nhẹ ({acoustic_abnormal_rate:.0f}% acoustic, {linguistic_abnormal_rate:.0f}% linguistic), "
            statement += "đề xuất cần theo dõi trong các lần kiểm tra tiếp theo. "
        
        # Add AI risk assessment
        statement += f"Phân tích AI xếp mức độ nguy cơ ở **{risk_level}**. "
        
        # Conclusion
        if mmse_score >= 27 and acoustic_abnormal_rate < 15 and linguistic_abnormal_rate < 15:
            statement += "Tổng thể, các chỉ số cho thấy chức năng nhận thức đang được duy trì tốt."
        elif mmse_score >= 24:
            statement += "Cần theo dõi định kỳ để đánh giá xu hướng thay đổi theo thời gian."
        else:
            statement += "Khuyến nghị đánh giá chuyên sâu hơn với bác sĩ thần kinh hoặc tâm lý lâm sàng."
        
        return statement
    
    def _extract_key_clinical_findings(
        self,
        assessment_result: Dict,
        acoustic: Dict,
        linguistic: Dict,
        shap_explanation: Dict
    ) -> List[Dict]:
        """Extract most clinically significant findings - TODO: Full implementation"""
        findings = []
        
        # MMSE domain findings
        domain_scores = assessment_result.get("domain_scores", {}) or {}
        for domain, scores in domain_scores.items():
            if isinstance(scores, dict):
                score = scores.get("score", 0)
                max_score = scores.get("max", 1)
                percentage = (score / max_score * 100) if max_score > 0 else 0
                if percentage < 75:
                    findings.append({
                        "category": "MMSE",
                        "domain": domain,
                        "finding": f"{self._translate_domain_name(domain)}: {score}/{max_score} ({percentage:.0f}%)",
                        "severity": "severe" if percentage < 50 else "moderate"
                    })
        
        return findings[:10]  # Return top 10
    
    def _generate_comparison_to_norms(
        self,
        assessment_result: Dict,
        acoustic: Dict,
        linguistic: Dict
    ) -> Dict:
        """Compare to population norms - TODO: Full implementation"""
        mmse_score = assessment_result.get("adjusted_score", 0) or assessment_result.get("raw_score", 0)
        
        # Simplified percentile
        if mmse_score >= 29:
            percentile = 95
        elif mmse_score >= 27:
            percentile = 75
        elif mmse_score >= 24:
            percentile = 50
        else:
            percentile = 25
        
        return {
            "mmse_percentile": {
                "percentile": percentile,
                "interpretation": f"Cao hơn {percentile}% dân số cùng độ tuổi và học vấn" if percentile >= 50 
                                else f"Thấp hơn {100-percentile}% dân số cùng độ tuổi và học vấn"
            },
            "speech_comparison": "So sánh với dân số chuẩn",
            "interpretation": "So với dân số cùng độ tuổi và học vấn"
        }
    
    def _generate_cognitive_profile(self, assessment_result: Dict, qa_history: List[Dict]) -> Dict:
        """Generate detailed cognitive profile across domains"""
        domain_scores = assessment_result.get("domain_scores", {}) or {}
        
        profile = {
            "title": "Profile Nhận Thức Chi Tiết",
            "domains": [],
            "strengths": [],
            "weaknesses": [],
            "pattern_interpretation": ""
        }
        
        # Analyze each domain
        for domain, scores in domain_scores.items():
            if not isinstance(scores, dict):
                continue
                
            score = scores.get("score", 0)
            max_score = scores.get("max", 1)
            percentage = (score / max_score * 100) if max_score > 0 else 0
            
            domain_profile = {
                "domain": self._translate_domain_name(domain),
                "score": f"{score}/{max_score}",
                "percentage": percentage,
                "status": self._classify_domain_performance(percentage),
                "color": self._get_performance_color(percentage),
                "description": self._get_domain_description(domain),
                "clinical_note": self._get_domain_clinical_note(domain, percentage)
            }
            
            profile["domains"].append(domain_profile)
            
            # Identify strengths and weaknesses
            if percentage >= 90:
                profile["strengths"].append(self._translate_domain_name(domain))
            elif percentage < 75:
                profile["weaknesses"].append(self._translate_domain_name(domain))
        
        # Generate pattern interpretation
        profile["pattern_interpretation"] = self._interpret_cognitive_pattern(profile["domains"])
        
        return profile
    
    def _classify_domain_performance(self, percentage: float) -> str:
        """Classify performance level"""
        if percentage >= 90:
            return "Xuất sắc"
        elif percentage >= 80:
            return "Tốt"
        elif percentage >= 70:
            return "Trung bình"
        elif percentage >= 50:
            return "Dưới trung bình"
        else:
            return "Kém"
    
    def _get_performance_color(self, percentage: float) -> str:
        """Get color for performance level"""
        if percentage >= 90:
            return "green"
        elif percentage >= 80:
            return "lightgreen"
        elif percentage >= 70:
            return "yellow"
        elif percentage >= 50:
            return "orange"
        else:
            return "red"
    
    def _get_domain_description(self, domain: str) -> str:
        """Get description for each domain"""
        descriptions = {
            "orientation": "Biết rõ thời gian (ngày, tháng, năm) và không gian (nơi đang ở)",
            "registration": "Nghe và nhớ ngay lập tức thông tin mới",
            "attention": "Tập trung và thực hiện phép tính đơn giản",
            "executive": "Lập kế hoạch, suy luận trừu tượng, linh hoạt tư duy",
            "recall": "Nhớ lại thông tin sau một khoảng thời gian",
            "language": "Đặt tên, lặp lại, hiểu và thực hiện lệnh",
            "visuospatial": "Nhận thức không gian và vẽ hình"
        }
        return descriptions.get(domain, "")
    
    def _get_domain_clinical_note(self, domain: str, percentage: float) -> str:
        """Get clinical note for domain performance"""
        if percentage >= 90:
            return f"{self._translate_domain_name(domain)} hoạt động tốt, không có vấn đề"
        
        clinical_notes = {
            "orientation": "Mất định hướng là dấu hiệu sớm của Alzheimer's disease",
            "registration": "Immediate memory thường còn tốt cho đến giai đoạn muộn",
            "attention": "Attention deficits thường thấy trong vascular dementia và Lewy body dementia",
            "executive": "Executive dysfunction là dấu hiệu sớm của MCI và predictor mạnh của chuyển đổi MCI→AD",
            "recall": "Delayed recall là marker quan trọng nhất của Alzheimer's disease",
            "language": "Language deficits (anomia) xuất hiện sớm trong AD",
            "visuospatial": "Visuospatial deficits đặc trưng cho posterior cortical atrophy và Lewy body dementia"
        }
        
        note = clinical_notes.get(domain, "")
        if percentage < 50:
            return f"⚠️ Suy giảm đáng kể. {note}"
        elif percentage < 75:
            return f"⚠️ Có khó khăn. {note}"
        else:
            return f"Hơi yếu. {note}"
    
    def _interpret_cognitive_pattern(self, domains: List[Dict]) -> str:
        """Interpret the pattern of cognitive strengths and weaknesses"""
        # Get performance levels
        performances = {d["domain"]: d["percentage"] for d in domains}
        
        # Check for specific patterns
        recall_pct = performances.get("Gợi nhớ", 100)
        orientation_pct = performances.get("Định hướng", 100)
        executive_pct = performances.get("Chức năng điều hành", 100)
        visuospatial_pct = performances.get("Thị giác-Không gian", 100)
        
        # Alzheimer's Disease pattern
        if recall_pct < 70 or orientation_pct < 80:
            return """
**Pattern: Suy giảm trí nhớ + Mất định hướng**
Đây là pattern điển hình của **Alzheimer's Disease**. Recall (gợi nhớ) và orientation (định hướng) 
bị ảnh hưởng sớm nhất trong AD. Cần đánh giá chuyên sâu hơn.
            """.strip()
        
        # Executive + Attention pattern
        elif executive_pct < 70 and performances.get("Chú ý", 100) < 70:
            return """
**Pattern: Suy giảm chức năng điều hành + Chú ý**
Pattern này gợi ý vấn đề ở **frontal-subcortical circuits**. Có thể thấy trong:
- Vascular dementia (do stroke hoặc vấn đề tim mạch)
- Frontotemporal dementia
- Parkinson's disease dementia
Cần đánh giá thêm về yếu tố nguy cơ tim mạch.
            """.strip()
        
        # Visuospatial pattern
        elif visuospatial_pct < 70:
            return """
**Pattern: Suy giảm thị giác-không gian**
Visuospatial deficits đặc trưng cho:
- **Posterior Cortical Atrophy (PCA)** - variant của AD
- **Lewy Body Dementia**
Cần theo dõi các triệu chứng khác như visual hallucinations, motor problems.
            """.strip()
        
        # All good
        elif all(p >= 85 for p in performances.values()):
            return """
**Pattern: Hiệu suất đồng đều tốt**
Tất cả các domains đều hoạt động tốt. Đây là dấu hiệu tích cực cho thấy không có 
suy giảm nhận thức đáng kể ở bất kỳ lĩnh vực nào.
            """.strip()
        
        # Uneven pattern
        else:
            return """
**Pattern: Suy giảm không đồng đều**
Một số domains tốt hơn những domains khác. Pattern này có thể phản ánh:
- Giai đoạn sớm của suy giảm nhận thức (một số domains bị ảnh hưởng trước)
- Ảnh hưởng từ yếu tố khác (giáo dục, nghề nghiệp, sức khỏe)
Cần theo dõi để xem pattern phát triển như thế nào theo thời gian.
            """.strip()
    
    def _generate_speech_language_profile(self, acoustic: Dict, linguistic: Dict) -> Dict:
        """Generate speech and language profile"""
        return {
            "title": "Profile Giọng Nói và Ngôn Ngữ",
            "acoustic_summary": self._summarize_acoustic_profile(acoustic),
            "linguistic_summary": self._summarize_linguistic_profile(linguistic),
            "integration": self._integrate_speech_language_findings(acoustic, linguistic),
            "clinical_interpretation": self._interpret_speech_language_clinically(acoustic, linguistic)
        }
    
    def _summarize_acoustic_profile(self, acoustic: Dict) -> Dict:
        """Summarize acoustic findings by category"""
        by_category = acoustic.get("by_category", {}) or {}
        
        summary = {
            "categories": [],
            "overall_status": ""
        }
        
        for category, features in by_category.items():
            if not isinstance(features, list):
                continue
            abnormal = [f for f in features if f.get("severity") not in ["normal", "borderline"]]
            
            summary["categories"].append({
                "name": category,
                "total": len(features),
                "abnormal": len(abnormal),
                "status": "Bình thường" if not abnormal else "Cần chú ý" if len(abnormal) > len(features)/2 else "Có một vài điểm"
            })
        
        total_abnormal = len([f for f in acoustic.get("features", []) if f.get("severity") not in ["normal", "borderline"]])
        total_features = len(acoustic.get("features", []))
        
        if total_features > 0:
            abnormal_rate = total_abnormal / total_features
            if abnormal_rate < 0.15:
                summary["overall_status"] = "✅ Đặc trưng âm thanh tốt"
            elif abnormal_rate < 0.30:
                summary["overall_status"] = "⚠️ Có một số bất thường về âm thanh"
            else:
                summary["overall_status"] = "⚠️ Nhiều bất thường về âm thanh - cần đánh giá thêm"
        else:
            summary["overall_status"] = "Không có dữ liệu"
        
        return summary
    
    def _summarize_linguistic_profile(self, linguistic: Dict) -> Dict:
        """Summarize linguistic findings by category"""
        by_category = linguistic.get("by_category", {}) or {}
        
        summary = {
            "categories": [],
            "overall_status": ""
        }
        
        for category, features in by_category.items():
            if not isinstance(features, list):
                continue
            abnormal = [f for f in features if f.get("severity") not in ["normal", "borderline"]]
            
            summary["categories"].append({
                "name": category,
                "total": len(features),
                "abnormal": len(abnormal),
                "status": "Bình thường" if not abnormal else "Cần chú ý" if len(abnormal) > len(features)/2 else "Có một vài điểm"
            })
        
        total_abnormal = len([f for f in linguistic.get("features", []) if f.get("severity") not in ["normal", "borderline"]])
        total_features = len(linguistic.get("features", []))
        
        if total_features > 0:
            abnormal_rate = total_abnormal / total_features
            if abnormal_rate < 0.15:
                summary["overall_status"] = "✅ Sử dụng ngôn ngữ tốt"
            elif abnormal_rate < 0.30:
                summary["overall_status"] = "⚠️ Có một số khó khăn về ngôn ngữ"
            else:
                summary["overall_status"] = "⚠️ Nhiều khó khăn về ngôn ngữ - cần đánh giá thêm"
        else:
            summary["overall_status"] = "Không có dữ liệu"
        
        return summary
    
    def _integrate_speech_language_findings(self, acoustic: Dict, linguistic: Dict) -> str:
        """Integrate acoustic and linguistic findings"""
        acoustic_features = acoustic.get("features", []) or []
        linguistic_features = linguistic.get("features", []) or []
        
        acoustic_abnormal = len([f for f in acoustic_features if f.get("severity") not in ["normal", "borderline"]])
        linguistic_abnormal = len([f for f in linguistic_features if f.get("severity") not in ["normal", "borderline"]])
        
        acoustic_rate = (acoustic_abnormal / len(acoustic_features) * 100) if acoustic_features else 0
        linguistic_rate = (linguistic_abnormal / len(linguistic_features) * 100) if linguistic_features else 0
        
        if acoustic_rate < 15 and linguistic_rate < 15:
            return "Giọng nói và ngôn ngữ hài hòa, cả hai đều tốt. Đây là dấu hiệu tích cực."
        elif acoustic_rate > 30 and linguistic_rate < 15:
            return "Acoustic abnormalities WITHOUT linguistic problems. Pattern này gợi ý vấn đề về motor control hơn là cognitive decline."
        elif acoustic_rate < 15 and linguistic_rate > 30:
            return "Linguistic abnormalities WITHOUT acoustic problems. Pattern này gợi ý vấn đề về language processing/cognitive hơn là motor."
        else:
            return "Cả acoustic và linguistic đều có vấn đề. Cần đánh giá toàn diện."
    
    def _interpret_speech_language_clinically(self, acoustic: Dict, linguistic: Dict) -> str:
        """Clinical interpretation of speech/language profile"""
        acoustic_features = acoustic.get("features", []) or []
        linguistic_features = linguistic.get("features", []) or []
        
        severe_acoustic = [f for f in acoustic_features if f.get("severity") == "severe"]
        severe_linguistic = [f for f in linguistic_features if f.get("severity") == "severe"]
        
        interpretation = "**Giải thích lâm sàng:**\n\n"
        
        if severe_acoustic:
            interpretation += f"Có {len(severe_acoustic)} đặc trưng âm thanh bất thường nghiêm trọng.\n"
        
        if severe_linguistic:
            interpretation += f"Có {len(severe_linguistic)} đặc trưng ngôn ngữ bất thường nghiêm trọng.\n"
        
        if not severe_acoustic and not severe_linguistic:
            interpretation += "Không có bất thường nghiêm trọng. Các chỉ số trong giới hạn chấp nhận được.\n"
        
        return interpretation
    
    def _generate_risk_stratification(
        self,
        assessment_result: Dict,
        acoustic: Dict,
        linguistic: Dict,
        shap_explanation: Dict
    ) -> Dict:
        """Stratify risk level and provide evidence"""
        clinical_interp = shap_explanation.get("clinical_interpretation", {}) or {}
        risk_level = clinical_interp.get("overall_risk_level", "Không xác định")
        
        shap_analysis = shap_explanation.get("shap_analysis", {}) or {}
        
        return {
            "risk_level": risk_level,
            "risk_color": clinical_interp.get("risk_color", "gray"),
            "confidence": clinical_interp.get("confidence", 0),
            "evidence": self._compile_risk_evidence(assessment_result, acoustic, linguistic, shap_explanation),
            "risk_factors_count": len(shap_analysis.get("risk_factors", [])),
            "protective_factors_count": len(shap_analysis.get("protective_factors", [])),
            "interpretation": self._interpret_risk_level(risk_level, clinical_interp)
        }
    
    def _compile_risk_evidence(
        self,
        assessment_result: Dict,
        acoustic: Dict,
        linguistic: Dict,
        shap_explanation: Dict
    ) -> List[str]:
        """Compile evidence supporting risk assessment"""
        evidence = []
        
        # MMSE evidence
        mmse_score = assessment_result.get("adjusted_score", 0) or assessment_result.get("raw_score", 0)
        if mmse_score < 24:
            evidence.append(f"❌ Điểm MMSE thấp ({mmse_score}/30) - nguy cơ cao")
        elif mmse_score < 27:
            evidence.append(f"⚠️ Điểm MMSE borderline ({mmse_score}/30) - nguy cơ trung bình")
        else:
            evidence.append(f"✅ Điểm MMSE tốt ({mmse_score}/30) - yếu tố bảo vệ")
        
        # Acoustic evidence
        acoustic_features = acoustic.get("features", []) or []
        acoustic_abnormal = len([f for f in acoustic_features if f.get("severity") not in ["normal", "borderline"]])
        acoustic_total = len(acoustic_features)
        if acoustic_total > 0:
            abnormal_rate = acoustic_abnormal / acoustic_total
            if abnormal_rate > 0.30:
                evidence.append(f"❌ Nhiều bất thường acoustic ({acoustic_abnormal}/{acoustic_total}) - nguy cơ")
            elif abnormal_rate > 0.15:
                evidence.append(f"⚠️ Một số bất thường acoustic - cần theo dõi")
            else:
                evidence.append(f"✅ Acoustic features tốt - yếu tố bảo vệ")
        
        # Linguistic evidence
        linguistic_features = linguistic.get("features", []) or []
        linguistic_abnormal = len([f for f in linguistic_features if f.get("severity") not in ["normal", "borderline"]])
        linguistic_total = len(linguistic_features)
        if linguistic_total > 0:
            abnormal_rate = linguistic_abnormal / linguistic_total
            if abnormal_rate > 0.30:
                evidence.append(f"❌ Nhiều bất thường linguistic ({linguistic_abnormal}/{linguistic_total}) - nguy cơ")
            elif abnormal_rate > 0.15:
                evidence.append(f"⚠️ Một số bất thường linguistic - cần theo dõi")
            else:
                evidence.append(f"✅ Linguistic features tốt - yếu tố bảo vệ")
        
        # Top SHAP risk factors
        shap_analysis = shap_explanation.get("shap_analysis", {}) or {}
        risk_factors = shap_analysis.get("risk_factors", [])[:3]
        if risk_factors:
            evidence.append("**Top risk factors from AI:**")
            for factor in risk_factors:
                feature_name = factor.get("feature_name_vi") or factor.get("feature", "N/A")
                shap_value = factor.get("shap_value", 0) or factor.get("absolute_importance", 0)
                evidence.append(f"  - {feature_name} (SHAP: +{shap_value:.3f})")
        
        return evidence
    
    def _interpret_risk_level(self, risk_level: str, clinical_interp: Dict) -> str:
        """Interpret risk level in context"""
        interpretations = {
            "Bình thường": """
Nguy cơ thấp:
Các chỉ số cho thấy chức năng nhận thức đang được duy trì tốt. Nguy cơ suy giảm nhận thức
ở mức bình thường cho độ tuổi (khoảng 1-2%/năm sau 65 tuổi). Tiếp tục duy trì lối sống lành mạnh
và kiểm tra định kỳ.
            """.strip(),
            "Nguy cơ thấp": """
Nguy cơ thấp:
Có một vài dấu hiệu nhỏ nhưng tổng thể vẫn tốt. Nguy cơ tiến triển thành MCI khoảng 3-5%/năm.
Đây là thời điểm tốt để tăng cường các biện pháp dự phòng.
            """.strip(),
            "Nguy cơ trung bình": """
Nguy cơ trung bình:
Có một số dấu hiệu cần chú ý. Nguy cơ tiến triển thành MCI khoảng 10-15%/năm.
Cần theo dõi sát và áp dụng can thiệp sớm. Với các biện pháp phù hợp, có thể làm chậm
hoặc ngăn chặn tiến triển.
            """.strip(),
            "Nguy cơ cao": """
Nguy cơ cao:
Có nhiều dấu hiệu đáng lo ngại. Nguy cơ tiến triển thành dementia trong 3-5 năm là cao (>20%).
Cần đánh giá chuyên sâu và can thiệp tích cực NGAY. Can thiệp sớm có thể tạo ra sự khác biệt lớn.
            """.strip()
        }
        return interpretations.get(risk_level, "Cần đánh giá thêm để xác định mức độ nguy cơ.")
    
    def _generate_differential_considerations(self, results: Dict) -> Dict:
        """Generate differential diagnostic considerations"""
        assessment_result = results.get("assessment_result", {}) or {}
        domain_scores = assessment_result.get("domain_scores", {}) or {}
        mmse_score = assessment_result.get("adjusted_score", 0) or assessment_result.get("raw_score", 0)
        
        return {
            "title": "Các Chẩn Đoán Cần Xem Xét (Differential Diagnosis)",
            "note": """
Lưu ý quan trọng:
Phân tích này KHÔNG phải là chẩn đoán y tế. Chỉ có bác sĩ có chuyên môn mới có thể đưa ra chẩn đoán chính thức.
Phần này chỉ liệt kê các khả năng cần xem xét dựa trên pattern của findings.
            """.strip(),
            "considerations": self._generate_differential_list(domain_scores, mmse_score),
            "next_steps": """
Bước tiếp theo:
Nếu có dấu hiệu suy giảm nhận thức, bác sĩ sẽ cần:
- Lấy tiền sử bệnh chi tiết
- Khám lâm sàng thần kinh
- Xét nghiệm máu (loại trừ thiếu vitamin B12, thyroid, v.v.)
- Neuroimaging (MRI hoặc CT) để xem cấu trúc não
- Neuropsychological testing đầy đủ
            """.strip()
        }
    
    def _generate_differential_list(self, domain_scores: Dict, mmse_score: float) -> List[Dict]:
        """Generate list of differential diagnostic considerations"""
        differentials = []
        
        # Calculate percentages
        recall_pct = 100
        orientation_pct = 100
        executive_pct = 100
        visuospatial_pct = 100
        
        if isinstance(domain_scores.get("recall"), dict):
            recall_scores = domain_scores["recall"]
            recall_pct = (recall_scores.get("score", 0) / recall_scores.get("max", 1) * 100) if recall_scores.get("max", 0) > 0 else 100
        
        if isinstance(domain_scores.get("orientation"), dict):
            orientation_scores = domain_scores["orientation"]
            orientation_pct = (orientation_scores.get("score", 0) / orientation_scores.get("max", 1) * 100) if orientation_scores.get("max", 0) > 0 else 100
        
        if isinstance(domain_scores.get("executive"), dict):
            executive_scores = domain_scores["executive"]
            executive_pct = (executive_scores.get("score", 0) / executive_scores.get("max", 1) * 100) if executive_scores.get("max", 0) > 0 else 100
        
        if isinstance(domain_scores.get("visuospatial"), dict):
            visuospatial_scores = domain_scores["visuospatial"]
            visuospatial_pct = (visuospatial_scores.get("score", 0) / visuospatial_scores.get("max", 1) * 100) if visuospatial_scores.get("max", 0) > 0 else 100
        
        # Alzheimer's Disease pattern
        if recall_pct < 70 or orientation_pct < 80:
            differentials.append({
                "condition": "Alzheimer's Disease (AD)",
                "likelihood": "Cần xem xét",
                "supporting_evidence": [
                    "Suy giảm recall (trí nhớ gần)" if recall_pct < 70 else None,
                    "Mất định hướng" if orientation_pct < 80 else None,
                    "Pattern điển hình của AD"
                ],
                "additional_tests": "MRI (xem hippocampal atrophy), PET scan (amyloid/tau)",
                "description": "Nguyên nhân phổ biến nhất của dementia, chiếm 60-70% các trường hợp"
            })
        
        # Vascular Cognitive Impairment
        if executive_pct < 70:
            differentials.append({
                "condition": "Vascular Cognitive Impairment (VCI)",
                "likelihood": "Cần xem xét",
                "supporting_evidence": [
                    "Suy giảm chức năng điều hành",
                    "Pattern suggestive of frontal-subcortical dysfunction"
                ],
                "additional_tests": "MRI (xem white matter lesions, old strokes), Đánh giá yếu tố nguy cơ tim mạch",
                "description": "Do vấn đề tim mạch ảnh hưởng lên não. Có thể can thiệp bằng cách kiểm soát yếu tố nguy cơ"
            })
        
        # Lewy Body Dementia / Posterior Cortical Atrophy
        if visuospatial_pct < 70:
            differentials.append({
                "condition": "Lewy Body Dementia (LBD) hoặc Posterior Cortical Atrophy (PCA)",
                "likelihood": "Cần xem xét",
                "supporting_evidence": [
                    "Suy giảm visuospatial đáng kể",
                    "Pattern đặc trưng của posterior cortex involvement"
                ],
                "additional_tests": "MRI (xem posterior atrophy), Đánh giá visual hallucinations và motor symptoms",
                "description": "LBD có triệu chứng motor (như Parkinson's) và visual hallucinations. PCA là variant của AD với visual symptoms nổi bật"
            })
        
        # Mild Cognitive Impairment
        if 24 <= mmse_score < 27:
            differentials.append({
                "condition": "Mild Cognitive Impairment (MCI)",
                "likelihood": "Khả năng cao",
                "supporting_evidence": [
                    f"Điểm MMSE {mmse_score}/30 - trong khoảng MCI",
                    "Có suy giảm nhưng chưa ảnh hưởng nhiều đến sinh hoạt"
                ],
                "additional_tests": "MoCA test, Neuropsychological battery đầy đủ, MRI, Theo dõi longitudinal",
                "description": "Giai đoạn chuyển tiếp giữa bình thường và dementia. 10-15%/năm tiến triển thành AD"
            })
        
        # Non-dementia causes (always include)
        differentials.append({
            "condition": "Nguyên nhân có thể điều trị được",
            "likelihood": "Nên loại trừ",
            "supporting_evidence": [
                "Depression (pseudodementia)",
                "Thiếu vitamin B12 hoặc folate",
                "Hypothyroidism",
                "Medication effects",
                "Sleep disorders (sleep apnea)",
                "Hearing/vision loss"
            ],
            "additional_tests": "CBC, B12, folate, TSH, medication review, sleep study nếu nghi ngờ",
            "description": "Những nguyên nhân này CÓ THỂ ĐIỀU TRỊ và cải thiện hoàn toàn. Rất quan trọng phải loại trừ!"
        })
        
        # Filter out None values
        for diff in differentials:
            if "supporting_evidence" in diff:
                diff["supporting_evidence"] = [e for e in diff["supporting_evidence"] if e is not None]
        
        return differentials
    
    def _generate_clinical_recommendations_summary(self, results: Dict) -> List[str]:
        """Generate summary of clinical recommendations"""
        recommendations = []
        assessment_result = results.get("assessment_result", {}) or {}
        shap_explanation = results.get("shap_explanation", {}) or {}
        
        mmse_score = assessment_result.get("adjusted_score", 0) or assessment_result.get("raw_score", 0)
        clinical_interp = shap_explanation.get("clinical_interpretation", {}) or {}
        risk_level = clinical_interp.get("overall_risk_level", "")
        
        if mmse_score < 24 or risk_level == "Nguy cơ cao":
            recommendations.extend([
                "🚨 **URGENT:** Đặt lịch khám bác sĩ thần kinh trong 1-2 tuần",
                "📋 Chuẩn bị: danh sách thuốc, tiền sử bệnh, triệu chứng chi tiết",
                "🧠 Xem xét làm: MRI não, xét nghiệm máu đầy đủ, neuropsych testing"
            ])
        elif mmse_score < 27 or risk_level == "Nguy cơ trung bình":
            recommendations.extend([
                "📅 Đặt lịch khám trong 1 tháng",
                "📊 Kiểm tra lại MMSE sau 3-6 tháng",
                "🏃 Bắt đầu các biện pháp dự phòng ngay"
            ])
        else:
            recommendations.extend([
                "✅ Tiếp tục duy trì lối sống lành mạnh",
                "📆 Kiểm tra định kỳ hàng năm",
                "💪 Tăng cường hoạt động trí tuệ và xã hội"
            ])
        
        return recommendations
    
    def _generate_prognosis_discussion(self, results: Dict) -> Dict:
        """Generate prognosis discussion"""
        assessment_result = results.get("assessment_result", {}) or {}
        shap_explanation = results.get("shap_explanation", {}) or {}
        
        mmse_score = assessment_result.get("adjusted_score", 0) or assessment_result.get("raw_score", 0)
        clinical_interp = shap_explanation.get("clinical_interpretation", {}) or {}
        risk_level = clinical_interp.get("overall_risk_level", "")
        
        return {
            "title": "Thảo Luận về Tiên Lượng",
            "note": """
Lưu ý quan trọng:
Tiên lượng là DỰ ĐOÁN dựa trên nghiên cứu, KHÔNG phải là KẾT CỤC chắc chắn.
Mỗi người là một cá thể riêng biệt và có thể có diễn biến khác nhau.
Can thiệp sớm có thể thay đổi đáng kể tiên lượng.
            """.strip(),
            "current_status_prognosis": self._generate_status_prognosis(mmse_score, risk_level),
            "modifiable_factors": self._identify_modifiable_factors(),
            "protective_factors": self._identify_protective_factors(results),
            "hope_message": """
Thông điệp Hi vọng:
Ngay cả khi có dấu hiệu suy giảm nhận thức, nghiên cứu cho thấy nhiều can thiệp hiệu quả:

- Lifestyle modifications: Exercise, diet, sleep, social engagement có thể làm chậm tiến triển 30-40%
- Cognitive training: Brain training, learning new skills giúp build cognitive reserve
- Medical management: Kiểm soát yếu tố nguy cơ (huyết áp, đái tháo đường, cholesterol)
- Early treatment: Các thuốc mới cho thấy hiệu quả trong early AD
- Clinical trials: Nhiều trial đang nghiên cứu treatments mới

Chìa khóa: Phát hiện sớm + Can thiệp tích cực = Tiên lượng tốt hơn nhiều!
            """.strip()
        }
    
    def _generate_status_prognosis(self, mmse_score: float, risk_level: str) -> str:
        """Generate prognosis based on current status"""
        if mmse_score >= 27 and risk_level in ["Bình thường", "Nguy cơ thấp"]:
            return """
Tiên lượng: Tốt

- Chức năng nhận thức hiện tại tốt
- Nguy cơ suy giảm: 1-2%/năm (bình thường cho tuổi)
- Với lối sống lành mạnh, có thể duy trì độc lập nhiều năm
- Nếu có suy giảm, tiến triển sẽ chậm
            """.strip()
        elif mmse_score >= 24:
            return """
Tiên lượng: Cần theo dõi và can thiệp

- Có dấu hiệu MCI (Mild Cognitive Impairment)
- Nguy cơ tiến triển thành dementia: 10-15%/năm
- Nhưng 20-30% MCI cases có thể ỔN ĐỊNH hoặc CẢI THIỆN
- Can thiệp sớm rất quan trọng: Lifestyle changes có thể giảm nguy cơ 30-40%
            """.strip()
        else:
            return """
Tiên lượng: Cần can thiệp tích cực

- Có dấu hiệu suy giảm nhận thức đáng kể
- Nếu là dementia, tiến triển trung bình 3-5 điểm MMSE/năm
- NHƯNG: 15-20% cases do nguyên nhân CÓ THỂ ĐIỀU TRỊ (B12, thyroid, depression)
- Early-stage treatment có thể làm chậm 6-12 tháng
- Quality of life có thể được cải thiện đáng kể với support phù hợp
            """.strip()
    
    def _identify_modifiable_factors(self) -> List[Dict]:
        """Identify modifiable risk factors"""
        return [
            {
                "factor": "Yếu tố tim mạch",
                "action": "Kiểm tra huyết áp, đường huyết, cholesterol. Kiểm soát tốt các yếu tố này giảm 30-40% nguy cơ dementia",
                "impact": "Cao"
            },
            {
                "factor": "Hoạt động thể chất",
                "action": "Exercise 150 phút/tuần (aerobic + strength training). Exercise giảm 28% nguy cơ AD",
                "impact": "Cao"
            },
            {
                "factor": "Hoạt động trí tuệ",
                "action": "Đọc sách, học ngôn ngữ mới, chơi nhạc cụ, làm puzzles. Build cognitive reserve",
                "impact": "Trung bình-Cao"
            },
            {
                "factor": "Giao tiếp xã hội",
                "action": "Duy trì friendships, tham gia hoạt động nhóm. Social isolation tăng 50% nguy cơ dementia",
                "impact": "Cao"
            },
            {
                "factor": "Chế độ ăn",
                "action": "Mediterranean diet hoặc MIND diet. Giàu vegetables, fish, olive oil, nuts",
                "impact": "Trung bình"
            },
            {
                "factor": "Giấc ngủ",
                "action": "7-8 giờ/đêm, điều trị sleep apnea nếu có. Poor sleep tăng risk",
                "impact": "Trung bình"
            },
            {
                "factor": "Thính lực",
                "action": "Điều trị hearing loss nếu có. Untreated hearing loss tăng 200-500% risk",
                "impact": "Cao"
            }
        ]
    
    def _identify_protective_factors(self, results: Dict) -> List[str]:
        """Identify existing protective factors"""
        protective = []
        
        # From SHAP
        shap_explanation = results.get("shap_explanation", {}) or {}
        shap_analysis = shap_explanation.get("shap_analysis", {}) or {}
        protective_factors = shap_analysis.get("protective_factors", [])
        
        if protective_factors:
            protective.append(f"✅ {len(protective_factors)} yếu tố bảo vệ được AI xác định")
            for factor in protective_factors[:3]:
                feature_name = factor.get("feature_name_vi") or factor.get("feature", "N/A")
                protective.append(f"  - {feature_name}")
        
        # From MMSE domains
        assessment_result = results.get("assessment_result", {}) or {}
        domain_scores = assessment_result.get("domain_scores", {}) or {}
        strong_domains = []
        
        for domain, scores in domain_scores.items():
            if isinstance(scores, dict):
                score = scores.get("score", 0)
                max_score = scores.get("max", 1)
                pct = (score / max_score * 100) if max_score > 0 else 0
                if pct >= 90:
                    strong_domains.append(self._translate_domain_name(domain))
        
        if strong_domains:
            protective.append(f"✅ Các domain nhận thức mạnh: {', '.join(strong_domains)}")
        
        return protective if protective else ["Cần xây dựng thêm các yếu tố bảo vệ"]
    
    def generate_technical_appendix(self, results: Dict) -> Dict:
        """Technical Appendix Section - TODO: Implement"""
        return {"note": "Section implementation in progress"}


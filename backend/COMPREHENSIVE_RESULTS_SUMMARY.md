# Comprehensive Results - Test Summary

**File:** `test_clinical_results_test_clinical_view_1767410629.json`  
**Size:** 36,248 bytes  
**Generated:** 2026-01-03

## 📊 Overview

- **Session ID:** test_clinical_view_1767410629
- **MMSE Score:** 24/35 (MCI range)
- **Risk Level:** nguy_co_nhe (Mild MCI)
- **User:** Female, age 72, education 10 years
- **Total Sections:** 9

---

## 1. Assessment Result

- **MMSE Score:** 24.0/35.0
- **MCI Probability:** 0.65 (65%)
- **Risk Level:** nguy_co_nhe (Mild Cognitive Impairment)
- **Confidence:** 0.82
- **Education-specific thresholds:** Applied (medium education 10-12 years)

---

## 2. Feature Summary

- **Acoustic Features:** 14 total
- **Linguistic Features:** 4 total
- **Total Features:** 18
- **Abnormal Features:** 11 (61.1%)
  - Abnormal Acoustic: 8
  - Abnormal Linguistic: 3

---

## 3. SHAP Explanation

### Feature Contributions: **18 features analyzed**

### Top 5 Risk Factors:

1. **Tần suất dừng lời (Pause Rate)**
   - Contribution: 0.30
   - Value: 0.435 lần dừng/giây
   - Clinical Range: **Concerning**
   - Explanation: "Bất thường - Dừng lời thường xuyên, khó tổ chức ngôn ngữ"
   - Real-world analogy: "Như người cao tuổi tìm từ: dừng nhiều, chần chừ"
   - **MCI Relevance:** Pause rate cao (>0.4) là biomarker MCI mạnh nhất (AUC 0.89 - Luz et al. 2024)

2. **Độ rung giọng (Jitter)**
   - Contribution: 0.24
   - Value: 0.0235% (2.35%)
   - Clinical Range: **Concerning**
   - Explanation: "Bất thường - Khớp thanh rung không ổn định, có thể do mệt mỏi hoặc bệnh lý"
   - Real-world analogy: "Như giọng nói khàn đặc trưng khi bị viêm họng"
   - **MCI Relevance:** Jitter tăng cao (>2%) gắn liền với MCI do suy giảm kiểm soát thần kinh-cơ (Fraser et al. 2016)

3. **Mật độ ý tưởng (Idea Density)**
   - Contribution: 0.2175
   - Value: 0.38 ý tưởng/câu
   - Clinical Range: **Borderline**
   - Explanation: "Cần lưu ý - Câu dài nhưng ít ý, hơi lan man"
   - Real-world analogy: "Như nói lan man: dài dòng, ít điểm chính"
   - **MCI Relevance:** Idea density < 0.40 là predictor Alzheimer mạnh (Fraser et al. 2016, Nun Study)

4. **Đa dạng từ vựng (TTR)**
   - Contribution: 0.21
   - Value: 0.42 tỷ lệ
   - Clinical Range: **Borderline**
   - Explanation: "Cần lưu ý - Từ vựng hạn chế, hay lặp từ"
   - Real-world analogy: "Như từ vựng hạn chế: hay dùng 'cái đó', 'cái kia'"
   - **MCI Relevance:** TTR < 0.50 là predictor MCI mạnh (Fraser et al. 2016)

5. **MMSE Recall Domain**
   - Contribution: 0.20
   - Value: 1/3 điểm
   - Clinical Range: **Concerning**
   - Explanation: "Nhớ lại yếu (1/3 điểm). Bạn khó nhớ lại thông tin cũ."

### Top Protective Factors:

1. **Tần số cơ bản trung bình (F0)**
   - Contribution: 0.08 (protective)
   - Value: 186.5 Hz
   - Status: Normal range for female

### Key Concerns:

- 5 features in "concerning" or "severe" range
- Multiple acoustic and linguistic biomarkers indicating MCI risk

---

## 4. Recommendations (9 total)

### High Priority:

1. **🏃‍♂️ Vận động thể chất (Bằng chứng mạnh nhất)**
   - Priority: HIGH
   - Evidence: Meta-analysis - Aerobic exercise giảm 45% nguy cơ suy giảm nhận thức (Sofi et al. 2011)
   - Actions:
     - Đi bộ nhanh 30 phút x 5 ngày/tuần (bắt buộc)
     - Tập aerobic cường độ vừa
     - Kết hợp tập sức mạnh 2 lần/tuần

2. **🗣️ Luyện tập tốc độ xử lý ngôn ngữ**
   - Priority: HIGH
   - Reason: Pause rate cao (0.435 lần/giây) - biomarker MCI mạnh nhất
   - Actions:
     - Bài tập đọc to: 15 phút/ngày
     - Kể chuyện có chuẩn bị
     - Trò chuyện có chủ đích
   - Expected improvement: Sau 3 tháng: giảm 20-30% thời gian dừng lời

3. **📚 Mở rộng vốn từ vựng**
   - Priority: HIGH
   - Reason: TTR thấp (0.42) - từ vựng hạn chế
   - Actions:
     - Học 5 từ mới mỗi ngày
     - Chơi ô chữ, Scrabble
     - Viết nhật ký
     - Đọc sách đa dạng
   - Expected improvement: Sau 6 tháng: tăng 15-25% TTR

4. **💡 Luyện tập tư duy súc tích**
   - Priority: HIGH
   - Reason: Idea density thấp (0.38) - predictor Alzheimer mạnh nhất
   - Actions:
     - Luyện viết tóm tắt
     - Trò chuyện có cấu trúc
     - Chơi trò "giải thích nhanh"
   - **Critical:** Nun Study - idea density < 0.40 dự báo Alzheimer 10+ năm trước

5. **🧠 Kích thích nhận thức đa dạng**
   - Priority: HIGH
   - Actions:
     - Học ngôn ngữ mới
     - Chơi nhạc cụ
     - Đọc sách phức tạp
     - Chơi board games

6. **😴 Ngủ đủ 7-9 giờ/đêm**
   - Priority: HIGH
   - Reason: Giấc ngủ là thời gian não "dọn dẹp" amyloid-beta

7. **👥 Tương tác xã hội thường xuyên**
   - Priority: HIGH
   - Evidence: Social engagement giảm 50% nguy cơ suy giảm nhận thức

### Medium Priority:

8. **🥗 Chế độ ăn MIND Diet**
   - Priority: MEDIUM
   - Evidence: MIND diet giảm 53% nguy cơ AD khi tuân thủ nghiêm (Morris et al. 2015)

9. **📊 Theo dõi tiến triển**
   - Priority: MEDIUM
   - Follow-up interval: 6 tháng (moderate risk)
   - Actions:
     - Đặt lịch đánh giá lại
     - Ghi nhật ký các hoạt động can thiệp
     - Theo dõi các triệu chứng mới

---

## 5. Detailed Analysis

### Acoustic Features (7 analyzed):

- **Jitter:** 0.0235% (Concerning - >0.020%)
- **Shimmer:** 0.0625% (Concerning - >0.050%)
- **HNR:** 12.0 dB (Borderline - <12.0 indicates poor quality)
- **Pause Rate:** 0.435 pauses/sec (Concerning - >0.40 = strongest MCI predictor)
- **Speaking Rate:** 96.5 words/min (Concerning - <100 wpm)
- **F0 Mean:** 186.5 Hz (Normal for female)
- **F0 CV:** 0.085 (Borderline - <0.10 = flat prosody)

### Linguistic Features (4 analyzed):

- **TTR:** 0.42 (Borderline - <0.50 indicates vocabulary decline)
- **Pronoun Ratio:** 0.38 (Concerning - >0.35 indicates anomia)
- **Idea Density:** 0.38 (Borderline - <0.40 predicts Alzheimer's)
- **MLU:** 5.5 words/sentence (Concerning - <6.0 indicates syntactic simplification)

---

## 6. Multimodal Analysis

- **Combined Risk Score:** 0.65 (65%)
- **Risk Level:** nguy_co_nhe (Mild MCI)
- **Acoustic Features:** 7 analyzed
- **Linguistic Features:** 4 analyzed

---

## 7. Citations

Includes citations for:
- MMSE (Folstein 1975)
- SHAP methodology (Lundberg & Lee 2017)
- Acoustic biomarkers (Fraser et al. 2016, Luz et al. 2024)
- Linguistic biomarkers (Fraser et al. 2016, Nun Study)
- Interventions (exercise, diet, cognitive training, etc.)

---

## ✅ Key Highlights

1. **Clinical Interpretation System Working:**
   - ✅ 18 SHAP feature contributions với clinical interpretations
   - ✅ Vietnamese explanations với real-world analogies
   - ✅ Clinical ranges (optimal/normal/borderline/concerning/severe)
   - ✅ MCI relevance explanations với citations

2. **Personalized Recommendations:**
   - ✅ 9 evidence-based recommendations
   - ✅ Priority levels (high/medium)
   - ✅ Specific actions với expected improvements
   - ✅ Citations for each recommendation

3. **Population Norms Integration:**
   - ✅ Percentile calculations
   - ✅ Age/gender-specific norms
   - ✅ Clinical thresholds

4. **Comprehensive Structure:**
   - ✅ All 9 sections generated
   - ✅ Detailed feature analysis
   - ✅ SHAP explanations với clinical context
   - ✅ Actionable recommendations

---

## 📁 File Location

Full JSON file: `backend/test_clinical_results_test_clinical_view_1767410629.json`

Open in any JSON viewer or text editor to see complete structure.


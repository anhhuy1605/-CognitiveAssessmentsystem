# Hướng Dẫn Đọc Biểu Đồ Phân Tích MCI/AD

## 📊 Tổng Quan

Script phân tích tạo ra **6 biểu đồ** để đánh giá nguy cơ MCI/AD từ đặc điểm giọng nói. Mỗi biểu đồ tập trung vào một khía cạnh khác nhau của giọng nói.

---

## 📈 FIGURE 1: Waveform & Spectrogram Comparison
**"So sánh dạng sóng và phổ tần số"**

### **Cột 1: Waveform (Dạng sóng)**
**Mục đích:** Xem cấu trúc tín hiệu âm thanh theo thời gian

**Cách đọc:**
- **Trục X (ngang):** Thời gian (giây)
- **Trục Y (dọc):** Biên độ (amplitude) - độ lớn của sóng âm
- **Đường xanh lá:** Dạng sóng gốc (waveform)
- **Đường đỏ:** Amplitude envelope (bao bọc biên độ) - cho thấy cường độ giọng nói
- **Vùng đỏ mờ:** Các đoạn pause dài >2 giây (bất thường)

**Ý nghĩa lâm sàng:**
- ✅ **Bình thường:** Dạng sóng đều đặn, envelope ổn định
- ⚠️ **Bất thường:** 
  - Nhiều vùng đỏ (pause dài) → Có thể do khó tìm từ, suy nghĩ chậm
  - Envelope không đều → Cường độ giọng nói thay đổi nhiều (mệt mỏi)

### **Cột 2: Mel Spectrogram (Phổ tần số)**
**Mục đích:** Xem tần số âm thanh theo thời gian (giống "nhiệt kế" của giọng nói)

**Cách đọc:**
- **Trục X (ngang):** Thời gian (giây)
- **Trục Y (dọc):** Tần số (Hz) - từ thấp (dưới) đến cao (trên)
- **Màu sắc:** 
  - **Vàng/Xanh sáng:** Năng lượng cao (âm thanh mạnh)
  - **Tím/Đen:** Năng lượng thấp (im lặng hoặc âm thanh yếu)
- **Vạch đỏ dọc:** Đánh dấu các đoạn pause dài >2 giây

**Ý nghĩa lâm sàng:**
- ✅ **Bình thường:** Phổ tần số đều đặn, ít khoảng trống (pause)
- ⚠️ **Bất thường:**
  - Nhiều vạch đỏ (pause dài) → Ngừng nói nhiều, khó diễn đạt
  - Phổ tần số không đều → Giọng nói không ổn định

---

## 🎵 FIGURE 2: Pitch Analysis - MCI Indicators
**"Phân tích độ cao giọng nói - Dấu hiệu MCI"**

### **Cột 1: F0 Contour with Confidence Band**
**Mục đích:** Xem độ cao giọng nói (pitch) thay đổi như thế nào

**Cách đọc:**
- **Trục X (ngang):** Thời gian (giây)
- **Trục Y (dọc):** Tần số F0 (Hz) - độ cao giọng nói
  - **Thấp (100-150 Hz):** Giọng trầm (nam giới)
  - **Cao (200-300 Hz):** Giọng cao (nữ giới)
- **Đường xanh lá:** F0 contour - độ cao giọng nói theo thời gian
- **Vùng xanh dương mờ:** Confidence band (±1 độ lệch chuẩn) - vùng dao động bình thường
- **Đường đỏ gạch:** Giá trị trung bình F0
- **Vùng đỏ mờ:** Các đoạn pitch drop đột ngột (>30Hz) - bất thường

**Ý nghĩa lâm sàng:**
- ✅ **Bình thường:** F0 dao động đều, ít pitch drop
- ⚠️ **Bất thường:**
  - Nhiều vùng đỏ (pitch drop) → Giọng nói không ổn định, có thể do:
    * Khó điều khiển cơ thanh quản
    * Mệt mỏi khi nói
    * Suy giảm motor control

### **Cột 2: Pitch Variability Over Time**
**Mục đích:** Xem độ dao động của pitch theo thời gian

**Cách đọc:**
- **Trục X (ngang):** Thời gian (giây)
- **Trục Y (dọc):** Pitch Std (Hz) - độ dao động của pitch
- **Đường vàng:** Pitch variability (độ lệch chuẩn) trong từng cửa sổ thời gian
- **Đường đỏ gạch:** Ngưỡng bất thường (30 Hz)
- **Vùng xanh:** Vùng bình thường (<30 Hz)
- **Vùng đỏ:** Vùng bất thường (>30 Hz)

**Ý nghĩa lâm sàng:**
- ✅ **Bình thường:** Variability <30 Hz, dao động đều
- ⚠️ **Bất thường:**
  - Variability >30 Hz → Pitch không ổn định
  - Nhiều điểm vượt ngưỡng đỏ → Giọng nói run rẩy, không kiểm soát được

---

## 🗣️ FIGURE 3: Speech Rate & Pause Patterns
**"Tốc độ nói và mẫu pause"**

### **Cột 1: Speech Rate Timeline**
**Mục đích:** Xem tốc độ nói thay đổi như thế nào theo thời gian

**Cách đọc:**
- **Trục X (ngang):** Thời gian (giây)
- **Trục Y (dọc):** Speech Rate (words/min) - số từ mỗi phút
- **Đường xanh lá:** Tốc độ nói trong từng cửa sổ 5 giây
- **Đường đỏ gạch:** Ngưỡng chậm (<100 words/min)
- **Vùng đỏ mờ:** Các đoạn nói chậm (<100 words/min)

**Ý nghĩa lâm sàng:**
- ✅ **Bình thường:** 120-180 words/min, ổn định
- ⚠️ **Bất thường:**
  - <100 words/min → Nói chậm, có thể do:
    * Khó tìm từ
    * Suy nghĩ chậm
    * Processing speed giảm (dấu hiệu MCI)

### **Cột 2: Pause Duration Histogram**
**Mục đích:** Xem phân bố độ dài các pause

**Cách đọc:**
- **Trục X (ngang):** Pause Duration (giây) - độ dài pause
- **Trục Y (dọc):** Frequency - số lần xuất hiện
- **Cột xanh dương:** Số lượng pause ở mỗi độ dài
- **Đường đỏ gạch:** Ngưỡng bất thường (2 giây)
- **Vùng xanh:** Vùng bình thường (<2 giây)
- **Vùng đỏ:** Vùng bất thường (>2 giây)

**Ý nghĩa lâm sàng:**
- ✅ **Bình thường:** Hầu hết pause <1 giây, ít pause dài
- ⚠️ **Bất thường:**
  - Nhiều pause >2 giây → Ngừng nói lâu, có thể do:
    * Khó tìm từ
    * Suy nghĩ chậm
    * Word-finding difficulty (dấu hiệu MCI)

### **Cột 3: Cumulative Pause Time Percentage**
**Mục đích:** Xem tổng thời gian pause chiếm bao nhiêu % tổng thời gian

**Cách đọc:**
- **Trục X (ngang):** Thời gian (giây)
- **Trục Y (dọc):** Cumulative Pause Time (%) - % thời gian pause tích lũy
- **Đường đỏ:** % pause tích lũy theo thời gian
- **Vùng đỏ mờ:** Vùng đã pause

**Ý nghĩa lâm sàng:**
- ✅ **Bình thường:** <20% thời gian là pause
- ⚠️ **Bất thường:**
  - >30% thời gian là pause → Nói ít, pause nhiều
  - Đường dốc đứng → Nhiều pause liên tiếp

---

## 🎤 FIGURE 4: Voice Quality Indicators
**"Chỉ số chất lượng giọng nói"**

### **Cột 1: Jitter & Shimmer vs Baseline**
**Mục đích:** So sánh độ ổn định giọng nói với ngưỡng bình thường

**Cách đọc:**
- **Trục X (ngang):** Loại chỉ số (Jitter, Shimmer)
- **Trục Y (dọc):** Giá trị (%)
- **Cột xanh lá:** Bình thường (< ngưỡng)
- **Cột vàng:** Hơi bất thường (70-100% ngưỡng)
- **Cột đỏ:** Bất thường (> ngưỡng)
- **Đường đỏ gạch:** Ngưỡng Jitter (1.0%)
- **Đường cam gạch:** Ngưỡng Shimmer (3.0%)

**Giải thích:**
- **Jitter:** Độ dao động của pitch (chu kỳ F0)
  - ✅ <1.0%: Giọng ổn định
  - ⚠️ >1.0%: Giọng run rẩy, không ổn định
- **Shimmer:** Độ dao động của biên độ (amplitude)
  - ✅ <3.0%: Biên độ ổn định
  - ⚠️ >3.0%: Biên độ thay đổi nhiều, giọng không đều

**Ý nghĩa lâm sàng:**
- ✅ **Bình thường:** Cả 2 chỉ số dưới ngưỡng
- ⚠️ **Bất thường:**
  - Jitter cao → Khó điều khiển cơ thanh quản
  - Shimmer cao → Khó kiểm soát hơi thở, biên độ
  - Cả 2 cao → Motor control giảm (dấu hiệu MCI)

### **Cột 2: Energy Contour with Fatigue Indicators**
**Mục đích:** Xem cường độ giọng nói (energy) thay đổi theo thời gian

**Cách đọc:**
- **Trục X (ngang):** Thời gian (giây)
- **Trục Y (dọc):** Energy (RMS) - cường độ giọng nói
- **Đường xanh lá:** Energy contour - cường độ theo thời gian
- **Đường đỏ gạch:** Ngưỡng thấp (70% giá trị trung bình)
- **Vùng đỏ mờ:** Các đoạn low energy (mệt mỏi)
- **Chú thích vàng:** "Low Energy" - đánh dấu các đoạn mệt mỏi

**Ý nghĩa lâm sàng:**
- ✅ **Bình thường:** Energy ổn định, ít đoạn thấp
- ⚠️ **Bất thường:**
  - Nhiều vùng đỏ (low energy) → Mệt mỏi khi nói
  - Energy giảm dần → Fatigue, không đủ sức để nói to
  - Có thể do:
    * Suy giảm thể lực
    * Khó kiểm soát hơi thở
    * Motor control giảm

---

## 🔥 FIGURE 5: MFCC Heatmap Comparison
**"So sánh bản đồ nhiệt MFCC"**

### **Mục đích:** Xem đặc trưng phổ tần số (MFCC) của giọng nói

**Cách đọc:**
- **Trục X (ngang):** Thời gian (giây)
- **Trục Y (dọc):** MFCC Coefficient (1-13) - 13 đặc trưng phổ tần số
- **Màu sắc:**
  - **Vàng/Xanh sáng:** Giá trị cao (đặc trưng mạnh)
  - **Tím/Đen:** Giá trị thấp (đặc trưng yếu)
- **Vạch đỏ gạch:** Các đoạn có variability thấp (bất thường)

**Giải thích MFCC:**
- **MFCC (Mel-Frequency Cepstral Coefficients):** 13 đặc trưng mô tả "dấu vân tay" của giọng nói
  - MFCC 1-3: Năng lượng tổng thể
  - MFCC 4-7: Đặc trưng phổ tần số thấp
  - MFCC 8-13: Đặc trưng phổ tần số cao

**Ý nghĩa lâm sàng:**
- ✅ **Bình thường:** 
  - Nhiều màu sắc đa dạng → Variability cao, giọng nói phong phú
  - Pattern đều đặn → Giọng nói ổn định
- ⚠️ **Bất thường:**
  - Nhiều vạch đỏ (variability thấp) → Giọng nói đơn điệu, ít thay đổi
  - Pattern đơn giản → Giọng nói "phẳng", không có ngữ điệu
  - Có thể do:
    * Prosody giảm (ngữ điệu kém)
    * Emotional expression giảm
    * Motor control giảm

---

## 🎯 FIGURE 6: Summary Dashboard - MCI/AD Risk Indicators
**"Bảng tổng hợp - Chỉ số nguy cơ MCI/AD"**

### **Mục đích:** Tổng hợp tất cả chỉ số thành 1 biểu đồ radar

**Cách đọc:**
- **Dạng biểu đồ:** Radar chart (biểu đồ mạng nhện)
- **8 trục (từ trung tâm ra ngoài):**
  1. **Speech Rate Deviation:** Độ lệch tốc độ nói
  2. **Pause Frequency:** Tần suất pause
  3. **Pitch Instability:** Độ không ổn định của pitch
  4. **Jitter/Shimmer Abnormality:** Bất thường jitter/shimmer
  5. **Energy Decline:** Sự suy giảm energy
  6. **Articulation Difficulty:** Khó khăn phát âm
  7. **MFCC Pattern Irregularity:** Bất thường pattern MFCC
  8. **Overall Confidence:** Độ tin cậy tổng thể

- **Thang điểm:** 0.0 (trung tâm) → 1.0 (ngoài cùng)
  - **0.0-0.3:** Bình thường (xanh lá)
  - **0.3-0.6:** Hơi bất thường (vàng)
  - **0.6-1.0:** Bất thường (đỏ)

- **Màu sắc:**
  - **Xanh lá:** Low Risk (0-2 indicators)
  - **Vàng:** Moderate Risk (3-4 indicators)
  - **Đỏ:** High Risk (5-7 indicators)

**Cách đọc từng patient:**
1. **Xem hình dạng:**
   - Hình tròn nhỏ (gần trung tâm) → Tốt, ít bất thường
   - Hình sao lớn (ra ngoài) → Nhiều bất thường

2. **Xem màu sắc:**
   - Xanh lá → Low Risk
   - Vàng → Moderate Risk
   - Đỏ → High Risk

3. **Xem các trục nổi bật:**
   - Trục nào dài nhất → Vấn đề đó nghiêm trọng nhất
   - Ví dụ: "Pause Frequency" dài → Nhiều pause, khó tìm từ

**Ý nghĩa lâm sàng:**
- ✅ **Low Risk (Xanh lá):**
  - Hầu hết trục <0.3
  - Hình dạng gần tròn, nhỏ
  - → Giọng nói bình thường, ít dấu hiệu MCI

- ⚠️ **Moderate Risk (Vàng):**
  - Một số trục 0.3-0.6
  - Hình dạng không đều
  - → Có dấu hiệu cần theo dõi

- 🚨 **High Risk (Đỏ):**
  - Nhiều trục >0.6
  - Hình dạng lớn, không đều
  - → Nhiều dấu hiệu MCI/AD, cần đánh giá kỹ hơn

---

## 📋 Tóm Tắt Cách Đọc

### **Quy trình đọc biểu đồ:**
1. **Bắt đầu với Figure 6 (Summary Dashboard):**
   - Xem risk level tổng thể (Low/Moderate/High)
   - Xem trục nào nổi bật nhất

2. **Xem chi tiết các figure khác:**
   - **Figure 1:** Xem có nhiều pause không?
   - **Figure 2:** Xem pitch có ổn định không?
   - **Figure 3:** Xem tốc độ nói và pause patterns
   - **Figure 4:** Xem chất lượng giọng nói (jitter/shimmer)
   - **Figure 5:** Xem đặc trưng phổ tần số

3. **Kết hợp thông tin:**
   - Nếu nhiều figure đều bất thường → Risk cao
   - Nếu chỉ 1-2 figure bất thường → Risk thấp/trung bình

### **Dấu hiệu MCI/AD thường gặp:**
- ✅ Nhiều pause dài (>2 giây)
- ✅ Tốc độ nói chậm (<100 words/min)
- ✅ Pitch không ổn định (variability >30 Hz)
- ✅ Jitter/Shimmer cao
- ✅ Energy giảm dần (mệt mỏi)
- ✅ MFCC variability thấp (giọng đơn điệu)

### **Kết luận:**
- **Low Risk:** 0-2 dấu hiệu → Giọng nói bình thường
- **Moderate Risk:** 3-4 dấu hiệu → Cần theo dõi
- **High Risk:** 5-7 dấu hiệu → Nhiều khả năng MCI/AD

---

## 📖 Tài Liệu Tham Khảo

- Fraser et al. (2016) - Linguistic features for dementia detection
- Pakhomov et al. (2011) - Computerized analysis in Alzheimer's
- Research on acoustic markers for MCI/AD detection




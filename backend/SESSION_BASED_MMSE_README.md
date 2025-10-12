# 🧠 Session-Based MMSE Assessment System

## Tổng quan

Hệ thống đánh giá MMSE mới sử dụng phương pháp **session-based** thay vì tính điểm ngay lập tức. Điều này đảm bảo:

- ✅ **MMSE score chỉ được tính khi hoàn thành toàn bộ test**
- ✅ **Theo dõi từng câu hỏi riêng biệt**
- ✅ **Progress tracking theo thời gian thực**
- ✅ **Aggregate scoring** từ tất cả câu trả lời
- ✅ **Không tính điểm từng phần** - chỉ tổng kết cuối cùng

## 🔄 Quy trình đánh giá MMSE

### **Flow Chuẩn:**
```
1. Start Session → 2. Submit Questions → 3. Complete Session → 4. Get Final Score
```

### **API Endpoints:**

#### **1. Khởi tạo Session**
```http
POST /api/mmse/session/start
Content-Type: application/json

{
  "user_email": "patient@example.com",
  "user_info": {
    "name": "Nguyễn Văn A",
    "age": 70,
    "education": 16
  }
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "123",
  "status": "in_progress",
  "total_questions": 12,
  "message": "MMSE session started successfully"
}
```

#### **2. Submit từng câu hỏi**
```http
POST /api/mmse/session/{session_id}/question
Content-Type: multipart/form-data

Form Data:
- audio: [audio file]
- question_id: "orientation_time"
- question_content: "Hôm nay là ngày nào?"
- user_name: "Nguyễn Văn A"
- user_age: "70"
- user_education: "16"
- user_email: "patient@example.com"
```

**Response:**
```json
{
  "success": true,
  "session_id": "123",
  "question_id": "orientation_time",
  "progress": {
    "completed_questions": 1,
    "total_questions": 12,
    "completion_percentage": 8.33,
    "is_complete": false
  },
  "transcript": "Hôm nay là thứ hai",
  "score": 1,
  "message": "Question orientation_time submitted successfully"
}
```

#### **3. Theo dõi tiến độ**
```http
GET /api/mmse/session/{session_id}/progress
```

**Response:**
```json
{
  "success": true,
  "progress": {
    "session_id": "123",
    "status": "in_progress",
    "completed_questions": 5,
    "total_questions": 12,
    "completion_percentage": 41.67,
    "is_complete": false
  }
}
```

#### **4. Hoàn thành và tính tổng điểm**
```http
POST /api/mmse/session/{session_id}/complete
```

**Response:**
```json
{
  "success": true,
  "assessment_result": {
    "session_id": "123",
    "status": "completed",
    "final_mmse_score": 25,
    "cognitive_level": "normal",
    "question_results": [
      {
        "question_id": "orientation_time",
        "score": 5,
        "transcript": "Hôm nay là thứ hai",
        "audio_features": {...}
      }
      // ... tất cả 12 câu hỏi
    ],
    "recommendations": [
      "Tiếp tục duy trì lối sống năng động",
      "Tham gia các hoạt động trí tuệ hàng ngày"
    ]
  },
  "message": "MMSE assessment completed successfully"
}
```

#### **5. Lấy kết quả đầy đủ**
```http
GET /api/mmse/session/{session_id}/results
```

## 📊 Cơ chế tính điểm

### **Logic chính:**
- ❌ **KHÔNG tính điểm ngay lập tức** từ mỗi audio
- ❌ **KHÔNG aggregate từng phần**
- ✅ **Lưu trữ từng câu trả lời** với transcript và score tạm thời
- ✅ **Chỉ tính tổng MMSE** khi tất cả câu hỏi hoàn thành
- ✅ **Aggregate từ tất cả data** để có đánh giá chính xác nhất

### **Database Schema:**

#### **`sessions` table:**
```sql
- id: Session ID
- user_id: Email người dùng
- mode: 'personal'/'community'
- status: 'in_progress'/'completed'/'error'
- mmse_score: NULL (đến khi complete)
- cognitive_level: NULL (đến khi complete)
```

#### **`questions` table:**
```sql
- session_id: Liên kết với session
- question_id: ID câu hỏi (orientation_time, registration, etc.)
- question_content: Nội dung câu hỏi
- audio_file: File ghi âm
- auto_transcript: Transcript từ AI
- score: Điểm số cho câu hỏi này (1-5 points)
- user_name, user_age, user_education, user_email: Thông tin user
```

#### **`stats` table:** (Tạo khi complete)
```sql
- session_id: Liên kết session
- summary: Tổng kết MMSE score và cognitive level
- detailed_results: Chi tiết từng câu hỏi
- chart_data: Dữ liệu biểu đồ
- exercise_recommendations: Gợi ý bài tập
```

## 🎯 Ưu điểm của Session-Based Approach

### **Clinical Accuracy:**
- ✅ **Comprehensive assessment** - Xem xét toàn bộ pattern
- ✅ **Context awareness** - Hiểu được progression qua các câu hỏi
- ✅ **Quality control** - Đảm bảo tất cả câu hỏi được trả lời
- ✅ **Consistency** - Standardized workflow

### **User Experience:**
- ✅ **Real-time feedback** - Xem progress sau mỗi câu hỏi
- ✅ **Flexible pacing** - Có thể dừng và tiếp tục
- ✅ **Error prevention** - Không cho complete sớm
- ✅ **Data integrity** - Tất cả responses được lưu trữ

### **Technical Benefits:**
- ✅ **Scalable** - Handle multiple concurrent sessions
- ✅ **Auditable** - Full audit trail của từng câu hỏi
- ✅ **Recoverable** - Resume interrupted sessions
- ✅ **Analytics-ready** - Rich data cho research

## 🚨 Deprecated Endpoint

### **Legacy Single-Shot Assessment:**
```http
POST /api/mmse/assess  # ⚠️ DEPRECATED
```

**Warning:** Endpoint này tính MMSE score ngay lập tức từ single audio - không recommended cho clinical use.

## 🧪 Testing

### **Run Session-Based Test:**
```bash
cd backend
python test_session_mmse.py
```

### **Manual Testing với cURL:**

```bash
# 1. Start session
curl -X POST http://localhost:5001/api/mmse/session/start \
  -H "Content-Type: application/json" \
  -d '{"user_email": "test@example.com", "user_info": {"name": "Test User", "age": 70}}'

# 2. Submit question
curl -X POST http://localhost:5001/api/mmse/session/{session_id}/question \
  -F "audio=@question_audio.wav" \
  -F "question_id=orientation_time" \
  -F "question_content=Hôm nay là ngày nào?" \
  -F "user_email=test@example.com"

# 3. Check progress
curl http://localhost:5001/api/mmse/session/{session_id}/progress

# 4. Complete assessment (sau khi đủ 12 câu hỏi)
curl -X POST http://localhost:5001/api/mmse/session/{session_id}/complete
```

## 📈 Migration Strategy

### **For Existing Systems:**
1. **Gradual migration** - Support both approaches temporarily
2. **Data preservation** - Migrate existing single assessments to sessions
3. **User education** - Train staff on new workflow
4. **Fallback support** - Legacy endpoint vẫn available

### **Data Compatibility:**
- ✅ **Existing assessments** vẫn viewable
- ✅ **New assessments** sử dụng session-based
- ✅ **Unified reporting** cho cả hai loại
- ✅ **Audit trail** maintained

## 🎊 Summary

**Session-Based MMSE Assessment** đảm bảo:

- 🧠 **Clinical accuracy** - Comprehensive evaluation
- 📊 **Data integrity** - Complete audit trail
- 🔄 **User experience** - Real-time feedback
- 🛡️ **Quality control** - Prevents premature completion
- 📈 **Research value** - Rich analytics data

**MMSE scores are now calculated only after completing the entire assessment!** 🎯✨

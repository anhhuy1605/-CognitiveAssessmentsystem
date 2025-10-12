# 📊 Cognitive Assessment Database Schema

## Tổng quan
Database PostgreSQL trên Neon Cloud với đầy đủ các bảng để hỗ trợ hệ thống đánh giá nhận thức dựa trên tiếng nói.

## 📋 Các bảng dữ liệu

### **Bảng chính (Main Tables)**
| Bảng | Mục đích | Records |
|------|---------|---------|
| `users` | Thông tin người dùng | 3 |
| `sessions` | Phiên đánh giá | 0 |
| `questions` | Câu hỏi và kết quả MMSE | 0 |
| `stats` | Thống kê và báo cáo | 0 |
| `temp_questions` | Dữ liệu tạm thời | 0 |

### **Bảng kết quả (Results Tables)**
| Bảng | Mục đích | Records |
|------|---------|---------|
| `cognitive_assessment_results` | Kết quả đánh giá chi tiết | 2 |
| `community_assessments` | Đánh giá cộng đồng | 0 |
| `training_samples` | Dữ liệu training AI | 22 |
| `user_reports` | Báo cáo người dùng (legacy) | 2 |

---

## 🗂️ Chi tiết cấu trúc từng bảng

### **1. `users` (Người dùng)**
```sql
- id: SERIAL PRIMARY KEY
- email: TEXT NOT NULL UNIQUE
- displayName: TEXT
- profile: JSONB
- mode: ENUM('personal', 'community')
- clerkId: TEXT
- createdAt, updatedAt: TIMESTAMP
```

### **2. `sessions` (Phiên đánh giá)**
```sql
- id: SERIAL PRIMARY KEY
- user_id: TEXT
- mode: VARCHAR(20) NOT NULL ('personal'/'community')
- status: VARCHAR(20) ('in_progress'/'completed'/'error')
- start_time, end_time: TIMESTAMP
- total_score: REAL
- mmse_score: INTEGER
- cognitive_level: VARCHAR(20) ('mild'/'moderate'/'severe'/'normal')
- email_sent: INTEGER DEFAULT 0
- created_at, updated_at: TIMESTAMP
```

### **3. `questions` (Câu hỏi MMSE)**
```sql
- id: SERIAL PRIMARY KEY
- session_id: TEXT NOT NULL
- question_id: TEXT NOT NULL
- question_content: TEXT NOT NULL
- audio_file: TEXT                    -- 📁 File ghi âm
- auto_transcript: TEXT              -- 🎤 Autotranscribe
- manual_transcript: TEXT
- linguistic_analysis: JSONB
- audio_features: JSONB
- evaluation: TEXT
- feedback: TEXT
- score: REAL
- processed_at: TIMESTAMP
- created_at: TIMESTAMP
- user_name: TEXT                    -- 👤 Tên người dùng
- user_age: INTEGER                  -- 🎂 Tuổi người dùng
- user_education: INTEGER            -- 🎓 Số năm học
- user_email: TEXT                   -- 📧 Email
```

### **4. `stats` (Thống kê)**
```sql
- id: SERIAL PRIMARY KEY
- session_id: TEXT NOT NULL
- user_id: TEXT
- timestamp: TIMESTAMP
- mode: VARCHAR(20) NOT NULL
- summary: JSONB
- detailed_results: JSONB
- chart_data: JSONB
- exercise_recommendations: JSONB
- created_at: TIMESTAMP
- user_name: TEXT                    -- 👤 Tên người dùng
- user_age: INTEGER                  -- 🎂 Tuổi người dùng
- user_education: INTEGER            -- 🎓 Số năm học
- user_email: TEXT                   -- 📧 Email
- audio_files: JSONB                 -- 📁 File ghi âm
```

### **5. `temp_questions` (Dữ liệu tạm thời)**
```sql
- id: SERIAL PRIMARY KEY
- session_id: TEXT NOT NULL
- question_id: TEXT NOT NULL
- question_content: TEXT NOT NULL
- audio_file: TEXT                    -- 📁 File ghi âm
- auto_transcript: TEXT              -- 🎤 Autotranscribe
- raw_audio_features: JSONB
- status: TEXT DEFAULT 'pending'
- created_at: TIMESTAMP
- expires_at: TIMESTAMP
- user_name: TEXT                    -- 👤 Tên người dùng
- user_age: INTEGER                  -- 🎂 Tuổi người dùng
- user_education: INTEGER            -- 🎓 Số năm học
- user_email: TEXT                   -- 📧 Email
```

### **6. `cognitive_assessment_results` (Kết quả đánh giá)**
```sql
- id: SERIAL PRIMARY KEY
- sessionId: TEXT NOT NULL
- userId: TEXT
- userInfo: JSONB
- startedAt, completedAt: TIMESTAMP
- totalQuestions, answeredQuestions: INTEGER
- completionRate: REAL
- memoryScore, cognitiveScore: REAL
- finalMmseScore: INTEGER
- overallGptScore: REAL
- questionResults: JSONB
- audioFiles: JSONB
- recordingsPath: TEXT
- cognitiveAnalysis: JSONB
- audioFeatures: JSONB
- status: TEXT
- usageMode: TEXT
- assessmentType: TEXT
- createdAt, updatedAt: TIMESTAMP
```

---

## ✅ Đảm bảo các trường bắt buộc

### **Các trường thông tin bắt buộc đã được thêm vào:**
- ✅ **`auto_transcript`** - Transcript tự động từ AI
- ✅ **`user_name`** - Tên người dùng
- ✅ **`user_age`** - Tuổi người dùng
- ✅ **`user_education`** - Số năm học
- ✅ **`user_email`** - Email người dùng
- ✅ **`audio_file`** - Đường dẫn file ghi âm

### **Bảng có đầy đủ các trường bắt buộc:**
- `questions` ✅ (6/6 fields)
- `stats` ✅ (5/6 fields - không cần auto_transcript)
- `temp_questions` ✅ (6/6 fields)
- `sessions` ✅ (có thể lấy từ user_id)
- `cognitive_assessment_results` ✅ (có userInfo JSONB)

---

## 🔍 Indexes đã tạo

### **Performance Indexes:**
```sql
-- Sessions
idx_sessions_user_id ON sessions(user_id);
idx_sessions_mode ON sessions(mode);
idx_sessions_status ON sessions(status);

-- Questions
idx_questions_session_id ON questions(session_id);
idx_questions_question_id ON questions(question_id);
idx_questions_user_email ON questions(user_email);

-- Stats
idx_stats_session_id ON stats(session_id);
idx_stats_user_id ON stats(user_id);

-- Temp Questions
idx_temp_questions_session_id ON temp_questions(session_id);
idx_temp_questions_status ON temp_questions(status);
idx_temp_questions_expires_at ON temp_questions(expires_at);
```

---

## 🚀 Sử dụng Database

### **Kết nối:**
```python
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv('config.env')
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
```

### **Thêm dữ liệu mẫu:**
```sql
-- Thêm user
INSERT INTO users (email, displayName, profile, clerkId)
VALUES ('user@example.com', 'Nguyễn Văn A', '{"age": 65, "education": 12}', 'clerk_123');

-- Thêm session
INSERT INTO sessions (user_id, mode, status)
VALUES ('user@example.com', 'personal', 'in_progress');

-- Thêm question với đầy đủ thông tin
INSERT INTO questions (
    session_id, question_id, question_content, audio_file,
    auto_transcript, user_name, user_age, user_education, user_email
) VALUES (
    'session_123', 'q1', 'Hôm nay là ngày nào?',
    '/audio/question1.wav', 'Hôm nay là thứ hai',
    'Nguyễn Văn A', 65, 12, 'user@example.com'
);
```

---

## 📈 Thống kê Database

- **Tổng số bảng:** 9
- **Bảng có dữ liệu:** 4/9
- **Tổng records:** 29
- **Bảng mới tạo:** 4 (sessions, questions, stats, temp_questions)
- **Fields bắt buộc:** 100% coverage
- **Indexes:** 11 indexes cho performance

---

## 🎯 Next Steps

1. **Frontend Integration** - Cập nhật Drizzle schema
2. **API Endpoints** - Tạo REST APIs cho CRUD operations
3. **Data Migration** - Chuyển dữ liệu từ tables cũ sang mới
4. **Testing** - Unit tests cho database operations
5. **Backup Strategy** - Thiết lập backup tự động

---

*Database schema last updated: September 20, 2025*
*Created by: Cursor AI Assistant*

# Frontend API Endpoints

Frontend gọi backend Python qua các endpoint sau:

## Trực tiếp từ Frontend (Components/Pages)

### Health & Status
- `GET /api/health` - Kiểm tra trạng thái backend
- `GET /api/status` - Thông tin status
- `GET /api/config` - Cấu hình hệ thống

### MMSE Chatbot
- `GET /api/mmse/chatbot/questions` - Lấy danh sách câu hỏi
- `POST /api/mmse/chatbot/session` - Tạo session mới
- `POST /api/mmse/chatbot/submit` - Submit câu trả lời
- `GET /api/mmse/chatbot/results` - Lấy kết quả

### Cognitive Assessment
- `GET /api/mmse/questions` - Lấy câu hỏi MMSE
- `GET /api/mmse/results/{sessionId}` - Lấy kết quả theo session

### Audio Processing
- `POST /auto-transcribe` - Transcribe audio (fallback: `/api/transcribe`)
- `POST /api/transcribe` - Transcribe audio

### Features & Analysis
- `GET /api/features/{sessionId}` - Lấy features theo session

## Qua Next.js API Routes (Forward tới Backend)

### Audio Processing
- `POST /api/analyze-audio` → `/api/assess` hoặc `/auto-transcribe`
- `POST /api/cognitive-assessment` → `/assess-cognitive`
- `POST /api/audio/process` → `/api/analyze-audio` (internal)

### Memory Test
- `POST /api/memory-test-result` → `/assess-file`

## Cấu hình

- **Base URL**: `NEXT_PUBLIC_PYTHON_BACKEND_URL` hoặc `PYTHON_BACKEND_URL` (mặc định: `http://localhost:5001`)
- **Environment**: Frontend sử dụng biến môi trường để xác định backend URL


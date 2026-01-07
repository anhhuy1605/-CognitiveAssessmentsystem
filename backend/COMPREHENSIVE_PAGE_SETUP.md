# Comprehensive Page Setup & Testing

## Tổng quan

Sau khi test và lưu session vào database, cần đảm bảo session có thể được truy cập từ Comprehensive page.

## Các bước đã thực hiện

### 1. ✅ Lưu session vào database
- Script `test_chatbot_with_database.py` đã lưu session `test_db_1767431871` vào database
- Session đã có đầy đủ:
  - 30 Q&A pairs
  - 26 questions có acoustic features (123 features mỗi question)
  - 42 linguistic features
  - Comprehensive results đã được generate

### 2. ✅ API Endpoints

#### GET `/api/mmse/chatbot/results/<session_id>`
- Lấy comprehensive results cho một session cụ thể
- Endpoint này đã được implement trong `backend/services/mmse_chatbot_api.py`
- Frontend comprehensive page sử dụng endpoint này

#### GET `/api/mmse/chatbot/sessions`
- **MỚI**: List tất cả completed sessions
- Để comprehensive page có thể hiển thị danh sách sessions
- Frontend đã được update để fetch từ API này

### 3. ✅ Frontend Updates

File `frontend/app/(main)/results/comprehensive-page.tsx` đã được update:
- `fetchCompletedSessions()` giờ fetch từ API trước, fallback về localStorage
- Có thể hiển thị danh sách sessions từ database

## Cách kiểm tra

### 1. Kiểm tra session có tồn tại trong service

```bash
cd backend
python test_comprehensive_page_access.py test_db_1767431871
```

### 2. Kiểm tra API endpoint

```bash
# Start backend nếu chưa chạy
python app.py

# Test API endpoint
curl http://localhost:5001/api/mmse/chatbot/results/test_db_1767431871
```

### 3. Truy cập Comprehensive page

1. Start frontend: `cd frontend && npm run dev`
2. Mở browser: `http://localhost:3000/results/comprehensive?sessionId=test_db_1767431871`

Hoặc không có sessionId để xem danh sách:
- `http://localhost:3000/results/comprehensive`
- Page sẽ hiển thị danh sách completed sessions từ API

## Session hiện có

- **Session ID**: `test_db_1767431871`
- **MMSE Score**: 15/35
- **Risk Level**: `nguy_co_nhe`
- **Features**: 
  - Acoustic: 123 features (aggregated)
  - Linguistic: 42 features
- **Q&A Pairs**: 30 pairs
- **Status**: ✅ Completed và đã lưu vào database

## Lưu ý

1. **Backend phải đang chạy** để API hoạt động
2. **Session phải tồn tại trong service** (MMSEChatbotService)
3. **Session phải có `completed_at`** để được coi là completed
4. Frontend sẽ cache sessions trong localStorage để offline access

## Troubleshooting

### Session không hiển thị trên page

1. Kiểm tra backend đang chạy: `http://localhost:5001/api/mmse/chatbot/sessions`
2. Kiểm tra session trong service:
   ```python
   from services.mmse_chatbot_service import MMSEChatbotService
   service = MMSEChatbotService()
   state = service.get_session('test_db_1767431871')
   print(state.completed_at)  # Phải có giá trị
   ```

### API trả về lỗi

- Kiểm tra logs trong backend console
- Đảm bảo `chatbot_service` đã được initialize
- Kiểm tra session có `completed_at` không None

## Next Steps

1. ✅ Session đã được lưu vào database
2. ✅ API endpoints đã sẵn sàng
3. ✅ Frontend đã được update
4. ⏳ **Cần test thực tế trên browser** để verify


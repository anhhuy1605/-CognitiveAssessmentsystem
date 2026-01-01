# CORS Fix cho Vercel Frontend

## 🔍 Vấn Đề

Frontend đã deploy trên Vercel (`https://cognitiveassessmentsystem-frontend.vercel.app/`) nhưng khi click "Bắt đầu trò chuyện" trong MMSE chatbot, nút cứ xoay tròn và không vào được.

## 🔧 Nguyên Nhân

1. **CORS Configuration**: Backend chỉ cho phép localhost, không có domain Vercel
2. **API URL**: Frontend có thể chưa config đúng `NEXT_PUBLIC_API_URL` trên Vercel
3. **Error Handling**: Không có logging chi tiết để debug

## ✅ Giải Pháp Đã Áp Dụng

### 1. Fix CORS Configuration (`backend/app.py`)

**Trước:**
```python
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000", "*"],
        # "*" không hoạt động đúng với credentials
    }
})
```

**Sau:**
```python
# Cho phép các origins cụ thể
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://cognitiveassessmentsystem-frontend.vercel.app",
]

CORS(app, resources={...})

# Cho phép TẤT CẢ *.vercel.app domains (cho preview deployments)
@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin and origin.endswith('.vercel.app'):
        response.headers.add('Access-Control-Allow-Origin', origin)
        # ... other headers
    return response
```

### 2. Better Error Handling (`backend/services/mmse_chatbot_api.py`)

- ✅ Thêm logging chi tiết cho mọi request
- ✅ Handle errors gracefully với fallback mode
- ✅ Log request headers và data để debug

### 3. Environment Variables

**Trên Railway (Backend):**
```bash
CORS_ORIGINS=https://cognitiveassessmentsystem-frontend.vercel.app,http://localhost:3000
```

**Trên Vercel (Frontend):**
```bash
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
# hoặc
NEXT_PUBLIC_PYTHON_BACKEND_URL=https://your-backend.railway.app
```

## 🚀 Testing

### 1. Test CORS từ Browser Console

Mở browser console trên Vercel frontend và chạy:

```javascript
fetch('https://your-backend.railway.app/api/mmse/chatbot/session', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: 'test123',
    user_info: { name: 'Test', age: '50', gender: 'male' }
  })
})
.then(r => r.json())
.then(console.log)
.catch(console.error)
```

Nếu thấy CORS error → CORS chưa fix đúng
Nếu thấy response → CORS OK

### 2. Check Backend Logs

Xem logs trên Railway để thấy:
- ✅ "✅ CORS configured..."
- ✅ "📨 Received session creation request..."
- ✅ "✅ Session created successfully..."

### 3. Check Network Tab

Trong browser DevTools → Network tab:
- Xem request có `OPTIONS` (preflight) không
- Xem response headers có `Access-Control-Allow-Origin` không
- Xem status code (200 = OK, 500 = server error, CORS error = no CORS headers)

## 📋 Checklist Deployment

### Backend (Railway)
- [ ] Set `CORS_ORIGINS` environment variable (optional, có default)
- [ ] Deploy code mới
- [ ] Check logs để confirm CORS config
- [ ] Test `/api/health` endpoint từ browser

### Frontend (Vercel)
- [ ] Set `NEXT_PUBLIC_API_URL` hoặc `NEXT_PUBLIC_PYTHON_BACKEND_URL` = backend URL
- [ ] Redeploy frontend
- [ ] Test MMSE chatbot page

## 🔍 Debugging Tips

### Nếu vẫn không hoạt động:

1. **Check Browser Console:**
   - CORS error? → Backend CORS chưa đúng
   - Network error? → Backend URL sai hoặc backend down
   - 500 error? → Backend code có bug (check logs)

2. **Check Network Tab:**
   - Request có đến backend không?
   - Response status code?
   - Response headers có CORS headers không?

3. **Check Backend Logs:**
   - Có log "Received session creation request" không?
   - Có error gì không?

4. **Test trực tiếp API:**
   ```bash
   curl -X POST https://your-backend.railway.app/api/mmse/chatbot/session \
     -H "Content-Type: application/json" \
     -H "Origin: https://cognitiveassessmentsystem-frontend.vercel.app" \
     -d '{"session_id":"test","user_info":{"name":"Test"}}' \
     -v
   ```
   
   Xem response headers có `Access-Control-Allow-Origin` không.

## ✅ Expected Behavior

Sau khi fix:
1. Frontend gọi `/api/mmse/chatbot/session`
2. Backend nhận request và log "📨 Received session creation request"
3. Backend tạo session và return response
4. Frontend nhận response và chuyển sang chat interface
5. Nút "Bắt đầu trò chuyện" không còn xoay tròn


# Test API Endpoint - Hướng dẫn sử dụng

## Tạo Test Session với đầy đủ Features

### Cách 1: Sử dụng PowerShell Script (Khuyến nghị)

```powershell
cd backend
.\test_api_endpoint.ps1
```

Script này sẽ:
1. Tạo test session với đầy đủ features (acoustic, linguistic, SHAP)
2. Hiển thị session ID và summary
3. Hỏi bạn có muốn query results ngay không
4. Lưu kết quả vào file JSON

### Cách 2: Sử dụng PowerShell Command

```powershell
# Create test session
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/mmse/chatbot/test/create-full-session" -Method POST -ContentType "application/json"

# Get session ID
$sessionId = $response.session_id

# Get results
$results = Invoke-RestMethod -Uri "http://localhost:8000/api/mmse/chatbot/results/$sessionId" -Method GET

# Save to file
$results | ConvertTo-Json -Depth 10 | Out-File -FilePath "test_results_$sessionId.json" -Encoding UTF8
```

### Cách 3: Sử dụng curl (nếu có)

```bash
# Create test session
curl -X POST http://localhost:8000/api/mmse/chatbot/test/create-full-session \
  -H "Content-Type: application/json" \
  -o test_session.json

# Get session ID từ response
SESSION_ID=$(cat test_session.json | grep -o '"session_id":"[^"]*' | cut -d'"' -f4)

# Get results
curl -X GET http://localhost:8000/api/mmse/chatbot/results/$SESSION_ID \
  -o test_results.json
```

### Cách 4: Chạy Python Script trực tiếp

```bash
cd backend
python test_comprehensive_results.py
```

## Test Session bao gồm:

- ✅ **26 acoustic features** cho 8 questions
- ✅ **14 linguistic features**
- ✅ **Domain scores** và **question scores**
- ✅ **Multimodal risk calculation**
- ✅ **SHAP explanations**
- ✅ **Comprehensive results** với tất cả sections

## Output Files:

- `test_comprehensive_results_{session_id}.json` - Full comprehensive results
- `test_comprehensive_summary_{session_id}.txt` - Summary text
- `test_api_results_{session_id}.json` - API response (nếu dùng script)

## API Endpoints:

1. **POST** `/api/mmse/chatbot/test/create-full-session`
   - Tạo test session với đầy đủ features
   - Response: `{ success, session_id, summary, api_endpoint }`

2. **GET** `/api/mmse/chatbot/results/{session_id}`
   - Lấy comprehensive results cho session
   - Response: `{ success, data: { comprehensive_results }, _debug }`

## Lưu ý:

- Đảm bảo backend server đang chạy trên `http://localhost:8000`
- Nếu dùng port khác, thay đổi `$baseUrl` trong script
- Test session được lưu trong memory, sẽ mất khi server restart


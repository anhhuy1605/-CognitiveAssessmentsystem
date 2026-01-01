# 🔧 Fix Vercel Deployment Issues

## ❌ Vấn Đề Hiện Tại

### 1. Frontend đang gọi `localhost:5001` thay vì production backend
```
localhost:5001/api/mmse/chatbot/questions:1 Failed to load resource: net::ERR_CONNECTION_REFUSED
```

**Nguyên nhân:** Environment variable `NEXT_PUBLIC_API_URL` chưa được set trên Vercel

### 2. File JSON không tìm thấy
```
mmse_audio_questions_standardized.json:1 Failed to load resource: the server responded with a status of 404
```

**Nguyên nhân:** File có trong `frontend/public/` nhưng có thể path không đúng hoặc chưa được build

---

## ✅ Giải Pháp

### Bước 1: Set Environment Variables trên Vercel

1. Vào **Vercel Dashboard** → Project của bạn
2. Vào **Settings** → **Environment Variables**
3. Thêm các biến sau:

```bash
# Backend API URL (QUAN TRỌNG!)
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
# hoặc
NEXT_PUBLIC_PYTHON_BACKEND_URL=https://your-backend.railway.app

# Frontend URL (optional)
NEXT_PUBLIC_APP_URL=https://cognitiveassessmentsystem-frontend.vercel.app
```

**Lưu ý:**
- Thay `https://your-backend.railway.app` bằng URL thực tế của backend trên Railway
- Sau khi set, cần **Redeploy** frontend để áp dụng

### Bước 2: Kiểm Tra File JSON

File `mmse_audio_questions_standardized.json` cần có trong:
- ✅ `frontend/public/mmse_audio_questions_standardized.json` (đã có)
- ✅ Frontend sẽ tự động serve file từ `/public/` folder

Nếu vẫn 404, kiểm tra:
1. File có tồn tại trong `frontend/public/` không?
2. File có được commit vào git không?
3. Vercel có build file này không?

### Bước 3: Redeploy Frontend

Sau khi set environment variables:
1. Vào Vercel Dashboard
2. Click **Deployments**
3. Click **Redeploy** trên deployment mới nhất
4. Hoặc push code mới để trigger auto-deploy

---

## 🔍 Debugging

### Kiểm Tra Environment Variables

Thêm vào code để debug (temporary):

```typescript
// frontend/app/(main)/mmse-chatbot/page.tsx
console.log('API_BASE_URL:', process.env.NEXT_PUBLIC_API_URL);
console.log('NODE_ENV:', process.env.NODE_ENV);
```

Sau khi deploy, mở browser console và xem giá trị.

### Test Backend Connection

Mở browser console trên Vercel frontend và chạy:

```javascript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';
console.log('Testing:', API_URL);

fetch(`${API_URL}/api/health`)
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);
```

Nếu thấy response → Backend OK
Nếu thấy CORS error → Backend CORS chưa fix
Nếu thấy connection refused → API_URL sai

---

## 📋 Checklist

### Trước khi deploy:
- [ ] Backend đã deploy lên Railway và chạy OK
- [ ] Backend CORS đã được fix (cho phép Vercel domain)
- [ ] File `mmse_audio_questions_standardized.json` có trong `frontend/public/`
- [ ] Environment variables đã được set trên Vercel

### Sau khi deploy:
- [ ] Frontend có thể load được từ backend (`/api/mmse/chatbot/questions`)
- [ ] Frontend có thể fallback về local JSON nếu backend fail
- [ ] MMSE chatbot page load được và không còn lỗi connection refused

---

## 🚨 Các Lỗi Khác (Không Quan Trọng)

### Ethereum/MetaMask Error
```
Uncaught TypeError: Cannot set property ethereum of #<Window>
```
**Giải thích:** Lỗi từ MetaMask browser extension, không phải từ code của bạn. Có thể ignore.

### Clerk Warnings
```
Clerk: Clerk has been loaded with development keys
Clerk: The prop "afterSignInUrl" is deprecated
```
**Giải thích:** Chỉ là warnings, không phải errors. Có thể fix sau bằng cách:
- Set production Clerk keys trên Vercel
- Update deprecated props trong Clerk config

---

## 🎯 Expected Result

Sau khi fix:
1. ✅ Frontend gọi đúng production backend URL
2. ✅ MMSE questions load được từ backend
3. ✅ Nếu backend fail, fallback về local JSON
4. ✅ MMSE chatbot page hoạt động bình thường
5. ✅ Không còn lỗi "connection refused"

---

## 📞 Nếu Vẫn Không Hoạt Động

1. **Check Vercel Build Logs:**
   - Vào Vercel Dashboard → Deployments → Click vào deployment
   - Xem build logs có lỗi gì không

2. **Check Browser Console:**
   - Mở DevTools (F12)
   - Xem Console và Network tabs
   - Copy error messages

3. **Check Backend Logs:**
   - Vào Railway Dashboard
   - Xem logs có request từ Vercel không
   - Xem có CORS errors không

4. **Test Backend Directly:**
   ```bash
   curl https://your-backend.railway.app/api/mmse/chatbot/questions
   ```
   Nếu không response → Backend có vấn đề


# 🚀 HƯỚNG DẪN DEPLOY CHI TIẾT - TỪNG BƯỚC NHỎ

**Dành cho:** Anh Đình Phúc  
**Thời gian ước tính:** 1-2 giờ (lần đầu)  
**Chi phí:** $30-60/tháng

---

## 📋 MỤC LỤC

1. [Chuẩn bị trước khi deploy](#bước-0-chuẩn-bị)
2. [Tạo secrets](#bước-1-tạo-secrets)
3. [Tạo tài khoản Neon](#bước-2-tạo-database-neon)
4. [Tạo tài khoản Clerk](#bước-3-tạo-authentication-clerk)
5. [Deploy Backend lên Railway](#bước-4-deploy-backend-railway)
6. [Tạo Vercel Blob](#bước-5-tạo-vercel-blob)
7. [Deploy Frontend lên Vercel](#bước-6-deploy-frontend-vercel)
8. [Test hệ thống](#bước-7-test-hệ-thống)

---

## BƯỚC 0: CHUẨN BỊ

### Cần có sẵn:
- [ ] Email (Gmail OK)
- [ ] GitHub account
- [ ] Credit card (cho Vercel/Railway Pro nếu cần)
- [ ] OpenAI API key (nếu chưa có)
- [ ] Google Gemini API key (nếu chưa có)

### Cài đặt tools (nếu chưa có):
```bash
# 1. Git (kiểm tra)
git --version

# 2. Python (kiểm tra)
python --version  # Cần >= 3.11

# 3. Node.js (kiểm tra)
node --version    # Cần >= 18.17

# Nếu thiếu, download:
# - Git: https://git-scm.com/downloads
# - Python: https://www.python.org/downloads/
# - Node.js: https://nodejs.org/
```

---

## BƯỚC 1: TẠO SECRETS

### 1.1. Mở Terminal/PowerShell
```bash
# Windows: Nhấn Win + X → chọn PowerShell
# hoặc search "PowerShell"

# Chuyển đến thư mục project
cd D:\CognitiveAssessmentsystem
```

### 1.2. Chạy script tạo secrets
```bash
python scripts/generate_secrets.py
```

### 1.3. Lưu output
**⚠️ QUAN TRỌNG:**
1. Script sẽ in ra màn hình nhiều secrets
2. **Copy TẤT CẢ** text từ màn hình
3. **Paste vào Notepad++** hoặc Text Editor
4. **Save file:** `my-secrets.txt` (TẠM THỜI)
5. **Đừng đóng file này** - cần dùng suốt quá trình deploy

**Output sẽ có dạng:**
```
SECRET_KEY=XrT8k2mP9vLq3nWx...
JWT_SECRET_KEY=Zy4pQw7sA1dF6gH...
AES_KEY=...
...
```

### 1.4. Mở sẵn các trang web cần dùng
Mở từng tab này trên browser:

1. **Neon:** https://console.neon.tech
2. **Railway:** https://railway.app
3. **Vercel:** https://vercel.com
4. **Clerk:** https://dashboard.clerk.com
5. **OpenAI:** https://platform.openai.com/api-keys
6. **Gemini:** https://makersuite.google.com/app/apikey

---

## BƯỚC 2: TẠO DATABASE (NEON)

### 2.1. Đăng ký Neon
1. Vào: https://console.neon.tech
2. Click **"Sign Up"**
3. Chọn **"Continue with GitHub"** (dễ nhất)
4. Authorize Neon → Done

### 2.2. Tạo Project mới
1. Click **"Create a project"**
2. Điền thông tin:
   ```
   Project name: cognitive-assessment-prod
   Region: AWS / US East (Ohio)  [gần Việt Nam nhất]
   Postgres version: 15 (mặc định OK)
   ```
3. Click **"Create Project"**
4. Đợi 10-20 giây...

### 2.3. Lấy DATABASE_URL
1. Sau khi tạo xong, màn hình sẽ hiện **"Connection string"**
2. Copy **toàn bộ** string (dạng `postgresql://...`)
3. Paste vào file `my-secrets.txt` của bạn:
   ```
   DATABASE_URL=postgresql://user:pass@ep-...neon.tech/neondb?sslmode=require
   ```
4. **Lưu file lại!**

### 2.4. Enable Autoscaling (Optional nhưng recommended)
1. Trong Neon dashboard
2. Click **"Settings"** (bên trái)
3. **"Compute"** tab
4. Enable **"Autoscaling"**
5. Click **"Save changes"**

✅ **XONG BƯỚC 2!** Database đã sẵn sàng.

---

## BƯỚC 3: TẠO AUTHENTICATION (CLERK)

### 3.1. Đăng ký Clerk
1. Vào: https://dashboard.clerk.com
2. Click **"Sign up"**
3. Chọn **"Continue with GitHub"**
4. Authorize Clerk

### 3.2. Tạo Application
1. Click **"+ Add application"**
2. Điền thông tin:
   ```
   Application name: Cognitive Assessment
   ```
3. Chọn sign-in methods (tick):
   - [x] Email
   - [x] Google (optional)
   - [x] Password
4. Click **"Create application"**

### 3.3. Lấy API Keys
1. Sau khi tạo xong, sẽ thấy màn hình với 2 keys
2. Copy **Publishable Key** (bắt đầu với `pk_test_...`)
   ```
   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
   ```
3. Copy **Secret Key** (bắt đầu với `sk_test_...`)
   ```
   CLERK_SECRET_KEY=sk_test_...
   ```
4. Paste cả 2 vào file `my-secrets.txt`
5. **Lưu file!**

### 3.4. Cấu hình URLs (làm sau, bước 7)
*Chưa cần làm bây giờ, sẽ quay lại sau khi có Vercel URL*

✅ **XONG BƯỚC 3!** Authentication đã setup.

---

## BƯỚC 4: DEPLOY BACKEND (RAILWAY)

### 4.1. Đăng ký Railway
1. Vào: https://railway.app
2. Click **"Login"**
3. Chọn **"Login with GitHub"**
4. Authorize Railway

### 4.2. Tạo Project mới
1. Click **"New Project"**
2. Chọn **"Deploy from GitHub repo"**
3. Nếu chưa connect GitHub:
   - Click **"Configure GitHub App"**
   - Select **"All repositories"** hoặc chọn repo cụ thể
   - Click **"Install & Authorize"**
4. Chọn repository: `CognitiveAssessmentsystem`
5. Railway sẽ tự động phát hiện code


### 4.3. Configure Service
1. Sau khi Railway phát hiện repo
2. Click vào service vừa tạo
3. Click **"Settings"** tab
4. Scroll xuống **"Root Directory"**
5. Set: `backend`
6. Click **"Deploy"** (chờ build failed - OK, vì chưa có env vars)

### 4.4. Thêm Environment Variables
1. Click tab **"Variables"**
2. Click **"Raw Editor"** (ở góc phải)
3. Mở file `my-secrets.txt` của bạn
4. Copy & Paste những dòng sau:

```bash
# Critical
SECRET_KEY=<copy từ my-secrets.txt>
DATABASE_URL=<copy từ Neon>
OPENAI_API_KEY=<copy từ OpenAI dashboard>
GEMINI_API_KEY=<copy từ Google dashboard>

# Config
FLASK_ENV=production
FLASK_DEBUG=false
LOG_LEVEL=info
PYTHON_ENV=production

# CORS - SẼ UPDATE SAU KHI CÓ VERCEL URL
CORS_ORIGINS=http://localhost:3000

# Server
WEB_CONCURRENCY=2
GUNICORN_TIMEOUT=300
MAX_UPLOAD_SIZE_MB=16

# Storage
STORAGE_PATH=/tmp/storage
UPLOAD_PATH=/tmp/uploads
MODEL_PATH=./models
```

5. Click **"Add"** hoặc **"Update Variables"**

### 4.5. Trigger Deploy lại
1. Click tab **"Deployments"**
2. Click **"Deploy"** button (hoặc push code lên GitHub)
3. Đợi build (5-10 phút) - **CÀ PHÊ TIME ☕**

### 4.6. Lấy Railway URL
1. Sau khi build xong (status = SUCCESS)
2. Click tab **"Settings"**
3. Scroll xuống **"Domains"**
4. Copy URL (dạng: `https://cognitive-backend-production-xxxx.up.railway.app`)
5. Paste vào `my-secrets.txt`:
   ```
   RAILWAY_BACKEND_URL=https://your-app.up.railway.app
   ```
6. **Lưu file!**

### 4.7. Test Backend
Mở terminal mới:
```bash
# Replace URL với Railway URL của bạn
curl https://your-app.up.railway.app/api/health

# Nếu OK, sẽ trả về:
# {"status":"healthy",...}
```

**Nếu gặp lỗi:**
- Click tab **"Logs"** trong Railway
- Đọc error message
- Thường là thiếu env vars hoặc Dockerfile có vấn đề

✅ **XONG BƯỚC 4!** Backend đã live trên Railway.

---

## BƯỚC 5: TẠO VERCEL BLOB (STORAGE)

### 5.1. Đăng ký Vercel
1. Vào: https://vercel.com
2. Click **"Sign Up"**
3. Chọn **"Continue with GitHub"**
4. Authorize Vercel

### 5.2. Tạo Storage
1. Trong Vercel dashboard
2. Click **"Storage"** (menu bên trái)
3. Click **"Create Database"**
4. Chọn **"Blob"**
5. Điền:
   ```
   Store Name: cognitive-audio-files
   ```
6. Click **"Create"**

### 5.3. Lấy Token
1. Sau khi tạo xong
2. Click vào store vừa tạo
3. Click tab **".env.local"**
4. Copy dòng `BLOB_READ_WRITE_TOKEN=...`
5. Paste vào `my-secrets.txt`
6. **Lưu file!**

✅ **XONG BƯỚC 5!** File storage đã sẵn sàng.

---

## BƯỚC 6: DEPLOY FRONTEND (VERCEL)

### 6.1. Import Project
1. Trong Vercel dashboard
2. Click **"Add New..."** → **"Project"**
3. Click **"Import Git Repository"**
4. Chọn repo: `CognitiveAssessmentsystem`
5. Click **"Import"**

### 6.2. Configure Project
1. **Framework Preset:** Next.js (auto-detect)
2. **Root Directory:** Click **"Edit"** → Chọn `frontend`
3. **Build Command:** `npm run build` (mặc định OK)
4. **Output Directory:** `.next` (mặc định OK)
5. **Install Command:** `npm install` (mặc định OK)

### 6.3. Thêm Environment Variables
Click **"Environment Variables"** (mở rộng):

Thêm từng biến sau (click **"Add"** cho mỗi biến):

```bash
# Database
DATABASE_URL=<copy từ Neon>

# Backend URL
NEXT_PUBLIC_PYTHON_BACKEND_URL=<copy Railway URL từ my-secrets.txt>

# App URL - để tạm http://localhost:3000, sẽ update sau
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Clerk
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=<copy từ my-secrets.txt>
CLERK_SECRET_KEY=<copy từ my-secrets.txt>

# Storage
BLOB_READ_WRITE_TOKEN=<copy từ my-secrets.txt>

# Optional
NODE_ENV=production
```

**⚠️ Lưu ý:**
- Chọn **"Production"** cho Environment
- Mỗi biến thêm riêng, đừng paste cả block

### 6.4. Deploy
1. Click **"Deploy"**
2. Đợi build (3-5 phút) - **CÀ PHÊ TIME #2 ☕**

### 6.5. Lấy Vercel URL
1. Sau khi deploy xong
2. Click **"Visit"** button
3. Copy URL (dạng: `https://your-app.vercel.app`)
4. Paste vào `my-secrets.txt`:
   ```
   VERCEL_FRONTEND_URL=https://your-app.vercel.app
   ```
5. **Lưu file!**

### 6.6. Update Environment Variables
Bây giờ phải update lại env vars với URL thật:

1. Trong Vercel project
2. Click **"Settings"** → **"Environment Variables"**
3. Tìm `NEXT_PUBLIC_APP_URL`
4. Click **"Edit"**
5. Thay `http://localhost:3000` → `https://your-app.vercel.app` (Vercel URL thật)
6. Click **"Save"**
7. Click **"Redeploy"** (để apply thay đổi)

### 6.7. Update CORS_ORIGINS trên Railway
1. Quay lại Railway dashboard
2. Click vào backend project
3. Click tab **"Variables"**
4. Tìm `CORS_ORIGINS`
5. Update thành:
   ```
   CORS_ORIGINS=https://your-app.vercel.app,https://your-app-git-*.vercel.app
   ```
   (thay `your-app` bằng Vercel URL thật của bạn)
6. Click **"Update Variables"**
7. Railway sẽ tự restart

### 6.8. Update Clerk URLs
1. Quay lại Clerk dashboard
2. Click vào Application
3. Click **"Domains"** (bên trái)
4. Thêm domain:
   ```
   https://your-app.vercel.app
   ```
5. Click **"Add domain"**

✅ **XONG BƯỚC 6!** Frontend đã live trên Vercel.

---

## BƯỚC 7: TEST HỆ THỐNG

### 7.1. Test Backend Health
Mở terminal:
```bash
curl https://your-app.up.railway.app/api/health
```

**Expected:**
```json
{
  "status": "healthy",
  "timestamp": "...",
  "model_loaded": true
}
```

**Nếu lỗi:**
- Check Railway logs
- Verify DATABASE_URL
- Check OPENAI_API_KEY

### 7.2. Test Frontend Access
1. Mở browser
2. Vào: `https://your-app.vercel.app`
3. Trang web nên load

**Nếu blank page:**
- Mở DevTools (F12)
- Check Console tab
- Xem error messages
- Thường là CORS hoặc backend không connect

### 7.3. Test Authentication
1. Trên trang web
2. Click **"Sign In"** hoặc **"Register"**
3. Clerk modal nên hiện ra
4. Thử đăng ký account mới

**Nếu không hiện:**
- Check Clerk keys trong Vercel env vars
- Check Clerk dashboard → Domains

### 7.4. Test Full Flow
1. **Đăng nhập** với account vừa tạo
2. **Vào trang MMSE assessment**
3. **Upload audio file** (hoặc record)
4. **Submit assessment**
5. **Xem kết quả**

**Check từng bước:**
- Nếu upload lỗi → Check BLOB_READ_WRITE_TOKEN
- Nếu processing lỗi → Check Railway logs, OPENAI_API_KEY
- Nếu save lỗi → Check DATABASE_URL

### 7.5. Check Logs
**Railway (Backend):**
```bash
# Xem logs real-time
railway logs --tail 100
```

Hoặc trong Railway dashboard → Logs tab

**Vercel (Frontend):**
1. Vercel dashboard
2. Click project
3. Click **"Logs"** tab
4. Xem errors

### 7.6. Monitor trong 1 giờ
Sau khi deploy:
- Mở Railway logs
- Mở Vercel logs
- Test nhiều lần
- Check memory usage (Railway → Metrics)

✅ **XONG BƯỚC 7!** Hệ thống đã hoạt động!

---

## BƯỚC 8: POST-DEPLOYMENT (Optional nhưng nên làm)

### 8.1. Xóa file secrets tạm
```bash
# XÓA file my-secrets.txt
rm my-secrets.txt

# Hoặc move vào nơi an toàn (1Password, Bitwarden)
```

### 8.2. Setup Custom Domain (Optional)
**Nếu có domain riêng (ví dụ: cognitiveassessment.com):**

1. **Vercel:**
   - Settings → Domains
   - Add domain: `cognitiveassessment.com`
   - Follow DNS instructions
   - Update NEXT_PUBLIC_APP_URL

2. **Railway:**
   - Settings → Domains
   - Add domain: `api.cognitiveassessment.com`
   - Follow DNS instructions
   - Update NEXT_PUBLIC_PYTHON_BACKEND_URL

3. **Update Clerk:**
   - Add new domain to Clerk
   - Update CORS_ORIGINS trên Railway

### 8.3. Setup Monitoring (Recommended)
**Sentry (Error Tracking):**
1. Sign up: https://sentry.io
2. Create project
3. Copy DSN
4. Add to Vercel & Railway env vars:
   ```
   SENTRY_DSN=https://...@sentry.io/...
   ```

**UptimeRobot (Uptime Monitoring):**
1. Sign up: https://uptimerobot.com (Free)
2. Add monitor:
   - Type: HTTP(s)
   - URL: `https://your-app.railway.app/api/health`
   - Interval: 5 minutes
3. Add email alert

### 8.4. Setup Backups
**Database (Neon):**
1. Neon dashboard → Settings
2. Enable **"Auto Backups"**
3. Retention: 7 days (free) hoặc 30 days (paid)

**Code:**
```bash
# Ensure code is pushed to GitHub
git add .
git commit -m "Production deployment complete"
git push origin main
```

### 8.5. Document Production URLs
Tạo file `PRODUCTION_URLS.md`:
```markdown
# Production URLs

- Frontend: https://your-app.vercel.app
- Backend: https://your-app.railway.app
- Database: Neon console
- Clerk: https://dashboard.clerk.com
- Railway: https://railway.app/project/xxxxx
- Vercel: https://vercel.com/yourname/cognitive

Deployed: 2025-10-08
By: Đình Phúc
```

---

## 🚨 TROUBLESHOOTING - LỖI THƯỜNG GẶP

### Lỗi 1: Backend build failed
**Triệu chứng:** Railway build lỗi
**Nguyên nhân:** Dockerfile hoặc requirements.txt có vấn đề
**Fix:**
1. Check Railway logs
2. Verify `backend/Dockerfile` tồn tại
3. Verify `backend/requirements.txt` đúng
4. Try rebuild: Click **"Deploy"** lại

### Lỗi 2: Backend crashed after deploy
**Triệu chứng:** Build OK nhưng app crash
**Nguyên nhân:** Thiếu env vars hoặc sai DATABASE_URL
**Fix:**
1. Railway → Logs → Đọc error
2. Check tất cả env vars đã add chưa
3. Check DATABASE_URL format (phải bắt đầu với `postgresql://`)
4. Restart: Railway → Settings → Restart

### Lỗi 3: Frontend build failed
**Triệu chứng:** Vercel build lỗi
**Nguyên nhân:** TypeScript errors hoặc thiếu env vars
**Fix:**
1. Check Vercel build logs
2. Test build local:
   ```bash
   cd frontend
   npm install
   npm run build
   ```
3. Fix errors local trước
4. Push code, Vercel sẽ auto rebuild

### Lỗi 4: CORS error
**Triệu chứng:** Frontend console: "CORS policy blocked"
**Nguyên nhân:** CORS_ORIGINS chưa có Vercel URL
**Fix:**
1. Railway → Variables
2. Update `CORS_ORIGINS=https://your-app.vercel.app`
3. Restart backend

### Lỗi 5: 502 Bad Gateway
**Triệu chứng:** Backend trả về 502
**Nguyên nhân:** App quá tải hoặc OOM
**Fix:**
1. Upgrade Railway plan (8GB RAM)
2. Hoặc giảm model size:
   ```
   WHISPER_MODEL_SIZE=tiny
   ```

### Lỗi 6: Database connection failed
**Triệu chứng:** "could not connect to server"
**Nguyên nhân:** DATABASE_URL sai hoặc Neon down
**Fix:**
1. Copy lại DATABASE_URL từ Neon dashboard
2. Paste vào Railway variables
3. Verify format: `postgresql://user:pass@host.neon.tech:5432/db`
4. Restart backend

### Lỗi 7: Clerk authentication not working
**Triệu chứng:** Sign in button không hoạt động
**Nguyên nhân:** Clerk keys sai hoặc domain chưa add
**Fix:**
1. Clerk dashboard → API Keys
2. Copy lại keys
3. Update trong Vercel env vars
4. Clerk → Domains → Add Vercel URL
5. Redeploy frontend

### Lỗi 8: File upload failed
**Triệu chứng:** Upload audio lỗi
**Nguyên nhân:** BLOB_READ_WRITE_TOKEN sai
**Fix:**
1. Vercel dashboard → Storage → Blob
2. Copy token lại
3. Update trong Vercel env vars
4. Redeploy frontend

---

## 📊 MONITORING CHECKLIST

### Daily (first week):
- [ ] Check Railway logs for errors
- [ ] Check Vercel logs for errors
- [ ] Test main functionality
- [ ] Monitor memory usage (Railway → Metrics)

### Weekly:
- [ ] Review error trends
- [ ] Check database size (Neon dashboard)
- [ ] Review costs
- [ ] Test full user flow

### Monthly:
- [ ] Rotate secrets (SECRET_KEY, JWT_SECRET_KEY)
- [ ] Update dependencies
- [ ] Review and optimize
- [ ] Backup database manually (just in case)

---

## 💰 COST OPTIMIZATION TIPS

### Start Cheap ($5/month):
```
Railway Starter: $5 (512MB RAM)
Vercel Hobby: $0 (free)
Neon Free: $0 (0.5GB)
Total: $5/month
```

### When to Upgrade:
- **Railway → Pro ($20):** Khi backend crash vì OOM
- **Vercel → Pro ($20):** Khi cần serverless functions > 10s
- **Neon → Pro ($19):** Khi DB > 0.5GB hoặc cần autoscaling

### Save Money:
- Use Whisper `tiny` model instead of `base`
- Enable caching (Redis later)
- Lazy load ML models
- Monitor API usage (OpenAI/Gemini)

---

## ✅ SUCCESS CHECKLIST

Deploy thành công khi:

- [x] ✅ File secrets đã tạo
- [ ] ✅ Neon database created
- [ ] ✅ Clerk authentication setup
- [ ] ✅ Railway backend deployed
- [ ] ✅ Vercel blob created
- [ ] ✅ Vercel frontend deployed
- [ ] ✅ Health check returns 200
- [ ] ✅ Frontend loads
- [ ] ✅ Authentication works
- [ ] ✅ Can upload audio
- [ ] ✅ MMSE assessment completes
- [ ] ✅ Results display correctly
- [ ] ✅ No critical errors in logs

**Khi tất cả checked: 🎉 DEPLOYMENT SUCCESSFUL!**

---

## 📞 LIÊN HỆ HỖ TRỢ

**Gặp vấn đề không fix được?**

1. **Check docs:**
   - Railway: https://docs.railway.app
   - Vercel: https://vercel.com/docs
   - Neon: https://neon.tech/docs

2. **Check logs kỹ:**
   - Railway → Logs tab
   - Vercel → Logs tab
   - Browser DevTools → Console

3. **Search error:**
   - Google error message
   - Stack Overflow
   - GitHub Issues

4. **Community:**
   - Railway Discord
   - Vercel Discord
   - Railway/Vercel Twitter support

---

## 🎊 CHÚC MỪNG!

Nếu đã đến đây, anh Đình Phúc đã deploy thành công production! 🚀

**Next steps:**
1. Share link với team test
2. Gather feedback
3. Monitor for 1 week
4. Iterate and improve

**System is LIVE:** ✅  
**Production URL:** `https://your-app.vercel.app`  
**API URL:** `https://your-app.railway.app`

---

*Hướng dẫn này được tạo bởi Cursor AI*  
*Date: 2025-10-08*  
*Version: 1.0*

# 📤 HƯỚNG DẪN PUSH CODE LÊN GITHUB

## ✅ ĐÃ TẠO .gitignore

File `.gitignore` đã được tạo để bảo vệ secrets!

---

## 🚀 CÁCH 1: Command Line (PowerShell)

### Bước 1: Mở PowerShell
```bash
# Nhấn Win + X → chọn PowerShell
# Hoặc search "PowerShell"

# Chuyển đến thư mục project
cd D:\CognitiveAssessmentsystem
```

### Bước 2: Tạo repo trên GitHub
1. Vào: https://github.com
2. Click **"+"** (góc phải) → **"New repository"**
3. Điền:
   - Name: `CognitiveAssessmentsystem`
   - Description: `Vietnamese Cognitive Assessment with AI (MMSE)`
   - Private: ✅ (recommended)
   - **KHÔNG tick** "Add README", "Add .gitignore", "Choose license"
4. Click **"Create repository"**

### Bước 3: Run commands
```bash
# 1. Check Git đã init chưa
git status

# Nếu chưa init:
git init

# 2. Add remote (THAY YOUR_USERNAME!)
git remote add origin https://github.com/YOUR_USERNAME/CognitiveAssessmentsystem.git

# 3. Check files sẽ commit (verify .gitignore hoạt động)
git status

# Phải KHÔNG thấy:
# - .env files
# - my-secrets.txt
# - *.log files
# - node_modules/
# - __pycache__/

# 4. Add all files
git add .

# 5. Commit
git commit -m "Initial commit: Production deployment ready

- Backend Dockerfile và configs
- Frontend Next.js configs
- Security middleware
- Deploy scripts và docs
- .gitignore để bảo vệ secrets"

# 6. Rename branch to main
git branch -M main

# 7. Push
git push -u origin main
```

### Bước 4: Authentication
Khi push lần đầu:
- **Username:** your-github-username
- **Password:** Personal Access Token (KHÔNG phải password)

**Tạo Personal Access Token:**
1. GitHub → Settings (click avatar)
2. Scroll xuống → **Developer settings**
3. **Personal access tokens** → **Tokens (classic)**
4. Click **"Generate new token (classic)"**
5. Điền:
   - Note: `CognitiveAssessment Deploy`
   - Expiration: 90 days
   - Scopes: ✅ `repo` (full control of private repositories)
6. Click **"Generate token"**
7. **COPY TOKEN NGAY** - chỉ hiện 1 lần!
8. Paste vào PowerShell khi hỏi password

### Bước 5: Verify
```bash
# Check remote
git remote -v

# Mở browser
# Vào: https://github.com/YOUR_USERNAME/CognitiveAssessmentsystem
```

---

## 🖥️ CÁCH 2: GitHub Desktop (Dễ hơn)

### Bước 1: Download GitHub Desktop
1. Vào: https://desktop.github.com/
2. Click **"Download for Windows"**
3. Install
4. Mở GitHub Desktop
5. **Sign in** với GitHub account

### Bước 2: Add repository
1. File → **Add Local Repository**
2. Click **"Choose..."**
3. Chọn: `D:\CognitiveAssessmentsystem`
4. Click **"Add Repository"**

### Bước 3: Review changes
1. Xem list files bên trái
2. Verify KHÔNG thấy:
   - `.env` files
   - `my-secrets.txt`
   - `.log` files
   - `node_modules/`

### Bước 4: Commit
1. Ô **"Summary"** (bắt buộc):
   ```
   Initial commit: Production deployment ready
   ```
2. Ô **"Description"** (optional):
   ```
   - Backend Dockerfile và configs
   - Frontend Next.js configs
   - Security middleware
   - Deploy scripts và docs
   ```
3. Click **"Commit to main"**

### Bước 5: Publish
1. Click **"Publish repository"** (button lớn ở top)
2. Điền:
   - Name: `CognitiveAssessmentsystem` (auto-fill)
   - Description: `Vietnamese Cognitive Assessment with AI`
   - ✅ **Keep this code private** (recommended)
   - Organization: None (để personal account)
3. Click **"Publish repository"**
4. Đợi upload (2-5 phút)

### Bước 6: Verify
1. Mở browser
2. Vào: https://github.com/YOUR_USERNAME/CognitiveAssessmentsystem
3. Check files đã up chưa

---

## ⚠️ SECURITY CHECKLIST - TRƯỚC KHI PUSH

**CRITICAL:** Verify những file sau KHÔNG được commit:

```bash
# Run trong PowerShell:
git status

# Check output KHÔNG chứa:
```

❌ **KHÔNG được có:**
- `.env`
- `.env.local`
- `.env.production`
- `config.env`
- `my-secrets.txt`
- `secrets.txt`
- `PRODUCTION_URLS.md` (nếu có URLs thật)

✅ **Được phép có:**
- `.env.example`
- `env.template`
- `*.md` files (docs)
- Source code (`.py`, `.ts`, `.tsx`, `.js`)
- Config files (`Dockerfile`, `next.config.js`, etc.)

---

## 🔍 VERIFY .gitignore HOẠT ĐỘNG

### Test 1: Check git status
```bash
cd D:\CognitiveAssessmentsystem
git status

# Output KHÔNG được chứa:
# - .env
# - node_modules/
# - __pycache__/
# - *.log
```

### Test 2: Tạo file test
```bash
# Tạo file .env test
echo "TEST_SECRET=abc123" > .env

# Check git status
git status

# .env KHÔNG được hiện trong untracked files
# Nếu hiện → .gitignore có vấn đề!
```

### Test 3: Check files sẽ commit
```bash
git add .
git status

# Review list files trong "Changes to be committed"
# Verify KHÔNG có secrets
```

---

## 🚨 NẾU GẶP LỖI

### Lỗi 1: "fatal: not a git repository"
```bash
# Fix:
git init
git remote add origin https://github.com/YOUR_USERNAME/CognitiveAssessmentsystem.git
```

### Lỗi 2: "error: src refspec main does not exist"
```bash
# Fix: Phải commit trước
git add .
git commit -m "Initial commit"
git branch -M main
git push -u origin main
```

### Lỗi 3: "Authentication failed"
```bash
# Fix: Dùng Personal Access Token thay vì password
# Tạo token tại: https://github.com/settings/tokens
# Chọn scope: repo
```

### Lỗi 4: "remote origin already exists"
```bash
# Fix:
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/CognitiveAssessmentsystem.git
```

### Lỗi 5: File quá lớn (>100MB)
```bash
# Check files lớn:
find . -type f -size +100M

# Thường là:
# - node_modules/ (đã ignore)
# - model files (đã ignore)
# - audio files (đã ignore)

# Nếu vẫn bị, dùng Git LFS:
git lfs install
git lfs track "*.pth"
git lfs track "*.bin"
```

---

## 📋 POST-PUSH CHECKLIST

Sau khi push thành công:

- [ ] Verify trên GitHub: Files đã up
- [ ] Check secrets KHÔNG bị leak
- [ ] README.md hiển thị OK
- [ ] Update `HUONG_DAN_DEPLOY_CHI_TIET.md`:
  - Thay `YOUR_USERNAME` → username thật
- [ ] Tiếp tục với deployment (Railway/Vercel)

---

## 🎉 SUCCESS!

Khi thấy code trên GitHub:

**Next steps:**
1. ✅ Code đã an toàn trên GitHub
2. ➡️ Tiếp tục với BƯỚC 4 trong `HUONG_DAN_DEPLOY_CHI_TIET.md`
3. ➡️ Deploy Backend lên Railway
4. ➡️ Deploy Frontend lên Vercel

---

## 💡 TIPS

### Tip 1: Branch protection
Sau khi có code trên GitHub:
1. Repo → Settings → Branches
2. Add rule cho `main` branch
3. ✅ Require pull request before merging

### Tip 2: .gitignore test file
Tạo file `.gitignore-test.sh` để test:
```bash
#!/bin/bash
# Test .gitignore

echo "🔍 Testing .gitignore..."

# Create test files
echo "secret" > .env.test
echo "secret" > my-secrets.txt
mkdir -p node_modules/test
echo "test" > node_modules/test/file.js

# Check git status
echo ""
echo "Running: git status"
git status

# Cleanup
rm .env.test my-secrets.txt
rm -rf node_modules/

echo ""
echo "✅ Test complete. Verify no secrets in output above."
```

### Tip 3: Pre-commit hook
Tạo `.git/hooks/pre-commit`:
```bash
#!/bin/bash
# Pre-commit hook to prevent committing secrets

if git diff --cached --name-only | grep -E '\.env$|secrets\.txt$'
then
    echo "❌ ERROR: Attempting to commit secrets!"
    echo "Files blocked:"
    git diff --cached --name-only | grep -E '\.env$|secrets\.txt$'
    exit 1
fi

echo "✅ Pre-commit check passed"
```

---

**Ready to push?** 🚀  
**Follow steps above!** ⬆️


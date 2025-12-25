# 🚀 Cognitive Assessment System - Deployment Guide

## Backend Deployment Issues & Solutions

### ❌ Issue: Backend fails to run in production
**Symptoms:**
- Backend deploys successfully but crashes on startup
- No environment variables loaded
- Missing API keys for AI services

**Root Cause:**
Backend requires environment variables from `.env` or `config.env` files, but these files are not committed to Git for security reasons.

### ✅ Solution: Environment Variables Setup

#### 1. **Create `.env` file in backend directory**

Copy `backend-env.production.example` to `backend/.env` and fill in your production values:

```bash
cd backend
cp backend-env.production.example .env
# Edit .env with your actual production values
```

#### 2. **Required Environment Variables for Production**

| Variable | Source | Description |
|----------|--------|-------------|
| `DATABASE_URL` | Railway/Neon | PostgreSQL connection string |
| `OPENAI_API_KEY` | OpenAI | API key for GPT evaluation |
| `GEMINI_API_KEY` | Google AI Studio | API key for Gemini transcription |
| `BLOB_READ_WRITE_TOKEN` | Vercel Blob | File storage token |
| `SECRET_KEY` | Generate random | Flask secret key (32+ chars) |
| `JWT_SECRET_KEY` | Generate random | JWT signing key |

#### 3. **Get API Keys**

- **OpenAI API Key**: https://platform.openai.com/api-keys
- **Gemini API Key**: https://aistudio.google.com/app/apikey
- **Vercel Blob Token**: Vercel dashboard → Storage → Blob
- **Database URL**: Railway/Neon dashboard → Connection string

#### 4. **Generate Secure Keys**

```bash
# Generate SECRET_KEY (32+ characters)
python -c "import secrets; print(secrets.token_hex(32))"

# Generate JWT_SECRET_KEY (32+ characters)
python -c "import secrets; print(secrets.token_hex(32))"
```

#### 5. **Deployment Checklist**

- [ ] `.env` file created in `backend/` directory
- [ ] All required API keys filled in
- [ ] Database URL configured
- [ ] Secure keys generated (not using defaults)
- [ ] Test deployment locally with production env
- [ ] Verify all endpoints work in production

#### 6. **Local Testing with Production Environment**

```bash
cd backend
# Test with production environment
python -c "
import os
from dotenv import load_dotenv
load_dotenv('.env')
print('✅ Environment loaded successfully')
print(f'DATABASE_URL: {\"***\" + os.getenv(\"DATABASE_URL\", \"\")[-10:] if os.getenv(\"DATABASE_URL\") else \"NOT SET\"}')
print(f'OPENAI_API_KEY: {\"***\" + os.getenv(\"OPENAI_API_KEY\", \"\")[-4:] if os.getenv(\"OPENAI_API_KEY\") else \"NOT SET\"}')
print(f'GEMINI_API_KEY: {\"***\" + os.getenv(\"GEMINI_API_KEY\", \"\")[-4:] if os.getenv(\"GEMINI_API_KEY\") else \"NOT SET\"}')
"
```

#### 7. **Common Issues & Fixes**

**Issue: "No environment file found"**
- Solution: Create `backend/.env` file with required variables

**Issue: "API key invalid"**
- Solution: Verify API keys are correct and have sufficient credits

**Issue: "Database connection failed"**
- Solution: Check DATABASE_URL format and database permissions

**Issue: "Blob storage failed"**
- Solution: Verify Vercel Blob token and permissions

#### 8. **Railway Deployment Specific**

For Railway deployment, set these environment variables in Railway dashboard:

```bash
# Railway Environment Variables (Dashboard)
DATABASE_URL=postgresql://...
OPENAI_API_KEY=sk-proj-...
GEMINI_API_KEY=AIzaSy...
BLOB_READ_WRITE_TOKEN=vercel_blob_...
SECRET_KEY=<generated-32-char-key>
JWT_SECRET_KEY=<generated-32-char-key>
WEB_CONCURRENCY=2
GUNICORN_TIMEOUT=300
LOG_LEVEL=info
```

### 📝 Notes

- Never commit `.env` files to GitHub
- Use different API keys for development and production
- Test all functionality after deployment
- Monitor logs for any runtime errors
- Keep API keys secure and rotate regularly

### 🔧 Quick Fix for Deployer

If you're deploying this system, run these commands:

```bash
# 1. Create environment file
cd backend
cp backend-env.production.example .env

# 2. Edit .env with your production values
# (Use your favorite editor)

# 3. Test environment loading
python -c "from dotenv import load_dotenv; import os; load_dotenv('.env'); print('✅ Environment loaded')"

# 4. Deploy
# (Follow your deployment platform's instructions)
```

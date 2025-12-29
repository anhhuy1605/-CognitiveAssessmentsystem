# PHẦN 10: YÊU CẦU HỆ THỐNG

## 1. Hardware Requirements

### 1.1. Development Environment

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| **CPU** | 4 cores (2.0 GHz) | 8+ cores (3.0+ GHz) | Multi-core for parallel processing |
| **RAM** | 8 GB | 16 GB+ | 16GB+ required for Whisper ASR model |
| **Storage** | 20 GB free | 50 GB+ free | For dependencies, models, audio files |
| **Network** | 10 Mbps | 50+ Mbps | For API calls (Gemini, OpenAI) |
| **GPU** | Not required | CUDA-capable GPU (optional) | For faster ML model inference |

**Notes:**
- **RAM**: 16GB+ strongly recommended for running Whisper ASR model and ML inference
- **Storage**: Includes space for:
  - Python packages (~5-10 GB)
  - Node.js packages (~2-3 GB)
  - ML models (PhoBERT, transformers) (~5-10 GB)
  - Audio files and temporary data (~5-10 GB)
  - Database (if local) (~1-5 GB)
- **GPU**: Optional but recommended for faster processing. CPU-only mode is fully supported.

---

### 1.2. Production Server

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| **CPU** | 4 cores (2.5 GHz) | 8+ cores (3.5+ GHz) | For concurrent requests |
| **RAM** | 8 GB | 16 GB+ | For ML models and caching |
| **Storage** | 50 GB SSD | 100+ GB SSD | Fast I/O for audio processing |
| **Network** | 100 Mbps | 1 Gbps+ | For API calls and file uploads |
| **GPU** | Not required | CUDA-capable GPU (optional) | For faster inference |

**Deployment Platforms:**
- **Railway**: Recommended (supports Docker, auto-scaling)
- **Heroku**: Supported (requires buildpacks)
- **AWS EC2**: Supported (t2.medium+ recommended)
- **DigitalOcean**: Supported (4GB+ droplet recommended)
- **Vercel**: Frontend only (backend requires separate hosting)

**Container Requirements:**
- **Docker**: Supported (see `backend/Dockerfile`)
- **Memory Limit**: 2GB+ for container
- **CPU Limit**: 2+ cores recommended

---

### 1.3. Client (End User)

#### Desktop

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 10, macOS 10.14+, Linux (Ubuntu 18.04+) | Latest stable version |
| **CPU** | Dual-core (1.5 GHz) | Quad-core (2.0+ GHz) |
| **RAM** | 4 GB | 8 GB+ |
| **Browser** | Chrome 90+, Firefox 88+, Edge 90+, Safari 14+ | Latest version |
| **Network** | 5 Mbps | 25+ Mbps |
| **Microphone** | Built-in or USB | USB with noise cancellation |

#### Mobile

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | iOS 14+, Android 8.0+ | iOS 16+, Android 12+ |
| **RAM** | 2 GB | 4 GB+ |
| **Browser** | Safari (iOS), Chrome (Android) | Latest version |
| **Network** | 4G (5 Mbps) | 4G/5G (25+ Mbps) |
| **Microphone** | Built-in | Built-in with noise cancellation |

**Browser Compatibility:**
- ✅ Chrome 90+ (Desktop & Mobile)
- ✅ Firefox 88+ (Desktop)
- ✅ Edge 90+ (Desktop)
- ✅ Safari 14+ (Desktop & iOS)
- ⚠️ Opera 76+ (Desktop)
- ❌ Internet Explorer (not supported)

**Required Browser Features:**
- MediaRecorder API (for audio recording)
- getUserMedia API (for microphone access)
- Web Audio API (for audio processing)
- Fetch API (for HTTP requests)
- WebSocket API (optional, for real-time features)

---

## 2. Software Requirements

### 2.1. Backend (Python)

| Software | Version | Required | Notes |
|----------|---------|----------|-------|
| **Python** | 3.8+ | ✅ Yes | 3.11.6 recommended (used in Dockerfile) |
| **pip** | 23.0+ | ✅ Yes | Latest version recommended |
| **FFmpeg** | 4.0+ | ✅ Yes | For audio format conversion |
| **Java** | 8+ | ⚠️ Optional | Only if using VnCoreNLP (deprecated) |

**Python Version Details:**
- **Minimum**: Python 3.8 (from `setup.py`)
- **Recommended**: Python 3.11.6 (from `backend/Dockerfile`)
- **Tested Versions**: 3.8, 3.9, 3.10, 3.11

**System Dependencies (Linux/macOS):**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    python3.11 \
    python3-pip \
    ffmpeg \
    libsndfile1 \
    libpq-dev \
    gcc \
    g++

# macOS (Homebrew)
brew install python@3.11 ffmpeg libsndfile postgresql
```

**System Dependencies (Windows):**
- Install Python 3.11 from [python.org](https://www.python.org/downloads/)
- Install FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html) or via Chocolatey:
  ```powershell
  choco install ffmpeg
  ```

---

### 2.2. Frontend (Node.js)

| Software | Version | Required | Notes |
|----------|---------|----------|-------|
| **Node.js** | >= 18.17.0 | ✅ Yes | LTS version recommended |
| **npm** | >= 9.0.0 | ✅ Yes | Comes with Node.js |
| **pnpm** | Latest | ⚠️ Optional | Alternative to npm |

**Node.js Version Details:**
- **Minimum**: Node.js 18.17.0 (from `package.json` engines)
- **Recommended**: Node.js 20.x LTS or 22.x LTS
- **npm**: >= 9.0.0 (from `package.json` engines)

**Installation:**
```bash
# Using nvm (recommended)
nvm install 20
nvm use 20

# Or download from nodejs.org
# https://nodejs.org/
```

---

### 2.3. Database

| Software | Version | Required | Notes |
|----------|---------|----------|-------|
| **PostgreSQL** | 14+ | ✅ Yes | For production (Neon) |
| **SQLite** | 3.30+ | ⚠️ Optional | For local development/testing |

**PostgreSQL Details:**
- **Production**: Neon PostgreSQL (serverless, managed)
- **Local Development**: PostgreSQL 14+ or SQLite
- **Connection**: Via `DATABASE_URL` environment variable

**Neon Database:**
- **Tier**: Free tier available (3 GB storage, 1 project)
- **Limits**: 
  - Free: 3 GB storage, 1 project
  - Pro: 10 GB storage, unlimited projects
  - Scale: Custom limits
- **Connection String Format**: `postgresql://user:password@host/database`

---

### 2.4. Development Tools (Optional)

| Tool | Purpose | Required |
|------|---------|----------|
| **Git** | Version control | Recommended |
| **Docker** | Containerization | Optional |
| **VS Code** | Code editor | Recommended |
| **Postman** | API testing | Optional |

---

## 3. External Services

### 3.1. Gemini API (Google AI)

**Purpose:** Speech-to-Text (ASR) for Vietnamese audio transcription

**API Details:**
- **Service**: Google Generative AI (Gemini)
- **Model**: `gemini-2.5-flash` (default, configurable)
- **Endpoint**: `https://generativelanguage.googleapis.com/v1beta/models/`
- **Authentication**: API Key (GEMINI_API_KEY)

**Quota & Pricing:**

| Tier | Requests/Minute | Requests/Day | Cost |
|------|----------------|--------------|------|
| **Free Tier** | 15 | Unlimited* | Free |
| **Paid Tier** | 60+ | Unlimited | Pay-per-use |

**Limits:**
- **Free Tier**: 15 requests per minute (rate limit)
- **File Size**: Max 20 MB per audio file
- **Duration**: Recommended < 5 minutes per audio
- **Concurrent Requests**: Limited by quota

**Getting API Key:**
1. Visit: https://aistudio.google.com/app/apikey
2. Sign in with Google account
3. Create new API key
4. Copy key (format: `AIzaSy...`)

**Configuration:**
```bash
# Set environment variable
export GEMINI_API_KEY="AIzaSy_YOUR_KEY_HERE"

# Or in .env file
echo "GEMINI_API_KEY=AIzaSy_YOUR_KEY_HERE" >> .env
```

**Error Handling:**
- **Quota Exceeded**: Wait 1-2 minutes before retry
- **Invalid Key**: Check API key format
- **File Too Large**: Compress audio or split into chunks

---

### 3.2. OpenAI API

**Purpose:** GPT-4o evaluation for transcript analysis and validation

**API Details:**
- **Service**: OpenAI API
- **Model**: `gpt-4o` (default)
- **Endpoint**: `https://api.openai.com/v1/chat/completions`
- **Authentication**: API Key (OPENAI_API_KEY)

**Quota & Pricing:**

| Model | Input Cost | Output Cost | Context Window |
|-------|------------|-------------|----------------|
| **gpt-4o** | $2.50 / 1M tokens | $10.00 / 1M tokens | 128K tokens |

**Limits:**
- **Rate Limit**: Varies by tier (free tier: 3 requests/minute)
- **Token Limit**: 128K tokens per request
- **Concurrent Requests**: Limited by tier

**Getting API Key:**
1. Visit: https://platform.openai.com/api-keys
2. Sign in or create account
3. Create new API key
4. Copy key (format: `sk-proj-...`)

**Configuration:**
```bash
# Set environment variable
export OPENAI_API_KEY="sk-proj-YOUR_KEY_HERE"

# Or in .env file
echo "OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE" >> .env
```

**Cost Estimation:**
- **Per Assessment**: ~500-1000 tokens (~$0.0025-0.005)
- **Monthly (100 assessments)**: ~$0.25-0.50
- **Monthly (1000 assessments)**: ~$2.50-5.00

---

### 3.3. Neon Database

**Purpose:** PostgreSQL database for storing assessment results, sessions, and user data

**Service Details:**
- **Provider**: Neon (neon.tech)
- **Type**: Serverless PostgreSQL
- **Region**: Multiple regions available
- **Connection**: Via `DATABASE_URL` environment variable

**Tier & Limits:**

| Tier | Storage | Projects | Compute | Cost |
|------|---------|----------|---------|------|
| **Free** | 3 GB | 1 | Shared | Free |
| **Pro** | 10 GB | Unlimited | Dedicated | $19/month |
| **Scale** | Custom | Unlimited | Custom | Custom |

**Features:**
- ✅ Automatic backups
- ✅ Point-in-time recovery
- ✅ Branching (database branching for dev/staging)
- ✅ Serverless (auto-scaling)
- ✅ Connection pooling

**Getting Started:**
1. Visit: https://neon.tech
2. Sign up for free account
3. Create new project
4. Copy connection string (format: `postgresql://user:password@host/database`)

**Configuration:**
```bash
# Set environment variable
export DATABASE_URL="postgresql://user:password@host/database"

# Or in .env file
echo "DATABASE_URL=postgresql://user:password@host/database" >> .env
```

**Migration:**
```bash
# Frontend (Drizzle)
cd frontend
npm run drizzle:generate
npm run drizzle:migrate

# Backend (manual)
cd backend
python create_missing_tables.py
```

---

### 3.4. Vercel Blob (Optional)

**Purpose:** Audio file storage for production

**Service Details:**
- **Provider**: Vercel
- **Type**: Object storage
- **Use Case**: Store uploaded audio files

**Tier & Limits:**

| Tier | Storage | Bandwidth | Cost |
|------|---------|-----------|------|
| **Free** | 1 GB | 100 GB/month | Free |
| **Pro** | 100 GB | 1 TB/month | $20/month |

**Configuration:**
```bash
# Set environment variable
export BLOB_READ_WRITE_TOKEN="vercel_blob_token"

# Or in .env file
echo "BLOB_READ_WRITE_TOKEN=vercel_blob_token" >> .env
```

---

## 4. Installation Steps

### 4.1. Backend Installation

#### Step 1: Prerequisites

**Windows:**
```powershell
# Check Python version
python --version
# Should be 3.8 or higher

# Check FFmpeg
ffmpeg -version
# If not installed, download from https://ffmpeg.org/download.html
```

**Linux/macOS:**
```bash
# Check Python version
python3 --version
# Should be 3.8 or higher

# Install FFmpeg (if not installed)
# Ubuntu/Debian:
sudo apt-get install ffmpeg

# macOS:
brew install ffmpeg
```

#### Step 2: Clone Repository

```bash
# Clone the repository
git clone <repository-url>
cd CognitiveAssessmentsystem/backend
```

#### Step 3: Create Virtual Environment

**Windows:**
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1
# If PowerShell execution policy error, run:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Linux/macOS:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

#### Step 4: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Optional: Install additional modules
pip install -r requirements_modules.txt
```

**Expected Output:**
```
Successfully installed numpy-1.24.3 pandas-2.0.3 scikit-learn-1.3.0 ...
```

#### Step 5: Configure Environment Variables

```bash
# Create .env file
cd backend
touch .env  # Linux/macOS
# Or create .env file manually on Windows

# Add required variables
cat > .env << EOF
GEMINI_API_KEY=AIzaSy_YOUR_KEY_HERE
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
DATABASE_URL=postgresql://user:password@host/database
API_TOKEN=change-me-token
SECRET_KEY=your-secret-key-here
EOF
```

**Required Environment Variables:**
- `GEMINI_API_KEY`: Google Gemini API key (required)
- `OPENAI_API_KEY`: OpenAI API key (required)
- `DATABASE_URL`: PostgreSQL connection string (optional for local dev)
- `API_TOKEN`: Backend API authentication token (required)
- `SECRET_KEY`: Flask secret key (required)

#### Step 6: Verify Installation

```bash
# Check setup
python check_setup.py

# Expected output:
# ✅ Gemini API key: AIza...
# ✅ OpenAI API key: sk-proj-...
# ✅ Python version: 3.11.6
# ✅ FFmpeg: installed
# ✅ Hệ thống đã sẵn sàng!
```

#### Step 7: Initialize Database (Optional)

```bash
# Create database tables
python create_missing_tables.py

# Expected output:
# ✅ Created sessions table
# ✅ Created questions table
# ✅ Created stats table
# ✅ Created temp_questions table
```

#### Step 8: Start Backend Server

```bash
# Run Flask app
python app.py

# Expected output:
# * Running on http://127.0.0.1:5001
# * Debug mode: on
```

**Backend will be available at:** `http://localhost:5001`

---

### 4.2. Frontend Installation

#### Step 1: Prerequisites

```bash
# Check Node.js version
node --version
# Should be 18.17.0 or higher

# Check npm version
npm --version
# Should be 9.0.0 or higher
```

#### Step 2: Navigate to Frontend Directory

```bash
cd CognitiveAssessmentsystem/frontend
```

#### Step 3: Install Dependencies

```bash
# Install npm packages
npm install

# Expected output:
# added 1234 packages, and audited 1235 packages in 45s
```

**Note:** First installation may take 5-10 minutes depending on network speed.

#### Step 4: Configure Environment Variables

```bash
# Create .env.local file
touch .env.local  # Linux/macOS
# Or create .env.local file manually on Windows

# Add required variables
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:5001
DATABASE_URL=postgresql://user:password@host/database
NEXT_PUBLIC_BASE_PATH=
CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
BLOB_READ_WRITE_TOKEN=vercel_blob_token
EOF
```

**Required Environment Variables:**
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: `http://localhost:5001`)
- `DATABASE_URL`: PostgreSQL connection string (Neon)
- `CLERK_PUBLISHABLE_KEY`: Clerk authentication public key (optional)
- `CLERK_SECRET_KEY`: Clerk authentication secret key (optional)
- `BLOB_READ_WRITE_TOKEN`: Vercel Blob token (optional)

#### Step 5: Generate Database Schema

```bash
# Generate Drizzle migrations
npm run drizzle:generate

# Push schema to database
npm run drizzle:migrate
```

#### Step 6: Start Development Server

```bash
# Start Next.js dev server
npm run dev

# Expected output:
# ▲ Next.js 15.2.3
# - Local:        http://localhost:3000
# - ready started server on 0.0.0.0:3000
```

**Frontend will be available at:** `http://localhost:3000`

---

### 4.3. Full System Startup

#### Option 1: Manual Startup

**Terminal 1 (Backend):**
```bash
cd backend
source venv/bin/activate  # Linux/macOS
# Or: .\venv\Scripts\Activate.ps1  # Windows
python app.py
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

#### Option 2: Using Scripts

**Windows:**
```powershell
# Run complete system
.\start_complete_system.py
```

**Linux/macOS:**
```bash
# Run complete system
python3 start_complete_system.py
```

---

## 5. Verification Checklist

### 5.1. Backend Verification

- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip list`)
- [ ] FFmpeg installed and in PATH
- [ ] Environment variables configured (`.env` file)
- [ ] Gemini API key set and working
- [ ] OpenAI API key set and working
- [ ] Database connection working (if configured)
- [ ] Backend server starts without errors
- [ ] Health check endpoint responds: `http://localhost:5001/api/health`

### 5.2. Frontend Verification

- [ ] Node.js 18.17.0+ installed
- [ ] npm 9.0.0+ installed
- [ ] All dependencies installed (`npm list`)
- [ ] Environment variables configured (`.env.local` file)
- [ ] Database schema generated and migrated
- [ ] Frontend server starts without errors
- [ ] Frontend accessible at `http://localhost:3000`
- [ ] Can connect to backend API

### 5.3. Integration Verification

- [ ] Frontend can call backend API
- [ ] Audio recording works in browser
- [ ] Audio upload to backend works
- [ ] Transcription (Gemini ASR) works
- [ ] GPT evaluation works
- [ ] Database save works (if configured)
- [ ] Results display correctly

---

## 6. Troubleshooting

### 6.1. Common Installation Issues

**Issue: Python version mismatch**
```bash
# Solution: Use correct Python version
python3.11 -m venv venv
python3.11 -m pip install -r requirements.txt
```

**Issue: FFmpeg not found**
```bash
# Windows: Add FFmpeg to PATH
# Linux: sudo apt-get install ffmpeg
# macOS: brew install ffmpeg
```

**Issue: Node.js version too old**
```bash
# Solution: Update Node.js
nvm install 20
nvm use 20
```

**Issue: npm install fails**
```bash
# Solution: Clear cache and retry
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

**Issue: Database connection fails**
```bash
# Solution: Check DATABASE_URL format
# Should be: postgresql://user:password@host/database
# Not: postgres://user:password@host/database
```

### 6.2. Runtime Issues

**Issue: "Gemini API key not configured"**
```bash
# Solution: Set environment variable
export GEMINI_API_KEY="AIzaSy_YOUR_KEY"
# Or add to .env file
```

**Issue: "Quota exceeded" (Gemini)**
- **Cause**: Free tier limit (15 requests/minute)
- **Solution**: Wait 1-2 minutes before retry

**Issue: "Module not found" (Python)**
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt
```

**Issue: "Port already in use"**
```bash
# Solution: Change port or kill process
# Backend: Change port in app.py
# Frontend: Change port in package.json scripts
```

---

## 7. Production Deployment

### 7.1. Backend Deployment

**Using Docker:**
```bash
# Build image
docker build -t cognitive-backend:latest -f backend/Dockerfile .

# Run container
docker run -d \
  -p 5001:5001 \
  -e GEMINI_API_KEY="..." \
  -e OPENAI_API_KEY="..." \
  -e DATABASE_URL="..." \
  cognitive-backend:latest
```

**Using Railway:**
1. Connect GitHub repository
2. Set environment variables
3. Deploy automatically

**Using Heroku:**
```bash
heroku create cognitive-backend
heroku config:set GEMINI_API_KEY="..."
heroku config:set OPENAI_API_KEY="..."
heroku config:set DATABASE_URL="..."
git push heroku main
```

### 7.2. Frontend Deployment

**Using Vercel:**
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

**Using Netlify:**
```bash
# Build
npm run build

# Deploy
netlify deploy --prod
```

---

## 8. Summary

### Minimum Requirements Summary

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 4 cores | 8+ cores |
| **RAM** | 8 GB | 16 GB+ |
| **Storage** | 20 GB | 50 GB+ |
| **Python** | 3.8 | 3.11.6 |
| **Node.js** | 18.17.0 | 20.x LTS |
| **PostgreSQL** | 14+ | Neon (managed) |

### External Services Required

1. **Gemini API** (Free tier available)
2. **OpenAI API** (Pay-per-use)
3. **Neon Database** (Free tier available)

### Estimated Costs (Monthly)

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| **Gemini API** | Free (15 req/min) | Pay-per-use |
| **OpenAI API** | Limited | ~$0.25-5.00 (100-1000 assessments) |
| **Neon Database** | Free (3 GB) | $19/month (Pro) |
| **Vercel Blob** | Free (1 GB) | $20/month (Pro) |

**Total (Free Tier):** $0/month  
**Total (Paid Tier, 1000 assessments/month):** ~$44-49/month

---

## Notes

1. **Development vs Production**: Development can use free tiers. Production may require paid tiers for higher limits.

2. **API Keys**: Keep API keys secure. Never commit to version control. Use environment variables or secret management.

3. **Database**: Neon free tier is sufficient for development and small-scale production. Upgrade to Pro for larger deployments.

4. **Scaling**: System can scale horizontally by adding more backend instances behind a load balancer.

5. **Monitoring**: Set up monitoring for API quotas, database usage, and error rates in production.



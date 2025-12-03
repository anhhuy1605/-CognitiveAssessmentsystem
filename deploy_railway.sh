#!/bin/bash
# Railway Backend Deployment Script
# Run this after logging in to Railway

echo "🚂 Starting Railway Backend Deployment..."
echo "=========================================="

# Check if logged in
if ! railway status > /dev/null 2>&1; then
    echo "❌ Not logged in to Railway. Please run 'railway login' first"
    exit 1
fi

# Link project
echo "🔗 Linking project..."
railway link

# Set environment variables (no hardcoded secrets)
echo "⚙️ Setting environment variables..."

# Core Flask settings
railway variables set FLASK_ENV=production
railway variables set DEBUG=false

# Database (provide via prompt or paste; NEVER hardcode)
read -p "Enter DATABASE_URL (from Neon): " DBURL
railway variables set DATABASE_URL="$DBURL"

# Secrets (generated securely at runtime)
SECRET_KEY_GEN=$(python - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
)
JWT_SECRET_KEY_GEN=$(python - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
)
API_TOKEN_GEN=$(python - <<'PY'
import secrets
print(secrets.token_urlsafe(24))
PY
)
railway variables set SECRET_KEY="$SECRET_KEY_GEN"
railway variables set JWT_SECRET_KEY="$JWT_SECRET_KEY_GEN"
railway variables set API_TOKEN="$API_TOKEN_GEN"

# AI Services
railway variables set OPENAI_API_KEY="your_openai_key_here"
railway variables set GEMINI_API_KEY="your_gemini_key_here"
railway variables set GOOGLE_API_KEY="your_gemini_key_here"

# Authentication
railway variables set CLERK_SECRET_KEY="your_clerk_secret_key"

# Audio settings
railway variables set ENABLE_PAID_TRANSCRIPTION=true
railway variables set TRANSCRIPTION_BUDGET_LIMIT=10.00
railway variables set VI_ASR_MODEL="nguyenvulebinh/wav2vec2-large-vietnamese-250h"

# Storage
railway variables set STORAGE_PATH="./storage"
railway variables set UPLOAD_PATH="./uploads"
railway variables set RECORDINGS_PATH="./recordings"

# Performance
railway variables set MAX_WORKERS=4
railway variables set CACHE_TTL=3600

echo "🚀 Deploying to Railway..."
railway deploy

echo "⏳ Waiting for deployment..."
sleep 30

echo "🌐 Getting backend URL..."
BACKEND_URL=$(railway domain)
echo "✅ Backend deployed at: $BACKEND_URL"

echo ""
echo "🎉 Railway backend deployment completed!"
echo "Backend URL: $BACKEND_URL"
echo ""
echo "Next step: Copy this URL for Vercel frontend deployment"

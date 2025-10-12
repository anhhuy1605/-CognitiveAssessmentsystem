#!/usr/bin/env python3
# ==================================
# scripts/generate_secrets.py
# ==================================
"""
Generate cryptographically secure secrets for production deployment
Usage: python scripts/generate_secrets.py
"""

import secrets
import string
from datetime import datetime
import sys

def generate_secret(length=32):
    """Generate URL-safe secret token"""
    return secrets.token_urlsafe(length)

def generate_hex_secret(length=32):
    """Generate hexadecimal secret"""
    return secrets.token_hex(length)

def generate_password(length=16, include_symbols=True):
    """Generate random password with mixed characters"""
    alphabet = string.ascii_letters + string.digits
    if include_symbols:
        alphabet += "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def generate_django_secret():
    """Generate Django-style SECRET_KEY"""
    chars = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
    return ''.join(secrets.choice(chars) for _ in range(50))

def main():
    print("=" * 70)
    print("🔐 PRODUCTION SECRETS GENERATOR")
    print("=" * 70)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("⚠️  CRITICAL: Save these to password manager IMMEDIATELY")
    print("⚠️  DO NOT commit these to Git")
    print("⚠️  DO NOT share via chat/email")
    print()
    print("=" * 70)
    print()
    
    # ==================================
    # BACKEND SECRETS
    # ==================================
    print("# ==== BACKEND SECRETS (for Railway) ====")
    print()
    print("# Flask secret key")
    print(f"SECRET_KEY={generate_secret(32)}")
    print()
    print("# JWT secret key (if using JWT authentication)")
    print(f"JWT_SECRET_KEY={generate_secret(32)}")
    print()
    print("# Session secret (if using Flask-Session)")
    print(f"SESSION_SECRET_KEY={generate_secret(32)}")
    print()
    
    # ==================================
    # ENCRYPTION KEYS
    # ==================================
    print("# ==== ENCRYPTION KEYS ====")
    print()
    print("# AES encryption key (16, 24, or 32 bytes)")
    print(f"AES_KEY={generate_hex_secret(16)}")
    print()
    print("# General encryption key")
    print(f"ENCRYPTION_KEY={generate_hex_secret(32)}")
    print()
    
    # ==================================
    # DATABASE
    # ==================================
    print("# ==== DATABASE ====")
    print()
    print("# Get DATABASE_URL from Neon/Vercel dashboard")
    print("# Format: postgresql://user:password@host:5432/database")
    print("DATABASE_URL=postgresql://...")
    print()
    
    # ==================================
    # AI SERVICES
    # ==================================
    print("# ==== AI SERVICE KEYS (get from dashboards) ====")
    print()
    print("# OpenAI API key")
    print("# Get from: https://platform.openai.com/api-keys")
    print("OPENAI_API_KEY=sk-proj-...")
    print()
    print("# Google Gemini API key")
    print("# Get from: https://makersuite.google.com/app/apikey")
    print("GEMINI_API_KEY=AIzaSy...")
    print("GOOGLE_API_KEY=AIzaSy...  # Same as GEMINI_API_KEY")
    print()
    
    # ==================================
    # AUTHENTICATION
    # ==================================
    print("# ==== AUTHENTICATION (Clerk) ====")
    print()
    print("# Get from: https://dashboard.clerk.com")
    print("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...")
    print("CLERK_SECRET_KEY=sk_live_...")
    print()
    
    # ==================================
    # STORAGE
    # ==================================
    print("# ==== FILE STORAGE (Vercel Blob) ====")
    print()
    print("# Get from: Vercel Dashboard → Storage → Blob")
    print("BLOB_READ_WRITE_TOKEN=vercel_blob_rw_...")
    print()
    
    # ==================================
    # ADMIN CREDENTIALS
    # ==================================
    print("# ==== ADMIN CREDENTIALS (Example) ====")
    print()
    print(f"ADMIN_EMAIL=admin@yourdomain.com")
    print(f"ADMIN_PASSWORD={generate_password(16, include_symbols=True)}")
    print()
    print(f"# Or stronger password (24 chars):")
    print(f"ADMIN_PASSWORD_STRONG={generate_password(24, include_symbols=True)}")
    print()
    
    # ==================================
    # OPTIONAL SERVICES
    # ==================================
    print("# ==== OPTIONAL SERVICES ====")
    print()
    print("# Sentry (Error Tracking)")
    print("# Get from: https://sentry.io → Project Settings")
    print("SENTRY_DSN=https://...@sentry.io/...")
    print("NEXT_PUBLIC_SENTRY_DSN=https://...@sentry.io/...")  # Same as above
    print()
    print("# SendGrid (Email)")
    print("# Get from: https://app.sendgrid.com/settings/api_keys")
    print("SENDGRID_API_KEY=SG....")
    print()
    print("# Stripe (Payments)")
    print("# Get from: https://dashboard.stripe.com/apikeys")
    print("STRIPE_SECRET_KEY=sk_live_...")
    print("STRIPE_PUBLISHABLE_KEY=pk_live_...")
    print("STRIPE_WEBHOOK_SECRET=whsec_...")
    print()
    
    # ==================================
    # WARNINGS
    # ==================================
    print()
    print("=" * 70)
    print("⚠️  SECURITY WARNINGS:")
    print("=" * 70)
    print("1. SAVE these secrets to password manager (1Password, Bitwarden)")
    print("2. NEVER commit .env files to Git")
    print("3. Use DIFFERENT secrets for staging/production")
    print("4. ROTATE secrets every 90 days")
    print("5. NEVER share secrets via chat/email/screenshot")
    print("6. Enable 2FA on all service accounts")
    print("7. Audit secret access regularly")
    print()
    
    # ==================================
    # DEPLOYMENT INSTRUCTIONS
    # ==================================
    print("=" * 70)
    print("📍 WHERE TO ADD THESE:")
    print("=" * 70)
    print()
    print("🚂 RAILWAY (Backend):")
    print("   1. Go to: https://railway.app/dashboard")
    print("   2. Select your project")
    print("   3. Click 'Variables' tab")
    print("   4. Click 'Raw Editor'")
    print("   5. Paste backend secrets (SECRET_KEY, DATABASE_URL, etc.)")
    print("   6. Click 'Save'")
    print()
    print("▲ VERCEL (Frontend):")
    print("   1. Go to: https://vercel.com/dashboard")
    print("   2. Select your project")
    print("   3. Settings → Environment Variables")
    print("   4. Add each variable:")
    print("      - DATABASE_URL")
    print("      - NEXT_PUBLIC_PYTHON_BACKEND_URL")
    print("      - NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY")
    print("      - CLERK_SECRET_KEY")
    print("      - BLOB_READ_WRITE_TOKEN")
    print("   5. Select 'Production' environment")
    print("   6. Click 'Save'")
    print()
    print("🗄️  NEON (Database):")
    print("   1. Go to: https://console.neon.tech")
    print("   2. Create new project")
    print("   3. Copy 'Connection String'")
    print("   4. Use as DATABASE_URL")
    print()
    
    # ==================================
    # VERIFICATION CHECKLIST
    # ==================================
    print("=" * 70)
    print("✅ VERIFICATION CHECKLIST:")
    print("=" * 70)
    print("Before deploying, verify:")
    print("  [ ] All secrets saved to password manager")
    print("  [ ] API keys obtained from service dashboards")
    print("  [ ] DATABASE_URL from Neon copied")
    print("  [ ] Clerk keys from dashboard copied")
    print("  [ ] Vercel Blob token created")
    print("  [ ] Different secrets for staging vs production")
    print("  [ ] 2FA enabled on all service accounts")
    print("  [ ] .env files in .gitignore")
    print("  [ ] No secrets in code (grep checked)")
    print()
    
    print("=" * 70)
    print("✅ SECRETS GENERATED SUCCESSFULLY!")
    print("=" * 70)
    print()
    print("📌 NEXT STEPS:")
    print("1. Copy this output to password manager")
    print("2. Get API keys from service dashboards")
    print("3. Add to Railway & Vercel dashboards")
    print("4. Test deployment with .env.local first")
    print("5. Then deploy to production")
    print()
    print("🚨 REMEMBER: Close this terminal after copying!")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Secret generation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)


# 🚀 SignovaX Production Deployment Guide

## Complete Step-by-Step Guide for Vercel + Render.com

Your live site: https://signova-x.vercel.app/

---

## 📋 Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│          VERCEL (Frontend)                               │
│     https://signova-x.vercel.app                         │
│                                                           │
│  ┌──────────┬──────────┬──────────┬──────────┐          │
│  │ Chart    │Watchlist │ Signals  │ Trading  │          │
│  │ (React)  │(NIFTY/   │  Panel   │  Panel   │          │
│  │          │ SENSEX)  │          │          │          │
│  └──────────┴──────────┴──────────┴──────────┘          │
└─────────────────────────────────────────────────────────┘
                         ↓ HTTPS API Calls
┌─────────────────────────────────────────────────────────┐
│      RENDER.COM (Backend)                                │
│   https://signovax-api.onrender.com                      │
│                                                           │
│  ┌──────────────┬───────────────┬──────────────┐        │
│  │ ML API       │ Trading API   │ Data Engine  │        │
│  │ (Port 8000)  │ (Port 8001)   │ (yfinance)   │        │
│  │              │               │              │        │
│  │ /index-      │ /api/signals/ │ /health      │        │
│  │  candles     │  generate     │              │        │
│  │ /predict     │ /api/paper/   │              │        │
│  └──────────────┴───────────────┴──────────────┘        │
└─────────────────────────────────────────────────────────┘
```

---

## PART 1: Backend Deployment (Render.com)

### Step 1: Prepare Backend for Production

#### 1.1 Create Requirements File

```bash
cd /Users/daxpanara/Projects/SignovaX
```

Create `requirements.txt`:

```bash
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pandas==2.1.3
numpy==1.26.2
yfinance==0.2.32
python-multipart==0.0.6
pydantic==2.5.0
joblib==1.3.2
scikit-learn==1.3.2
xgboost==2.0.3
websockets==12.0
python-dateutil==2.8.2
EOF
```

#### 1.2 Create Unified API Server

Create `backend/main.py` (combines both ML API and Trading API):

```bash
mkdir -p backend
```

Create this file to merge both APIs:

```python
# backend/main.py
"""
SignovaX Production API
Combines ML API (port 8000) and Trading API (port 8001) into one service
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

# Import existing APIs
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ml'))

from ml.api import app as ml_app
from backend.trading_api import app as trading_app

# Create main production app
app = FastAPI(
    title="SignovaX Production API",
    description="Professional Trading System - ML + Trading Engine",
    version="2.0.0"
)

# CORS for Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://signova-x.vercel.app",
        "http://localhost:3000",
        "http://localhost:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount ML API routes
app.mount("/ml", ml_app)

# Mount Trading API routes
app.mount("/trading", trading_app)

# Health check
@app.get("/")
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "SignovaX Production API",
        "ml_api": "mounted at /ml",
        "trading_api": "mounted at /trading"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
```

#### 1.3 Create Procfile for Render

```bash
cat > Procfile << 'EOF'
web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
EOF
```

#### 1.4 Create render.yaml (Render Blueprint)

```bash
cat > render.yaml << 'EOF'
services:
  - type: web
    name: signovax-api
    env: python
    region: oregon
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: PORT
        value: 8000
    healthCheckPath: /health
EOF
```

---

### Step 2: Deploy to Render.com

#### 2.1 Commit Changes to Git

```bash
cd /Users/daxpanara/Projects/SignovaX

git add .
git commit -m "Add production backend for Render deployment"
git push origin main
```

#### 2.2 Create Render Service

1. Go to https://render.com
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select your `SignovaX` repository

5. **Configure Service:**
   - **Name**: `signovax-api`
   - **Region**: Oregon (US West)
   - **Branch**: `main`
   - **Root Directory**: (leave blank)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

6. **Environment Variables:**
   Add these in Render dashboard:
   ```
   PYTHON_VERSION = 3.11.0
   PORT = 8000
   ```

7. Click **"Create Web Service"**

8. Wait 5-10 minutes for deployment

9. Your API will be live at:
   ```
   https://signovax-api.onrender.com
   ```

#### 2.3 Test Render Deployment

```bash
# Test health
curl https://signovax-api.onrender.com/health

# Test ML API
curl https://signovax-api.onrender.com/ml/health

# Test index candles
curl "https://signovax-api.onrender.com/ml/index-candles?symbol=NIFTY50&interval=1d&limit=2"
```

---

## PART 2: Frontend Deployment (Vercel)

### Step 3: Update Frontend for Production

#### 3.1 Update Environment Variables

Create `frontend/.env.production`:

```bash
cd frontend

cat > .env.production << 'EOF'
REACT_APP_ML_API_URL=https://signovax-api.onrender.com/ml
REACT_APP_TRADING_API_URL=https://signovax-api.onrender.com/trading
REACT_APP_BACKEND_URL=https://signovax-api.onrender.com
EOF
```

#### 3.2 Update API Base URLs

Edit `frontend/src/services/marketApi.js`:

```javascript
// Change this line
const ML_API = process.env.REACT_APP_ML_API_URL || 'http://localhost:8000';

// To this:
const ML_API = process.env.REACT_APP_ML_API_URL ||
               (process.env.NODE_ENV === 'production'
                 ? 'https://signovax-api.onrender.com/ml'
                 : 'http://localhost:8000');
```

Edit `frontend/src/services/api.js`:

```javascript
// Change this line
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

// To this:
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL ||
                    (process.env.NODE_ENV === 'production'
                      ? 'https://signovax-api.onrender.com'
                      : 'http://localhost:8000');
```

#### 3.3 Create Vercel Configuration

Create `vercel.json`:

```bash
cd /Users/daxpanara/Projects/SignovaX

cat > vercel.json << 'EOF'
{
  "version": 2,
  "builds": [
    {
      "src": "frontend/package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "build"
      }
    }
  ],
  "routes": [
    {
      "src": "/static/(.*)",
      "dest": "/frontend/build/static/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/frontend/build/index.html"
    }
  ],
  "env": {
    "REACT_APP_ML_API_URL": "https://signovax-api.onrender.com/ml",
    "REACT_APP_TRADING_API_URL": "https://signovax-api.onrender.com/trading",
    "REACT_APP_BACKEND_URL": "https://signovax-api.onrender.com"
  }
}
EOF
```

#### 3.4 Update package.json for Vercel

Edit `frontend/package.json` and add:

```json
{
  "scripts": {
    "vercel-build": "CI=false npm run build"
  }
}
```

---

### Step 4: Deploy to Vercel

#### 4.1 Install Vercel CLI (if not installed)

```bash
npm install -g vercel
```

#### 4.2 Login to Vercel

```bash
vercel login
```

#### 4.3 Deploy

```bash
cd /Users/daxpanara/Projects/SignovaX

# Commit changes
git add .
git commit -m "Configure production deployment for Vercel"
git push origin main

# Deploy to Vercel
vercel --prod
```

**OR use Vercel Dashboard:**

1. Go to https://vercel.com/dashboard
2. Import your existing project or update it
3. Go to **Settings** → **Environment Variables**
4. Add:
   ```
   REACT_APP_ML_API_URL = https://signovax-api.onrender.com/ml
   REACT_APP_TRADING_API_URL = https://signovax-api.onrender.com/trading
   REACT_APP_BACKEND_URL = https://signovax-api.onrender.com
   ```

5. Go to **Deployments** → Click **"Redeploy"**

6. Select **"Use existing Build Cache"** → Uncheck it
7. Click **"Redeploy"**

---

## PART 3: Verify Production Deployment

### Step 5: Test Everything

#### 5.1 Test Backend APIs

```bash
# Health check
curl https://signovax-api.onrender.com/health

# NIFTY50 data
curl "https://signovax-api.onrender.com/ml/index-candles?symbol=NIFTY50&interval=1d&limit=2"

# SENSEX data
curl "https://signovax-api.onrender.com/ml/index-candles?symbol=SENSEX&interval=1d&limit=2"

# Trading API health
curl https://signovax-api.onrender.com/trading/api/health

# Risk status
curl https://signovax-api.onrender.com/trading/api/risk/status
```

#### 5.2 Test Frontend

1. Open https://signova-x.vercel.app/
2. Check browser console (F12)
3. Look for API calls to `signovax-api.onrender.com`
4. Verify:
   - ✅ NIFTY50 loads in watchlist
   - ✅ SENSEX loads in watchlist
   - ✅ Chart displays data
   - ✅ Signals can be generated
   - ✅ No CORS errors

---

## PART 4: Troubleshooting

### Issue 1: CORS Errors

**Symptom**: Browser console shows CORS policy error

**Fix**: Update backend CORS in `backend/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://signova-x.vercel.app",
        "https://*.vercel.app",  # All Vercel previews
        "http://localhost:3000",
        "http://localhost:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Then redeploy on Render.

---

### Issue 2: Render Service Sleeping

**Symptom**: First request takes 30-60 seconds

**Cause**: Free tier Render services sleep after 15 min inactivity

**Solutions**:

**Option A: Keep-Alive Ping (Free)**

Create a cron job to ping every 10 minutes:

1. Go to https://cron-job.org/
2. Create free account
3. Add job:
   - URL: `https://signovax-api.onrender.com/health`
   - Interval: Every 10 minutes
   - Method: GET

**Option B: Upgrade to Paid Plan**
- Render Starter: $7/month (no sleep)

---

### Issue 3: Environment Variables Not Working

**Fix**: In Vercel dashboard:

1. Go to Project Settings
2. Environment Variables
3. Make sure variables are set for **Production** environment
4. Click "Redeploy" (without cache)

---

### Issue 4: Build Fails on Vercel

**Fix**: Check build logs

Common fixes:

```bash
# In frontend/package.json
"scripts": {
  "vercel-build": "CI=false npm run build"
}
```

This disables treating warnings as errors.

---

### Issue 5: API Timeout

**Symptom**: Requests timeout after 30s

**Cause**: Render free tier has 30s timeout

**Fix**: Add loading states in frontend:

```javascript
const fetchWithTimeout = async (url, options, timeout = 25000) => {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(id);
    return response;
  } catch (error) {
    clearTimeout(id);
    throw error;
  }
};
```

---

## PART 5: Monitoring & Maintenance

### Set Up Monitoring

#### 5.1 Render Dashboard

- Check logs: https://dashboard.render.com/
- Monitor CPU/Memory usage
- Check request metrics

#### 5.2 Vercel Analytics

- Enable Analytics in Vercel dashboard
- Monitor page load times
- Track API call success rates

#### 5.3 Error Tracking (Optional)

Add Sentry:

```bash
npm install @sentry/react @sentry/tracing
```

```javascript
// frontend/src/index.js
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: "YOUR_SENTRY_DSN",
  environment: process.env.NODE_ENV,
});
```

---

## PART 6: Cost Optimization

### Free Tier Limits

**Render.com Free:**
- 750 hours/month
- Sleeps after 15 min inactivity
- 512 MB RAM
- Shared CPU

**Vercel Free:**
- 100 GB bandwidth/month
- Unlimited deployments
- Automatic HTTPS
- Global CDN

### Recommended for Production

**Month 1-3 (Testing):**
- Render Free + Vercel Free = $0/month
- Use cron-job.org keep-alive

**After Validation:**
- Render Starter ($7/month) - No sleep, better performance
- Vercel Pro ($20/month) - If you exceed bandwidth

---

## Quick Reference

### Production URLs

```
Frontend:  https://signova-x.vercel.app/
Backend:   https://signovax-api.onrender.com/
ML API:    https://signovax-api.onrender.com/ml/
Trading:   https://signovax-api.onrender.com/trading/
```

### Key Endpoints

```
Health:        GET  /health
Index Candles: GET  /ml/index-candles?symbol=NIFTY50&interval=1d&limit=2
Signals:       POST /trading/api/signals/generate
Portfolio:     GET  /trading/api/paper/portfolio
Risk Status:   GET  /trading/api/risk/status
```

### Deployment Commands

```bash
# Backend (Render)
git push origin main  # Auto-deploys via GitHub integration

# Frontend (Vercel)
vercel --prod  # Or push to main for auto-deploy
```

---

## 📋 Deployment Checklist

### Pre-Deployment

- [ ] All code committed to GitHub
- [ ] `requirements.txt` updated
- [ ] Environment variables configured
- [ ] CORS origins updated
- [ ] API URLs updated in frontend

### Render Deployment

- [ ] Service created on Render
- [ ] GitHub repo connected
- [ ] Environment variables set
- [ ] Build command configured
- [ ] Health check working
- [ ] Test all API endpoints

### Vercel Deployment

- [ ] Project connected to Vercel
- [ ] Environment variables set
- [ ] Build settings configured
- [ ] Custom domain added (optional)
- [ ] HTTPS enabled
- [ ] Test frontend functionality

### Post-Deployment

- [ ] NIFTY50 loads in watchlist
- [ ] SENSEX loads in watchlist
- [ ] Chart displays correctly
- [ ] Signals generate successfully
- [ ] No console errors
- [ ] Mobile responsive
- [ ] Set up monitoring
- [ ] Configure keep-alive (if free tier)

---

## 🎉 Success!

Your SignovaX system is now live in production!

- **Frontend**: https://signova-x.vercel.app/
- **Backend**: https://signovax-api.onrender.com/

NIFTY50 and SENSEX now work on your live site! 🚀

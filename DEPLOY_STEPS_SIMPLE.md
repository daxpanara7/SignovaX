# 🚀 Deploy to Production - Simple Steps

Your live site: **https://signova-x.vercel.app/**

---

## ✅ Step 1: Push Code to GitHub (1 minute)

```bash
cd /Users/daxpanara/Projects/SignovaX

# Run the deployment script
./DEPLOY_TO_PRODUCTION.sh

# Or manually:
git add .
git commit -m "Deploy NIFTY50 and SENSEX to production"
git push origin main
```

---

## ✅ Step 2: Deploy Backend on Render.com (5 minutes)

### Option A: Automatic (Recommended)

1. Go to https://dashboard.render.com/
2. Click **"New +"** → **"Web Service"**
3. Connect GitHub → Select `SignovaX` repo
4. Render will detect `render.yaml` and auto-configure
5. Click **"Apply"**
6. Wait 5-10 minutes for build

**Your API will be at**: `https://signovax-api.onrender.com`

### Option B: Manual Setup

1. **Name**: `signovax-api`
2. **Root Directory**: (leave blank)
3. **Environment**: `Python 3`
4. **Build Command**: `pip install -r requirements.txt`
5. **Start Command**: `cd ml && uvicorn api:app --host 0.0.0.0 --port $PORT`
6. Click **"Create Web Service"**

---

## ✅ Step 3: Update Vercel Environment (2 minutes)

1. Go to https://vercel.com/dashboard
2. Select your `SignovaX` project
3. Go to **Settings** → **Environment Variables**
4. Add these variables for **Production**:

```
REACT_APP_ML_API_URL = https://signovax-api.onrender.com
REACT_APP_BACKEND_URL = https://signovax-api.onrender.com
```

5. Go to **Deployments**
6. Click the **"..."** menu on latest deployment
7. Click **"Redeploy"**
8. **Uncheck** "Use existing Build Cache"
9. Click **"Redeploy"**

---

## ✅ Step 4: Test Production (2 minutes)

### Test Backend

Open these in browser:

```
https://signovax-api.onrender.com/health
https://signovax-api.onrender.com/index-candles?symbol=NIFTY50&interval=1d&limit=2
https://signovax-api.onrender.com/index-candles?symbol=SENSEX&interval=1d&limit=2
```

You should see JSON data.

### Test Frontend

1. Open: https://signova-x.vercel.app/
2. Check watchlist - NIFTY50 and SENSEX should load
3. Click on NIFTY50 - chart should appear
4. Open browser console (F12) - check for errors

**If you see prices and charts = SUCCESS!** ✅

---

## 🔧 Troubleshooting

### Problem: "Fetching..." stuck on NIFTY50/SENSEX

**Solution**:
1. Open browser console (F12)
2. Look for API errors
3. Check if API URL is correct: `https://signovax-api.onrender.com`
4. Verify Render service is running (not sleeping)

### Problem: CORS Error

**Fix in Render**:
1. Your `ml/api.py` already has CORS configured
2. Just redeploy on Render
3. Or add your domain to CORS origins

### Problem: Render Service Sleeping

**Cause**: Free tier sleeps after 15 min inactivity

**Quick Fix**:
1. Go to https://cron-job.org/
2. Create free account
3. Add job: `https://signovax-api.onrender.com/health` every 10 minutes

---

## 📱 Keep Service Awake (Optional)

### Use UptimeRobot (Free)

1. Go to https://uptimerobot.com/
2. Sign up free
3. Add Monitor:
   - **Type**: HTTP(s)
   - **URL**: `https://signovax-api.onrender.com/health`
   - **Interval**: 5 minutes
4. Save

This pings your API every 5 minutes to keep it awake.

---

## ✅ Success Checklist

- [ ] Code pushed to GitHub
- [ ] Render service deployed (green status)
- [ ] Vercel environment variables set
- [ ] Vercel redeployed
- [ ] Backend health check works
- [ ] NIFTY50 API returns data
- [ ] SENSEX API returns data
- [ ] Frontend loads at signova-x.vercel.app
- [ ] Watchlist shows NIFTY50 price
- [ ] Watchlist shows SENSEX price
- [ ] Chart displays when clicking symbols
- [ ] No console errors in browser

---

## 🎉 Done!

Your SignovaX system is now live with NIFTY50 and SENSEX working!

**Links**:
- Frontend: https://signova-x.vercel.app/
- Backend: https://signovax-api.onrender.com/

---

## 📊 What Happens Next?

1. **First Load**: May take 30-60 seconds (Render waking up)
2. **After That**: Loads in 2-5 seconds
3. **Prices Update**: Every 30 seconds
4. **Service Sleeps**: After 15 min of no activity (free tier)

---

## 💰 Costs

**Current Setup**:
- Render.com Free: $0/month
- Vercel Free: $0/month
- **Total: FREE** ✅

**If you want no sleeping**:
- Render Starter: $7/month
- Keeps service always awake
- Better performance

---

## 🔗 Quick Commands

```bash
# Redeploy everything
./DEPLOY_TO_PRODUCTION.sh

# Test backend
curl https://signovax-api.onrender.com/health

# Test NIFTY50
curl "https://signovax-api.onrender.com/index-candles?symbol=NIFTY50&interval=1d&limit=2"

# Check Render logs
https://dashboard.render.com/

# Check Vercel deployments
https://vercel.com/dashboard
```

---

**Need help?** Check the detailed guide: [PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md)

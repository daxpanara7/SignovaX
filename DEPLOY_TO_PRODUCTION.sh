#!/bin/bash

echo "🚀 SignovaX Production Deployment Script"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ] && [ ! -d "frontend" ]; then
    echo "❌ Error: Run this script from the SignovaX root directory"
    exit 1
fi

echo "📋 Step 1: Commit all changes to Git"
echo "-----------------------------------"
git add .
git status

read -p "Commit message: " commit_msg
if [ -z "$commit_msg" ]; then
    commit_msg="Deploy to production"
fi

git commit -m "$commit_msg"
echo "✅ Changes committed"
echo ""

echo "📤 Step 2: Push to GitHub"
echo "------------------------"
git push origin main
echo "✅ Pushed to GitHub"
echo ""

echo "🎯 Step 3: Deployment Status"
echo "----------------------------"
echo ""
echo "✅ Backend will auto-deploy on Render.com"
echo "   👉 Check: https://dashboard.render.com/"
echo ""
echo "✅ Frontend will auto-deploy on Vercel"
echo "   👉 Check: https://vercel.com/dashboard"
echo ""

echo "⏰ Step 4: Wait for deployments (5-10 minutes)"
echo "---------------------------------------------"
echo ""
echo "Render.com:"
echo "  - Building Python dependencies..."
echo "  - Starting uvicorn server..."
echo "  - Health check at /health"
echo ""
echo "Vercel:"
echo "  - Building React app..."
echo "  - Deploying to CDN..."
echo "  - HTTPS certificate"
echo ""

echo "🔗 Step 5: Production URLs"
echo "--------------------------"
echo ""
echo "Frontend:  https://signova-x.vercel.app/"
echo "Backend:   https://signovax-api.onrender.com/"
echo "Health:    https://signovax-api.onrender.com/health"
echo ""

echo "✅ Step 6: Test Production"
echo "--------------------------"
echo ""
echo "Run these tests after deployment completes:"
echo ""
echo "# Test backend health"
echo "curl https://signovax-api.onrender.com/health"
echo ""
echo "# Test NIFTY50 data"
echo "curl 'https://signovax-api.onrender.com/index-candles?symbol=NIFTY50&interval=1d&limit=2'"
echo ""
echo "# Test SENSEX data"
echo "curl 'https://signovax-api.onrender.com/index-candles?symbol=SENSEX&interval=1d&limit=2'"
echo ""

echo "🎉 Deployment script complete!"
echo ""
echo "📝 Next steps:"
echo "1. Wait 5-10 minutes for builds to complete"
echo "2. Check Render dashboard for backend status"
echo "3. Check Vercel dashboard for frontend status"
echo "4. Open https://signova-x.vercel.app/ and test"
echo "5. Verify NIFTY50 and SENSEX load in watchlist"
echo ""

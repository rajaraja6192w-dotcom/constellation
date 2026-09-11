# 🚂 RAILWAY DEPLOYMENT GUIDE - CONSTELLATION V2

## 📅 Last Updated: September 11, 2026
## ⚡ Deployment Time: 15-30 minutes

---

## ✅ WHAT'S READY:

All files are configured for Railway deployment:

- ✅ `railway_app.py` - Combined bot + webhook in one process
- ✅ `Procfile` - Railway start command
- ✅ `railway.toml` - Railway configuration
- ✅ `runtime.txt` - Python version
- ✅ `requirements.txt` - All dependencies
- ✅ All cache files removed
- ✅ Test files removed

---

## 🚀 DEPLOYMENT STEPS:

### Step 1: Create Railway Account

1. Go to: https://railway.app
2. Click "Start a New Project"
3. Sign up with GitHub (recommended)
4. Free tier includes:
   - $5 credit/month
   - 500 hours execution time
   - Enough for this bot!

### Step 2: Create New Project

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. If you haven't pushed to GitHub yet:
   - Go to: https://github.com/new
   - Create new repository: `constellation-bot`
   - Follow instructions to push code

**OR**

1. Click "Deploy from local folder"
2. Install Railway CLI:
   ```bash
   # Windows (PowerShell)
   iwr https://railway.app/install.ps1 | iex
   
   # Or download from: https://docs.railway.app/develop/cli
   ```

### Step 3: Push Code to GitHub (Recommended)

```bash
# Initialize git (if not done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Constellation V2 with Railway support"

# Add remote (replace with your repo URL)
git remote add origin https://github.com/YOUR_USERNAME/constellation-bot.git

# Push
git push -u origin main
```

### Step 4: Deploy on Railway

**Option A: Deploy from GitHub**

1. In Railway dashboard, click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your repository
4. Railway will auto-detect Python project
5. Click "Deploy"

**Option B: Deploy with Railway CLI**

```bash
# Login to Railway
railway login

# Initialize project
railway init

# Link to project
railway link

# Deploy
railway up
```

### Step 5: Configure Environment Variables

1. In Railway dashboard, go to your project
2. Click "Variables" tab
3. Add these variables:

```
BOT_TOKEN=8768449848:AAG-QNkVtMXybzQ6SKcGiwOE-8HJlBK3pbs
PORT=5000
```

**IMPORTANT:** Replace `BOT_TOKEN` with your actual token if different!

### Step 6: Get Your Railway URL

1. In Railway dashboard, go to "Settings"
2. Under "Domains", click "Generate Domain"
3. You'll get a URL like: `https://constellation-bot-production.up.railway.app`
4. **Save this URL!** You'll need it for Ko-fi webhook

### Step 7: Configure Ko-fi Webhook

1. Go to Ko-fi: https://ko-fi.com
2. Go to Settings → Webhooks
3. Add webhook URL: `https://YOUR-RAILWAY-URL.railway.app/kofi-webhook`
   - Example: `https://constellation-bot-production.up.railway.app/kofi-webhook`
4. Enable for: **Subscriptions**
5. Save

### Step 8: Test Deployment

**Check Health:**
```bash
curl https://YOUR-RAILWAY-URL.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "bot": "running"
}
```

**Test Bot:**
- Send `/start` to your Telegram bot
- Should receive welcome message

**Test Webhook:**
- Go to Ko-fi
- Use webhook test feature
- Or manually test with curl

---

## 🔧 RAILWAY CONFIGURATION:

### File Structure:
```
ConstellationV2/
├── railway_app.py          # Main app (bot + webhook combined)
├── Procfile                # Railway start command
├── railway.toml            # Railway config
├── runtime.txt             # Python version
├── requirements.txt        # Dependencies
├── config.py               # Bot config
├── database.py             # MongoDB
├── commands/               # Bot commands
├── handlers/               # Callbacks
├── utils/                  # Helpers
└── data/                   # JSON data
```

### How It Works:

1. **Single Process:** Bot and webhook run in same process (Railway free tier friendly)
2. **Background Thread:** Bot runs in background thread
3. **Flask Frontend:** Webhook runs on main thread
4. **Shared Resources:** Both share same bot instance

### Environment Variables:

```bash
BOT_TOKEN=your_bot_token_here
PORT=5000                    # Railway sets this automatically
```

### Resource Usage:

```
RAM: ~200-300MB
CPU: Minimal
Network: Low
Cost: FREE (within $5 credit)
```

---

## 💰 RAILWAY PRICING:

### Free Tier:
- $5 credit/month
- 500 hours execution time
- More than enough for this bot!

### Usage Estimate:
```
Bot runs 24/7 = 720 hours/month
BUT Railway free tier includes 500 hours
So you get: ~20 days free per month

If you need more:
- Hobby plan: $5/month (unlimited hours)
- Perfect for this bot!
```

---

## 🧪 TESTING:

### Local Test First:
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python railway_app.py

# Test
curl http://localhost:5000/health
```

### Production Test:
```bash
# Health check
curl https://YOUR-RAILWAY-URL.railway.app/health

# Ko-fi webhook test (replace YOUR_TELEGRAM_ID)
curl -X POST https://YOUR-RAILWAY-URL.railway.app/kofi-webhook \
  -d "data={\"type\":\"Subscription\",\"is_subscription_payment\":true,\"is_first_subscription_payment\":true,\"tier_name\":\"Constellation | Basic\",\"message\":\"telegram_id: YOUR_TELEGRAM_ID\",\"message_id\":\"test123\"}"
```

---

## 📊 MONITORING:

### Railway Dashboard:

1. **Deployments:** View deploy history
2. **Logs:** Real-time logs (click "View Logs")
3. **Metrics:** CPU, RAM, Network usage
4. **Variables:** Manage environment variables

### Check Logs:
```bash
# Using Railway CLI
railway logs

# Or in dashboard:
# Click project → "View Logs"
```

### Important Logs to Watch:

```
✅ Good:
- "Bot started successfully!"
- "Starting Flask server on port"
- "Ko-fi Webhook received"
- "Premium notification sent"

❌ Problems:
- "Error starting bot"
- "MongoDB connection failed"
- "Could not extract Telegram ID"
- "Failed to send notification"
```

---

## 🐛 TROUBLESHOOTING:

### Deployment Fails:

**Issue:** Build fails
```bash
Solution:
- Check requirements.txt is correct
- Verify Python version in runtime.txt
- Check Railway logs for errors
```

**Issue:** Bot not responding
```bash
Solution:
- Check BOT_TOKEN is set correctly
- Verify MongoDB connection
- Check logs for errors
```

**Issue:** Webhook not working
```bash
Solution:
- Verify Railway URL is correct
- Check Ko-fi webhook URL is HTTPS
- Test /health endpoint first
- Check Railway logs
```

### Bot Stops Working:

**Issue:** Bot goes offline after few hours
```bash
Solution:
- Railway free tier has 500 hours/month limit
- Upgrade to Hobby plan ($5/month)
- Or optimize by deploying only during active hours
```

**Issue:** Webhook returns 404
```bash
Solution:
- Check URL: must end with /kofi-webhook
- Verify deployment is running
- Check Railway logs
```

### Premium Not Activating:

**Issue:** Payment received but no activation
```bash
Solution:
- Check Railway logs for webhook data
- Verify Telegram ID in Ko-fi message
- Check MongoDB connection
- Manual activation: use database functions
```

---

## 🔄 UPDATING YOUR BOT:

### With GitHub:
```bash
# Make changes
git add .
git commit -m "Update: your changes"
git push

# Railway auto-deploys from GitHub!
```

### With Railway CLI:
```bash
# Deploy latest changes
railway up
```

### Manual Deploy:
1. In Railway dashboard
2. Click "Deploy" → "Trigger Deploy"
3. Railway rebuilds and redeploys

---

## 📁 IMPORTANT FILES:

### Must Have:
- ✅ `railway_app.py` - Main application
- ✅ `requirements.txt` - Dependencies
- ✅ `Procfile` - Start command
- ✅ `config.py` - Configuration
- ✅ `database.py` - MongoDB
- ✅ `commands/` folder
- ✅ `handlers/` folder
- ✅ `utils/` folder
- ✅ `data/` folder

### Optional:
- `railway.toml` - Railway config (optional, has defaults)
- `runtime.txt` - Python version (optional, auto-detected)
- `.gitignore` - Git ignore file

---

## 🔐 SECURITY:

### Environment Variables:

**DO NOT commit these:**
- BOT_TOKEN
- MongoDB connection string (if you add it)
- Any API keys

**Use Railway Variables instead!**

### .gitignore:

Make sure you have:
```
__pycache__/
*.pyc
*.pyo
*.pyd
.env
*.log
.vscode/
.idea/
```

---

## ✅ DEPLOYMENT CHECKLIST:

### Pre-Deployment:
- [x] All cache files removed
- [x] Test files removed
- [x] Railway files created
- [x] Dependencies listed
- [x] Code tested locally

### Railway Setup:
- [ ] Railway account created
- [ ] Project created
- [ ] Code pushed to GitHub (or Railway)
- [ ] Environment variables set
- [ ] Domain generated

### Post-Deployment:
- [ ] Health check passes
- [ ] Bot responds to /start
- [ ] Webhook URL configured in Ko-fi
- [ ] Premium test successful
- [ ] Logs monitored

---

## 🎯 COMPLETE WORKFLOW:

```
1. Clean Project ✓
   - Removed cache files
   - Removed test files
   - Created Railway files

2. Push to GitHub
   - git init
   - git add .
   - git commit
   - git push

3. Deploy on Railway
   - Create project
   - Link GitHub repo
   - Set environment variables
   - Deploy!

4. Get Railway URL
   - Generate domain
   - Copy URL

5. Configure Ko-fi
   - Add webhook URL
   - Enable subscriptions
   - Test webhook

6. Test Everything
   - Health check
   - Bot commands
   - Premium purchase
   - Monitor logs

7. GO LIVE! 🚀
```

---

## 💡 TIPS:

1. **Use GitHub:** Easier to track changes and auto-deploy
2. **Monitor Logs:** Check logs regularly for errors
3. **Test First:** Always test locally before deploying
4. **Backup Data:** MongoDB Atlas has automatic backups
5. **Watch Credits:** Monitor Railway usage in dashboard
6. **Upgrade When Ready:** Hobby plan ($5/mo) for 24/7 uptime

---

## 📞 SUPPORT:

### Railway Issues:
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway
- Twitter: @Railway

### Bot Issues:
- Check logs in Railway dashboard
- Read troubleshooting section above
- Verify environment variables

---

## 🌟 ADVANTAGES OF RAILWAY:

✅ **Easy Deployment:** Push and deploy
✅ **Auto HTTPS:** SSL certificate included
✅ **Free Tier:** $5 credit/month
✅ **Auto Scaling:** Handles traffic spikes
✅ **Logs:** Real-time log viewing
✅ **Metrics:** CPU, RAM, Network monitoring
✅ **GitHub Integration:** Auto-deploy on push
✅ **Environment Variables:** Secure config
✅ **Custom Domains:** Add your own domain
✅ **Zero Config:** Works out of the box

---

## 🎉 READY TO DEPLOY!

Your project is fully configured for Railway deployment!

**Next Steps:**
1. Push code to GitHub
2. Create Railway project
3. Link repository
4. Set environment variables
5. Deploy!
6. Configure Ko-fi webhook
7. Test everything
8. **GO LIVE!** 🚀

**Time Required:** 15-30 minutes

---

**Made with ❤️ for Constellation V2**
**Railway Deployment Ready!**

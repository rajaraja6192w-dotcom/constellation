# 🚀 QUICK START GUIDE - CONSTELLATION V2

## Run the Bot & Webhook Server

### Option 1: Start Both Services (Recommended)

**Create a startup script:**

**Windows (start_all.cmd):**
```batch
@echo off
echo Starting Constellation V2...
echo.

echo [1/2] Starting Main Bot...
start "Constellation Bot" python main.py

echo [2/2] Starting Ko-fi Webhook Server...
timeout /t 2 /nobreak > nul
start "Ko-fi Webhook" python kofi_webhook.py

echo.
echo ✅ Both services started!
echo.
echo Bot running in window: "Constellation Bot"
echo Webhook running in window: "Ko-fi Webhook"
echo.
echo Press any key to close this window...
pause > nul
```

Save as `start_all.cmd` and double-click to run!

---

### Option 2: Start Services Separately

**1. Start Main Bot:**
```bash
python main.py
```

**2. Start Webhook Server (in another terminal):**
```bash
python kofi_webhook.py
```

---

### Verify Everything is Running:

**Check Main Bot:**
- Open Telegram
- Send `/start` to your bot
- Should receive welcome message ✅

**Check Webhook Server:**
- Open browser
- Go to: http://localhost:5000/health
- Should see: `{"status":"healthy"}` ✅

---

## 📁 What's What:

### Main Components:
- `main.py` - Telegram bot server (handles user commands)
- `kofi_webhook.py` - Ko-fi webhook server (handles payments)
- `database.py` - MongoDB connection & data functions
- `config.py` - Bot configuration & data loading

### Commands:
- `commands/` - All bot commands (/start, /stats, /premium, etc.)
- `handlers/` - Button callbacks & interactions
- `utils/` - Helper functions (game logic, keyboards, etc.)

### Data:
- `data/lights.json` - All lights and rarities
- `data/gears.json` - Craftable gear items
- `data/potions.json` - Shop potions
- `data/premium_tiers.json` - Premium subscription tiers
- `data/world_config.json` - World events (Heaven Approach, etc.)

### Website:
- `premium-website/` - Ko-fi premium landing page
  - `index.html` - Main page structure
  - `script.js` - Interactive features & QR modal
  - `style.css` - Space theme styling
  - `qrcode.png` - Ko-fi payment QR code ✅

---

## 🧪 Testing Premium System:

### 1. Test Website Locally:
```bash
cd premium-website
python -m http.server 8000
```
Then open: http://localhost:8000

### 2. Test Premium Purchase Flow:
1. Visit website
2. Click "Select Pro"
3. Should show QR code ✓
4. Should show Telegram ID copy button ✓
5. Should show step-by-step instructions ✓

### 3. Test Webhook (Manual):
```bash
# Test endpoint
curl http://localhost:5000/health

# Simulate payment
curl -X POST http://localhost:5000/kofi-webhook \
  -d "data={\"type\":\"Subscription\",\"is_subscription_payment\":true,\"is_first_subscription_payment\":true,\"tier_name\":\"Constellation | Basic\",\"message\":\"telegram_id: YOUR_TELEGRAM_ID\",\"message_id\":\"test123\"}"
```

Expected: Receive Telegram notification with premium activation!

---

## 🔧 Configuration Checklist:

### Before Going Live:

**1. MongoDB Connection:**
- ✅ Already configured in `database.py`
- ✅ SSL connection working
- ✅ Using MongoDB Atlas

**2. Bot Token:**
- ✅ Set in `config.py`
- ✅ Current token: `8768449848:AAG-QNkVtMXybzQ6SKcGiwOE-8HJlBK3pbs`

**3. Ko-fi Setup (YOU NEED TO DO):**
- [ ] Create membership tiers on Ko-fi
- [ ] Generate Ko-fi QR code
- [ ] Replace `premium-website/qrcode.png`
- [ ] Deploy webhook with HTTPS
- [ ] Configure Ko-fi webhook URL

**4. Website URLs (YOU NEED TO UPDATE):**
Edit `handlers/callbacks.py` (line ~1252):
```python
# Change placeholder URLs to your actual URLs
url="https://YOUR-WEBSITE.com"
url="https://t.me/YOUR_USERNAME"
```

---

## 📊 Monitor & Debug:

### Check Logs:
Both `main.py` and `kofi_webhook.py` print logs to console.

**Main Bot Logs:**
```
✅ Config loaded: 34 lights, 10 gears, 6 potions
✅ Gear names: [...]
🤖 Bot started successfully!
User 123456789 started the bot
```

**Webhook Logs:**
```
INFO - Ko-fi Webhook received: {...}
INFO - Premium notification sent to user 123456789
```

### Common Issues:

**Bot won't start:**
- Check MongoDB connection string
- Verify bot token is correct
- Check data files exist (lights.json, etc.)

**Webhook not working:**
- Check port 5000 is not in use
- Verify Flask is installed: `pip install flask`
- Check firewall allows port 5000

**Premium not activating:**
- Check user included Telegram ID in message
- Check user has started bot first
- Check server logs for errors
- Try manual activation via database

---

## 🎯 Next Steps:

1. **Test Locally:**
   - Run both services ✓
   - Test all commands in Telegram ✓
   - Test premium website locally ✓

2. **Setup Ko-fi:**
   - Create membership tiers
   - Generate QR code
   - Configure webhook
   - See: `SETUP_COMPLETE.md`

3. **Deploy:**
   - Deploy webhook to production (HTTPS)
   - Deploy premium website
   - Update URLs in code
   - See: `SETUP_COMPLETE.md`

4. **Go Live:**
   - Test with real payment
   - Announce to users
   - Monitor for issues
   - Enjoy! 🎉

---

## 📚 Documentation:

- **SETUP_COMPLETE.md** - Full setup guide & deployment
- **KOFI_INTEGRATION_COMPLETE.md** - Technical details
- **ConstellationV1.md** - Bot features & commands
- **premium-website/README_QRCODE.md** - QR code setup

---

## 🆘 Need Help?

**Check These First:**
1. Are both services running?
2. Is MongoDB connection working?
3. Did user start the bot? (`/start`)
4. Are Ko-fi tiers created correctly?
5. Is webhook URL HTTPS?

**Still stuck? Check logs for error messages!**

---

**🌟 READY TO START? 🌟**

Run: `python main.py` and `python kofi_webhook.py`

Or double-click: `start_all.cmd` (if you created it)

**Good luck! 🚀**

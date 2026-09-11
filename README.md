# 🌟 Constellation V2 - Telegram RNG Bot

A feature-rich Telegram bot for collecting lights, crafting gears, and enjoying premium subscriptions with Ko-fi integration!

[![Railway](https://img.shields.io/badge/Deploy%20on-Railway-blueviolet?logo=railway)](https://railway.app)
[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB-green?logo=mongodb)](https://mongodb.com)

## ✨ Features

### 🎮 Core Gameplay:
- 🎲 **34+ Collectible Lights** - Rare & exclusive lights to collect
- 🔄 **Auto-Roll System** - 24/7 playtime tracking
- 🔨 **10 Craftable Gears** - Craft from collected lights
- 🎒 **120-Slot Inventory** - Store your collection
- ⚔️ **Equipment System** - Equip lights & gears for bonuses
- 🏪 **Potion Shop** - Buy luck boosters with amount parameter

### 🏆 Progression:
- 🎯 **Daily Quests** - Complete challenges for rewards
- 🏅 **Achievement System** - Unlock achievements
- 📊 **Leaderboards** - Compete with others
- ✨ **Heaven Approach Event** - 0.5% chance for exclusive lights

### 💎 Premium Subscriptions:
- **Basic ($1.99/mo):** 100k coins, 150 potions, +250% luck, 2x multiplier
- **Pro ($3.99/mo):** 200k coins, 300 potions, +500% luck, exclusive lights, shop discount
- 🔄 **Ko-fi Integration** - Automatic premium activation via QR code payment
- 💌 **Instant Notifications** - Get rewards immediately

### 🎨 Exclusive Content (Pro):
- 🌆 **Cybernight** - Exclusive light
- 🎸 **O'Sound** - Exclusive light
- 🎻 **Remembrance** - Exclusive light
- 🔮 **Light Preview** - See upcoming lights
- 💸 **30% Shop Discount** - Save on all purchases

## 🚀 Quick Deploy on Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

### One-Click Deployment:

1. **Click "Deploy on Railway" button above**
2. **Set environment variable:**
   ```
   BOT_TOKEN=your_telegram_bot_token
   ```
3. **Wait 2-3 minutes for deployment**
4. **Get your Railway URL from dashboard**
5. **Configure Ko-fi webhook** (see below)
6. **Done!** 🎉

### Manual Deployment:

See **[RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md)** for detailed instructions.

## 📋 Requirements

- Python 3.11+
- MongoDB Atlas (free tier)
- Telegram Bot Token
- Ko-fi Account (for premium features)

## 🛠️ Local Development

### 1. Install Dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configure Bot:
Edit `config.py` and set your bot token:
```python
BOT_TOKEN = "your_bot_token_here"
```

### 3. Run Bot & Webhook:
```bash
# Option 1: Use startup script
start_all.cmd

# Option 2: Run manually
python railway_app.py
```

### 4. Test:
```bash
# Health check
curl http://localhost:5000/health

# Test in Telegram
/start
```

## 🔧 Configuration

### Environment Variables:
```bash
BOT_TOKEN=your_telegram_bot_token_here
PORT=5000  # Optional, Railway sets automatically
```

### Data Files:
- `data/lights.json` - All lights and rarities
- `data/gears.json` - Craftable gear items
- `data/potions.json` - Shop potions
- `data/premium_tiers.json` - Premium subscription tiers
- `data/world_config.json` - World events configuration

## 💳 Ko-fi Integration

### Setup Premium Payments:

1. **Create Ko-fi Account:** https://ko-fi.com
2. **Create Membership Tiers:**
   - Basic: $1.99/month
   - Pro: $3.99/month
3. **Configure Webhook:**
   - URL: `https://your-railway-url.railway.app/kofi-webhook`
   - Enable for: Subscriptions
4. **Generate QR Code** and replace `premium-website/qrcode.png`

See **[SETUP_COMPLETE.md](SETUP_COMPLETE.md)** for detailed Ko-fi setup.

## 🎮 Commands

### User Commands:
- `/start` - Welcome & server join
- `/stats` - View your profile
- `/inventory` - View your collection
- `/roll` - Manual roll (if auto-roll off)
- `/craft` - Craft gear from lights
- `/equip` - Equip items
- `/shop` - Browse potion shop
- `/buy <id> [amount]` - Buy items
- `/use_potion <id>` - Use a potion
- `/premium` - View premium plans
- `/leaderboard [type]` - View rankings
- `/quest` - View daily quests
- `/achievement` - View achievements
- `/discard` - Discard items
- `/help` - Show all commands

### Admin Commands:
- `/server` - Manage servers

## 📊 Project Structure

```
ConstellationV2/
├── railway_app.py          # Main app (bot + webhook)
├── config.py               # Configuration
├── database.py             # MongoDB functions
├── commands/               # Bot commands (15 files)
├── handlers/               # Callback handlers
├── utils/                  # Helper functions
├── data/                   # JSON data files
├── premium-website/        # Ko-fi landing page
├── requirements.txt        # Dependencies
├── Procfile                # Railway start command
├── railway.toml            # Railway config
└── .gitignore              # Git ignore file
```

## 📚 Documentation

- **[README_FIRST.md](README_FIRST.md)** - Start here! Overview & quick start
- **[RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md)** - Railway deployment guide
- **[SETUP_COMPLETE.md](SETUP_COMPLETE.md)** - Ko-fi setup (detailed)
- **[START_HERE.md](START_HERE.md)** - How to run locally
- **[KOFI_INTEGRATION_COMPLETE.md](KOFI_INTEGRATION_COMPLETE.md)** - Technical docs
- **[ConstellationV1.md](ConstellationV1.md)** - Bot features & commands
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Complete project status
- **[QUICK_REFERENCE.txt](QUICK_REFERENCE.txt)** - Quick reference card

## 🧪 Testing

### Local Testing:
```bash
# Run bot
python railway_app.py

# Test webhook
python test_webhook.py

# Health check
curl http://localhost:5000/health
```

### Production Testing:
```bash
# Health check
curl https://your-railway-url.railway.app/health

# Test premium activation
curl -X POST https://your-railway-url.railway.app/kofi-webhook \
  -d "data={\"type\":\"Subscription\",\"is_subscription_payment\":true,\"tier_name\":\"Constellation | Basic\",\"message\":\"telegram_id: YOUR_ID\"}"
```

## 🐛 Troubleshooting

### Bot not responding:
- Check BOT_TOKEN is set correctly
- Verify MongoDB connection
- Check Railway logs

### Webhook not working:
- Verify Railway URL is correct
- Check Ko-fi webhook configuration
- Test /health endpoint first

### Premium not activating:
- Check user included telegram_id in Ko-fi message
- Verify user has started bot (/start)
- Check Railway logs for errors

See **[RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md)** for detailed troubleshooting.

## 💰 Costs

### Development: FREE
- All code open source
- No external services required

### Running Costs:
- **MongoDB Atlas:** FREE (512MB tier)
- **Railway:** FREE ($5 credit/month) or $5/mo unlimited
- **Ko-fi:** 5% platform fee on transactions

**Total:** $0-5/month

## 📈 Features Roadmap

- [ ] Trading system between users
- [ ] Guild/clan system
- [ ] PvP battles
- [ ] Seasonal events
- [ ] Web dashboard
- [ ] Analytics dashboard

## 🤝 Contributing

This is a private project, but feel free to fork and customize!

## 📄 License

Private project - All rights reserved

## 👤 Author

Built with ❤️ by Kiro AI Assistant
Version: 1.3.4+

## 🙏 Acknowledgments

- python-telegram-bot library
- MongoDB Atlas
- Railway deployment platform
- Ko-fi payment platform

## 📞 Support

For issues or questions:
1. Check documentation files
2. Review troubleshooting sections
3. Check Railway/Ko-fi logs

---

**🚀 Ready to Deploy!**

Follow **[RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md)** to get started!

**Made with ❤️ for Constellation V2**

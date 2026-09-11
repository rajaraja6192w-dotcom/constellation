# 🌌 CONSTELLATION RNG BOT V1.3.4 - COMPLETE DOCUMENTATION

## 📅 Last Updated: September 10, 2026
## 🎯 Status: PRODUCTION READY

---

## 📋 TABLE OF CONTENTS
1. [Bot Overview](#bot-overview)
2. [Installation & Setup](#installation--setup)
3. [Commands Reference](#commands-reference)
4. [Premium System](#premium-system)
5. [Game Mechanics](#game-mechanics)
6. [World System](#world-system)
7. [Database Structure](#database-structure)
8. [Configuration](#configuration)
9. [Troubleshooting](#troubleshooting)

---

## 🤖 BOT OVERVIEW

**Constellation RNG** is a Telegram-based RNG (Random Number Generator) game where players roll for rare "Lights", craft gears, complete quests, and compete on leaderboards.

### Key Features:
- ✅ 117+ collectible Lights (regular + special + exclusive)
- ✅ 10 servers with 100 players each
- ✅ 5 craftable gear tiers for luck bonuses
- ✅ 6 luck potions + special Null Potion
- ✅ Dynamic world system (weather, events, time periods)
- ✅ 28+ achievements & daily quests
- ✅ Premium subscription system (Basic & Pro)
- ✅ Auto-roll & auto-craft features
- ✅ Real-time leaderboards
- ✅ 24/7 playtime tracking

---

## 🚀 INSTALLATION & SETUP

### Requirements:
```
Python 3.14+
MongoDB Atlas (or local MongoDB)
Telegram Bot Token
```

### Installation Steps:

1. **Clone/Download Bot Files**
```bash
cd ConstellationV2
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

**Required Packages:**
- python-telegram-bot
- pymongo
- certifi (for SSL)
- apscheduler

3. **Configure Bot Token**
Edit `config.py`:
```python
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
```

4. **Configure MongoDB**
Edit `database.py`:
```python
MONGO_URI = "YOUR_MONGODB_URI"
```

5. **Run Bot**
```bash
python main.py
```

Or use provided script:
```bash
restart_bot_fresh.cmd
```

---

## 📖 COMMANDS REFERENCE

### 🎮 Basic Commands
| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Start bot & view main menu | `/start` |
| `/roll` | Same as /start (quick access) | `/roll` |
| `/help` | Show complete command guide | `/help` |

### 🌐 Server Commands
| Command | Description | Required |
|---------|-------------|----------|
| `/play` | Select or join a server | First-time |
| `/changeserver` | Switch to different server | After joining |
| `/serverinfo` | View current server info | After joining |

**Note:** All commands except `/start`, `/roll`, `/play` require server membership!

### 🎲 Rolling & Inventory
| Command | Description | Example |
|---------|-------------|---------|
| Roll Button | Roll for Lights (3s cooldown) | Button in menu |
| Auto-Roll Toggle | Enable/disable auto-roll | Button in settings |
| Inventory Button | View Light collection | Button in menu |
| `/discard [name]` | Remove a Light | `/discard Common` |
| `/autodiscard [rarity]` | Auto-discard below rarity | `/autodiscard 1000` |

### 🔨 Crafting & Gear
| Command | Description | Example |
|---------|-------------|---------|
| `/craft` | Open crafting menu | `/craft` |
| Auto-Craft Toggle | Enable/disable crafting | Button in craft menu |
| `/equip_gear [name]` | Equip a gear | `/equip_gear Lucky Glove` |
| `/unequip_gear [slot]` | Remove gear | `/unequip_gear left_hand` |
| `/equip_light [name]` | Showcase light | `/equip_light Divine` |

### 🧪 Potions
| Command | Description | Duration | Luck Bonus |
|---------|-------------|----------|------------|
| `/use angelic` | Use Angelic Potion | 10 min | +25% |
| `/use divine` | Use Divine Potion | 15 min | +50% |
| `/use mythical` | Use Mythical Potion | 20 min | +75% |
| `/use celestial` | Use Celestial Potion | 30 min | +100% |
| `/use ethereal` | Use Ethereal Potion | 45 min | +150% |
| `/use null` | Unlock Anomaly light | Instant | 1 use only |

### 💰 Shop & Economy
| Command | Description |
|---------|-------------|
| `/buy` | Open shop menu |
| Buy Coins | Purchase coins with real money |
| Buy Potions | Purchase luck potions |

### 💎 Premium
| Command | Description |
|---------|-------------|
| `/premium` | View premium subscription plans |

### 🏆 Progression
| Command | Description |
|---------|-------------|
| `/leaderboard` | View server rankings (Level, Coins, Playtime, Rolls) |
| `/achievement` | Check your achievements (28+ available) |
| `/quest` | View daily quests (5 active) |
| Profile Button | View your complete stats |

---

## 💎 PREMIUM SYSTEM

### Subscription Tiers

#### 🌟 BASIC - $1.99/month
**Monthly Rewards:**
- 💰 100,000 Coins
- 🧪 150 Luck Potions
- 🍀 +250% Permanent Luck Boost
- 💎 2x Coins & EXP Multiplier
- 🔄 Permanent Auto-Roll (Always ON!)
- 🏷️ Special Premium Title
- 📞 Priority Support

#### ⭐ PRO - $3.99/month (2x ALL Basic!)
**Monthly Rewards:**
- 💰 200,000 Coins (2x Basic)
- 🧪 300 Luck Potions (2x Basic)
- 🍀 +500% Permanent Luck Boost (2x Basic)
- 💎 2x Coins & EXP Multiplier
- 🔄 Permanent Auto-Roll (Always ON!)

**Exclusive Features:**
- ✨ 3 Exclusive Lights (Get 2 Random on Purchase):
  - 🌆 Cybernight
  - 🎸 O'Sound
  - 🎻 Remembrance
- 👼 15% Drop Rate During Heaven Approach Event (0.5% chance)
- 🔮 New Light Preview Access (See upcoming lights!)
- 💸 30% Shop Discount
- 🏷️ Elite Premium Title
- 📞 Premium Support + Feature Suggestions

### How to Subscribe:
1. Use `/premium` command
2. Select tier (Basic or Pro)
3. Contact admin with your Telegram ID
4. Pay via PayPal, Crypto, or Bank Transfer
5. Premium activates instantly!

### Premium Benefits:
- Auto-roll runs 24/7 even offline
- Never stop rolling!
- Huge luck boost for better drops
- Exclusive lights only available to Pro
- Get ahead with monthly rewards

---

## 🎮 GAME MECHANICS

### Rolling System
- **Cooldown**: 3 seconds per roll
- **Auto-Roll**: Available (free users can toggle, premium always ON)
- **Luck Formula**: Higher luck = higher chance for rare lights
- **World Bonuses**: Weather + Events + Time Period bonuses stack

### Luck Calculation
```
Total Luck = Base Luck + Gear Luck + Potion Luck + World Luck + Premium Luck
```

**Example:**
- Base: 100
- Lucky Glove (left): +150
- Lucky Clover (right): +250
- Divine Potion: +50%
- Eclipse Event: +50%
- Premium Pro: +500%
- **Total: 100 + 150 + 250 + 50 + 50 + 500 = 1,100**

### Inventory System
- **Default Slots**: 120
- **Max Slots**: Expandable with gears
- **Auto-Discard**: Set threshold to auto-remove common lights
- **Auto-Craft**: Automatically saves materials for gear recipes

### Crafting System
**5 Gear Tiers:**
1. **Lucky Glove** (Tier 1): +150 luck
2. **Lucky Clover** (Tier 2): +250 luck
3. **Lucky Charm** (Tier 3): +400 luck
4. **Lucky Amulet** (Tier 4): +600 luck
5. **Lucky Crown** (Tier 5): +850 luck

**Crafting Features:**
- Auto-craft when materials ready
- Reserve system prevents auto-discard
- Priority crafting for specific gears
- Two equipment slots: left_hand, right_hand

### Leveling System
- **EXP per Roll**: 15 XP
- **Level Up Rewards**: Coins + Potions
- **Premium Multiplier**: 2x EXP for all premium tiers

---

## 🌍 WORLD SYSTEM

### Weather Types (6 Total)
| Weather | Icon | Luck Bonus | Chance |
|---------|------|------------|--------|
| Rainy | 🌧️ | +10 | 16.67% |
| Sunny | ☀️ | +10 | 16.67% |
| Windy | 💨 | +10 | 16.67% |
| Foggy | 🌫️ | +20 | 16.67% |
| Cloudy | ☁️ | +20 | 16.67% |
| Lightning | ⚡ | +35 | 16.67% |

**Changes**: Every 5 minutes

### Event Types (7 Total)
| Event | Icon | Luck Bonus | Chance | Special Effects |
|-------|------|------------|--------|-----------------|
| Normal | 🌍 | +25 | 70% | None |
| Eclipse | 🌔 | +50 | 15% | Eclipse light unlock |
| Meteor Fall | ☄️ | +100 | 10% | 15x Meteorite chance, 1% Burnt effect (+60% luck) |
| Thunder Wrath | ⚡🌩️ | +300 | 4% | None |
| None | 🌌 | +1500 | 1% | 5% Anomaly chance from any roll |
| **Heaven Approach** | ✨👼 | +2000 | 0.5% | Divine blessing (+150% luck), 15% exclusive light (Pro only) |
| Poseidon Fury | 🌊🔱 | +800 | 2% | Kraken & Whale lights unlock, 10x water boost |

**Changes**: Every 10 minutes

### Time Periods (2 Total)
| Period | Icon | Hours | Exclusive Light | Boost |
|--------|------|-------|-----------------|-------|
| Night | 🌙 | 00:00-05:59, 18:00-23:59 | Moonlight | +25% |
| Morning | 🌅 | 06:00-17:59 | Sunrise | +25% |

**Changes**: Based on real-time clock

### Special Lights Unlock Conditions
- **Eclipse**: Only during Eclipse event
- **Godhand**: Only during Heaven Approach event
- **Kraken & Whale**: Only during Poseidon Fury event
- **Anomaly**: Null Potion OR 5% chance during None event
- **Exclusive (Pro)**: Only during Heaven Approach (15% chance)

---

## 💾 DATABASE STRUCTURE

### MongoDB Collections

#### users
```json
{
  "user_id": 123456789,
  "username": "player_name",
  "level": 10,
  "exp": 1500,
  "coins": 50000,
  "luck": 100,
  "inventory": {"Common": 5, "Rare": 2},
  "gear_inventory": {"Lucky Glove": 1},
  "equipped_gear": {"left_hand": "Lucky Glove", "right_hand": null},
  "equipped_light": "Divine",
  "potion_inventory": {"luck_potion_1": 5},
  "active_effects": [],
  "total_rolls": 1000,
  "highest_light": "Legendary",
  "achievements": ["first_roll", "level_10"],
  "daily_quests": [],
  "auto_roll": false,
  "auto_discard_threshold": 0,
  "auto_craft_enabled": false,
  "current_server": "Server 1",
  "server_join_time": 1234567890.0,
  "last_activity": 1234567890.0,
  "premium": {
    "active": false,
    "tier": null,
    "expire_time": null,
    "monthly_rewards_claimed": false
  },
  "exclusive_lights_granted": []
}
```

### Indexes
```python
users_collection.create_index("user_id", unique=True)
users_collection.create_index("current_server")
users_collection.create_index("level")
users_collection.create_index("coins")
```

---

## ⚙️ CONFIGURATION

### config.py
```python
# Bot Token
BOT_TOKEN = "YOUR_BOT_TOKEN"

# Inventory
MAX_INVENTORY_SLOTS = 120

# Data Files
DATA_DIR = "data/"
```

### Data Files
```
data/
├── lights.json           # All light definitions
├── gears.json           # Gear recipes & stats
├── potions.json         # Potion definitions
├── achievements.json    # Achievement definitions
├── daily_quests.json    # Quest definitions
├── world_config.json    # Weather, events, time config
└── premium_tiers.json   # Premium subscription data
```

---

## 🐛 TROUBLESHOOTING

### Common Issues

**1. MongoDB Connection Failed**
```python
# Solution: Check SSL certificates
pip install certifi
# Update database.py with proper SSL config
```

**2. Bot Not Responding**
- Check bot token is correct
- Verify bot is running (no errors in console)
- Check MongoDB connection
- Restart bot: `python main.py`

**3. Commands Not Working**
- Ensure user has joined a server (`/play`)
- Check command syntax
- Verify bot has all permissions

**4. Premium Not Activating**
```python
# Manual activation (admin only):
from database import activate_premium, get_user_data
user_data = get_user_data(USER_ID)
activate_premium(user_data, "pro", 30)  # tier, days
```

**5. Auto-Roll Not Working**
- Check `auto_roll` field in database
- Premium users have permanent auto-roll
- Free users can toggle on/off

### Debug Commands
```python
# Check user data
from database import get_user_data
user_data = get_user_data(USER_ID)
print(user_data)

# Check server membership
from database import get_user_server
server = get_user_server(user_data)
print(f"Server: {server}")

# Check premium status
from database import get_premium_status
premium = get_premium_status(user_data)
print(premium)
```

---

## 📞 SUPPORT & LINKS

- **Admin Contact**: @YourAdminUsername
- **Support Group**: [Link]
- **Updates Channel**: [Link]
- **Premium Website**: https://constellation-premium.space

---

## 📊 STATISTICS

- **Total Lights**: 117+ (regular + special + exclusive)
- **Gears**: 5 craftable tiers
- **Potions**: 6 + Null (drop-only)
- **Achievements**: 28+
- **Daily Quests**: 5 active
- **Servers**: 10 (100 players each)
- **Weather Types**: 6
- **Events**: 7
- **Time Periods**: 2

---

## 🔄 VERSION HISTORY

### V1.3.4 (Current)
- ✅ Added Telegram ID display in /start
- ✅ Required server membership for all commands
- ✅ Updated /help with latest data
- ✅ Fixed premium UI (all data correct)
- ✅ Fixed website modal (scrollable, correct data)
- ✅ Added Heaven Approach event
- ✅ Added 3 Exclusive Lights (Pro only)
- ✅ Premium system complete

### V1.3.3
- ✅ Premium subscription system
- ✅ Auto-roll & auto-craft
- ✅ 24/7 playtime tracking
- ✅ Leaderboard optimization
- ✅ MongoDB SSL fix for Python 3.14

### V1.3.2
- ✅ Server system (10 servers)
- ✅ World system (weather, events, time)
- ✅ Special lights unlock system
- ✅ Achievement system
- ✅ Daily quests

### V1.3.1
- ✅ Crafting system
- ✅ Gear equipment
- ✅ Auto-discard feature
- ✅ Potion effects

### V1.3.0
- ✅ Initial release
- ✅ Basic rolling system
- ✅ Inventory management
- ✅ Leveling system

---

## ✅ CHECKLIST FOR DEPLOYMENT

- [ ] Configure bot token in `config.py`
- [ ] Configure MongoDB URI in `database.py`
- [ ] Install all dependencies (`requirements.txt`)
- [ ] Test bot locally
- [ ] Update admin contact links
- [ ] Deploy premium website
- [ ] Setup payment gateway
- [ ] Test all commands
- [ ] Test premium activation
- [ ] Monitor logs for errors

---

**End of Documentation - Constellation RNG V1.3.4**

🌌 Built with ❤️ for the RNG community

"""MongoDB database management for user data"""

from pymongo import MongoClient
from pymongo.server_api import ServerApi
import logging
import ssl
import certifi

# MongoDB connection string
MONGODB_URI = "mongodb+srv://bmgobmgo749_db_user:V8q08aQn4vFy4NCl@cluster0.vblwdfo.mongodb.net/?appName=Cluster0"

# Initialize MongoDB client with SSL configuration for Python 3.14+ compatibility
client = None
db = None
users_collection = None
world_collection = None

def get_mongodb_client():
    """Get or create MongoDB client with proper SSL configuration."""
    global client, db, users_collection, world_collection
    
    if client is not None:
        return client
    
    try:
        # Create SSL context compatible with Python 3.14
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Initialize client with SSL settings
        client = MongoClient(
            MONGODB_URI,
            server_api=ServerApi('1'),
            tls=True,
            tlsAllowInvalidCertificates=True,
            tlsAllowInvalidHostnames=True,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )
        
        # Test connection
        client.admin.command('ping')
        logging.info("✅ Successfully connected to MongoDB!")
        
        # Get database and collections
        db = client['constellation_rng']
        users_collection = db['users']
        world_collection = db['world_state']
        
        # Create indexes (non-blocking)
        try:
            users_collection.create_index("user_id", unique=True)
            logging.info("✅ MongoDB indexes created")
        except Exception as e:
            logging.warning(f"Index creation warning: {e}")
        
        return client
        
    except Exception as e:
        logging.error(f"❌ MongoDB connection error: {e}")
        logging.warning("⚠️ Bot will run in fallback mode (no data persistence)")
        return None

# Initialize connection on module load (non-blocking)
try:
    get_mongodb_client()
except:
    pass

def ensure_connection():
    """Ensure MongoDB connection exists, reconnect if needed."""
    global users_collection, world_collection
    
    if users_collection is None or world_collection is None:
        get_mongodb_client()
    
    if users_collection is None:
        raise ConnectionError("MongoDB not available")

def get_user_data(user_id: int) -> dict:
    """Retrieves or initializes player data from MongoDB."""
    try:
        ensure_connection()
        
        # Find user in database
        user_data = users_collection.find_one({"user_id": user_id})
        
        # If user doesn't exist, create new user
        if user_data is None:
            import time
            user_data = {
                "user_id": user_id,
                "total_rolls": 0,
                "luck": 1.0,
                "highest_light": None,
                "equipped_light": None,
                "inventory": {},
                "gear_inventory": {},
                "potion_inventory": {},
                "equipped_gear": {"left_hand": None, "right_hand": None},
                "level": 1,
                "exp": 0,
                "coins": 0,
                "auto_roll": False,
                "is_rolling": False,
                "active_effects": [],
                "total_playtime": 0,
                "last_activity": time.time(),
                "session_start": time.time(),
                "achievements_claimed": [],
                "stats": {
                    "gears_crafted": 0,
                    "unique_gears_list": [],
                    "potions_used": 0,
                    "potions_bought": 0
                },
                "daily_quests": {
                    "quests": [],
                    "completed": [],
                    "claimed_completion_reward": False
                },
                "daily_stats": {
                    "rolls": 0,
                    "levels": 0,
                    "playtime_today": 0,
                    "session_start": time.time(),
                    "crafts": 0,
                    "potions_used": 0,
                    "rarest_today": 0
                },
                "last_quest_reset": "",
                # New features
                "max_inventory_slots": 120,
                "inventory_upgrades": 0,
                "auto_craft_settings": {},  # {gear_name: {"auto_add": bool, "auto_craft": bool}}
                "craft_reserves": {},  # {gear_name: {light_name: amount}}
                "auto_discard_threshold": 0,  # Rarity threshold for auto-discard (0 = disabled)
                "server_id": None,  # Current server (None = not selected yet)
                "server_join_time": None,  # When user joined current server
                # Premium subscription
                "premium": {
                    "active": False,
                    "tier": None,  # "basic" or "pro"
                    "expire_time": None,  # Timestamp when premium expires
                    "auto_renew": False,
                    "monthly_rewards_claimed": False
                }
            }
            # Insert to database
            users_collection.insert_one(user_data)
            logging.info(f"Created new user: {user_id}")
        
        return user_data
        
    except Exception as e:
        logging.error(f"Error getting user data for {user_id}: {e}")
        raise

def save_user_data(user_data: dict) -> bool:
    """Saves user data to MongoDB."""
    try:
        user_id = user_data.get("user_id")
        if not user_id:
            logging.error("No user_id in user_data")
            return False
        
        # Update user in database (upsert=True creates if doesn't exist)
        result = users_collection.update_one(
            {"user_id": user_id},
            {"$set": user_data},
            upsert=True
        )
        
        return result.acknowledged
        
    except Exception as e:
        logging.error(f"Error saving user data: {e}")
        return False

def add_exp(user_data: dict, amount: int) -> tuple:
    """Adds EXP to player and handles level ups. Returns (leveled_up: bool, rewards_text: str)."""
    user_data["exp"] += amount
    exp_needed = user_data["level"] * 100
    leveled_up = False
    rewards_lines = []
    levels_gained = 0
    
    while user_data["exp"] >= exp_needed:
        user_data["level"] += 1
        user_data["exp"] -= exp_needed
        leveled_up = True
        levels_gained += 1
        
        # Level up rewards
        current_level = user_data["level"]
        
        # Luck I Potion: 5 per level
        give_potion_reward(user_data, "luck_potion_1", 5)
        rewards_lines.append("🧪 Luck I Potion x5")
        
        # Luck II Potion: 3 per level
        give_potion_reward(user_data, "luck_potion_2", 3)
        rewards_lines.append("💊 Luck II Potion x3")
        
        # Luck III Potion: 1 every 10 levels
        if current_level % 10 == 0:
            give_potion_reward(user_data, "luck_potion_3", 1)
            rewards_lines.append("⚗️ Luck III Potion x1")
        
        # Angelic Potion: 1 every 100 levels
        if current_level % 100 == 0:
            give_potion_reward(user_data, "angelic_potion", 1)
            rewards_lines.append("✨ Angelic Potion x1")
        
        # Coins reward
        coins_reward = current_level * 50
        add_coins(user_data, coins_reward)
        rewards_lines.append(f"💰 {coins_reward} Coins")
        
        exp_needed = user_data["level"] * 100
    
    # Track daily levels
    if leveled_up:
        if "daily_stats" not in user_data:
            user_data["daily_stats"] = {}
        user_data["daily_stats"]["levels"] = user_data["daily_stats"].get("levels", 0) + levels_gained
    
    # Save to database
    save_user_data(user_data)
    
    rewards_text = "\n".join(rewards_lines) if rewards_lines else ""
    return leveled_up, rewards_text

def give_potion_reward(user_data: dict, potion_id: str, amount: int) -> bool:
    """Give potion reward to user."""
    if "potion_inventory" not in user_data:
        user_data["potion_inventory"] = {}
    
    if potion_id not in user_data["potion_inventory"]:
        user_data["potion_inventory"][potion_id] = 0
    
    user_data["potion_inventory"][potion_id] += amount
    return True

def add_coins(user_data: dict, amount: int) -> bool:
    """Add coins to user."""
    if "coins" not in user_data:
        user_data["coins"] = 0
    
    user_data["coins"] += amount
    return save_user_data(user_data)

def use_potion(user_data: dict, potion_id: str) -> tuple:
    """Use a potion. Returns (success, message)."""
    from config import POTIONS
    import time
    
    # Check if potion exists
    if potion_id not in POTIONS:
        return False, "Potion not found!"
    
    # Check if user has potion
    if "potion_inventory" not in user_data:
        user_data["potion_inventory"] = {}
    
    if potion_id not in user_data["potion_inventory"] or user_data["potion_inventory"][potion_id] <= 0:
        return False, "You don't have this potion!"
    
    potion = POTIONS[potion_id]
    effect = potion["effect"]
    
    # Initialize active_effects if not exists
    if "active_effects" not in user_data:
        user_data["active_effects"] = []
    
    # Deduct potion
    user_data["potion_inventory"][potion_id] -= 1
    
    # Track usage
    track_potion_used(user_data)
    
    # Add effect
    effect_data = {
        "potion_id": potion_id,
        "name": potion["name"],
        "icon": potion["icon"],
        "type": effect["type"],
        "amount": effect["amount"],
        "duration": effect["duration"],
        "start_time": time.time(),
        "expire_time": time.time() + effect["duration"] if effect["duration"] > 0 else 0
    }
    
    user_data["active_effects"].append(effect_data)
    
    save_user_data(user_data)
    
    return True, f"Used {potion['icon']} {potion['name']}!"

def clean_expired_effects(user_data: dict):
    """Remove expired effects. Returns True if any effects were removed."""
    import time
    
    if "active_effects" not in user_data:
        return False
    
    current_time = time.time()
    original_count = len(user_data["active_effects"])
    
    # Keep effects that are either instant (duration=0) or not expired yet
    user_data["active_effects"] = [
        effect for effect in user_data["active_effects"]
        if effect.get("duration", 0) == 0 or effect.get("expire_time", 0) > current_time
    ]
    
    removed_count = original_count - len(user_data["active_effects"])
    
    if removed_count > 0:
        save_user_data(user_data)
        return True
    
    return False

def get_active_luck_bonus(user_data: dict) -> float:
    """Calculate total luck bonus from active effects."""
    import time
    
    if "active_effects" not in user_data:
        return 0.0
    
    current_time = time.time()
    total_bonus = 0.0
    
    for effect in user_data["active_effects"]:
        # Check if not expired
        if effect["duration"] == 0 or effect["expire_time"] > current_time:
            if effect["type"] in ["luck_boost", "instant_luck"]:
                total_bonus += effect["amount"]
    
    return total_bonus

def consume_instant_effects(user_data: dict):
    """Consume instant effects (like Angelic Potion) after use."""
    if "active_effects" not in user_data:
        return
    
    # Remove instant effects
    user_data["active_effects"] = [
        effect for effect in user_data["active_effects"]
        if effect["type"] != "instant_luck"
    ]
    
    save_user_data(user_data)

def update_inventory(user_data: dict, light_name: str, amount: int = 1) -> bool:
    """Updates inventory and saves to database."""
    try:
        if light_name not in user_data["inventory"]:
            user_data["inventory"][light_name] = 0
        
        user_data["inventory"][light_name] += amount
        
        # Remove if count is 0 or negative
        if user_data["inventory"][light_name] <= 0:
            del user_data["inventory"][light_name]
        
        # Save to database
        return save_user_data(user_data)
        
    except Exception as e:
        logging.error(f"Error updating inventory: {e}")
        return False

def update_gear_inventory(user_data: dict, gear_name: str, amount: int = 1) -> bool:
    """Updates gear inventory and saves to database."""
    try:
        if gear_name not in user_data["gear_inventory"]:
            user_data["gear_inventory"][gear_name] = 0
        
        user_data["gear_inventory"][gear_name] += amount
        
        # Remove if count is 0 or negative
        if user_data["gear_inventory"][gear_name] <= 0:
            del user_data["gear_inventory"][gear_name]
        
        # Save to database
        return save_user_data(user_data)
        
    except Exception as e:
        logging.error(f"Error updating gear inventory: {e}")
        return False

def equip_light(user_data: dict, light: dict) -> bool:
    """Equips a light and saves to database."""
    try:
        user_data["equipped_light"] = light
        return save_user_data(user_data)
    except Exception as e:
        logging.error(f"Error equipping light: {e}")
        return False

def equip_gear(user_data: dict, gear_name: str, hand: str) -> bool:
    """Equips a gear and saves to database."""
    try:
        if hand not in ["left_hand", "right_hand"]:
            return False
        
        user_data["equipped_gear"][hand] = gear_name
        return save_user_data(user_data)
    except Exception as e:
        logging.error(f"Error equipping gear: {e}")
        return False

def unequip_gear(user_data: dict, hand: str) -> tuple:
    """Unequips a gear from specified hand. Returns (success, gear_name_or_message)."""
    try:
        if hand not in ["left_hand", "right_hand"]:
            return False, "Invalid hand! Use 'left_hand' or 'right_hand'."
        
        # Check if there's a gear equipped
        current_gear = user_data["equipped_gear"].get(hand)
        if not current_gear:
            hand_display = "LEFT" if hand == "left_hand" else "RIGHT"
            return False, f"No gear equipped on {hand_display} hand!"
        
        # Remove the gear
        user_data["equipped_gear"][hand] = None
        success = save_user_data(user_data)
        
        if success:
            return True, current_gear
        else:
            return False, "Failed to save unequip state."
    except Exception as e:
        logging.error(f"Error unequipping gear: {e}")
        return False, f"Error: {str(e)}"

def set_auto_roll(user_data: dict, enabled: bool) -> bool:
    """Sets auto-roll state and saves to database."""
    try:
        user_data["auto_roll"] = enabled
        return save_user_data(user_data)
    except Exception as e:
        logging.error(f"Error setting auto_roll: {e}")
        return False

def set_rolling_state(user_data: dict, is_rolling: bool) -> bool:
    """Sets rolling state and saves to database."""
    try:
        user_data["is_rolling"] = is_rolling
        result = save_user_data(user_data)
        
        # Verify the save was successful by reading back
        if result:
            verification = users_collection.find_one({"user_id": user_data["user_id"]})
            if verification and verification.get("is_rolling") == is_rolling:
                logging.info(f"Successfully set is_rolling={is_rolling} for user {user_data['user_id']}")
                return True
            else:
                logging.error(f"Failed to verify is_rolling state for user {user_data['user_id']}")
                return False
        return result
    except Exception as e:
        logging.error(f"Error setting rolling state: {e}")
        return False

def update_highest_light(user_data: dict, light: dict) -> bool:
    """Updates highest light if current is better."""
    try:
        current_highest = user_data["highest_light"]
        rolled_numeric_rarity = light.get("numeric_rarity", light["rarity"])
        
        if isinstance(rolled_numeric_rarity, str):
            rolled_numeric_rarity = 999999
        
        if current_highest is None:
            user_data["highest_light"] = light
            return save_user_data(user_data)
        else:
            highest_numeric = current_highest.get("numeric_rarity", current_highest["rarity"])
            if isinstance(highest_numeric, str):
                highest_numeric = 999999
            
            if rolled_numeric_rarity > highest_numeric:
                user_data["highest_light"] = light
                return save_user_data(user_data)
        
        return True
        
    except Exception as e:
        logging.error(f"Error updating highest light: {e}")
        return False

def increment_total_rolls(user_data: dict) -> bool:
    """Increments total rolls counter."""
    try:
        user_data["total_rolls"] += 1
        
        # Also increment daily rolls
        if "daily_stats" not in user_data:
            user_data["daily_stats"] = {}
        user_data["daily_stats"]["rolls"] = user_data["daily_stats"].get("rolls", 0) + 1
        
        return save_user_data(user_data)
    except Exception as e:
        logging.error(f"Error incrementing rolls: {e}")
        return False

def track_gear_crafted(user_data: dict, gear_name: str):
    """Track gear crafting stats."""
    if "stats" not in user_data:
        user_data["stats"] = {"gears_crafted": 0, "unique_gears_list": []}
    
    user_data["stats"]["gears_crafted"] = user_data["stats"].get("gears_crafted", 0) + 1
    
    # Track unique gears
    unique_list = user_data["stats"].get("unique_gears_list", [])
    if gear_name not in unique_list:
        unique_list.append(gear_name)
        user_data["stats"]["unique_gears_list"] = unique_list
    
    # Also track daily crafts
    if "daily_stats" not in user_data:
        user_data["daily_stats"] = {}
    user_data["daily_stats"]["crafts"] = user_data["daily_stats"].get("crafts", 0) + 1
    
    save_user_data(user_data)

def track_potion_used(user_data: dict):
    """Track potion usage stats."""
    if "stats" not in user_data:
        user_data["stats"] = {"potions_used": 0}
    
    user_data["stats"]["potions_used"] = user_data["stats"].get("potions_used", 0) + 1
    
    # Also track daily
    if "daily_stats" not in user_data:
        user_data["daily_stats"] = {}
    user_data["daily_stats"]["potions_used"] = user_data["daily_stats"].get("potions_used", 0) + 1
    
    save_user_data(user_data)

def track_potion_bought(user_data: dict):
    """Track potion purchase stats."""
    if "stats" not in user_data:
        user_data["stats"] = {"potions_bought": 0}
    
    user_data["stats"]["potions_bought"] = user_data["stats"].get("potions_bought", 0) + 1
    save_user_data(user_data)

def track_rare_light(user_data: dict, rarity: int):
    """Track rarest light rolled today."""
    if "daily_stats" not in user_data:
        user_data["daily_stats"] = {}
    
    current_rarest = user_data["daily_stats"].get("rarest_today", 0)
    if rarity > current_rarest:
        user_data["daily_stats"]["rarest_today"] = rarity
    
    save_user_data(user_data)

def update_activity(user_data: dict):
    """Update last activity time. 
    Playtime now runs continuously once user joins a server (no idle timeout).
    Playtime is calculated based on server_join_time."""
    import time
    
    user_id = user_data.get("user_id", "unknown")
    threshold_before = user_data.get("auto_discard_threshold", 0)
    
    current_time = time.time()
    
    # Simply update last activity timestamp
    user_data["last_activity"] = current_time
    
    # Initialize session_start if not exists (for compatibility)
    if "session_start" not in user_data:
        user_data["session_start"] = current_time
    
    save_user_data(user_data)
    
    # Verify threshold wasn't lost
    threshold_after = user_data.get("auto_discard_threshold", 0)
    if threshold_before != threshold_after:
        logging.warning(f"⚠️ update_activity changed auto_discard_threshold for user {user_id}: {threshold_before} → {threshold_after}")

def get_playtime_display(user_data: dict) -> str:
    """Get formatted playtime display.
    Playtime is calculated continuously from server join time (no idle timeout)."""
    import time
    
    # Check if user has joined a server
    server_id = user_data.get("server_id")
    if not server_id:
        return "0m (No server)"
    
    # Get server join time
    server_join_time = user_data.get("server_join_time")
    if not server_join_time:
        # If no join time recorded, use current time as baseline
        return "0m"
    
    current_time = time.time()
    
    # Calculate total playtime: time since joining server
    playtime_on_server = current_time - server_join_time
    
    # Convert to hours and minutes
    hours = int(playtime_on_server // 3600)
    minutes = int((playtime_on_server % 3600) // 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

def get_total_playtime_seconds(user_data: dict) -> float:
    """Get total playtime in seconds for leaderboard sorting.
    Returns continuous playtime since joining server."""
    import time
    
    # Check if user has joined a server
    server_id = user_data.get("server_id")
    if not server_id:
        return 0.0
    
    # Get server join time
    server_join_time = user_data.get("server_join_time")
    if not server_join_time:
        return 0.0
    
    current_time = time.time()
    
    # Calculate playtime: time since joining server
    playtime_seconds = current_time - server_join_time
    
    return max(0.0, playtime_seconds)  # Ensure non-negative



# ============================================
# WORLD STATE MANAGEMENT
# ============================================

def get_world_state_from_db() -> dict:
    """Get world state from database."""
    try:
        world_state = world_collection.find_one({"_id": "global_world"})
        if world_state:
            # Remove MongoDB _id field
            world_state.pop("_id", None)
        return world_state
    except Exception as e:
        logging.error(f"Error getting world state: {e}")
        return None

def save_world_state_to_db(world_state: dict):
    """Save world state to database."""
    try:
        world_collection.update_one(
            {"_id": "global_world"},
            {"$set": world_state},
            upsert=True
        )
    except Exception as e:
        logging.error(f"Error saving world state: {e}")

def get_current_world_state() -> dict:
    """Get current world state, regenerating if needed."""
    from utils.world_manager import get_world_state
    
    db_state = get_world_state_from_db()
    world_state = get_world_state(db_state)
    
    # Save if new or regenerated
    if not db_state or world_state != db_state:
        save_world_state_to_db(world_state)
    
    return world_state

def give_burnt_effect(user_data: dict):
    """Give Burnt effect to user (+60% luck)."""
    import time
    
    # Check if already has Burnt effect
    for effect in user_data.get("active_effects", []):
        if effect.get("potion_id") == "burnt_effect":
            return  # Already has effect
    
    # Add Burnt effect (permanent until used)
    burnt_effect = {
        "potion_id": "burnt_effect",
        "name": "Burnt",
        "icon": "🔥",
        "type": "luck_boost",
        "amount": 0.60,  # 60% as decimal
        "duration": 0,  # Instant (consumed on next roll)
        "start_time": time.time(),
        "expire_time": 0
    }
    
    if "active_effects" not in user_data:
        user_data["active_effects"] = []
    
    user_data["active_effects"].append(burnt_effect)
    save_user_data(user_data)

# ============================================
# AUTO-CRAFT SYSTEM
# ============================================

def set_auto_craft(user_data: dict, gear_name: str, auto_add: bool, auto_craft: bool) -> bool:
    """Set auto-craft settings for a gear."""
    try:
        if "auto_craft_settings" not in user_data:
            user_data["auto_craft_settings"] = {}
        
        user_data["auto_craft_settings"][gear_name] = {
            "auto_add": auto_add,
            "auto_craft": auto_craft
        }
        
        return save_user_data(user_data)
    except Exception as e:
        logging.error(f"Error setting auto-craft: {e}")
        return False

def get_auto_craft_settings(user_data: dict, gear_name: str) -> dict:
    """Get auto-craft settings for a gear."""
    if "auto_craft_settings" not in user_data:
        return {"auto_add": False, "auto_craft": False}
    
    return user_data["auto_craft_settings"].get(gear_name, {"auto_add": False, "auto_craft": False})

def check_auto_craft(user_data: dict, light_name: str):
    """Check if any gear with auto-add enabled needs this light, and auto-craft if ready."""
    import logging
    from config import GEARS
    
    logging.info(f"🔨 check_auto_craft called for light: '{light_name}'")
    logging.info(f"🔨 GEARS loaded: {list(GEARS.keys())}")
    
    if "auto_craft_settings" not in user_data:
        logging.info(f"🔨 No auto-craft settings found for user {user_data['user_id']}")
        return []
    
    crafted_gears = []
    
    logging.info(f"🔨 Auto-craft settings: {user_data['auto_craft_settings']}")
    
    for gear_name, settings in user_data["auto_craft_settings"].items():
        logging.info(f"🔨 Checking gear: '{gear_name}', settings: {settings}")
        
        if not settings.get("auto_add", False):
            logging.info(f"🔨 {gear_name}: Auto-add is OFF, skipping")
            continue
        
        # Check if this gear needs the light we just got
        if gear_name not in GEARS:
            logging.warning(f"🔨 {gear_name}: Not found in GEARS!")
            logging.warning(f"🔨 Available gears: {list(GEARS.keys())}")
            continue
        
        recipe = GEARS[gear_name]["recipe"]
        if light_name not in recipe:
            logging.info(f"🔨 {gear_name}: Doesn't need {light_name}")
            continue
        
        # Check if reserve is already full for this light
        required_amount = recipe[light_name]
        
        # Get current reserve
        if "craft_reserves" not in user_data:
            user_data["craft_reserves"] = {}
        
        if gear_name not in user_data["craft_reserves"]:
            user_data["craft_reserves"][gear_name] = {}
        
        current_reserve = user_data["craft_reserves"][gear_name].get(light_name, 0)
        
        # If reserve is already full, skip
        if current_reserve >= required_amount:
            logging.info(f"🔨 {gear_name}: Reserve for {light_name} is FULL ({current_reserve}/{required_amount}), skipping")
            continue
        
        logging.info(f"🔨 {gear_name}: Needs {light_name}! Auto-adding to reserve (current: {current_reserve}/{required_amount})...")
        
        # Auto-add: Move light from inventory to reserve
        user_id = user_data["user_id"]
        success, msg = add_light_to_reserve(user_data, gear_name, light_name, 1)
        
        if success:
            logging.info(f"🔨 {gear_name}: {msg}")
        else:
            logging.error(f"🔨 {gear_name}: Failed to add to reserve - {msg}")
            continue
        
        # Refresh user data after adding to reserve
        user_data_fresh = get_user_data(user_id)
        
        # Check if auto-craft is enabled and we can craft with reserve
        if settings.get("auto_craft", False):
            can_craft_it, missing = can_craft_with_reserve(user_data_fresh, gear_name)
            logging.info(f"🔨 {gear_name}: Can craft with reserve = {can_craft_it}, Missing = {missing}")
            
            if can_craft_it:
                logging.info(f"🔨 {gear_name}: Attempting to craft with reserve...")
                success = craft_with_reserve(user_data_fresh, gear_name)
                if success:
                    logging.info(f"🔨 {gear_name}: AUTO-CRAFTED SUCCESSFULLY!")
                    crafted_gears.append(gear_name)
                    # Update the original user_data reference
                    user_data.update(get_user_data(user_id))
                else:
                    logging.error(f"🔨 {gear_name}: Craft failed!")
            else:
                logging.info(f"🔨 {gear_name}: Not ready yet, missing materials in reserve")
        else:
            logging.info(f"🔨 {gear_name}: Auto-craft is OFF, light added to reserve only")
    
    logging.info(f"🔨 Auto-craft result: {crafted_gears}")
    return crafted_gears

def is_light_needed_for_auto_add(user_data: dict, light_name: str) -> bool:
    """Check if a light is needed for any gear with auto-add enabled.
    Returns True only if:
    1. Gear has auto-add enabled
    2. Gear recipe needs this light
    3. Reserve for this light is NOT yet full (still needs more)
    """
    from config import GEARS
    
    if "auto_craft_settings" not in user_data:
        return False
    
    for gear_name, settings in user_data["auto_craft_settings"].items():
        # Only check gears with auto-add enabled
        if not settings.get("auto_add", False):
            continue
        
        # Check if gear exists
        if gear_name not in GEARS:
            continue
        
        # Check if gear needs this light
        recipe = GEARS[gear_name]["recipe"]
        if light_name not in recipe:
            continue
        
        # Check if reserve is already full for this light
        required_amount = recipe[light_name]
        
        # Get current reserve
        if "craft_reserves" not in user_data:
            user_data["craft_reserves"] = {}
        
        if gear_name not in user_data["craft_reserves"]:
            user_data["craft_reserves"][gear_name] = {}
        
        current_reserve = user_data["craft_reserves"][gear_name].get(light_name, 0)
        
        # If reserve is not full yet, we still need this light
        if current_reserve < required_amount:
            logging.info(f"🔨 Light {light_name} is needed for {gear_name} (auto-add enabled, reserve: {current_reserve}/{required_amount})")
            return True
        else:
            logging.info(f"🔨 Light {light_name} reserve FULL for {gear_name} ({current_reserve}/{required_amount}), not saving from discard")
    
    return False

# ============================================
# INVENTORY UPGRADE SYSTEM
# ============================================

def calculate_upgrade_cost(current_upgrades: int) -> int:
    """Calculate cost for next inventory upgrade. Formula: 10^(n+1) coins."""
    return 10 ** (current_upgrades + 1)

def upgrade_inventory_slots(user_data: dict) -> tuple:
    """Upgrade inventory slots. Returns (success, message)."""
    try:
        current_upgrades = user_data.get("inventory_upgrades", 0)
        cost = calculate_upgrade_cost(current_upgrades)
        coins = user_data.get("coins", 0)
        
        if coins < cost:
            return False, f"Not enough coins! Need {cost:,} coins."
        
        # Deduct coins
        user_data["coins"] -= cost
        
        # Increase slots
        user_data["inventory_upgrades"] = current_upgrades + 1
        user_data["max_inventory_slots"] = user_data.get("max_inventory_slots", 120) + 10
        
        save_user_data(user_data)
        
        return True, f"Upgraded! +10 slots (now {user_data['max_inventory_slots']} slots)"
    
    except Exception as e:
        logging.error(f"Error upgrading inventory: {e}")
        return False, "Upgrade failed!"

def get_max_inventory_slots(user_data: dict) -> int:
    """Get max inventory slots for user."""
    return user_data.get("max_inventory_slots", 120)

# ============================================
# CRAFT RESERVES SYSTEM
# ============================================

def add_light_to_reserve(user_data: dict, gear_name: str, light_name: str, amount: int = 1) -> tuple:
    """Add light from inventory to craft reserve. Returns (success, message)."""
    try:
        # Check if user has enough light in inventory
        current_inv = user_data["inventory"].get(light_name, 0)
        if current_inv < amount:
            return False, f"Not enough {light_name} in inventory! Have {current_inv}, need {amount}."
        
        # Initialize craft_reserves if not exists
        if "craft_reserves" not in user_data:
            user_data["craft_reserves"] = {}
        
        if gear_name not in user_data["craft_reserves"]:
            user_data["craft_reserves"][gear_name] = {}
        
        # Transfer from inventory to reserve
        user_data["inventory"][light_name] -= amount
        if user_data["inventory"][light_name] <= 0:
            del user_data["inventory"][light_name]
        
        # Add to reserve
        current_reserve = user_data["craft_reserves"][gear_name].get(light_name, 0)
        user_data["craft_reserves"][gear_name][light_name] = current_reserve + amount
        
        save_user_data(user_data)
        return True, f"Added {amount}x {light_name} to {gear_name} reserve"
    
    except Exception as e:
        logging.error(f"Error adding to reserve: {e}")
        return False, "Failed to add to reserve"

def get_craft_reserve(user_data: dict, gear_name: str) -> dict:
    """Get craft reserve for a gear."""
    if "craft_reserves" not in user_data:
        return {}
    return user_data["craft_reserves"].get(gear_name, {})

def can_craft_with_reserve(user_data: dict, gear_name: str) -> tuple:
    """Check if can craft with reserved materials. Returns (can_craft, missing)."""
    import logging
    
    try:
        from config import GEARS
        
        logging.info(f"🔨 can_craft_with_reserve called for: '{gear_name}'")
        logging.info(f"🔨 Available gears: {list(GEARS.keys())}")
        logging.info(f"🔨 Gear name type: {type(gear_name)}, length: {len(gear_name)}")
        
        if gear_name not in GEARS:
            logging.error(f"❌ Gear '{gear_name}' not found in GEARS!")
            logging.error(f"❌ Checking each gear name:")
            for g in GEARS.keys():
                logging.error(f"  - '{g}' (len={len(g)}) == '{gear_name}'? {g == gear_name}")
            return False, {}
        
        recipe = GEARS[gear_name]["recipe"]
        reserve = get_craft_reserve(user_data, gear_name)
        missing = {}
        
        for light_name, required_amount in recipe.items():
            current_reserve = reserve.get(light_name, 0)
            if current_reserve < required_amount:
                missing[light_name] = required_amount - current_reserve
        
        return len(missing) == 0, missing
    
    except Exception as e:
        logging.error(f"❌ Exception in can_craft_with_reserve: {e}")
        import traceback
        traceback.print_exc()
        return False, {}

def craft_with_reserve(user_data: dict, gear_name: str) -> bool:
    """Craft gear using reserved materials."""
    from config import GEARS
    
    can_craft_it, missing = can_craft_with_reserve(user_data, gear_name)
    
    if not can_craft_it:
        return False
    
    # Deduct materials from reserve
    if "craft_reserves" not in user_data:
        return False
    
    if gear_name not in user_data["craft_reserves"]:
        return False
    
    recipe = GEARS[gear_name]["recipe"]
    for light_name, required_amount in recipe.items():
        user_data["craft_reserves"][gear_name][light_name] -= required_amount
        if user_data["craft_reserves"][gear_name][light_name] <= 0:
            del user_data["craft_reserves"][gear_name][light_name]
    
    # Clean up empty reserve
    if not user_data["craft_reserves"][gear_name]:
        del user_data["craft_reserves"][gear_name]
    
    # Add gear to inventory
    update_gear_inventory(user_data, gear_name, 1)
    
    # Track crafting stats
    track_gear_crafted(user_data, gear_name)
    
    return True

# ============================================
# DISCARD SYSTEM
# ============================================

def discard_light(user_data: dict, light_name: str, amount: int) -> tuple:
    """Discard light from inventory. Returns (success, message)."""
    try:
        current = user_data["inventory"].get(light_name, 0)
        
        if current <= 0:
            return False, f"You don't have any {light_name}!"
        
        if amount > current:
            return False, f"You only have {current}x {light_name}, can't discard {amount}!"
        
        # Remove from inventory
        user_data["inventory"][light_name] -= amount
        if user_data["inventory"][light_name] <= 0:
            del user_data["inventory"][light_name]
        
        save_user_data(user_data)
        return True, f"Discarded {amount}x {light_name}"
    
    except Exception as e:
        logging.error(f"Error discarding light: {e}")
        return False, "Failed to discard"

def set_auto_discard_threshold(user_data: dict, threshold: int) -> bool:
    """Set auto-discard threshold. Lights with rarity <= threshold will be auto-discarded."""
    try:
        user_id = user_data.get("user_id", "unknown")
        old_threshold = user_data.get("auto_discard_threshold", 0)
        user_data["auto_discard_threshold"] = threshold
        logging.info(f"🗑️ Setting auto_discard_threshold for user {user_id}: {old_threshold} → {threshold}")
        result = save_user_data(user_data)
        logging.info(f"🗑️ Save result: {result}")
        return result
    except Exception as e:
        logging.error(f"Error setting auto-discard threshold: {e}")
        return False

def get_auto_discard_threshold(user_data: dict) -> int:
    """Get auto-discard threshold."""
    return user_data.get("auto_discard_threshold", 0)

def should_auto_discard(light: dict, user_data: dict) -> bool:
    """Check if light should be auto-discarded based on threshold."""
    import logging
    
    threshold = get_auto_discard_threshold(user_data)
    
    logging.info(f"🗑️ Auto-discard check: light={light.get('name')}, threshold={threshold}")
    
    if threshold == 0:
        logging.info(f"🗑️ Auto-discard DISABLED (threshold=0)")
        return False  # Auto-discard disabled
    
    # Get numeric rarity
    rarity = light.get("numeric_rarity", light.get("rarity", 0))
    
    if isinstance(rarity, str):
        logging.info(f"🗑️ Special light (rarity=string), keeping")
        return False  # Special lights, don't auto-discard
    
    should_discard = rarity <= threshold
    logging.info(f"🗑️ Light rarity={rarity}, threshold={threshold}, discard={should_discard}")
    
    return should_discard

# ============================================
# SERVER SYSTEM
# ============================================

def get_user_server(user_data: dict) -> str:
    """Get user's current server ID. Returns None if not selected."""
    return user_data.get("server_id", None)

def set_user_server(user_data: dict, server_id: str) -> bool:
    """Set user's server. Returns success status."""
    try:
        import time
        
        old_server = user_data.get("server_id", None)
        user_data["server_id"] = server_id
        user_data["server_join_time"] = time.time()
        
        user_id = user_data.get("user_id", "unknown")
        logging.info(f"🌐 User {user_id} switched server: {old_server} → {server_id}")
        
        return save_user_data(user_data)
    except Exception as e:
        logging.error(f"Error setting user server: {e}")
        return False

def get_server_player_count(server_id: str) -> int:
    """Get number of players in a server."""
    try:
        count = users_collection.count_documents({"server_id": server_id})
        return count
    except Exception as e:
        logging.error(f"Error getting server player count: {e}")
        return 0

def is_server_full(server_id: str, max_capacity: int = 100) -> bool:
    """Check if server is at max capacity."""
    return get_server_player_count(server_id) >= max_capacity

def get_all_servers_info() -> dict:
    """Get player counts for all servers."""
    try:
        # Aggregate to get counts per server
        pipeline = [
            {"$match": {"server_id": {"$ne": None}}},
            {"$group": {"_id": "$server_id", "count": {"$sum": 1}}}
        ]
        
        result = users_collection.aggregate(pipeline)
        server_counts = {doc["_id"]: doc["count"] for doc in result}
        
        return server_counts
    except Exception as e:
        logging.error(f"Error getting all servers info: {e}")
        return {}

def get_server_leaderboard(server_id: str, sort_by: str = "level", limit: int = 100) -> list:
    """Get leaderboard for a specific server.
    
    Args:
        server_id: Server ID to get leaderboard for
        sort_by: Field to sort by (level, total_rolls, coins, playtime)
        limit: Number of players to return
    
    Returns:
        List of user data dicts sorted by the specified field
    """
    try:
        import time
        current_time = time.time()
        
        # Sort order mapping
        if sort_by == "level":
            sort_field = "level"
        elif sort_by == "rolls":
            sort_field = "total_rolls"
        elif sort_by == "coins":
            sort_field = "coins"
        elif sort_by == "playtime":
            # For playtime, we need to calculate it dynamically
            # Get all players in server
            players = list(users_collection.find({"server_id": server_id}))
            
            # Calculate real-time playtime for each player
            for player in players:
                join_time = player.get("server_join_time")
                if join_time and isinstance(join_time, (int, float)):
                    player["total_playtime"] = current_time - join_time
                else:
                    player["total_playtime"] = 0
            
            # Sort by playtime
            players.sort(key=lambda x: x.get("total_playtime", 0), reverse=True)
            return players[:limit]
        else:
            # Default to level if invalid
            sort_field = "level"
        
        # For other fields, use standard query
        players = users_collection.find(
            {"server_id": server_id}
        ).sort(sort_field, -1).limit(limit)
        
        return list(players)
    except Exception as e:
        logging.error(f"Error getting server leaderboard: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_global_leaderboard(sort_by: str = "level", limit: int = 100) -> list:
    """Get global leaderboard across all servers.
    
    Args:
        sort_by: Field to sort by (level, total_rolls, coins, playtime)
        limit: Number of players to return
    
    Returns:
        List of user data dicts sorted by the specified field
    """
    try:
        import time
        current_time = time.time()
        
        # Sort order mapping
        if sort_by == "level":
            sort_field = "level"
        elif sort_by == "rolls":
            sort_field = "total_rolls"
        elif sort_by == "coins":
            sort_field = "coins"
        elif sort_by == "playtime":
            # For playtime, calculate it dynamically
            # Get all players who have joined a server
            players = list(users_collection.find({"server_id": {"$exists": True, "$ne": None}}))
            
            # Calculate real-time playtime for each player
            for player in players:
                join_time = player.get("server_join_time")
                if join_time and isinstance(join_time, (int, float)):
                    player["total_playtime"] = current_time - join_time
                else:
                    player["total_playtime"] = 0
            
            # Sort by playtime
            players.sort(key=lambda x: x.get("total_playtime", 0), reverse=True)
            return players[:limit]
        else:
            # Default to level if invalid
            sort_field = "level"
        
        # For other fields, use standard query
        players = users_collection.find().sort(sort_field, -1).limit(limit)
        
        return list(players)
    except Exception as e:
        logging.error(f"Error getting global leaderboard: {e}")
        return []



# ============================================
# PREMIUM SUBSCRIPTION SYSTEM
# ============================================

def get_premium_status(user_data: dict) -> dict:
    """Get user's premium subscription status.
    
    Returns:
        dict: Premium info with active, tier, days_left, auto_renew
    """
    import time
    
    premium = user_data.get("premium", {})
    
    if not premium.get("active"):
        return {"active": False, "tier": None, "days_left": 0}
    
    expire_time = premium.get("expire_time")
    if not expire_time:
        return {"active": False, "tier": None, "days_left": 0}
    
    current_time = time.time()
    
    # Check if expired
    if current_time > expire_time:
        # Expire premium
        premium["active"] = False
        premium["tier"] = None
        user_data["premium"] = premium
        save_user_data(user_data)
        return {"active": False, "tier": None, "days_left": 0}
    
    # Calculate days left
    seconds_left = expire_time - current_time
    days_left = int(seconds_left / 86400)
    
    return {
        "active": True,
        "tier": premium.get("tier"),
        "days_left": days_left,
        "auto_renew": premium.get("auto_renew", False),
        "expire_time": expire_time
    }

def activate_premium(user_data: dict, tier: str, duration_days: int = 30) -> bool:
    """Activate premium subscription for user.
    
    Args:
        user_data: User data dict
        tier: "basic" or "pro"
        duration_days: Duration in days (default 30)
    
    Returns:
        bool: Success status
    """
    import time
    
    try:
        current_time = time.time()
        expire_time = current_time + (duration_days * 86400)
        
        if "premium" not in user_data:
            user_data["premium"] = {}
        
        user_data["premium"]["active"] = True
        user_data["premium"]["tier"] = tier
        user_data["premium"]["expire_time"] = expire_time
        user_data["premium"]["monthly_rewards_claimed"] = False
        
        # Enable auto-roll permanently for premium users
        user_data["auto_roll"] = True
        
        # For Pro tier, grant 2 random exclusive lights
        if tier == "pro":
            grant_exclusive_lights(user_data)
        
        logging.info(f"Activated {tier} premium for user {user_data['user_id']} for {duration_days} days")
        return save_user_data(user_data)
        
    except Exception as e:
        logging.error(f"Error activating premium: {e}")
        return False

def claim_monthly_premium_rewards(user_data: dict) -> dict:
    """Claim monthly premium rewards.
    
    Returns:
        dict: Rewards claimed with coins, potions count
    """
    import json
    
    try:
        premium = user_data.get("premium", {})
        
        if not premium.get("active"):
            return {"success": False, "message": "Premium not active"}
        
        if premium.get("monthly_rewards_claimed"):
            return {"success": False, "message": "Monthly rewards already claimed"}
        
        tier = premium.get("tier")
        
        # Load premium tiers
        with open("data/premium_tiers.json", "r", encoding="utf-8") as f:
            tiers = json.load(f)
        
        if tier not in tiers:
            return {"success": False, "message": "Invalid tier"}
        
        benefits = tiers[tier]["benefits"]
        
        # Add coins
        coins_reward = benefits["monthly_coins"]
        user_data["coins"] = user_data.get("coins", 0) + coins_reward
        
        # Add luck potions
        potions_reward = benefits["monthly_luck_potions"]
        if "potion_inventory" not in user_data:
            user_data["potion_inventory"] = {}
        
        user_data["potion_inventory"]["luck_potion_1"] = user_data["potion_inventory"].get("luck_potion_1", 0) + potions_reward
        
        # Mark as claimed
        user_data["premium"]["monthly_rewards_claimed"] = True
        
        save_user_data(user_data)
        
        return {
            "success": True,
            "coins": coins_reward,
            "potions": potions_reward,
            "tier": tier
        }
        
    except Exception as e:
        logging.error(f"Error claiming premium rewards: {e}")
        return {"success": False, "message": str(e)}

def get_premium_multipliers(user_data: dict) -> dict:
    """Get premium multipliers for coins, exp, and luck.
    
    Returns:
        dict: Multipliers with coins_mult, exp_mult, luck_boost_percent
    """
    import json
    
    premium = user_data.get("premium", {})
    
    if not premium.get("active"):
        return {
            "coins_mult": 1.0,
            "exp_mult": 1.0,
            "luck_boost_percent": 0,
            "shop_discount": 0
        }
    
    tier = premium.get("tier")
    
    try:
        with open("data/premium_tiers.json", "r", encoding="utf-8") as f:
            tiers = json.load(f)
        
        if tier not in tiers:
            return {
                "coins_mult": 1.0,
                "exp_mult": 1.0,
                "luck_boost_percent": 0,
                "shop_discount": 0
            }
        
        benefits = tiers[tier]["benefits"]
        
        return {
            "coins_mult": benefits.get("coins_multiplier", 1.0),
            "exp_mult": benefits.get("exp_multiplier", 1.0),
            "luck_boost_percent": benefits.get("luck_boost_percent", 0),
            "shop_discount": benefits.get("shop_discount_percent", 0)
        }
        
    except Exception as e:
        logging.error(f"Error getting premium multipliers: {e}")
        return {
            "coins_mult": 1.0,
            "exp_mult": 1.0,
            "luck_boost_percent": 0,
            "shop_discount": 0
        }

def has_exclusive_light_access(user_data: dict) -> bool:
    """Check if user has access to exclusive lights (Pro tier only)."""
    premium = user_data.get("premium", {})
    
    if not premium.get("active"):
        return False
    
    return premium.get("tier") == "pro"

def get_premium_title(user_data: dict) -> str:
    """Get user's premium title.
    
    Returns:
        str: Premium title or empty string
    """
    import json
    
    premium = user_data.get("premium", {})
    
    if not premium.get("active"):
        return ""
    
    tier = premium.get("tier")
    
    try:
        with open("data/premium_tiers.json", "r", encoding="utf-8") as f:
            tiers = json.load(f)
        
        if tier in tiers:
            return tiers[tier]["benefits"].get("title", "")
        
        return ""
        
    except Exception as e:
        logging.error(f"Error getting premium title: {e}")
        return ""

def grant_exclusive_lights(user_data: dict) -> list:
    """Grant 2 random exclusive lights to Pro tier user on purchase.
    
    Args:
        user_data: User data dict
    
    Returns:
        list: List of granted exclusive light names
    """
    import random
    from config import EXCLUSIVE_LIGHTS
    
    try:
        # Check if already granted (prevent duplicate grants)
        if "exclusive_lights_granted" not in user_data:
            user_data["exclusive_lights_granted"] = []
        
        # Get all exclusive lights
        exclusive_names = [light["name"] for light in EXCLUSIVE_LIGHTS]
        
        # Randomly select 2 of 3
        granted = random.sample(exclusive_names, 2)
        
        # Store which lights were granted
        user_data["exclusive_lights_granted"] = granted
        
        # Add to inventory
        for light_name in granted:
            update_inventory(user_data, light_name, 1)
        
        logging.info(f"Granted exclusive lights to user {user_data['user_id']}: {granted}")
        save_user_data(user_data)
        
        return granted
        
    except Exception as e:
        logging.error(f"Error granting exclusive lights: {e}")
        return []

def has_exclusive_light_unlocked(user_data: dict, light_name: str) -> bool:
    """Check if user has unlocked a specific exclusive light.
    
    Args:
        user_data: User data dict
        light_name: Name of the exclusive light
    
    Returns:
        bool: True if light is unlocked
    """
    granted_lights = user_data.get("exclusive_lights_granted", [])
    return light_name in granted_lights

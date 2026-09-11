"""Daily quest management system"""

import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from config import DAILY_QUESTS_DATA

def get_today_date() -> str:
    """Get today's date as string (YYYY-MM-DD)."""
    return datetime.now().strftime("%Y-%m-%d")

def get_time_until_reset() -> str:
    """Get time remaining until daily reset (midnight)."""
    now = datetime.now()
    tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    time_diff = tomorrow - now
    
    hours = time_diff.seconds // 3600
    minutes = (time_diff.seconds % 3600) // 60
    
    return f"{hours}h {minutes}m"

def should_reset_daily_quests(user_data: dict) -> bool:
    """Check if daily quests should be reset."""
    last_reset = user_data.get("last_quest_reset", "")
    today = get_today_date()
    return last_reset != today

def generate_daily_quests() -> List[Dict]:
    """Generate 4 random daily quests from the pool."""
    quest_pool = DAILY_QUESTS_DATA["quest_pool"]
    
    # Collect all available quests
    all_quests = []
    for category, quests in quest_pool.items():
        all_quests.extend(quests)
    
    # Randomly select 4 quests
    selected = random.sample(all_quests, min(4, len(all_quests)))
    
    return selected

def reset_daily_quests(user_data: dict):
    """Reset daily quests for a new day."""
    today = get_today_date()
    
    # Generate new quests
    quests = generate_daily_quests()
    
    # Initialize quest data
    user_data["daily_quests"] = {
        "quests": quests,
        "completed": [],
        "claimed_completion_reward": False
    }
    
    # Reset daily stats
    user_data["daily_stats"] = {
        "rolls": 0,
        "levels": 0,
        "playtime_today": 0,
        "session_start": time.time(),
        "crafts": 0,
        "potions_used": 0,
        "rarest_today": 0
    }
    
    user_data["last_quest_reset"] = today
    
    logging.info(f"Reset daily quests for user {user_data['user_id']}")

def check_quest_completion(user_data: dict, quest: Dict) -> bool:
    """Check if a quest is completed."""
    req = quest["requirement"]
    req_type = req["type"]
    req_value = req["value"]
    
    daily_stats = user_data.get("daily_stats", {})
    
    if req_type == "daily_rolls":
        return daily_stats.get("rolls", 0) >= req_value
    
    elif req_type == "daily_levels":
        return daily_stats.get("levels", 0) >= req_value
    
    elif req_type == "daily_playtime":
        # Update current session time
        session_start = daily_stats.get("session_start", time.time())
        current_session = time.time() - session_start
        total_today = daily_stats.get("playtime_today", 0) + current_session
        return total_today >= req_value
    
    elif req_type == "daily_crafts":
        return daily_stats.get("crafts", 0) >= req_value
    
    elif req_type == "daily_rare_light":
        return daily_stats.get("rarest_today", 0) >= req_value
    
    elif req_type == "daily_potions_used":
        return daily_stats.get("potions_used", 0) >= req_value
    
    return False

def get_quest_progress(user_data: dict, quest: Dict) -> str:
    """Get formatted progress string for a quest."""
    req = quest["requirement"]
    req_type = req["type"]
    req_value = req["value"]
    
    daily_stats = user_data.get("daily_stats", {})
    
    if req_type == "daily_rolls":
        current = daily_stats.get("rolls", 0)
        return f"{current}/{req_value} rolls"
    
    elif req_type == "daily_levels":
        current = daily_stats.get("levels", 0)
        return f"{current}/{req_value} level ups"
    
    elif req_type == "daily_playtime":
        session_start = daily_stats.get("session_start", time.time())
        current_session = time.time() - session_start
        total_today = daily_stats.get("playtime_today", 0) + current_session
        
        req_minutes = req_value / 60
        current_minutes = total_today / 60
        return f"{current_minutes:.0f}/{req_minutes:.0f} minutes"
    
    elif req_type == "daily_crafts":
        current = daily_stats.get("crafts", 0)
        return f"{current}/{req_value} crafts"
    
    elif req_type == "daily_rare_light":
        current = daily_stats.get("rarest_today", 0)
        if current >= req_value:
            return f"✅ Obtained (1 in {current:,})"
        return f"Need: 1 in {req_value:,}+"
    
    elif req_type == "daily_potions_used":
        current = daily_stats.get("potions_used", 0)
        return f"{current}/{req_value} potions"
    
    return "Unknown"

def claim_quest_reward(user_data: dict, quest: Dict) -> Dict:
    """Claim a quest reward. Returns reward details."""
    from database import give_potion_reward, add_coins
    
    reward = quest.get("reward", {})
    reward_summary = {}
    
    # Give coins (random range)
    if "coins" in reward:
        coins_range = reward["coins"]
        if isinstance(coins_range, list) and len(coins_range) == 2:
            coins = random.randint(coins_range[0], coins_range[1])
        else:
            coins = coins_range
        add_coins(user_data, coins)
        reward_summary["coins"] = coins
    
    # Give potions
    if "potions" in reward:
        reward_summary["potions"] = {}
        for potion_id, amount in reward["potions"].items():
            give_potion_reward(user_data, potion_id, amount)
            reward_summary["potions"][potion_id] = amount
    
    return reward_summary

def claim_completion_reward(user_data: dict) -> Dict:
    """Claim the reward for completing all 4 quests. Returns reward details."""
    from database import give_potion_reward, add_coins, use_potion
    
    completion_data = DAILY_QUESTS_DATA["completion_reward"]
    reward = completion_data["reward"]
    reward_summary = {}
    
    # Give coins (random range)
    if "coins" in reward:
        coins_range = reward["coins"]
        coins = random.randint(coins_range[0], coins_range[1])
        add_coins(user_data, coins)
        reward_summary["coins"] = coins
    
    # Give potions
    if "potions" in reward:
        reward_summary["potions"] = {}
        for potion_id, amount in reward["potions"].items():
            give_potion_reward(user_data, potion_id, amount)
            reward_summary["potions"][potion_id] = amount
    
    # Apply Daily Blessing effect
    if "effect" in reward:
        effect_data = reward["effect"]
        
        # Create effect entry
        effect_entry = {
            "potion_id": "daily_blessing",
            "name": effect_data["name"],
            "icon": effect_data["icon"],
            "type": effect_data["type"],
            "amount": effect_data["amount"],
            "duration": effect_data["duration"],
            "start_time": time.time(),
            "expire_time": time.time() + effect_data["duration"]
        }
        
        if "active_effects" not in user_data:
            user_data["active_effects"] = []
        
        user_data["active_effects"].append(effect_entry)
        reward_summary["effect"] = effect_data
    
    return reward_summary

def update_daily_stat(user_data: dict, stat_name: str, increment: int = 1):
    """Update a daily stat."""
    if "daily_stats" not in user_data:
        user_data["daily_stats"] = {}
    
    current = user_data["daily_stats"].get(stat_name, 0)
    user_data["daily_stats"][stat_name] = current + increment

def update_playtime(user_data: dict):
    """Update playtime stats."""
    if "daily_stats" not in user_data:
        user_data["daily_stats"] = {}
    
    daily_stats = user_data["daily_stats"]
    
    # Calculate session time
    session_start = daily_stats.get("session_start", time.time())
    current_session = time.time() - session_start
    
    # Add to today's playtime
    daily_stats["playtime_today"] = daily_stats.get("playtime_today", 0) + current_session
    
    # Add to total playtime
    if "total_playtime" not in user_data:
        user_data["total_playtime"] = 0
    user_data["total_playtime"] += current_session
    
    # Reset session start
    daily_stats["session_start"] = time.time()

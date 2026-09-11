"""Achievement management system"""

import logging
from typing import Dict, List, Tuple
from config import ACHIEVEMENTS

def check_achievement(user_data: dict, achievement_id: str, achievement_data: dict) -> bool:
    """Check if an achievement requirement is met."""
    req = achievement_data["requirement"]
    req_type = req["type"]
    req_value = req["value"]
    
    if req_type == "total_rolls":
        return user_data.get("total_rolls", 0) >= req_value
    
    elif req_type == "playtime":
        return user_data.get("total_playtime", 0) >= req_value
    
    elif req_type == "rarest_light":
        highest = user_data.get("highest_light")
        if not highest:
            return False
        rarity = highest.get("numeric_rarity", highest.get("rarity", 0))
        if isinstance(rarity, str):
            return False
        return rarity >= req_value
    
    elif req_type == "level":
        return user_data.get("level", 1) >= req_value
    
    elif req_type == "coins":
        return user_data.get("coins", 0) >= req_value
    
    elif req_type == "gears_crafted":
        return user_data.get("stats", {}).get("gears_crafted", 0) >= req_value
    
    elif req_type == "unique_gears_crafted":
        return len(user_data.get("stats", {}).get("unique_gears_list", [])) >= req_value
    
    elif req_type == "potions_used":
        return user_data.get("stats", {}).get("potions_used", 0) >= req_value
    
    elif req_type == "potions_bought":
        return user_data.get("stats", {}).get("potions_bought", 0) >= req_value
    
    elif req_type == "inventory_full":
        inventory = user_data.get("inventory", {})
        total_items = sum(inventory.values())
        return total_items >= 120
    
    elif req_type == "unique_lights":
        inventory = user_data.get("inventory", {})
        return len([k for k, v in inventory.items() if v > 0]) >= req_value
    
    elif req_type == "achievement_progress":
        # Check if 100% achievements complete AND min rolls met
        min_rolls = req.get("min_rolls", 0)
        if user_data.get("total_rolls", 0) < min_rolls:
            return False
        
        progress = calculate_achievement_progress(user_data)
        return progress >= req_value
    
    return False

def calculate_achievement_progress(user_data: dict) -> float:
    """Calculate overall achievement completion percentage."""
    claimed = user_data.get("achievements_claimed", [])
    
    total_achievements = 0
    completed_achievements = 0
    
    for page_key, page_data in ACHIEVEMENTS.items():
        if page_key == "page_5":  # Skip the 100% achievement itself
            continue
        
        for ach_id, ach_data in page_data["achievements"].items():
            total_achievements += 1
            if ach_id in claimed:
                completed_achievements += 1
            elif check_achievement(user_data, ach_id, ach_data):
                completed_achievements += 1
    
    if total_achievements == 0:
        return 0.0
    
    return (completed_achievements / total_achievements) * 100

def get_claimable_achievements(user_data: dict) -> List[Tuple[str, str, dict]]:
    """Get list of achievements that can be claimed (page_id, achievement_id, achievement_data)."""
    claimed = user_data.get("achievements_claimed", [])
    claimable = []
    
    for page_key, page_data in ACHIEVEMENTS.items():
        for ach_id, ach_data in page_data["achievements"].items():
            if ach_id not in claimed and check_achievement(user_data, ach_id, ach_data):
                claimable.append((page_key, ach_id, ach_data))
    
    return claimable

def claim_achievement_reward(user_data: dict, achievement_data: dict) -> Dict:
    """Apply achievement reward to user_data. Returns reward details."""
    from database import give_potion_reward, add_coins
    
    reward = achievement_data.get("reward", {})
    reward_summary = {}
    
    # Give coins
    if "coins" in reward:
        coins = reward["coins"]
        add_coins(user_data, coins)
        reward_summary["coins"] = coins
    
    # Give potions
    if "potions" in reward:
        reward_summary["potions"] = {}
        for potion_id, amount in reward["potions"].items():
            give_potion_reward(user_data, potion_id, amount)
            reward_summary["potions"][potion_id] = amount
    
    return reward_summary

def format_achievement_requirement(achievement_data: dict, user_data: dict) -> str:
    """Format achievement requirement with current progress."""
    req = achievement_data["requirement"]
    req_type = req["type"]
    req_value = req["value"]
    
    if req_type == "total_rolls":
        current = user_data.get("total_rolls", 0)
        return f"{current:,} / {req_value:,} rolls"
    
    elif req_type == "playtime":
        current = user_data.get("total_playtime", 0)
        req_hours = req_value / 3600
        current_hours = current / 3600
        return f"{current_hours:.1f} / {req_hours:.0f} hours"
    
    elif req_type == "rarest_light":
        highest = user_data.get("highest_light")
        if highest:
            rarity = highest.get("numeric_rarity", highest.get("rarity", 0))
            if isinstance(rarity, int):
                return f"Best: 1 in {rarity:,} (need: 1 in {req_value:,})"
        return f"Need: 1 in {req_value:,}"
    
    elif req_type == "level":
        current = user_data.get("level", 1)
        return f"Level {current} / {req_value}"
    
    elif req_type == "coins":
        current = user_data.get("coins", 0)
        return f"{current:,} / {req_value:,} coins"
    
    elif req_type == "gears_crafted":
        current = user_data.get("stats", {}).get("gears_crafted", 0)
        return f"{current} / {req_value} gears crafted"
    
    elif req_type == "unique_gears_crafted":
        current = len(user_data.get("stats", {}).get("unique_gears_list", []))
        return f"{current} / {req_value} unique gears"
    
    elif req_type == "potions_used":
        current = user_data.get("stats", {}).get("potions_used", 0)
        return f"{current} / {req_value} potions used"
    
    elif req_type == "potions_bought":
        current = user_data.get("stats", {}).get("potions_bought", 0)
        return f"{current} / {req_value} potions bought"
    
    elif req_type == "inventory_full":
        inventory = user_data.get("inventory", {})
        total_items = sum(inventory.values())
        return f"{total_items} / 120 inventory slots"
    
    elif req_type == "unique_lights":
        inventory = user_data.get("inventory", {})
        current = len([k for k, v in inventory.items() if v > 0])
        return f"{current} / {req_value} unique lights"
    
    elif req_type == "achievement_progress":
        progress = calculate_achievement_progress(user_data)
        rolls = user_data.get("total_rolls", 0)
        min_rolls = req.get("min_rolls", 0)
        return f"{progress:.1f}% achievements | {rolls:,} / {min_rolls:,} rolls"
    
    return "Unknown requirement"

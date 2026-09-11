"""Game logic functions"""

import random
from config import LIGHTS, SPECIAL_LIGHTS, EXCLUSIVE_LIGHTS, GEARS
from database import update_inventory, update_gear_inventory, save_user_data

def roll_light(luck_multiplier: float, user_data: dict = None, world_state: dict = None) -> dict:
    """RNG calculation logic with special lights support and world system.
    
    Uses a balanced weighted system where even with high luck, common lights are still obtainable.
    High luck increases chance for rares but doesn't eliminate commons completely.
    """
    from utils.world_manager import (
        is_eclipse_active, 
        check_anomaly_from_none_event, 
        get_meteorite_boost,
        is_light_available,
        get_time_exclusive_boost,
        check_exclusive_light_drop,
        is_poseidon_fury_active
    )
    from database import has_exclusive_light_unlocked
    from config import EXCLUSIVE_LIGHTS
    
    # Check for special unlock potions
    has_null_potion = False
    eclipse_event_active = False
    poseidon_fury_active = False
    anomaly_from_none = False
    meteorite_boost = 1.0
    exclusive_light_drop = False
    
    if user_data:
        # Check if Null Potion effect is active (Anomaly unlock)
        for effect in user_data.get("active_effects", []):
            if effect.get("potion_id") == "null_potion" and effect.get("anomaly_unlock"):
                has_null_potion = True
                break
    
    if world_state:
        # Check if Eclipse event is active
        eclipse_event_active = is_eclipse_active(world_state)
        
        # Check if Poseidon Fury event is active
        poseidon_fury_active = is_poseidon_fury_active(world_state)
        
        # Check if Anomaly can be obtained from None event (5% chance)
        anomaly_from_none = check_anomaly_from_none_event(world_state)
        
        # Get meteorite boost if Meteor Fall event
        meteorite_boost = get_meteorite_boost(world_state)
        
        # Check if exclusive light can drop (Heaven Approach, Pro only, 15% chance)
        if user_data:
            exclusive_light_drop = check_exclusive_light_drop(world_state, user_data)
    
    # Handle special unlocks first
    if has_null_potion or anomaly_from_none:
        # Return Anomaly light
        anomaly_light = next((s for s in SPECIAL_LIGHTS if s["name"] == "Anomaly"), None)
        if anomaly_light:
            return anomaly_light
    
    # Handle exclusive light drop during Heaven Approach
    if exclusive_light_drop and user_data:
        # Get user's unlocked exclusive lights
        unlocked_lights = [light for light in EXCLUSIVE_LIGHTS 
                          if has_exclusive_light_unlocked(user_data, light["name"])]
        
        if unlocked_lights:
            # Randomly choose one of the unlocked exclusive lights (using random module from top import)
            return random.choice(unlocked_lights)
    
    # Combine regular and special lights for rolling
    all_lights = []
    
    for light in LIGHTS:
        # Check if light is available based on time period
        if world_state and not is_light_available(light["name"], world_state):
            continue
        
        # Apply time exclusive boost for Sunrise/Moonlight
        light_copy = light.copy()
        if world_state:
            time_boost = get_time_exclusive_boost(light["name"], world_state)
            if time_boost > 0:
                # Increase luck for exclusive lights
                light_copy["temp_luck_multiplier"] = 1.0 + time_boost
        
        # Apply Meteorite boost if Meteor Fall event
        if light["name"] == "Meteorite" and meteorite_boost > 1.0:
            light_copy["temp_luck_multiplier"] = meteorite_boost
        
        all_lights.append(light_copy)
    
    # Add special lights with their numeric rarity for rolling
    for special in SPECIAL_LIGHTS:
        # Skip event-only lights if conditions not met
        if special.get("event_only"):
            # Eclipse light only during Eclipse event
            if special["name"] == "Eclipse" and not eclipse_event_active:
                continue
            # Godhand only during Heaven Approach
            if special["name"] == "Godhand" and not (world_state and world_state["event"]["name"] == "Heaven Approach"):
                continue
            # Kraken and Whale only during Poseidon Fury
            if special["name"] in ["Kraken", "Whale"] and not poseidon_fury_active:
                continue
        if special.get("potion_only"):
            continue
        
        light_copy = special.copy()
        light_copy["rarity"] = special["numeric_rarity"]
        all_lights.append(light_copy)
    
    # Sort from rarest to most common
    sorted_lights = sorted(all_lights, key=lambda x: x["rarity"], reverse=True)
    
    # Roll through each light
    for light in sorted_lights:
        # Apply temp multiplier if exists
        temp_multiplier = light.get("temp_luck_multiplier", 1.0)
        effective_luck = luck_multiplier * temp_multiplier
        
        # Calculate effective rarity with luck
        # Min rarity of 2 ensures even with infinite luck, still possible to miss
        effective_rarity = max(2, int(light["rarity"] / effective_luck))
        
        # Roll for this light
        if random.randint(1, effective_rarity) == 1:
            # Return the original special light data if it's a special light
            if "numeric_rarity" in light:
                return next(s for s in SPECIAL_LIGHTS if s["name"] == light["name"])
            
            # Return original light without temp data
            original_light = next(l for l in LIGHTS if l["name"] == light["name"])
            return original_light
    
    # Fallback to common (this ensures every roll gets something)
    return LIGHTS[-1]

def calculate_total_luck(user_data: dict, world_state: dict = None) -> float:
    """Calculate total luck including gear bonuses, potion effects, and world bonuses."""
    from database import get_active_luck_bonus
    from utils.world_manager import calculate_world_luck_bonus
    
    base_luck = user_data["luck"]
    gear_luck = 0.0
    
    # Add luck from equipped gears
    left_hand = user_data["equipped_gear"].get("left_hand")
    right_hand = user_data["equipped_gear"].get("right_hand")
    
    if left_hand and left_hand in GEARS:
        gear_luck += GEARS[left_hand]["stats"].get("luck", 0.0)
    
    if right_hand and right_hand in GEARS:
        gear_luck += GEARS[right_hand]["stats"].get("luck", 0.0)
    
    # Add luck from active potion effects
    potion_luck = get_active_luck_bonus(user_data) / 100.0  # Convert percentage to multiplier
    
    # Add luck from world state (weather + event)
    world_luck = 0.0
    if world_state:
        world_luck = calculate_world_luck_bonus(world_state) / 100.0  # Convert percentage to multiplier
    
    return base_luck + gear_luck + potion_luck + world_luck

def can_craft_gear(user_data: dict, gear_name: str) -> tuple:
    """Check if player has enough materials to craft gear. Returns (bool, missing_items)."""
    if gear_name not in GEARS:
        return False, {}
    
    recipe = GEARS[gear_name]["recipe"]
    inventory = user_data["inventory"]
    missing = {}
    
    for light_name, required_amount in recipe.items():
        current_amount = inventory.get(light_name, 0)
        if current_amount < required_amount:
            missing[light_name] = required_amount - current_amount
    
    return len(missing) == 0, missing

def craft_gear(user_data: dict, gear_name: str) -> bool:
    """Craft a gear and deduct materials from inventory."""
    can_craft_it, missing = can_craft_gear(user_data, gear_name)
    
    if not can_craft_it:
        return False
    
    # Deduct materials from inventory
    recipe = GEARS[gear_name]["recipe"]
    for light_name, required_amount in recipe.items():
        # Use negative amount to deduct
        update_inventory(user_data, light_name, -required_amount)
    
    # Add gear to inventory
    update_gear_inventory(user_data, gear_name, 1)
    
    # Track crafting stats
    from database import track_gear_crafted
    track_gear_crafted(user_data, gear_name)
    
    return True

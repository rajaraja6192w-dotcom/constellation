"""Roll handling functions"""

import logging
from datetime import datetime
from config import MAX_INVENTORY_SLOTS
from database import add_exp, update_inventory, increment_total_rolls, update_highest_light
from utils.game_logic import roll_light, calculate_total_luck

def process_single_roll(user_data: dict) -> str:
    """Executes a single roll action and updates statistics.
    
    OPTIMIZATION NOTE: Reduced DB queries from 10+ to 3 strategic refreshes.
    Only refresh user_data when database operations modify it significantly.
    """
    from database import (
        clean_expired_effects, 
        consume_instant_effects, 
        track_rare_light, 
        update_activity,
        get_current_world_state,
        give_burnt_effect,
        give_potion_reward,
        check_auto_craft,
        get_max_inventory_slots,
        get_user_data
    )
    from utils.world_manager import check_null_potion_drop, check_burnt_effect
    
    # OPTIMIZATION: Initial refresh to get latest settings
    user_id = user_data["user_id"]
    user_data = get_user_data(user_id)
    logging.info(f"🔄 Roll started - user_id={user_id}, auto_discard={user_data.get('auto_discard_threshold', 0)}")
    
    # Update activity and clean effects (minor updates, no refresh needed)
    update_activity(user_data)
    clean_expired_effects(user_data)
    
    # Get current world state (cached, not a DB query)
    world_state = get_current_world_state()
    
    # Increment total rolls (minor stat update, no refresh needed)
    increment_total_rolls(user_data)
    
    # Use total luck (base + gear bonuses + potion effects + world bonuses)
    total_luck = calculate_total_luck(user_data, world_state)
    rolled_light = roll_light(total_luck, user_data, world_state)
    
    # Check for Null Potion drop (0.1% chance) - minor addition, no refresh needed
    null_potion_dropped = check_null_potion_drop()
    if null_potion_dropped:
        give_potion_reward(user_data, "null_potion", 1)
    
    # Check for Burnt effect (1% chance during Meteor Fall) - minor effect, no refresh needed
    burnt_effect_gained = check_burnt_effect(world_state)
    if burnt_effect_gained:
        give_burnt_effect(user_data)
    
    # Consume instant effects (like Angelic Potion, Null Potion) after roll
    consume_instant_effects(user_data)
    
    # Track rare light for daily quest (stat tracking, no refresh needed)
    rarity = rolled_light.get("numeric_rarity", rolled_light.get("rarity", 0))
    if isinstance(rarity, int):
        track_rare_light(user_data, rarity)
    
    # Give EXP and check for level up
    leveled_up, rewards_text = add_exp(user_data, amount=15)
    
    # OPTIMIZATION: Refresh after add_exp since it modifies level, coins, potions (significant changes)
    user_data = get_user_data(user_id)
    logging.info(f"🔄 After add_exp (leveled_up={leveled_up}) - refreshed for level/rewards changes")
    
    # Store to Inventory (with dynamic max slots)
    max_slots = get_max_inventory_slots(user_data)
    total_items = sum(user_data["inventory"].values())
    inventory_full = total_items >= max_slots
    
    # PRIORITY CHECK: Auto-Add has higher priority than Auto-Discard
    from database import should_auto_discard, get_auto_discard_threshold, is_light_needed_for_auto_add
    
    # Check if light is needed for any gear with auto-add enabled
    needed_for_auto_add = is_light_needed_for_auto_add(user_data, rolled_light["name"])
    
    # Check auto-discard (but override if needed for auto-add)
    auto_discarded = False
    if not needed_for_auto_add:  # Only discard if NOT needed for auto-add
        auto_discarded = should_auto_discard(rolled_light, user_data)
        if auto_discarded:
            logging.info(f"🗑️ Light {rolled_light['name']} will be auto-discarded (not needed for crafting)")
    else:
        logging.info(f"🔨 Light {rolled_light['name']} SAVED from auto-discard (needed for auto-add craft)")
    
    if not inventory_full and not auto_discarded:
        update_inventory(user_data, rolled_light["name"], 1)
        
        # Check auto-craft (if enabled and materials ready)
        # This will auto-add to reserve if auto_add is enabled for any gear
        crafted_gears = check_auto_craft(user_data, rolled_light["name"])
        
        # OPTIMIZATION: Refresh if gears were crafted (inventory changed significantly)
        if crafted_gears:
            user_data = get_user_data(user_id)
            logging.info(f"🔄 After auto-craft - crafted {len(crafted_gears)} gear(s), refreshed data")
    else:
        crafted_gears = []

    # Highest record update (minor stat, no refresh needed)
    update_highest_light(user_data, rolled_light)
    
    # OPTIMIZATION: Final refresh to ensure auto-roll gets latest state
    user_data = get_user_data(user_id)
    logging.info(f"🔄 Roll complete - final refresh for auto-roll continuity")

    # Current Timestamp
    current_time = datetime.now().strftime("%H:%M:%S")
    
    # Format rarity display
    rarity_display = rolled_light["rarity"]
    if isinstance(rarity_display, int):
        rarity_display = f"1 in {rarity_display:,}"
    else:
        rarity_display = f"1 in {rarity_display}"
    
    # Format message output
    level_up_str = ""
    if leveled_up:
        level_up_str = f"\n\n🎉 <b>LEVEL UP! Now Level {user_data['level']}</b>\n<b>Rewards:</b>\n{rewards_text}"
    
    full_notice = f"\n⚠️ <i>Inventory Full ({max_slots} slots)! Item discarded.</i>" if inventory_full else ""
    
    # Auto-discard notification
    discard_notice = ""
    if auto_discarded:
        from database import get_auto_discard_threshold
        threshold = get_auto_discard_threshold(user_data)
        discard_notice = f"\n🗑️ <i>Auto-discarded (rarity ≤ {threshold})</i>"
    elif needed_for_auto_add and should_auto_discard(rolled_light, user_data):
        # Light would have been discarded but was saved for crafting
        from database import get_auto_discard_threshold
        threshold = get_auto_discard_threshold(user_data)
        discard_notice = f"\n🔨 <i>Saved from auto-discard (needed for craft, threshold: {threshold})</i>"
    
    # Auto-craft notification
    craft_str = ""
    if crafted_gears:
        from config import GEARS
        craft_details = []
        for g in crafted_gears:
            gear_info = GEARS[g]
            craft_details.append(
                f"{gear_info['icon']} {g} (Tier {gear_info['tier']}, +{gear_info['stats']['luck']} luck)"
            )
        craft_str = (
            f"\n\n🎉 <b>AUTO-CRAFT SUCCESS!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            + "\n".join([f"✨ {detail}" for detail in craft_details]) +
            f"\n━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 <i>Gear ready to equip!</i>"
        )
    
    # Bonus drops and effects
    bonus_str = ""
    if null_potion_dropped:
        bonus_str += "\n\n🎁 <b>BONUS DROP!</b> You found a <b>Null Potion</b>! 👾"
    if burnt_effect_gained:
        bonus_str += "\n\n🔥 <b>BURNT EFFECT GAINED!</b> +60% luck (instant)!"
    
    return (
        "✨ <b>CONSTELLATION REVEAL</b> ✨\n"
        "-----------------------------------\n"
        "You obtained:\n\n"
        f"{rolled_light['icon']} <b>{rolled_light['name'].upper()}</b> {rolled_light['icon']}\n"
        f"• Rarity: <code>{rarity_display}</code>\n"
        f"{full_notice}{discard_notice}{level_up_str}{craft_str}{bonus_str}\n"
        "-----------------------------------\n"
        f"🕒 <b>Time:</b> {current_time} | 🎲 <b>Total Rolls:</b> {user_data['total_rolls']:,}"
    )

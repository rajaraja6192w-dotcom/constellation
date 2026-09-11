"""Main callback handler for buttons"""

import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from database import get_user_data, set_auto_roll, set_rolling_state, save_user_data
from config import LIGHTS, SPECIAL_LIGHTS, GEARS, MAX_INVENTORY_SLOTS, POTIONS
from utils.keyboards import (
    get_main_keyboard, get_settings_keyboard, 
    get_inventory_main_keyboard, get_craft_keyboard
)
from utils.roll_handler import process_single_roll
from utils.game_logic import calculate_total_luck, can_craft_gear, craft_gear

# Store active auto-roll tasks per user
active_auto_rolls = {}

async def auto_roll_task(user_id: int, query, context):
    """Separate async task for auto-rolling that can be cancelled."""
    try:
        logging.info(f"🚀 Auto-roll task STARTED for user {user_id}")
        
        while True:
            # Get fresh user data
            user_data = get_user_data(user_id)
            
            # Check if should stop
            if not user_data.get("is_rolling", False):
                logging.info(f"⏹️ Auto-roll STOPPING: is_rolling=False for user {user_id}")
                break
            
            if not user_data.get("auto_roll", False):
                logging.info(f"⏹️ Auto-roll STOPPING: auto_roll=False for user {user_id}")
                break
            
            # Process single roll
            text_result = process_single_roll(user_data)
            
            # Update message
            try:
                user_data = get_user_data(user_id)  # Refresh for keyboard
                await query.edit_message_text(
                    text_result,
                    parse_mode="HTML",
                    reply_markup=get_main_keyboard(user_data)
                )
            except BadRequest as e:
                logging.debug(f"BadRequest during message edit: {e}")
                pass
            
            # Fixed delay: 3 seconds for all rolls
            delay = 3
            
            # Sleep with frequent cancellation checks
            for i in range(int(delay * 10)):
                user_data = get_user_data(user_id)
                if not user_data.get("is_rolling", False):
                    logging.info(f"⏹️ Auto-roll CANCELLED during sleep (iteration {i}/{ int(delay * 10)}) for user {user_id}")
                    raise asyncio.CancelledError()
                
                await asyncio.sleep(0.1)
    
    except asyncio.CancelledError:
        logging.info(f"🛑 Auto-roll task CANCELLED for user {user_id}")
    except Exception as e:
        logging.error(f"❌ Error in auto-roll task for user {user_id}: {e}")
    finally:
        # Clean up
        logging.info(f"🧹 Auto-roll task CLEANUP for user {user_id}")
        user_data = get_user_data(user_id)
        set_rolling_state(user_data, False)
        
        # Remove from active tasks
        if user_id in active_auto_rolls:
            del active_auto_rolls[user_id]
            logging.info(f"✅ Removed user {user_id} from active_auto_rolls")
        
        # Show stopped message
        try:
            user_data = get_user_data(user_id)
            await query.edit_message_text(
                "🛑 <b>Auto-Roll Stopped.</b>",
                parse_mode="HTML",
                reply_markup=get_main_keyboard(user_data)
            )
        except BadRequest:
            pass

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    logging.info(f"🔘 Button callback triggered: {query.data}")
    
    try:
        await query.answer()
    except Exception as e:
        logging.error(f"Error answering query: {e}")
        return

    user_id = query.from_user.id
    user_data = get_user_data(user_id)
    
    # Update activity on ANY button press
    from database import update_activity
    update_activity(user_data)
    user_data = get_user_data(user_id)  # Refresh after update

    try:
        # ACTION: MAIN MENU
        if query.data == "action_main":
            # Check if user has joined a server
            from database import get_user_server
            current_server = get_user_server(user_data)
            
            if not current_server:
                # User hasn't joined a server yet
                text = (
                    "⚠️ <b>You need to join a server first!</b>\n\n"
                    "🌐 <b>Why join a server?</b>\n"
                    "• Compete with players on server leaderboards\n"
                    "• Track your playtime and progress\n"
                    "• Join friends on the same server\n"
                    "• Choose from 10 different servers\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "💡 Use <b>/play</b> or click the button below to select your server!"
                )
                
                keyboard = [
                    [InlineKeyboardButton("🎮 Select Server", callback_data="refresh_servers")]
                ]
                
                await query.edit_message_text(
                    text, 
                    parse_mode="HTML", 
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
            
            # Cancel any active auto-roll
            if user_id in active_auto_rolls:
                task = active_auto_rolls[user_id]
                if not task.done():
                    task.cancel()
                    logging.info(f"Cancelled auto-roll from main menu for user {user_id}")
            
            set_rolling_state(user_data, False)
            user_data = get_user_data(user_id)
            
            # Get world state and display
            from database import get_current_world_state
            from utils.world_manager import get_world_display
            from commands.server import SERVERS
            
            world_state = get_current_world_state()
            world_display = get_world_display(world_state)
            
            # Get server info
            server_info = next((s for s in SERVERS if s["id"] == current_server), None)
            server_name = server_info["name"] if server_info else current_server
            
            text = (
                f"🌌 <b>Constellation RNG - Main Menu</b>\n"
                f"📍 <b>Server:</b> {server_name}\n\n"
                f"{world_display}\n\n"
                f"<i>Ready to roll!</i>"
            )
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=get_main_keyboard(user_data))

        # ACTION: ROLL (Manual)
        elif query.data == "action_roll":
            # Check if user has joined a server
            from database import get_user_server
            current_server = get_user_server(user_data)
            
            if not current_server:
                await query.answer("⚠️ Join a server first! Use /play", show_alert=True)
                return
            
            text_result = process_single_roll(user_data)
            await query.edit_message_text(text_result, parse_mode="HTML", reply_markup=get_main_keyboard(user_data))

        # ACTION: START AUTO-ROLL
        elif query.data == "action_start_auto":
            # Check if user has joined a server
            from database import get_user_server
            current_server = get_user_server(user_data)
            
            if not current_server:
                await query.answer("⚠️ Join a server first! Use /play", show_alert=True)
                return
            
            # Check if already rolling
            if user_id in active_auto_rolls:
                task = active_auto_rolls[user_id]
                if not task.done():
                    logging.warning(f"⚠️ User {user_id} already has active auto-roll task")
                    await query.answer("⚠️ Auto-roll already running!", show_alert=True)
                    return
            
            # Get fresh user data
            user_data = get_user_data(user_id)
            
            # Set rolling state in DB
            set_rolling_state(user_data, True)
            logging.info(f"▶️ Starting NEW auto-roll task for user {user_id}")
            
            # Create and store the background task
            task = asyncio.create_task(auto_roll_task(user_id, query, context))
            active_auto_rolls[user_id] = task
            logging.info(f"✅ Task created and stored for user {user_id}. Active tasks: {len(active_auto_rolls)}")
            
            # Acknowledge
            await query.answer("▶️ Auto-roll started!", show_alert=False)

        # ACTION: STOP AUTO ROLL
        elif query.data == "action_stop_auto":
            logging.info(f"🛑 STOP BUTTON PRESSED by user {user_id}")
            
            # Set rolling to False in database FIRST
            user_data = get_user_data(user_id)
            set_rolling_state(user_data, False)
            logging.info(f"✅ Set is_rolling=False in DB for user {user_id}")
            
            # Cancel the task if it exists
            if user_id in active_auto_rolls:
                task = active_auto_rolls[user_id]
                if not task.done():
                    task.cancel()
                    logging.info(f"✅ Cancelled task for user {user_id}")
                    await query.answer("⏹️ Stopping...", show_alert=False)
                    # Wait a bit for task to cleanup
                    await asyncio.sleep(0.3)
                else:
                    logging.info(f"ℹ️ Task already done for user {user_id}")
                    await query.answer("✅ Already stopped", show_alert=False)
            else:
                logging.warning(f"⚠️ No active task found for user {user_id}. Active tasks: {list(active_auto_rolls.keys())}")
                await query.answer("⚠️ No active auto-roll found", show_alert=False)
                
                # Force update message anyway
                user_data = get_user_data(user_id)
                try:
                    await query.edit_message_text(
                        "🛑 <b>Auto-Roll Stopped.</b>",
                        parse_mode="HTML",
                        reply_markup=get_main_keyboard(user_data)
                    )
                except BadRequest:
                    pass

        # ACTION: INVENTORY MAIN
        elif query.data == "action_inventory":
            text = (
                "🎒 <b>INVENTORY MENU</b>\n"
                "-----------------------------------\n"
                "Choose what you want to view:\n\n"
                "✨ <b>Lights</b> - View your collected lights\n"
                "🎒 <b>Gears & Items</b> - View your crafted gears\n"
                "🧪 <b>Potions</b> - View your potion inventory\n"
                "⚔️ <b>Equipment</b> - View your equipped items"
            )
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=get_inventory_main_keyboard())

        # INVENTORY: LIGHTS
        elif query.data == "inv_lights":
            from database import get_max_inventory_slots, calculate_upgrade_cost
            
            inventory = user_data["inventory"]
            max_slots = get_max_inventory_slots(user_data)
            total_items = sum(inventory.values())
            current_upgrades = user_data.get("inventory_upgrades", 0)
            next_upgrade_cost = calculate_upgrade_cost(current_upgrades)
            coins = user_data.get("coins", 0)
            
            lines = [f"✨ <b>LIGHT INVENTORY</b> ({total_items}/{max_slots})\n"]
            
            if not inventory:
                lines.append("<i>Your light inventory is empty. Start rolling!</i>")
            else:
                all_lights_display = LIGHTS + SPECIAL_LIGHTS
                
                for light in all_lights_display:
                    name = light["name"]
                    if name in inventory and inventory[name] > 0:
                        count = inventory[name]
                        is_eq = " (Equipped)" if user_data["equipped_light"] and user_data["equipped_light"]["name"] == name else ""
                        
                        rarity = light["rarity"]
                        if isinstance(rarity, int):
                            rarity_str = f"1 in {rarity:,}"
                        else:
                            rarity_str = f"1 in {rarity}"
                        
                        lines.append(f"{light['icon']} <b>{name}</b> x{count} ({rarity_str}){is_eq}")

            lines.append(f"\n<b>💰 Coins:</b> {coins:,}")
            lines.append(f"<b>📦 Upgrades:</b> {current_upgrades}")
            lines.append(f"<b>💎 Next Upgrade:</b> +10 slots for {next_upgrade_cost:,} coins")
            lines.append("\n<i>Use /equip_light &lt;light_name&gt; to equip a light.</i>")
            
            keyboard = [
                [InlineKeyboardButton("⬆️ Upgrade Inventory (+10 slots)", callback_data="upgrade_inventory")],
                [InlineKeyboardButton("⬅️ Back to Inventory", callback_data="action_inventory")]
            ]
            await query.edit_message_text("\n".join(lines), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        
        # UPGRADE INVENTORY
        elif query.data == "upgrade_inventory":
            from database import upgrade_inventory_slots, get_max_inventory_slots, calculate_upgrade_cost
            
            success, message = upgrade_inventory_slots(user_data)
            
            if success:
                await query.answer(f"✅ {message}", show_alert=True)
            else:
                await query.answer(f"❌ {message}", show_alert=True)
            
            # Refresh user data and rebuild lights inventory page
            user_data = get_user_data(user_id)
            
            inventory = user_data["inventory"]
            max_slots = get_max_inventory_slots(user_data)
            total_items = sum(inventory.values())
            current_upgrades = user_data.get("inventory_upgrades", 0)
            next_upgrade_cost = calculate_upgrade_cost(current_upgrades)
            coins = user_data.get("coins", 0)
            
            lines = [f"✨ <b>LIGHT INVENTORY</b> ({total_items}/{max_slots})\n"]
            
            if not inventory:
                lines.append("<i>Your light inventory is empty. Start rolling!</i>")
            else:
                all_lights_display = LIGHTS + SPECIAL_LIGHTS
                
                for light in all_lights_display:
                    name = light["name"]
                    if name in inventory and inventory[name] > 0:
                        count = inventory[name]
                        is_eq = " (Equipped)" if user_data["equipped_light"] and user_data["equipped_light"]["name"] == name else ""
                        
                        rarity = light["rarity"]
                        if isinstance(rarity, int):
                            rarity_str = f"1 in {rarity:,}"
                        else:
                            rarity_str = f"1 in {rarity}"
                        
                        lines.append(f"{light['icon']} <b>{name}</b> x{count} ({rarity_str}){is_eq}")

            lines.append(f"\n<b>💰 Coins:</b> {coins:,}")
            lines.append(f"<b>📦 Upgrades:</b> {current_upgrades}")
            lines.append(f"<b>💎 Next Upgrade:</b> +10 slots for {next_upgrade_cost:,} coins")
            lines.append("\n<i>Use /equip_light &lt;light_name&gt; to equip a light.</i>")
            
            keyboard = [
                [InlineKeyboardButton("⬆️ Upgrade Inventory (+10 slots)", callback_data="upgrade_inventory")],
                [InlineKeyboardButton("⬅️ Back to Inventory", callback_data="action_inventory")]
            ]
            await query.edit_message_text("\n".join(lines), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

        # INVENTORY: GEARS
        elif query.data == "inv_gears":
            from config import GEARS as GEARS_DATA
            
            gear_inv = user_data["gear_inventory"]
            
            lines = [f"🎒 <b>GEAR INVENTORY</b>\n"]
            if not gear_inv:
                lines.append("<i>You have no gears. Use /craft to craft gears!</i>")
            else:
                for gear_name, count in gear_inv.items():
                    if count > 0 and gear_name in GEARS_DATA:
                        gear = GEARS_DATA[gear_name]
                        lines.append(f"{gear['icon']} <b>{gear_name}</b> x{count} (Tier {gear['tier']})")
                        lines.append(f"   └ Luck: +{gear['stats']['luck']}")

            lines.append("\n<i>Use /equip_gear &lt;gear&gt; &lt;left|right&gt; to equip.</i>")
            keyboard = [[InlineKeyboardButton("⬅️ Back to Inventory", callback_data="action_inventory")]]
            await query.edit_message_text("\n".join(lines), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

        # INVENTORY: POTIONS
        elif query.data == "inv_potions":
            potion_inv = user_data.get("potion_inventory", {})
            
            lines = ["🧪 <b>POTION INVENTORY</b>\n"]
            if not potion_inv or all(count == 0 for count in potion_inv.values()):
                lines.append("<i>You have no potions. Level up to earn potions or buy from shop!</i>")
            else:
                for potion_id, count in potion_inv.items():
                    if count > 0 and potion_id in POTIONS:
                        potion = POTIONS[potion_id]
                        lines.append(f"{potion['icon']} <b>{potion['name']}</b> x{count}")
                        lines.append(f"   └ {potion['description']}")
                        lines.append(f"   └ ID: <code>{potion_id}</code>")
                        lines.append("")

            lines.append("<i>Use /use &lt;potion_id&gt; to activate a potion.</i>")
            keyboard = [[InlineKeyboardButton("⬅️ Back to Inventory", callback_data="action_inventory")]]
            await query.edit_message_text("\n".join(lines), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

        # INVENTORY: EQUIPMENT
        elif query.data == "inv_equipment":
            from utils.game_logic import calculate_total_luck
            from database import get_current_world_state
            from config import GEARS as GEARS_DATA
            
            left_hand = user_data["equipped_gear"].get("left_hand")
            right_hand = user_data["equipped_gear"].get("right_hand")
            equipped_light = user_data["equipped_light"]
            
            # Get world state for accurate luck calculation
            world_state = get_current_world_state()
            total_luck = calculate_total_luck(user_data, world_state)
            
            lines = ["⚔️ <b>EQUIPMENT STATUS</b>\n"]
            
            if equipped_light:
                lines.append(f"✨ <b>Equipped Light:</b> {equipped_light['icon']} {equipped_light['name']}")
            else:
                lines.append("✨ <b>Equipped Light:</b> None")
            
            lines.append("")
            
            if left_hand and left_hand in GEARS_DATA:
                gear = GEARS_DATA[left_hand]
                lines.append(f"👈 <b>Left Hand:</b> {gear['icon']} {left_hand}")
                lines.append(f"   └ Luck: +{gear['stats']['luck']}")
            else:
                lines.append("👈 <b>Left Hand:</b> Empty")
            
            lines.append("")
            
            if right_hand and right_hand in GEARS_DATA:
                gear = GEARS_DATA[right_hand]
                lines.append(f"👉 <b>Right Hand:</b> {gear['icon']} {right_hand}")
                lines.append(f"   └ Luck: +{gear['stats']['luck']}")
            else:
                lines.append("👉 <b>Right Hand:</b> Empty")
            
            lines.append("\n" + "="*35)
            lines.append(f"🍀 <b>Total Luck Multiplier:</b> {total_luck:.1f}x")
            
            keyboard = [[InlineKeyboardButton("⬅️ Back to Inventory", callback_data="action_inventory")]]
            await query.edit_message_text("\n".join(lines), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

        # ACTION: STATS
        elif query.data == "action_stats":
            import time
            from database import clean_expired_effects, get_active_luck_bonus, update_activity, get_playtime_display, get_current_world_state
            from utils.world_manager import calculate_world_luck_bonus
            
            # Update activity first
            update_activity(user_data)
            
            user_data = get_user_data(user_id)
            clean_expired_effects(user_data)
            user_data = get_user_data(user_id)
            
            # Get world state for luck bonus
            world_state = get_current_world_state()
            world_luck_bonus = calculate_world_luck_bonus(world_state)
            
            highest = user_data["highest_light"]
            equipped = user_data["equipped_light"]
            
            # Calculate luck breakdown
            from utils.game_logic import calculate_total_luck
            from config import GEARS
            
            base_luck = user_data['luck']
            
            # Calculate gear luck
            gear_luck = 0.0
            left_hand = user_data["equipped_gear"].get("left_hand")
            right_hand = user_data["equipped_gear"].get("right_hand")
            if left_hand and left_hand in GEARS:
                gear_luck += GEARS[left_hand]["stats"].get("luck", 0.0)
            if right_hand and right_hand in GEARS:
                gear_luck += GEARS[right_hand]["stats"].get("luck", 0.0)
            
            # Calculate potion luck (as percentage)
            potion_luck_pct = get_active_luck_bonus(user_data)
            
            # Calculate total luck with world bonuses
            total_luck = calculate_total_luck(user_data, world_state)
            
            if highest:
                highest_rarity = highest["rarity"]
                if isinstance(highest_rarity, int):
                    highest_rarity_str = f"1 in {highest_rarity:,}"
                else:
                    highest_rarity_str = f"1 in {highest_rarity}"
                highest_str = f"{highest['icon']} {highest['name']} ({highest_rarity_str})"
            else:
                highest_str = "None"
            
            equipped_str = f"{equipped['icon']} {equipped['name']}" if equipped else "None"
            exp_needed = user_data["level"] * 100
            coins = user_data.get("coins", 0)
            
            # Get playtime display
            playtime_display = get_playtime_display(user_data)
            
            active_effects = user_data.get("active_effects", [])
            
            text_stats = (
                "📊 <b>PLAYER STATS</b>\n"
                "===================================\n"
                f"• <b>Level:</b> {user_data['level']}\n"
                f"• <b>EXP:</b> {user_data['exp']}/{exp_needed}\n"
                f"• <b>Coins:</b> 💰 {coins:,}\n"
                f"• <b>Playtime:</b> ⏱️ {playtime_display}\n"
                f"• <b>Total Rolls:</b> {user_data['total_rolls']:,}\n"
                "===================================\n\n"
                "<b>🎯 EQUIPMENT</b>\n"
                f"• <b>Equipped Light:</b> {equipped_str}\n"
                f"• <b>Highest Light:</b> {highest_str}\n"
                "===================================\n\n"
                "<b>🍀 LUCK BREAKDOWN</b>\n"
                f"• <b>Base Luck:</b> {base_luck:.1f}x\n"
                f"• <b>Gear Bonus:</b> +{gear_luck:.1f}x\n"
                f"• <b>Potion Bonus:</b> +{potion_luck_pct}%\n"
                f"• <b>World Bonus:</b> +{world_luck_bonus}%\n"
                f"• <b>TOTAL LUCK:</b> <b>{total_luck:.1f}x</b>\n"
                "===================================\n\n"
            )
            
            if active_effects:
                text_stats += "<b>🧪 ACTIVE EFFECTS</b>\n"
                current_time = time.time()
                for effect in active_effects:
                    effect_amount = effect.get('amount', 0)
                    # Convert decimal to percentage if needed
                    if effect_amount < 1.0:
                        effect_amount *= 100
                    
                    if effect['duration'] == 0:
                        text_stats += f"  {effect['icon']} <b>{effect['name']}</b>\n"
                        text_stats += f"     └ +{effect_amount:.0f}% luck (next roll)\n"
                    else:
                        remaining = effect['expire_time'] - current_time
                        if remaining > 0:
                            minutes = int(remaining // 60)
                            seconds = int(remaining % 60)
                            text_stats += f"  {effect['icon']} <b>{effect['name']}</b>\n"
                            text_stats += f"     └ +{effect_amount:.0f}% luck ({minutes}m {seconds}s)\n"
                text_stats += "===================================\n\n"
            else:
                text_stats += "<b>🧪 ACTIVE EFFECTS</b>\n"
                text_stats += "<i>No active potion effects</i>\n"
                text_stats += "===================================\n\n"
            
            # Add premium status
            from database import get_premium_status
            premium_info = get_premium_status(user_data)
            
            text_stats += "<b>💎 PREMIUM STATUS</b>\n"
            if premium_info and premium_info.get("active"):
                tier = premium_info.get("tier", "").upper()
                days_left = premium_info.get("days_left", 0)
                icon = "🌟" if tier == "basic" else "⭐"
                
                text_stats += f"{icon} <b>Status:</b> ACTIVE ({tier})\n"
                text_stats += f"⏳ <b>Days Remaining:</b> {days_left} days\n"
                
                # Show premium benefits
                if tier == "basic":
                    text_stats += "✨ <b>Benefits:</b> Auto-roll, 100k coins/mo, 150 potions/mo, +250% luck\n"
                else:  # pro
                    text_stats += "✨ <b>Benefits:</b> Auto-roll, 200k coins/mo, 300 potions/mo, +500% luck, Exclusive Lights!\n"
            else:
                text_stats += "⚪ <b>Status:</b> FREE\n"
                text_stats += "💡 <i>Upgrade to premium for amazing benefits!</i>\n"
                text_stats += "   Use /premium to see plans\n"
            text_stats += "===================================\n\n"
            
            text_stats += "💡 <i>Playtime runs continuously once you join a server\n"
            text_stats += "   (no idle timeout, always counting!)</i>\n\n"
            text_stats += "📌 <i>Use /use to activate potions\n"
            text_stats += "   Use /buy to purchase potions</i>"
            
            await query.edit_message_text(text_stats, parse_mode="HTML", reply_markup=get_main_keyboard(user_data))

        # ACTION: CRAFT MENU
        elif query.data == "action_craft":
            text = (
                "🔨 <b>CRAFTING MENU</b>\n"
                "-----------------------------------\n"
                "Select a gear to view recipe and craft:\n\n"
                "Each gear provides luck bonuses when equipped!"
            )
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=get_craft_keyboard())

        # CRAFT SPECIFIC GEAR - WITH AUTO-ADD & RESERVE SYSTEM
        elif query.data.startswith("craft_"):
            from config import GEARS
            from database import get_auto_craft_settings, get_craft_reserve, can_craft_with_reserve
            
            gear_name = query.data.replace("craft_", "").replace("_", " ")
            
            if gear_name not in GEARS:
                await query.answer("❌ Gear not found!", show_alert=True)
                return
            
            gear = GEARS[gear_name]
            recipe = gear["recipe"]
            can_craft_it, missing = can_craft_gear(user_data, gear_name)
            
            # Get auto-craft settings and reserves
            settings = get_auto_craft_settings(user_data, gear_name)
            reserve = get_craft_reserve(user_data, gear_name)
            can_craft_reserve, missing_reserve = can_craft_with_reserve(user_data, gear_name)
            
            # Show recipe with inventory and reserve
            recipe_lines = []
            for light_name, amount in recipe.items():
                current_inv = user_data["inventory"].get(light_name, 0)
                current_reserve = reserve.get(light_name, 0)
                light_icon = next((a["icon"] for a in LIGHTS if a["name"] == light_name), "")
                status = "✅" if current_reserve >= amount else "❌"
                recipe_lines.append(
                    f"{status} {light_icon} {light_name}: Inv:{current_inv} | Reserve:{current_reserve}/{amount}"
                )
            
            auto_add_status = "🟢 ON" if settings.get("auto_add", False) else "⚪ OFF"
            auto_craft_status = "🟢 ON" if settings.get("auto_craft", False) else "⚪ OFF"
            
            text = (
                f"🔨 <b>CRAFT: {gear['icon']} {gear_name}</b>\n"
                f"Tier: {gear['tier']} | Luck Bonus: +{gear['stats']['luck']}\n"
                "===================================\n"
                "<b>📋 Recipe:</b>\n" + "\n".join(recipe_lines) + "\n"
                "===================================\n"
                f"<b>⚙️ Auto Settings:</b>\n"
                f"• Auto-Add: {auto_add_status} (Priority over discard)\n"
                f"• Auto-Craft: {auto_craft_status}\n\n"
            )
            
            keyboard = []
            
            # Toggle buttons
            auto_add_text = "🟢 Auto-Add: ON" if settings.get("auto_add", False) else "⚪ Auto-Add: OFF"
            keyboard.append([InlineKeyboardButton(auto_add_text, callback_data=f"toggle_add_{gear_name.replace(' ', '_')}")])
            
            auto_craft_text = "🟢 Auto-Craft: ON" if settings.get("auto_craft", False) else "⚪ Auto-Craft: OFF"
            keyboard.append([InlineKeyboardButton(auto_craft_text, callback_data=f"toggle_craft_{gear_name.replace(' ', '_')}")])
            
            # Manual add buttons for each light that needs more in reserve
            for light_name, amount in recipe.items():
                current_inv = user_data["inventory"].get(light_name, 0)
                current_reserve = reserve.get(light_name, 0)
                
                if current_reserve < amount and current_inv > 0:
                    can_add = min(amount - current_reserve, current_inv)
                    light_icon = next((a["icon"] for a in LIGHTS if a["name"] == light_name), "")
                    keyboard.append([InlineKeyboardButton(
                        f"➕ Add {light_icon} {light_name} ({can_add}x)",
                        callback_data=f"add_light_{gear_name.replace(' ', '_')}_{light_name.replace(' ', '_')}"
                    )])
            
            # Craft button
            if can_craft_reserve:
                keyboard.append([InlineKeyboardButton("🔨 Craft", callback_data=f"do_craft_{gear_name.replace(' ', '_')}")])
                text += "✅ <b>Reserve ready! You can craft!</b>"
            elif can_craft_it:
                text += "⚠️ <b>Materials in inventory ready, but not in reserve.</b>\n<i>Use Auto-Add or manually add to reserve.</i>"
            else:
                text += "❌ <b>Insufficient materials!</b>\n<i>Keep rolling to get more lights.</i>"
            
            keyboard.append([InlineKeyboardButton("🔙 Back to Craft Menu", callback_data="action_craft")])
            keyboard.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="action_main")])
            
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        
        # DO CRAFT - CRAFT WITH RESERVE
        elif query.data.startswith("do_craft_"):
            from config import GEARS
            from database import craft_with_reserve, can_craft_with_reserve, get_craft_reserve, get_auto_craft_settings
            
            gear_name = query.data.replace("do_craft_", "").replace("_", " ")
            
            if gear_name not in GEARS:
                await query.answer("❌ Gear not found!", show_alert=True)
                return
            
            gear = GEARS[gear_name]
            can_craft_it, missing = can_craft_with_reserve(user_data, gear_name)
            
            if not can_craft_it:
                await query.answer("❌ Reserve not ready! Add more lights to reserve.", show_alert=True)
                return
            
            # Craft the gear using reserve
            success = craft_with_reserve(user_data, gear_name)
            
            if success:
                # Create detailed craft success message
                craft_msg = (
                    f"🎉 CRAFT BERHASIL! 🎉\n\n"
                    f"{gear['icon']} {gear_name}\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"⭐ Tier: {gear['tier']}\n"
                    f"🍀 Luck Bonus: +{gear['stats']['luck']}\n\n"
                    f"✅ Gear sudah masuk inventory!\n"
                    f"Equip di menu Inventory untuk bonus luck."
                )
                await query.answer(craft_msg, show_alert=True)
                # Refresh user data
                user_data = get_user_data(user_id)
            else:
                await query.answer("❌ Crafting failed!", show_alert=True)
                return
            
            # Show updated craft page with new reserve status
            recipe = gear["recipe"]
            settings = get_auto_craft_settings(user_data, gear_name)
            reserve = get_craft_reserve(user_data, gear_name)
            can_craft_reserve, missing_reserve = can_craft_with_reserve(user_data, gear_name)
            
            recipe_lines = []
            for light_name, amount in recipe.items():
                current_inv = user_data["inventory"].get(light_name, 0)
                current_reserve = reserve.get(light_name, 0)
                light_icon = next((a["icon"] for a in LIGHTS if a["name"] == light_name), "")
                status = "✅" if current_reserve >= amount else "❌"
                recipe_lines.append(
                    f"{status} {light_icon} {light_name}: Inv:{current_inv} | Reserve:{current_reserve}/{amount}"
                )
            
            auto_add_status = "🟢 ON" if settings.get("auto_add", False) else "⚪ OFF"
            auto_craft_status = "🟢 ON" if settings.get("auto_craft", False) else "⚪ OFF"
            
            # Show success message on craft page
            text = (
                f"✨ <b>CRAFTING SUCCESS!</b> ✨\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎉 You crafted: {gear['icon']} <b>{gear_name}</b>\n"
                f"⭐ Tier {gear['tier']} | 🍀 Luck +{gear['stats']['luck']}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"<b>📋 Recipe:</b>\n" + "\n".join(recipe_lines) + "\n"
                "===================================\n"
                f"<b>⚙️ Auto Settings:</b>\n"
                f"• Auto-Add: {auto_add_status} (Priority over discard)\n"
                f"• Auto-Craft: {auto_craft_status}\n\n"
                f"💡 <i>Reserve cleared! Ready for next craft.</i>\n"
            )
            
            keyboard = []
            
            # Toggle buttons
            auto_add_text = "🟢 Auto-Add: ON" if settings.get("auto_add", False) else "⚪ Auto-Add: OFF"
            keyboard.append([InlineKeyboardButton(auto_add_text, callback_data=f"toggle_add_{gear_name.replace(' ', '_')}")])
            
            auto_craft_text = "🟢 Auto-Craft: ON" if settings.get("auto_craft", False) else "⚪ Auto-Craft: OFF"
            keyboard.append([InlineKeyboardButton(auto_craft_text, callback_data=f"toggle_craft_{gear_name.replace(' ', '_')}")])
            
            # Manual add buttons for each light that needs more in reserve
            for light_name, amount in recipe.items():
                current_inv = user_data["inventory"].get(light_name, 0)
                current_reserve = reserve.get(light_name, 0)
                
                if current_reserve < amount and current_inv > 0:
                    can_add = min(amount - current_reserve, current_inv)
                    light_icon = next((a["icon"] for a in LIGHTS if a["name"] == light_name), "")
                    keyboard.append([InlineKeyboardButton(
                        f"➕ Add {light_icon} {light_name} ({can_add}x)",
                        callback_data=f"add_light_{gear_name.replace(' ', '_')}_{light_name.replace(' ', '_')}"
                    )])
            
            # Craft button
            if can_craft_reserve:
                keyboard.append([InlineKeyboardButton("🔨 Craft", callback_data=f"do_craft_{gear_name.replace(' ', '_')}")])
                text += "✅ <b>Reserve ready! You can craft!</b>"
            else:
                text += "❌ <b>Reserve not ready yet!</b>\n<i>Add more lights to reserve.</i>"
            
            keyboard.append([InlineKeyboardButton("🔙 Back to Craft Menu", callback_data="action_craft")])
            keyboard.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="action_main")])
            
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

        # TOGGLE AUTO-ADD
        elif query.data.startswith("toggle_add_"):
            from config import GEARS
            from database import set_auto_craft, get_auto_craft_settings, get_craft_reserve, can_craft_with_reserve
            
            gear_name = query.data.replace("toggle_add_", "").replace("_", " ")
            
            if gear_name not in GEARS:
                await query.answer("❌ Gear not found!", show_alert=True)
                return
            
            # Get current settings
            settings = get_auto_craft_settings(user_data, gear_name)
            new_auto_add = not settings.get("auto_add", False)
            
            # Update settings
            set_auto_craft(user_data, gear_name, new_auto_add, settings.get("auto_craft", False))
            
            # Refresh and show updated page
            user_data = get_user_data(user_id)
            gear = GEARS[gear_name]
            recipe = gear["recipe"]
            settings = get_auto_craft_settings(user_data, gear_name)
            reserve = get_craft_reserve(user_data, gear_name)
            can_craft_reserve, missing_reserve = can_craft_with_reserve(user_data, gear_name)
            
            recipe_lines = []
            for light_name, amount in recipe.items():
                current_inv = user_data["inventory"].get(light_name, 0)
                current_reserve = reserve.get(light_name, 0)
                light_icon = next((a["icon"] for a in LIGHTS if a["name"] == light_name), "")
                status = "✅" if current_reserve >= amount else "❌"
                recipe_lines.append(
                    f"{status} {light_icon} {light_name}: Inv:{current_inv} | Reserve:{current_reserve}/{amount}"
                )
            
            auto_add_status = "🟢 ON" if settings.get("auto_add", False) else "⚪ OFF"
            auto_craft_status = "🟢 ON" if settings.get("auto_craft", False) else "⚪ OFF"
            
            text = (
                f"🔨 <b>CRAFT: {gear['icon']} {gear_name}</b>\n"
                f"Tier: {gear['tier']} | Luck Bonus: +{gear['stats']['luck']}\n"
                "===================================\n"
                "<b>📋 Recipe:</b>\n" + "\n".join(recipe_lines) + "\n"
                "===================================\n"
                f"<b>⚙️ Auto Settings:</b>\n"
                f"• Auto-Add: {auto_add_status} (Priority over discard)\n"
                f"• Auto-Craft: {auto_craft_status}\n\n"
            )
            
            keyboard = []
            
            # Toggle buttons
            auto_add_text = "🟢 Auto-Add: ON" if settings.get("auto_add", False) else "⚪ Auto-Add: OFF"
            keyboard.append([InlineKeyboardButton(auto_add_text, callback_data=f"toggle_add_{gear_name.replace(' ', '_')}")])
            
            auto_craft_text = "🟢 Auto-Craft: ON" if settings.get("auto_craft", False) else "⚪ Auto-Craft: OFF"
            keyboard.append([InlineKeyboardButton(auto_craft_text, callback_data=f"toggle_craft_{gear_name.replace(' ', '_')}")])
            
            # Manual add buttons for each light that needs more in reserve
            for light_name, amount in recipe.items():
                current_inv = user_data["inventory"].get(light_name, 0)
                current_reserve = reserve.get(light_name, 0)
                
                if current_reserve < amount and current_inv > 0:
                    can_add = min(amount - current_reserve, current_inv)
                    light_icon = next((a["icon"] for a in LIGHTS if a["name"] == light_name), "")
                    keyboard.append([InlineKeyboardButton(
                        f"➕ Add {light_icon} {light_name} ({can_add}x)",
                        callback_data=f"add_light_{gear_name.replace(' ', '_')}_{light_name.replace(' ', '_')}"
                    )])
            
            # Craft button
            if can_craft_reserve:
                keyboard.append([InlineKeyboardButton("🔨 Craft", callback_data=f"do_craft_{gear_name.replace(' ', '_')}")])
                text += "✅ <b>Reserve ready! You can craft!</b>"
            else:
                text += "❌ <b>Reserve not ready yet!</b>\n<i>Add more lights to reserve.</i>"
            
            keyboard.append([InlineKeyboardButton("🔙 Back to Craft Menu", callback_data="action_craft")])
            keyboard.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="action_main")])
            
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
            await query.answer(f"Auto-Add: {'ON ✅' if new_auto_add else 'OFF ⚪'}", show_alert=False)

        # TOGGLE AUTO-CRAFT
        elif query.data.startswith("toggle_craft_"):
            from config import GEARS
            from database import set_auto_craft, get_auto_craft_settings, get_craft_reserve, can_craft_with_reserve
            
            gear_name = query.data.replace("toggle_craft_", "").replace("_", " ")
            
            if gear_name not in GEARS:
                await query.answer("❌ Gear not found!", show_alert=True)
                return
            
            # Get current settings
            settings = get_auto_craft_settings(user_data, gear_name)
            new_auto_craft = not settings.get("auto_craft", False)
            
            # Update settings
            set_auto_craft(user_data, gear_name, settings.get("auto_add", False), new_auto_craft)
            
            # Refresh and show updated page
            user_data = get_user_data(user_id)
            gear = GEARS[gear_name]
            recipe = gear["recipe"]
            settings = get_auto_craft_settings(user_data, gear_name)
            reserve = get_craft_reserve(user_data, gear_name)
            can_craft_reserve, missing_reserve = can_craft_with_reserve(user_data, gear_name)
            
            recipe_lines = []
            for light_name, amount in recipe.items():
                current_inv = user_data["inventory"].get(light_name, 0)
                current_reserve = reserve.get(light_name, 0)
                light_icon = next((a["icon"] for a in LIGHTS if a["name"] == light_name), "")
                status = "✅" if current_reserve >= amount else "❌"
                recipe_lines.append(
                    f"{status} {light_icon} {light_name}: Inv:{current_inv} | Reserve:{current_reserve}/{amount}"
                )
            
            auto_add_status = "🟢 ON" if settings.get("auto_add", False) else "⚪ OFF"
            auto_craft_status = "🟢 ON" if settings.get("auto_craft", False) else "⚪ OFF"
            
            text = (
                f"🔨 <b>CRAFT: {gear['icon']} {gear_name}</b>\n"
                f"Tier: {gear['tier']} | Luck Bonus: +{gear['stats']['luck']}\n"
                "===================================\n"
                "<b>📋 Recipe:</b>\n" + "\n".join(recipe_lines) + "\n"
                "===================================\n"
                f"<b>⚙️ Auto Settings:</b>\n"
                f"• Auto-Add: {auto_add_status} (Priority over discard)\n"
                f"• Auto-Craft: {auto_craft_status}\n\n"
            )
            
            keyboard = []
            
            # Toggle buttons
            auto_add_text = "🟢 Auto-Add: ON" if settings.get("auto_add", False) else "⚪ Auto-Add: OFF"
            keyboard.append([InlineKeyboardButton(auto_add_text, callback_data=f"toggle_add_{gear_name.replace(' ', '_')}")])
            
            auto_craft_text = "🟢 Auto-Craft: ON" if settings.get("auto_craft", False) else "⚪ Auto-Craft: OFF"
            keyboard.append([InlineKeyboardButton(auto_craft_text, callback_data=f"toggle_craft_{gear_name.replace(' ', '_')}")])
            
            # Manual add buttons for each light that needs more in reserve
            for light_name, amount in recipe.items():
                current_inv = user_data["inventory"].get(light_name, 0)
                current_reserve = reserve.get(light_name, 0)
                
                if current_reserve < amount and current_inv > 0:
                    can_add = min(amount - current_reserve, current_inv)
                    light_icon = next((a["icon"] for a in LIGHTS if a["name"] == light_name), "")
                    keyboard.append([InlineKeyboardButton(
                        f"➕ Add {light_icon} {light_name} ({can_add}x)",
                        callback_data=f"add_light_{gear_name.replace(' ', '_')}_{light_name.replace(' ', '_')}"
                    )])
            
            # Craft button
            if can_craft_reserve:
                keyboard.append([InlineKeyboardButton("🔨 Craft", callback_data=f"do_craft_{gear_name.replace(' ', '_')}")])
                text += "✅ <b>Reserve ready! You can craft!</b>"
            else:
                text += "❌ <b>Reserve not ready yet!</b>\n<i>Add more lights to reserve.</i>"
            
            keyboard.append([InlineKeyboardButton("🔙 Back to Craft Menu", callback_data="action_craft")])
            keyboard.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="action_main")])
            
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
            await query.answer(f"Auto-Craft: {'ON ✅' if new_auto_craft else 'OFF ⚪'}", show_alert=False)

        # MANUAL ADD LIGHT TO RESERVE
        elif query.data.startswith("add_light_"):
            from config import GEARS
            from database import add_light_to_reserve, get_auto_craft_settings, get_craft_reserve, can_craft_with_reserve
            
            # Parse: add_light_GearName_LightName
            parts = query.data.replace("add_light_", "").split("_")
            
            # Find where gear name ends and light name starts by checking against GEARS
            gear_name = None
            light_name = None
            
            for i in range(1, len(parts)):
                potential_gear = " ".join(parts[:i])
                if potential_gear in GEARS:
                    gear_name = potential_gear
                    light_name = " ".join(parts[i:])
                    break
            
            if not gear_name or not light_name:
                await query.answer("❌ Invalid light/gear combination!", show_alert=True)
                return
            
            gear = GEARS[gear_name]
            recipe = gear["recipe"]
            
            if light_name not in recipe:
                await query.answer("❌ This light is not needed for this gear!", show_alert=True)
                return
            
            # Calculate how much we can add
            required_amount = recipe[light_name]
            reserve = get_craft_reserve(user_data, gear_name)
            current_reserve = reserve.get(light_name, 0)
            current_inv = user_data["inventory"].get(light_name, 0)
            
            can_add = min(required_amount - current_reserve, current_inv)
            
            if can_add <= 0:
                await query.answer("❌ No lights available to add!", show_alert=True)
                return
            
            # Add to reserve
            success, msg = add_light_to_reserve(user_data, gear_name, light_name, can_add)
            
            if not success:
                await query.answer(f"❌ {msg}", show_alert=True)
                return
            
            await query.answer(f"✅ Added {can_add}x {light_name}!", show_alert=False)
            
            # Refresh and show updated page
            user_data = get_user_data(user_id)
            settings = get_auto_craft_settings(user_data, gear_name)
            reserve = get_craft_reserve(user_data, gear_name)
            can_craft_reserve, missing_reserve = can_craft_with_reserve(user_data, gear_name)
            
            recipe_lines = []
            for light_name_iter, amount in recipe.items():
                current_inv = user_data["inventory"].get(light_name_iter, 0)
                current_reserve = reserve.get(light_name_iter, 0)
                light_icon = next((a["icon"] for a in LIGHTS if a["name"] == light_name_iter), "")
                status = "✅" if current_reserve >= amount else "❌"
                recipe_lines.append(
                    f"{status} {light_icon} {light_name_iter}: Inv:{current_inv} | Reserve:{current_reserve}/{amount}"
                )
            
            auto_add_status = "🟢 ON" if settings.get("auto_add", False) else "⚪ OFF"
            auto_craft_status = "🟢 ON" if settings.get("auto_craft", False) else "⚪ OFF"
            
            text = (
                f"🔨 <b>CRAFT: {gear['icon']} {gear_name}</b>\n"
                f"Tier: {gear['tier']} | Luck Bonus: +{gear['stats']['luck']}\n"
                "===================================\n"
                "<b>📋 Recipe:</b>\n" + "\n".join(recipe_lines) + "\n"
                "===================================\n"
                f"<b>⚙️ Auto Settings:</b>\n"
                f"• Auto-Add: {auto_add_status} (Priority over discard)\n"
                f"• Auto-Craft: {auto_craft_status}\n\n"
            )
            
            keyboard = []
            
            # Toggle buttons
            auto_add_text = "🟢 Auto-Add: ON" if settings.get("auto_add", False) else "⚪ Auto-Add: OFF"
            keyboard.append([InlineKeyboardButton(auto_add_text, callback_data=f"toggle_add_{gear_name.replace(' ', '_')}")])
            
            auto_craft_text = "🟢 Auto-Craft: ON" if settings.get("auto_craft", False) else "⚪ Auto-Craft: OFF"
            keyboard.append([InlineKeyboardButton(auto_craft_text, callback_data=f"toggle_craft_{gear_name.replace(' ', '_')}")])
            
            # Manual add buttons for each light that needs more in reserve
            for light_name_iter, amount in recipe.items():
                current_inv = user_data["inventory"].get(light_name_iter, 0)
                current_reserve = reserve.get(light_name_iter, 0)
                
                if current_reserve < amount and current_inv > 0:
                    can_add_btn = min(amount - current_reserve, current_inv)
                    light_icon = next((a["icon"] for a in LIGHTS if a["name"] == light_name_iter), "")
                    keyboard.append([InlineKeyboardButton(
                        f"➕ Add {light_icon} {light_name_iter} ({can_add_btn}x)",
                        callback_data=f"add_light_{gear_name.replace(' ', '_')}_{light_name_iter.replace(' ', '_')}"
                    )])
            
            # Craft button
            if can_craft_reserve:
                keyboard.append([InlineKeyboardButton("🔨 Craft", callback_data=f"do_craft_{gear_name.replace(' ', '_')}")])
                text += "✅ <b>Reserve ready! You can craft!</b>"
            else:
                text += "❌ <b>Reserve not ready yet!</b>\n<i>Add more lights to reserve.</i>"
            
            keyboard.append([InlineKeyboardButton("🔙 Back to Craft Menu", callback_data="action_craft")])
            keyboard.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="action_main")])
            
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

        # ACTION: SETTINGS
        elif query.data == "action_settings":
            from database import get_auto_discard_threshold
            
            user_data = get_user_data(user_id)
            threshold = get_auto_discard_threshold(user_data)
            
            discard_status = "⚪ OFF" if threshold == 0 else f"🟢 ON (≤{threshold})"
            
            await query.edit_message_text(
                "⚙️ <b>GAME SETTINGS</b>\n\n"
                "Configure your rolling preferences:\n\n"
                "<b>Auto-Roll:</b> When ON, you can start continuous auto-rolling.\n"
                f"<b>Auto-Discard:</b> {discard_status}\n"
                f"  └ Use <code>/autodiscard</code> to configure threshold",
                parse_mode="HTML",
                reply_markup=get_settings_keyboard(user_data)
            )

        elif query.data == "toggle_auto":
            new_state = not user_data["auto_roll"]
            set_auto_roll(user_data, new_state)
            
            user_data = get_user_data(user_id)
            
            if not new_state and user_data["is_rolling"]:
                set_rolling_state(user_data, False)
            
            await query.edit_message_reply_markup(reply_markup=get_settings_keyboard(user_data))

        # ACTION: PREMIUM
        elif query.data == "action_premium":
            from database import get_premium_status
            import json
            
            user_data = get_user_data(user_id)
            premium_info = get_premium_status(user_data)
            
            # Load premium tiers
            with open("data/premium_tiers.json", "r", encoding="utf-8") as f:
                tiers = json.load(f)
            
            if premium_info["active"]:
                tier = premium_info["tier"]
                tier_data = tiers[tier]
                days_left = premium_info["days_left"]
                
                text = (
                    f"{tier_data['icon']} <b>YOUR PREMIUM STATUS</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"✅ <b>Status:</b> ACTIVE\n"
                    f"💎 <b>Tier:</b> {tier_data['name']}\n"
                    f"⏰ <b>Days Left:</b> {days_left} days\n\n"
                    "<b>🎁 Your Benefits:</b>\n"
                    f"• Auto-Roll Always ON\n"
                    f"• +{tier_data['benefits']['luck_boost_percent']}% Permanent Luck\n"
                    f"• {tier_data['benefits']['coins_multiplier']}x Coins & EXP\n\n"
                    f"Use /premium for full details!"
                )
            else:
                text = (
                    "💎 <b>PREMIUM SUBSCRIPTION</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "⚪ <b>Status:</b> FREE\n\n"
                    "<b>Upgrade to Premium for:</b>\n"
                    "• 🔄 Auto-Roll Permanent\n"
                    "• 🍀 Huge Luck Boosts (250-500%)\n"
                    "• 💰 Up to 200k Coins/Month\n"
                    "• 🧪 Up to 300 Potions/Month\n"
                    "• ✨ Exclusive Lights (Pro)\n"
                    "• 💸 30% Shop Discount (Pro)\n\n"
                    f"🌟 <b>Basic:</b> $1.99/month\n"
                    f"⭐ <b>Pro:</b> $3.99/month (2x Basic!)\n\n"
                    f"Use /premium for full info!"
                )
            
            keyboard = [
                [InlineKeyboardButton("💎 View Premium Plans", callback_data="premium_plans")],
                [InlineKeyboardButton("⬅️ Back to Main", callback_data="action_main")]
            ]
            
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

        # VIEW PREMIUM STATUS (For active premium users)
        elif query.data == "view_premium_status":
            import json
            from database import get_premium_status
            import time
            
            user_data = get_user_data(user_id)
            premium_info = get_premium_status(user_data)
            
            if not premium_info or not premium_info.get("active"):
                await query.answer("❌ No active premium subscription!", show_alert=True)
                return
            
            # Load premium tiers
            with open("data/premium_tiers.json", "r", encoding="utf-8") as f:
                tiers = json.load(f)
            
            tier = premium_info.get("tier")
            tier_data = tiers[tier]
            days_left = premium_info.get("days_left")
            expire_time = premium_info.get("expire_time")
            
            # Calculate next reward date (30 days cycle)
            from datetime import datetime, timedelta
            if expire_time:
                next_reward = datetime.fromtimestamp(expire_time)
                next_reward_str = next_reward.strftime("%B %d, %Y")
            else:
                next_reward_str = "Unknown"
            
            # Check if monthly rewards claimed
            monthly_claimed = user_data.get("premium", {}).get("monthly_rewards_claimed", False)
            
            icon = tier_data.get("icon", "💎")
            tier_name = tier_data.get("name")
            
            text = (
                f"{icon} <b>YOUR PREMIUM STATUS</b> {icon}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"✅ <b>Status:</b> ACTIVE\n"
                f"💎 <b>Tier:</b> {tier_name}\n"
                f"⏳ <b>Days Remaining:</b> {days_left} days\n"
                f"📅 <b>Renewal Date:</b> {next_reward_str}\n\n"
                "<b>🎁 YOUR MONTHLY REWARDS:</b>\n"
                f"• 💰 <b>{tier_data['benefits']['monthly_coins']:,} Coins</b>\n"
                f"• 🧪 <b>{tier_data['benefits']['monthly_luck_potions']} Luck Potions</b>\n"
            )
            
            if monthly_claimed:
                text += "\n✅ <i>This month's rewards have been claimed!</i>\n"
                text += f"📆 <i>Next rewards available: {next_reward_str}</i>\n"
            else:
                text += "\n🎁 <i>Monthly rewards ready to claim!</i>\n"
                text += "<i>You'll receive them automatically on renewal</i>\n"
            
            text += "\n<b>✨ YOUR ACTIVE BENEFITS:</b>\n"
            text += f"• 🔄 <b>Permanent Auto-Roll</b> (Always ON!)\n"
            text += f"• 🍀 <b>+{tier_data['benefits']['luck_boost_percent']}% Permanent Luck</b>\n"
            text += f"• 💎 <b>{tier_data['benefits']['coins_multiplier']:.0f}x Coins & EXP</b>\n"
            
            if tier == "pro":
                exclusive_lights = user_data.get("exclusive_lights_granted", [])
                if exclusive_lights:
                    text += f"• ✨ <b>Exclusive Lights Unlocked:</b>\n"
                    for light in exclusive_lights:
                        if light == "Cybernight":
                            text += "   └ 🌆 Cybernight\n"
                        elif light == "O'Sound":
                            text += "   └ 🎸 O'Sound\n"
                        elif light == "Remembrance":
                            text += "   └ 🎻 Remembrance\n"
                else:
                    text += f"• ✨ <b>2 Exclusive Lights</b> (granted on purchase)\n"
                text += f"• 🔮 <b>Light Preview Access</b>\n"
                text += f"• 💸 <b>{tier_data['benefits']['shop_discount_percent']}% Shop Discount</b>\n"
            
            text += (
                "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "💡 <b>Need to Renew?</b>\n"
                "Your subscription will auto-renew if payment is active.\n"
                "To manually renew or upgrade, click the button below!\n\n"
                "🌟 <b>Thank you for being a premium member!</b> 🌟"
            )
            
            keyboard = [
                [InlineKeyboardButton("🔄 Renew / Upgrade", callback_data="renew_premium")],
                [InlineKeyboardButton("📊 View Full Plans", callback_data="premium_plans")],
                [InlineKeyboardButton("⬅️ Back to Main", callback_data="action_main")]
            ]
            
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        
        # RENEW PREMIUM (Show QR code)
        elif query.data == "renew_premium":
            text = (
                "🔄 <b>RENEW YOUR PREMIUM</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "To renew or upgrade your subscription:\n\n"
                "<b>📱 STEP 1:</b> Get your QR code\n"
                "Visit our premium website to see the Ko-fi QR code:\n"
                "🌐 <b>constellation-premium.space</b>\n\n"
                "<b>📷 STEP 2:</b> Scan QR Code\n"
                "Use your phone camera or Ko-fi app\n\n"
                "<b>💳 STEP 3:</b> Complete Payment\n"
                f"Make sure to include: <code>telegram_id: {user_id}</code>\n\n"
                "<b>✨ STEP 4:</b> Instant Activation\n"
                "Your premium will be renewed immediately!\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "💡 <i>You'll receive a notification once payment is confirmed</i>"
            )
            
            keyboard = [
                [InlineKeyboardButton("🌐 Open Premium Website", url="https://constellation-premium.space")],
                [InlineKeyboardButton("💬 Contact Admin", url="https://t.me/YourAdminUsername")],
                [InlineKeyboardButton("⬅️ Back", callback_data="view_premium_status")]
            ]
            
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

        # ACTION: SHOP
        elif query.data == "action_shop":
            user_data = get_user_data(user_id)
            
            text_shop = (
                "🏪 <b>POTION SHOP</b>\n"
                "-----------------------------------\n"
                f"💰 Your Coins: <b>{user_data.get('coins', 0):,}</b>\n\n"
                "<b>Available Potions:</b>\n\n"
            )
            
            for potion_id, potion in POTIONS.items():
                # Skip hidden potions (Null Potion - drop only)
                if potion.get("hidden", False):
                    continue
                    
                text_shop += f"{potion['icon']} <b>{potion['name']}</b>\n"
                text_shop += f"   └ {potion['description']}\n"
                text_shop += f"   └ Price: <b>💰 {potion['price']:,} coins</b>\n"
                text_shop += f"   └ Buy: <code>/buy {potion_id}</code>\n\n"
            
            text_shop += "-----------------------------------\n"
            text_shop += "💡 <b>Tip:</b> Null Potion (👾) can only be obtained\n"
            text_shop += "    as a rare drop from rolls (0.1% chance)!\n\n"
            text_shop += "<b>How to buy:</b>\n"
            text_shop += "Type: <code>/buy &lt;potion_id&gt;</code>\n"
            text_shop += "<i>Example: /buy luck_potion_1</i>"
            
            keyboard = [[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]]
            await query.edit_message_text(text_shop, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        
        # PREMIUM CALLBACKS
        elif query.data == "premium_plans":
            # Forward to premium command
            await query.message.reply_text("Loading premium plans...")
            from commands.premium import premium_command
            await premium_command(update, context)
            await query.answer()
        
        elif query.data == "buy_premium_basic":
            text = (
                "🌟 <b>CONSTELLATION | BASIC</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "💵 <b>Price:</b> $1.99/month\n\n"
                "<b>🎁 What You Get:</b>\n"
                "• 🔄 <b>Permanent Auto-Roll</b>\n"
                "• 💰 <b>100,000 Coins/month</b>\n"
                "• 🧪 <b>150 Luck Potions/month</b>\n"
                "• 🍀 <b>+250% Permanent Luck Boost</b>\n"
                "• 💎 <b>2x Coins & EXP Multiplier</b>\n"
                "• 🏷️ <b>Special Premium Title</b>\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "<b>🛒 Ready to Purchase?</b>\n\n"
                "Visit our secure premium website to complete your purchase:\n"
                "🌐 <b>constellation-premium.space</b>\n\n"
                "Or contact admin directly:\n"
                "1. Click button below\n"
                "2. Send your User ID: <code>{user_id}</code>\n"
                "3. Choose payment method\n"
                "4. Premium activates instantly!\n\n"
                "💳 <b>Accepted:</b> PayPal, Crypto, Bank Transfer"
            ).format(user_id=user_id)
            
            keyboard = [
                [InlineKeyboardButton("🌐 Visit Premium Website", url="https://constellation-premium.space")],
                [InlineKeyboardButton("💬 Contact Admin", url="https://t.me/YourAdminUsername")],
                [InlineKeyboardButton("⬅️ Back", callback_data="action_premium")]
            ]
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        
        elif query.data == "buy_premium_pro":
            text = (
                "⭐ <b>CONSTELLATION | PRO</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "💵 <b>Price:</b> $3.99/month\n"
                "<i>🎉 2x ALL Basic Rewards!</i>\n\n"
                "<b>🎁 What You Get:</b>\n"
                "• 🔄 <b>Permanent Auto-Roll</b>\n"
                "• 💰 <b>200,000 Coins/month</b> (2x Basic)\n"
                "• 🧪 <b>300 Luck Potions/month</b> (2x Basic)\n"
                "• 🍀 <b>+500% Permanent Luck Boost</b> (2x Basic)\n"
                "• 💎 <b>2x Coins & EXP Multiplier</b>\n\n"
                "<b>✨ PRO EXCLUSIVE:</b>\n"
                "• 🌆🎸🎻 <b>3 Exclusive Lights</b> (Get 2 Random):\n"
                "   └ Cybernight 🌆, O'Sound 🎸, Remembrance 🎻\n"
                "   └ Drops during Heaven Approach ✨👼 (0.5%, 15% rate)\n"
                "• 🔮 <b>New Light Preview Access</b>\n"
                "• 💸 <b>30% Shop Discount</b>\n"
                "• 🏷️ <b>Elite Premium Title</b>\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "<b>🛒 Ready to Purchase?</b>\n\n"
                "Visit our secure premium website to complete your purchase:\n"
                "🌐 <b>constellation-premium.space</b>\n\n"
                "Or contact admin directly:\n"
                "1. Click button below\n"
                "2. Send your User ID: <code>{user_id}</code>\n"
                "3. Choose payment method\n"
                "4. Premium activates instantly!\n\n"
                "💳 <b>Accepted:</b> PayPal, Crypto, Bank Transfer"
            ).format(user_id=user_id)
            
            keyboard = [
                [InlineKeyboardButton("🌐 Visit Premium Website", url="https://constellation-premium.space")],
                [InlineKeyboardButton("💬 Contact Admin", url="https://t.me/YourAdminUsername")],
                [InlineKeyboardButton("⬅️ Back", callback_data="action_premium")]
            ]
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        
        elif query.data == "compare_premium":
            import json
            with open("data/premium_tiers.json", "r", encoding="utf-8") as f:
                tiers = json.load(f)
            
            basic = tiers["basic"]
            pro = tiers["pro"]
            
            text = (
                "📊 <b>PREMIUM TIER COMPARISON</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"⭐ <b>BASIC - ${basic['price_usd']:.2f}/month</b>\n"
                f"• 🔄 Auto-Roll: ✅\n"
                f"• 💰 Monthly Coins: {basic['benefits']['monthly_coins']:,}\n"
                f"• 🧪 Monthly Potions: {basic['benefits']['monthly_luck_potions']}\n"
                f"• 🍀 Luck Boost: +{basic['benefits']['luck_boost_percent']}%\n"
                f"• 💰 Coins Mult: {basic['benefits']['coins_multiplier']}x\n"
                f"• ⭐ EXP Mult: {basic['benefits']['exp_multiplier']}x\n"
                f"• ✨ Exclusive Lights: ❌\n"
                f"• 🔮 Light Preview: ❌\n"
                f"• 💸 Shop Discount: ❌\n\n"
                f"💎 <b>PRO - ${pro['price_usd']:.2f}/month</b>\n"
                f"• 🔄 Auto-Roll: ✅\n"
                f"• 💰 Monthly Coins: {pro['benefits']['monthly_coins']:,}\n"
                f"• 🧪 Monthly Potions: {pro['benefits']['monthly_luck_potions']}\n"
                f"• 🍀 Luck Boost: +{pro['benefits']['luck_boost_percent']}%\n"
                f"• 💰 Coins Mult: {pro['benefits']['coins_multiplier']}x\n"
                f"• ⭐ EXP Mult: {pro['benefits']['exp_multiplier']}x\n"
                f"• ✨ Exclusive Lights: ✅ (2 random on purchase)\n"
                f"• 🔮 Light Preview: ✅\n"
                f"• 💸 Shop Discount: {pro['benefits']['shop_discount_percent']}%\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "💡 <b>Pro offers 2x rewards + exclusive features!</b>"
            )
            
            keyboard = [
                [InlineKeyboardButton(f"{basic['icon']} Buy Basic", callback_data="buy_premium_basic")],
                [InlineKeyboardButton(f"{pro['icon']} Buy Pro", callback_data="buy_premium_pro")],
                [InlineKeyboardButton("⬅️ Back", callback_data="action_premium")]
            ]
            
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        
        # SERVER CALLBACKS
        elif query.data.startswith("select_server_"):
            from handlers.server_callbacks import handle_server_selection
            await handle_server_selection(query, user_id)
        
        elif query.data == "refresh_servers":
            from handlers.server_callbacks import handle_refresh_servers
            await handle_refresh_servers(query, user_id)
        
        elif query.data.startswith("lb_"):
            from handlers.server_callbacks import handle_leaderboard_callback
            await handle_leaderboard_callback(query, user_id)
        
        elif query.data == "show_leaderboard":
            from handlers.server_callbacks import handle_show_leaderboard
            await handle_show_leaderboard(query, user_id)
        
        elif query.data == "close_menu":
            from handlers.server_callbacks import handle_close_menu
            await handle_close_menu(query)
        
        else:
            logging.warning(f"Unknown callback data: {query.data}")
            await query.answer("❌ Unknown action", show_alert=True)
            
    except Exception as e:
        logging.error(f"Error in button_callback for {query.data}: {e}")
        import traceback
        traceback.print_exc()
        try:
            await query.edit_message_text(
                "❌ <b>An error occurred.</b>\n\nPlease try again or use /start to restart.",
                parse_mode="HTML",
                reply_markup=get_main_keyboard(user_data)
            )
        except BadRequest:
            pass

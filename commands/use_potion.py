"""Use potion command handler"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_user_data, use_potion
from config import POTIONS

async def use_potion_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /use command to use potions with amount parameter.
    Usage: /use <potion_id> [amount]
    Example: /use luck_potion_2 10 (use 10 potions, duration stacks to 50 minutes)
    """
    try:
        user_id = update.effective_user.id
        user_data = get_user_data(user_id)
        
        # Update activity
        from database import update_activity
        update_activity(user_data)
        user_data = get_user_data(user_id)
        
        # Check if potion ID was provided
        if not context.args:
            # Show available potions
            text = "🧪 <b>USE POTION</b>\n"
            text += "-----------------------------------\n"
            text += "Your Potion Inventory:\n\n"
            
            potion_inv = user_data.get("potion_inventory", {})
            if not potion_inv or all(count == 0 for count in potion_inv.values()):
                text += "<i>You don't have any potions.</i>\n\n"
            else:
                for potion_id, count in potion_inv.items():
                    if count > 0 and potion_id in POTIONS:
                        potion = POTIONS[potion_id]
                        text += f"{potion['icon']} <b>{potion['name']}</b> x{count}\n"
                        text += f"   └ {potion['description']}\n"
                        text += f"   └ ID: <code>{potion_id}</code>\n\n"
            
            text += "-----------------------------------\n"
            text += "<b>Usage:</b> /use &lt;potion_id&gt; [amount]\n"
            text += "<i>Example: /use luck_potion_1</i>\n"
            text += "<i>Example: /use luck_potion_2 10 (use 10x, duration stacks!)</i>"
            
            keyboard = [[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]]
            await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        # Get potion ID and amount from command
        potion_id = context.args[0].lower()
        
        # Get amount (default = 1)
        amount = 1
        if len(context.args) >= 2:
            try:
                amount = int(context.args[1])
                if amount <= 0:
                    await update.message.reply_text("❌ Amount must be positive!", parse_mode="HTML")
                    return
            except ValueError:
                await update.message.reply_text("❌ Invalid amount! Must be a number.", parse_mode="HTML")
                return
        
        # Check if potion exists
        if potion_id not in POTIONS:
            text = f"❌ <b>Potion not found!</b>\n\nUse /use to see available potions."
            keyboard = [[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]]
            await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        # Check if user has enough potions
        potion_inv = user_data.get("potion_inventory", {})
        if potion_id not in potion_inv or potion_inv[potion_id] < amount:
            current = potion_inv.get(potion_id, 0)
            text = f"❌ <b>Not enough potions!</b>\n\nYou have: {current}x\nTrying to use: {amount}x"
            keyboard = [[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]]
            await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        # Use potions (multiple times if amount > 1)
        potion = POTIONS[potion_id]
        effect = potion['effect']
        
        # Initialize active_effects if not exists
        if "active_effects" not in user_data:
            user_data["active_effects"] = []
        
        # Deduct potions
        user_data["potion_inventory"][potion_id] -= amount
        
        # Calculate stacked duration
        import time
        stacked_duration = effect['duration'] * amount  # Duration multiplies!
        
        # Check if same potion effect already exists (extend it)
        existing_effect = None
        for eff in user_data["active_effects"]:
            # Match by potion_id AND type to handle same potion correctly
            if eff.get("potion_id") == potion_id and eff.get("type") == effect["type"]:
                existing_effect = eff
                break
        
        current_time = time.time()
        
        if existing_effect:
            # Extend existing effect - IMPORTANT: Add to expire_time, not just duration
            logging.info(f"Extending effect {potion_id}: current expire_time={existing_effect.get('expire_time')}, adding {stacked_duration}s")
            
            # Calculate remaining time
            remaining_time = max(0, existing_effect.get("expire_time", current_time) - current_time)
            
            # New total duration = remaining + new
            new_total_duration = remaining_time + stacked_duration
            
            # Update effect
            existing_effect["duration"] = new_total_duration
            existing_effect["expire_time"] = current_time + new_total_duration
            
            logging.info(f"Extended effect: new expire_time={existing_effect['expire_time']}, total duration={new_total_duration}s")
        else:
            # Add new effect
            effect_data = {
                "potion_id": potion_id,
                "name": potion["name"],
                "icon": potion["icon"],
                "type": effect["type"],
                "amount": effect["amount"],
                "duration": stacked_duration,
                "start_time": time.time(),
                "expire_time": time.time() + stacked_duration if stacked_duration > 0 else 0
            }
            user_data["active_effects"].append(effect_data)
        
        # Track usage stats (do this AFTER modifying effects)
        if "stats" not in user_data:
            user_data["stats"] = {"potions_used": 0}
        user_data["stats"]["potions_used"] = user_data["stats"].get("potions_used", 0) + amount
        
        # Also track daily
        if "daily_stats" not in user_data:
            user_data["daily_stats"] = {}
        user_data["daily_stats"]["potions_used"] = user_data["daily_stats"].get("potions_used", 0) + amount
        
        # Save ONCE at the end
        from database import save_user_data
        save_user_data(user_data)
        
        # Success message
        potion = POTIONS[potion_id]
        text = f"✅ <b>Used {amount}x {potion['icon']} {potion['name']}!</b>\n\n"
        text += f"• Effect: {potion['description']}\n"
        
        if stacked_duration > 0:
            duration_min = stacked_duration / 60
            duration_hours = duration_min / 60
            
            if duration_hours >= 1:
                text += f"• Duration: {duration_hours:.1f} hour(s)\n"
            else:
                text += f"• Duration: {duration_min:.0f} minute(s)\n"
            
            if amount > 1:
                text += f"• <b>Stacked!</b> {amount}x potion = {amount}x duration\n"
        else:
            text += "• Type: Instant (next roll only)\n"
        
        text += "\n<i>Effect is now active! Check /stats to see active effects.</i>"
        
        keyboard = [[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]]
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        
    except Exception as e:
        logging.error(f"Error in use_potion_command: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text(
            "❌ An error occurred. Please try again.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]])
        )

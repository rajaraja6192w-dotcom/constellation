"""Discard command handler"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import get_user_data, discard_light, update_activity
from config import LIGHTS, SPECIAL_LIGHTS

async def discard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Discard lights from inventory. Usage: /discard <light_name> <amount>"""
    try:
        user_id = update.effective_user.id
        user_data = get_user_data(user_id)
        update_activity(user_data)
        
        # Check arguments
        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ <b>Usage:</b> <code>/discard &lt;light_name&gt; &lt;amount&gt;</code>\n\n"
                "<b>Examples:</b>\n"
                "• <code>/discard Common 50</code>\n"
                "• <code>/discard Galaxius 1</code>\n\n"
                "<i>Light names are case-sensitive!</i>",
                parse_mode="HTML"
            )
            return
        
        # Parse arguments
        amount_str = context.args[-1]  # Last arg is amount
        light_name = " ".join(context.args[:-1])  # Everything else is light name
        
        try:
            amount = int(amount_str)
            if amount <= 0:
                await update.message.reply_text("❌ Amount must be positive!")
                return
        except ValueError:
            await update.message.reply_text("❌ Invalid amount! Must be a number.")
            return
        
        # Check if light exists
        all_lights = LIGHTS + SPECIAL_LIGHTS
        light_exists = any(l["name"] == light_name for l in all_lights)
        
        if not light_exists:
            await update.message.reply_text(
                f"❌ Light '<b>{light_name}</b>' not found!\n\n"
                "<i>Tip: Light names are case-sensitive.</i>",
                parse_mode="HTML"
            )
            return
        
        # Discard
        success, message = discard_light(user_data, light_name, amount)
        
        if success:
            await update.message.reply_text(
                f"🗑️ <b>Discarded Successfully!</b>\n\n"
                f"{message}\n\n"
                f"💡 <i>Tip: Use /autodiscard to set auto-discard threshold</i>",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(f"❌ {message}", parse_mode="HTML")
    
    except Exception as e:
        logging.error(f"Error in discard_command: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text("❌ An error occurred while discarding.")

async def autodiscard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set auto-discard threshold. Usage: /autodiscard <rarity_threshold>"""
    try:
        user_id = update.effective_user.id
        user_data = get_user_data(user_id)
        update_activity(user_data)
        
        from database import set_auto_discard_threshold, get_auto_discard_threshold
        
        # If no args, show current setting
        if len(context.args) == 0:
            current_threshold = get_auto_discard_threshold(user_data)
            
            if current_threshold == 0:
                status = "⚪ <b>DISABLED</b>"
                desc = "All lights will be added to inventory."
            else:
                status = f"🟢 <b>ENABLED</b> (Threshold: <code>{current_threshold}</code>)"
                desc = f"Lights with rarity ≤ {current_threshold} will be auto-discarded."
            
            text = (
                "🗑️ <b>AUTO-DISCARD SETTINGS</b>\n"
                "===================================\n\n"
                f"<b>Status:</b> {status}\n"
                f"<i>{desc}</i>\n\n"
                "===================================\n\n"
                "<b>How to use:</b>\n"
                "• <code>/autodiscard 0</code> - Disable\n"
                "• <code>/autodiscard 10</code> - Discard lights with rarity ≤ 10\n"
                "• <code>/autodiscard 200</code> - Discard lights with rarity ≤ 200\n\n"
                "<b>Examples:</b>\n"
                "• Set <code>200</code> → Common to Flame auto-discarded\n"
                "• Set <code>50</code> → Common to Rare auto-discarded\n"
                "• Set <code>0</code> → No auto-discard\n\n"
                "💡 <i>Tip: Check light rarities in /inventory to set appropriate threshold</i>"
            )
            
            await update.message.reply_text(text, parse_mode="HTML")
            return
        
        # Parse threshold
        try:
            threshold = int(context.args[0])
            if threshold < 0:
                await update.message.reply_text("❌ Threshold must be 0 or positive!")
                return
        except ValueError:
            await update.message.reply_text("❌ Invalid threshold! Must be a number.")
            return
        
        # Set threshold
        success = set_auto_discard_threshold(user_data, threshold)
        
        if success:
            if threshold == 0:
                await update.message.reply_text(
                    "✅ <b>Auto-discard DISABLED</b>\n\n"
                    "All lights will be added to inventory.",
                    parse_mode="HTML"
                )
            else:
                await update.message.reply_text(
                    f"✅ <b>Auto-discard ENABLED</b>\n\n"
                    f"<b>Threshold:</b> <code>{threshold}</code>\n\n"
                    f"Lights with rarity ≤ {threshold} will be automatically discarded.\n\n"
                    f"💡 <i>Use /autodiscard to check status</i>",
                    parse_mode="HTML"
                )
        else:
            await update.message.reply_text("❌ Failed to set auto-discard threshold.")
    
    except Exception as e:
        logging.error(f"Error in autodiscard_command: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text("❌ An error occurred.")

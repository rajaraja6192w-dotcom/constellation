"""Craft command handler"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import get_user_data
from utils.keyboards import get_craft_keyboard

async def craft_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows craft menu with available gears."""
    try:
        user_id = update.effective_user.id
        user_data = get_user_data(user_id)
        
        # Update activity
        from database import update_activity
        update_activity(user_data)
        
        text = (
            "🔨 <b>CRAFTING MENU</b>\n"
            "-----------------------------------\n"
            "Select a gear to craft:\n\n"
            "Each gear requires specific lights as materials.\n"
            "Click on a gear to see the recipe and craft it!"
        )
        
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=get_craft_keyboard())
    except Exception as e:
        logging.error(f"Error in craft_command: {e}")
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        back_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]
        ])
        try:
            await update.message.reply_text(
                "❌ An error occurred. Please try again.",
                reply_markup=back_button
            )
        except:
            pass

"""Buy command handler for buying potions with coins"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_user_data, give_potion_reward, save_user_data
from config import POTIONS

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /buy command to buy potions with coins.
    
    Usage: /buy <potion_id> [amount]
    Examples:
        /buy luck_potion_1
        /buy luck_potion_1 5
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
            text = "❌ <b>Usage: /buy &lt;potion_id&gt; [amount]</b>\n\n"
            text += "<i>Examples:</i>\n"
            text += "• /buy luck_potion_1 (buy 1)\n"
            text += "• /buy luck_potion_1 5 (buy 5)\n\n"
            text += "To see available potions and prices, click the 🏪 Shop button in the main menu."
            
            keyboard = [[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]]
            await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        # Get potion ID from command
        potion_id = context.args[0].lower()
        
        # Get amount (default 1)
        amount = 1
        if len(context.args) >= 2:
            try:
                amount = int(context.args[1])
                if amount <= 0:
                    await update.message.reply_text("❌ Amount must be a positive number!")
                    return
                if amount > 999:
                    await update.message.reply_text("❌ Maximum amount is 999 per purchase!")
                    return
            except ValueError:
                await update.message.reply_text("❌ Invalid amount! Please enter a number.")
                return
        
        # Check if potion exists
        if potion_id not in POTIONS:
            text = "❌ <b>Potion not found!</b>\n\n"
            text += "Use the 🏪 Shop button to see available potions."
            keyboard = [[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]]
            await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        potion = POTIONS[potion_id]
        price_per_item = potion['price']
        total_price = price_per_item * amount
        
        # Check if user has enough coins
        user_coins = user_data.get('coins', 0)
        if user_coins < total_price:
            # Calculate max affordable
            max_affordable = user_coins // price_per_item
            
            text = f"❌ <b>Not enough coins!</b>\n\n"
            text += f"{potion['icon']} <b>{potion['name']}</b>\n"
            text += f"• Price: <b>💰 {price_per_item:,} coins</b> each\n"
            text += f"• Wanted: <b>{amount}x</b> = <b>💰 {total_price:,} coins</b>\n"
            text += f"• You have: <b>💰 {user_coins:,} coins</b>\n\n"
            
            if max_affordable > 0:
                text += f"💡 <i>You can afford {max_affordable}x ({max_affordable * price_per_item:,} coins)</i>\n"
                text += f"<i>Try: /buy {potion_id} {max_affordable}</i>"
            else:
                text += f"<i>Need {total_price - user_coins:,} more coins. Keep leveling up!</i>"
            
            keyboard = [[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]]
            await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        # Deduct coins
        user_data['coins'] -= total_price
        
        # Give potions
        give_potion_reward(user_data, potion_id, amount)
        
        # Track purchase (track once per command, not per potion)
        from database import track_potion_bought
        track_potion_bought(user_data)
        
        # Save to database
        save_user_data(user_data)
        
        # Success message
        text = f"✅ <b>Purchase Successful!</b>\n\n"
        text += f"You bought: {potion['icon']} <b>{potion['name']}</b>\n"
        text += f"• Quantity: <b>{amount}x</b>\n"
        text += f"• Price per item: <b>💰 {price_per_item:,} coins</b>\n"
        text += f"• Total cost: <b>💰 {total_price:,} coins</b>\n"
        text += f"• Remaining coins: <b>💰 {user_data['coins']:,}</b>\n\n"
        text += f"<i>Use /use {potion_id} to activate this potion!</i>"
        
        keyboard = [[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]]
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        
    except Exception as e:
        logging.error(f"Error in buy_command: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text(
            "❌ An error occurred. Please try again.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]])
        )

"""Server membership check utility"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def check_server_membership(update: Update, user_data: dict) -> bool:
    """Check if user has joined a server. Returns True if joined, False otherwise.
    
    If user hasn't joined, sends a message prompting them to join.
    """
    from database import get_user_server
    
    current_server = get_user_server(user_data)
    
    if not current_server:
        # User hasn't joined a server
        user_name = update.effective_user.first_name
        user_id = update.effective_user.id
        
        text = (
            f"⚠️ <b>Server Required, {user_name}!</b>\n\n"
            f"👤 <b>Your Telegram ID:</b> <code>{user_id}</code>\n\n"
            "You must join a server before using this command.\n\n"
            "🌐 <b>Why join a server?</b>\n"
            "• Access all bot features\n"
            "• Compete on leaderboards\n"
            "• Track your progress\n"
            "• Join friends on same server\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 Use <b>/play</b> to select your server now!"
        )
        
        keyboard = [
            [InlineKeyboardButton("🎮 Select Server", callback_data="refresh_servers")],
            [InlineKeyboardButton("❓ Help", callback_data="action_help")]
        ]
        
        # Check if this is from a command or callback
        if update.callback_query:
            await update.callback_query.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        return False
    
    return True

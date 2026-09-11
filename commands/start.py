"""Start command handler"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import get_user_data, update_activity
from utils.keyboards import get_main_keyboard

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initializes user session."""
    try:
        user_id = update.effective_user.id
        user_data = get_user_data(user_id)
        update_activity(user_data)
        user_name = update.effective_user.first_name
        
        # Check if user has joined a server
        from database import get_user_server
        current_server = get_user_server(user_data)
        
        if not current_server:
            # User hasn't joined a server yet
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            text = (
                f"👋 <b>Welcome to Constellation RNG, {user_name}!</b>\n\n"
                f"👤 <b>Your Telegram ID:</b> <code>{user_id}</code>\n\n"
                "⚠️ <b>You need to join a server first!</b>\n\n"
                "🌐 <b>Why join a server?</b>\n"
                "• Compete with players on server leaderboards\n"
                "• Track your playtime and progress\n"
                "• Join friends on the same server\n"
                "• Choose from 10 different servers\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "💡 Use <b>/play</b> to select your server and start playing!"
            )
            
            keyboard = [
                [InlineKeyboardButton("🎮 Select Server", callback_data="refresh_servers")],
                [InlineKeyboardButton("❓ Help", url="https://t.me/your_bot_channel")]  # Optional
            ]
            
            await update.message.reply_text(
                text, 
                parse_mode="HTML", 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        # User has joined a server, proceed normally
        # Get world state
        from database import get_current_world_state
        from utils.world_manager import get_world_display
        from commands.server import SERVERS
        
        world_state = get_current_world_state()
        world_display = get_world_display(world_state)
        
        # Get server info
        server_info = next((s for s in SERVERS if s["id"] == current_server), None)
        server_name = server_info["name"] if server_info else current_server
        
        text = (
            f"🌌 <b>Welcome to Constellation RNG, {user_name}!</b> 🌌\n\n"
            f"👤 <b>Your Telegram ID:</b> <code>{user_id}</code>\n"
            f"📍 <b>Server:</b> {server_name}\n\n"
            f"{world_display}\n\n"
            "Roll rare Lights, level up your profile, and build your collection!"
        )
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=get_main_keyboard(user_data))
    except Exception as e:
        logging.error(f"Error in start_command: {e}")
        import traceback
        traceback.print_exc()
        try:
            await update.message.reply_text("❌ An error occurred. Please try again.")
        except:
            pass

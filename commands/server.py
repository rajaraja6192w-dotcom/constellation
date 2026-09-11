"""Server selection and management commands"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_user_data, update_activity

# Server names (10 servers, professional names)
SERVERS = [
    {"id": "aurora", "name": "🌅 Aurora", "emoji": "🌅"},
    {"id": "nebula", "name": "🌌 Nebula", "emoji": "🌌"},
    {"id": "phoenix", "name": "🔥 Phoenix", "emoji": "🔥"},
    {"id": "celestial", "name": "⭐ Celestial", "emoji": "⭐"},
    {"id": "eclipse", "name": "🌑 Eclipse", "emoji": "🌑"},
    {"id": "horizon", "name": "🌄 Horizon", "emoji": "🌄"},
    {"id": "zenith", "name": "🎯 Zenith", "emoji": "🎯"},
    {"id": "cosmos", "name": "🪐 Cosmos", "emoji": "🪐"},
    {"id": "stellar", "name": "✨ Stellar", "emoji": "✨"},
    {"id": "vortex", "name": "🌀 Vortex", "emoji": "🌀"}
]

MAX_SERVER_CAPACITY = 100

async def play_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show server selection menu."""
    try:
        user_id = update.effective_user.id
        user_data = get_user_data(user_id)
        update_activity(user_data)
        
        from database import get_user_server, get_server_player_count
        
        current_server = get_user_server(user_data)
        
        # Get player counts for all servers
        text = (
            "🎮 <b>SERVER SELECTION</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        
        if current_server:
            server_info = next((s for s in SERVERS if s["id"] == current_server), None)
            if server_info:
                text += f"📍 <b>Current Server:</b> {server_info['name']}\n\n"
        else:
            text += "⚠️ <i>You haven't selected a server yet!</i>\n\n"
        
        text += "🌐 <b>Available Servers:</b>\n\n"
        
        # Build keyboard
        keyboard = []
        for server in SERVERS:
            player_count = get_server_player_count(server["id"])
            capacity_status = "🟢" if player_count < 80 else "🟡" if player_count < 95 else "🔴"
            is_full = player_count >= MAX_SERVER_CAPACITY
            
            # Server status text
            status = f"{capacity_status} <code>{player_count:3d}/100</code>"
            if is_full:
                status += " <b>[FULL]</b>"
            elif current_server == server["id"]:
                status += " <b>[CURRENT]</b>"
            
            text += f"{server['emoji']} <b>{server['name'].replace(server['emoji'] + ' ', '')}</b> - {status}\n"
            
            # Button
            button_text = f"{server['emoji']} {server['name'].replace(server['emoji'] + ' ', '')}"
            if current_server == server["id"]:
                button_text += " ✓"
            elif is_full:
                button_text += " [FULL]"
            
            callback_data = f"select_server_{server['id']}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        text += (
            "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 <b>Tips:</b>\n"
            "• Choose server with friends to compete!\n"
            "• Use /changeserver to switch anytime\n"
            "• Playtime only counts when in a server\n"
            "• Check /leaderboard for rankings"
        )
        
        keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data="refresh_servers")])
        keyboard.append([InlineKeyboardButton("❌ Close", callback_data="close_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)
    
    except Exception as e:
        logging.error(f"Error in play_command: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text("❌ An error occurred.")

async def changeserver_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Alias for /play command - shows server selection menu."""
    await play_command(update, context)

async def server_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current server info and statistics."""
    try:
        user_id = update.effective_user.id
        user_data = get_user_data(user_id)
        update_activity(user_data)
        
        from database import get_user_server, get_server_player_count
        
        current_server = get_user_server(user_data)
        
        if not current_server:
            await update.message.reply_text(
                "⚠️ <b>No Server Selected</b>\n\n"
                "You haven't joined a server yet!\n"
                "Use /play to select a server.",
                parse_mode="HTML"
            )
            return
        
        # Get server info
        server_info = next((s for s in SERVERS if s["id"] == current_server), None)
        if not server_info:
            await update.message.reply_text("❌ Server not found!")
            return
        
        player_count = get_server_player_count(current_server)
        capacity_percent = (player_count / MAX_SERVER_CAPACITY) * 100
        
        # Capacity status
        if capacity_percent < 80:
            capacity_emoji = "🟢"
            capacity_text = "Low"
        elif capacity_percent < 95:
            capacity_emoji = "🟡"
            capacity_text = "Medium"
        else:
            capacity_emoji = "🔴"
            capacity_text = "High"
        
        text = (
            f"{server_info['emoji']} <b>SERVER INFO</b> {server_info['emoji']}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>Server:</b> {server_info['name']}\n"
            f"<b>Players:</b> {player_count}/{MAX_SERVER_CAPACITY}\n"
            f"<b>Capacity:</b> {capacity_emoji} {capacity_text} ({capacity_percent:.1f}%)\n"
            f"<b>Status:</b> {'🔴 FULL' if player_count >= MAX_SERVER_CAPACITY else '🟢 Open'}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 Use /changeserver to switch servers\n"
            "📊 Use /leaderboard to see rankings"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Change Server", callback_data="refresh_servers")],
            [InlineKeyboardButton("📊 Leaderboard", callback_data="show_leaderboard")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)
    
    except Exception as e:
        logging.error(f"Error in server_info_command: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text("❌ An error occurred.")

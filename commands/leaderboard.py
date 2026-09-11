"""Leaderboard command handler with server support"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import users_collection

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /leaderboard command with server and global options."""
    try:
        user_id = update.effective_user.id
        
        # Update activity
        from database import get_user_data, update_activity, get_user_server
        user_data = get_user_data(user_id)
        update_activity(user_data)
        
        current_server = get_user_server(user_data)
        
        # Parse arguments: /leaderboard [server/global] [category]
        scope = "server"  # Default to server leaderboard
        category = "level"  # Default to level
        
        if context.args:
            for arg in context.args:
                arg_lower = arg.lower()
                if arg_lower in ["global", "all"]:
                    scope = "global"
                elif arg_lower in ["server", "local"]:
                    scope = "server"
                elif arg_lower in ["level", "levels", "lvl"]:
                    category = "level"
                elif arg_lower in ["rolls", "roll"]:
                    category = "rolls"
                elif arg_lower in ["coins", "coin", "money"]:
                    category = "coins"
                elif arg_lower in ["playtime", "time", "hours"]:
                    category = "playtime"
        
        # If no server selected, force global
        if not current_server:
            scope = "global"
        
        # Get leaderboard data
        from database import get_server_leaderboard, get_global_leaderboard
        
        if scope == "server":
            top_users = get_server_leaderboard(current_server, category, limit=10)
            from commands.server import SERVERS
            server_info = next((s for s in SERVERS if s["id"] == current_server), None)
            server_name = server_info["name"] if server_info else current_server
            scope_text = f"{server_name} Server"
        else:
            top_users = get_global_leaderboard(category, limit=10)
            scope_text = "Global (All Servers)"
        
        # Generate leaderboard text and keyboard using helper
        from utils.leaderboard_helper import generate_leaderboard_text, generate_leaderboard_keyboard
        
        text = generate_leaderboard_text(
            top_users=top_users,
            category=category,
            scope=scope,
            scope_text=scope_text,
            current_user_id=user_id,
            current_server=current_server
        )
        
        reply_markup = generate_leaderboard_keyboard(
            scope=scope,
            category=category,
            has_server=bool(current_server)
        )
        
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)
        
    except Exception as e:
        logging.error(f"Error in leaderboard_command: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text("❌ An error occurred. Please try again.")


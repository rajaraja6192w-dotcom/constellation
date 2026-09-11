"""Server selection callback handlers"""

import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest

async def handle_server_selection(query, user_id):
    """Handle server selection callbacks."""
    from database import get_user_data, set_user_server, get_server_player_count, is_server_full, update_activity
    from commands.server import SERVERS, MAX_SERVER_CAPACITY
    
    # Extract server ID from callback_data
    server_id = query.data.replace("select_server_", "")
    
    user_data = get_user_data(user_id)
    update_activity(user_data)
    
    # Check if server is full
    if is_server_full(server_id, MAX_SERVER_CAPACITY):
        await query.answer("❌ Server is full! Please choose another server.", show_alert=True)
        return
    
    # Set server
    success = set_user_server(user_data, server_id)
    
    if success:
        server_info = next((s for s in SERVERS if s["id"] == server_id), None)
        if server_info:
            await query.answer(f"✅ Joined {server_info['name']}!", show_alert=True)
            
            # Show welcome message
            player_count = get_server_player_count(server_id)
            text = (
                f"{server_info['emoji']} <b>WELCOME TO {server_info['name'].upper()}</b> {server_info['emoji']}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"<b>Server:</b> {server_info['name']}\n"
                f"<b>Players:</b> {player_count}/{MAX_SERVER_CAPACITY}\n\n"
                "🎮 <b>Your playtime tracking has started!</b>\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "💡 <b>Tips:</b>\n"
                "• Use /start to begin rolling\n"
                "• Use /leaderboard to see server rankings\n"
                "• Use /changeserver to switch servers\n"
                "• Use /serverinfo to view server details"
            )
            
            keyboard = [
                [InlineKeyboardButton("🎲 Start Rolling", callback_data="action_main")],
                [InlineKeyboardButton("📊 Leaderboard", callback_data="show_leaderboard")],
                [InlineKeyboardButton("🔄 Change Server", callback_data="refresh_servers")]
            ]
            
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.answer("❌ Server not found!", show_alert=True)
    else:
        await query.answer("❌ Failed to join server!", show_alert=True)

async def handle_refresh_servers(query, user_id):
    """Handle refresh servers button."""
    from database import get_user_data, get_user_server, get_server_player_count, update_activity
    from commands.server import SERVERS, MAX_SERVER_CAPACITY
    
    user_data = get_user_data(user_id)
    update_activity(user_data)
    
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
    
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)

async def handle_leaderboard_callback(query, user_id):
    """Handle leaderboard button callbacks."""
    from database import get_user_data, get_user_server, get_server_leaderboard, get_global_leaderboard, update_activity
    from commands.server import SERVERS
    
    user_data = get_user_data(user_id)
    update_activity(user_data)
    
    current_server = get_user_server(user_data)
    
    # Parse callback data: lb_[scope]_[category]
    parts = query.data.split("_")
    if len(parts) < 3:
        await query.answer("❌ Invalid callback data", show_alert=True)
        return
    
    scope = parts[1]  # server or global
    category = parts[2]  # level, rolls, coins, playtime
    
    # If no server selected, force global
    if not current_server:
        scope = "global"
    
    # Get leaderboard data
    if scope == "server":
        top_users = get_server_leaderboard(current_server, category, limit=10)
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
    
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)

async def handle_close_menu(query):
    """Handle close menu button."""
    try:
        await query.delete_message()
    except BadRequest:
        await query.edit_message_text("Menu closed.", reply_markup=None)

async def handle_show_leaderboard(query, user_id):
    """Handle show leaderboard button - default to server level."""
    from database import get_user_data, get_user_server, get_server_leaderboard, get_global_leaderboard, update_activity
    from commands.server import SERVERS
    
    user_data = get_user_data(user_id)
    update_activity(user_data)
    
    current_server = get_user_server(user_data)
    
    # Determine default scope and category
    scope = "server" if current_server else "global"
    category = "level"
    
    # Get leaderboard data
    if scope == "server":
        top_users = get_server_leaderboard(current_server, category, limit=10)
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
    
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)


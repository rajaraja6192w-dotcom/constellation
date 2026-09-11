"""Helper functions for leaderboard generation"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def generate_leaderboard_text(
    top_users: list,
    category: str,
    scope: str,
    scope_text: str,
    current_user_id: int,
    current_server: str = None
) -> str:
    """Generate leaderboard text display.
    
    Args:
        top_users: List of user data dicts
        category: Category name (level, rolls, coins, playtime)
        scope: Scope (server or global)
        scope_text: Display text for scope (e.g., "Aurora Server", "Global")
        current_user_id: ID of current user to highlight
        current_server: Current server name (optional)
    
    Returns:
        Formatted leaderboard text
    """
    # Category display
    if category == "level":
        cat_emoji = "⭐"
        cat_name = "LEVEL"
    elif category == "rolls":
        cat_emoji = "🎲"
        cat_name = "TOTAL ROLLS"
    elif category == "coins":
        cat_emoji = "💰"
        cat_name = "COINS"
    else:  # playtime
        cat_emoji = "⏰"
        cat_name = "PLAYTIME"
    
    # Build leaderboard text
    text = f"{cat_emoji} <b>LEADERBOARD - {cat_name}</b> {cat_emoji}\n"
    text += f"📍 <b>{scope_text}</b>\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if not top_users:
        text += "⚠️ <i>No players found!</i>\n\n"
    else:
        for idx, user in enumerate(top_users, 1):
            medal = ""
            if idx == 1:
                medal = "🥇"
            elif idx == 2:
                medal = "🥈"
            elif idx == 3:
                medal = "🥉"
            else:
                medal = f"{idx:2d}."
            
            level = user.get("level", 1)
            
            # Get value based on category
            if category == "level":
                value = f"Lv.{level}"
            elif category == "rolls":
                rolls = user.get("total_rolls", 0)
                value = f"{rolls:,} rolls"
            elif category == "coins":
                coins = user.get("coins", 0)
                value = f"{coins:,} coins"
            else:  # playtime
                # Playtime is already calculated in get_server_leaderboard/get_global_leaderboard
                playtime = user.get("total_playtime", 0)
                if playtime > 0:
                    hours = playtime / 3600
                    minutes = int((playtime % 3600) / 60)
                    if hours >= 1:
                        value = f"{hours:.1f}h"
                    else:
                        value = f"{minutes}m"
                else:
                    value = "0m"
            
            # Check if this is current user
            is_you = " <b>(YOU)</b>" if user.get("user_id") == current_user_id else ""
            
            text += f"{medal} <code>Lv.{level:3d}</code> - {value}{is_you}\n"
    
    text += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    text += "💡 <b>Commands:</b>\n"
    
    if current_server:
        text += "• <code>/leaderboard server level</code>\n"
        text += "• <code>/leaderboard global level</code>\n"
    else:
        text += "⚠️ <i>Join a server (/play) to see server rankings!</i>\n"
    
    text += "• Categories: level, rolls, coins, playtime"
    
    return text


def generate_leaderboard_keyboard(scope: str, category: str, has_server: bool) -> InlineKeyboardMarkup:
    """Generate leaderboard keyboard buttons.
    
    Args:
        scope: Current scope (server or global)
        category: Current category (level, rolls, coins, playtime)
        has_server: Whether user has joined a server
    
    Returns:
        InlineKeyboardMarkup with leaderboard buttons
    """
    keyboard = []
    
    # Scope buttons (only if user has server)
    if has_server:
        scope_buttons = []
        if scope == "global":
            scope_buttons.append(InlineKeyboardButton("📍 Server", callback_data=f"lb_server_{category}"))
            scope_buttons.append(InlineKeyboardButton("🌐 Global ✓", callback_data=f"lb_global_{category}"))
        else:
            scope_buttons.append(InlineKeyboardButton("📍 Server ✓", callback_data=f"lb_server_{category}"))
            scope_buttons.append(InlineKeyboardButton("🌐 Global", callback_data=f"lb_global_{category}"))
        keyboard.append(scope_buttons)
    
    # Category buttons - Row 1
    cat_buttons = []
    cat_buttons.append(InlineKeyboardButton(
        "⭐ Level" + (" ✓" if category == "level" else ""),
        callback_data=f"lb_{scope}_level"
    ))
    cat_buttons.append(InlineKeyboardButton(
        "🎲 Rolls" + (" ✓" if category == "rolls" else ""),
        callback_data=f"lb_{scope}_rolls"
    ))
    keyboard.append(cat_buttons)
    
    # Category buttons - Row 2
    cat_buttons2 = []
    cat_buttons2.append(InlineKeyboardButton(
        "💰 Coins" + (" ✓" if category == "coins" else ""),
        callback_data=f"lb_{scope}_coins"
    ))
    cat_buttons2.append(InlineKeyboardButton(
        "⏰ Time" + (" ✓" if category == "playtime" else ""),
        callback_data=f"lb_{scope}_playtime"
    ))
    keyboard.append(cat_buttons2)
    
    # Action buttons
    keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data=f"lb_{scope}_{category}")])
    keyboard.append([InlineKeyboardButton("❌ Close", callback_data="close_menu")])
    
    return InlineKeyboardMarkup(keyboard)

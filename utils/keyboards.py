"""Keyboard layouts for bot"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import GEARS

def get_main_keyboard(user_data: dict = None):
    """Generates standard or auto-rolling main keyboards."""
    # Check if auto-roll is active
    if user_data and user_data.get("is_rolling", False):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🛑 Stop Auto-Roll", callback_data="action_stop_auto")]
        ])
    
    keyboard = []
    
    # If auto-roll is enabled, show "Start Auto-Roll" button
    if user_data and user_data.get("auto_roll", False):
        keyboard.append([InlineKeyboardButton("🔄 Start Auto-Roll", callback_data="action_start_auto")])
    else:
        keyboard.append([InlineKeyboardButton("🎲 Roll Light", callback_data="action_roll")])
    
    keyboard.extend([
        [
            InlineKeyboardButton("🎒 Inventory", callback_data="action_inventory"),
            InlineKeyboardButton("📊 Stats", callback_data="action_stats")
        ],
        [
            InlineKeyboardButton("🔨 Craft", callback_data="action_craft"),
            InlineKeyboardButton("💎 Premium", callback_data="action_premium")
        ]
    ])
    
    # Check if user has active premium - add "See Premium" button
    if user_data:
        from database import get_premium_status
        premium_info = get_premium_status(user_data)
        if premium_info and premium_info.get("active"):
            keyboard.append([
                InlineKeyboardButton("⭐ See Premium", callback_data="view_premium_status"),
                InlineKeyboardButton("🏪 Shop", callback_data="action_shop")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("⚙️ Settings", callback_data="action_settings"),
                InlineKeyboardButton("🏪 Shop", callback_data="action_shop")
            ])
    else:
        keyboard.append([
            InlineKeyboardButton("⚙️ Settings", callback_data="action_settings"),
            InlineKeyboardButton("🏪 Shop", callback_data="action_shop")
        ])
    
    return InlineKeyboardMarkup(keyboard)

def get_settings_keyboard(user_data: dict):
    """Generates settings toggle buttons."""
    auto_status = "🟢 ON" if user_data["auto_roll"] else "🔴 OFF"

    keyboard = [
        [InlineKeyboardButton(f"Auto-Roll: {auto_status}", callback_data="toggle_auto")],
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_inventory_main_keyboard():
    """Main inventory selection keyboard."""
    keyboard = [
        [InlineKeyboardButton("✨ Lights", callback_data="inv_lights")],
        [InlineKeyboardButton("🎒 Gears & Items", callback_data="inv_gears")],
        [InlineKeyboardButton("🧪 Potions", callback_data="inv_potions")],
        [InlineKeyboardButton("⚔️ Equipment", callback_data="inv_equipment")],
        [InlineKeyboardButton("⬅️ Main Menu", callback_data="action_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_craft_keyboard():
    """Generates craft menu with all available gears."""
    keyboard = []
    for gear_name, gear_data in GEARS.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{gear_data['icon']} {gear_name} (Tier {gear_data['tier']})",
                callback_data=f"craft_{gear_name.replace(' ', '_')}"
            )
        ])
    keyboard.append([InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")])
    return InlineKeyboardMarkup(keyboard)

def get_equip_keyboard(user_data: dict):
    """Generates buttons for equipping owned Lights - DEPRECATED, kept for compatibility."""
    keyboard = []
    keyboard.append([InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")])
    return InlineKeyboardMarkup(keyboard)

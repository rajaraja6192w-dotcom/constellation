"""Equip command handlers"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import get_user_data, equip_light, equip_gear as db_equip_gear, update_activity
from config import LIGHTS, SPECIAL_LIGHTS, GEARS

async def equip_light_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Equips a light by command. Usage: /equip_light <light_name>"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    try:
        user_id = update.effective_user.id
        user_data = get_user_data(user_id)
        update_activity(user_data)
        
        back_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]
        ])
        
        if not context.args:
            await update.message.reply_text(
                "❌ <b>Usage:</b> /equip_light &lt;light_name&gt;\n\n"
                "Example: <code>/equip_light Uncommon</code> or <code>/equip_light mythical</code>",
                parse_mode="HTML",
                reply_markup=back_button
            )
            return
        
        # Join all arguments and convert to lowercase for case-insensitive matching
        light_name_input = " ".join(context.args).strip().lower()
        
        # Search in both regular and special lights
        all_lights = LIGHTS + SPECIAL_LIGHTS
        selected_light = next((a for a in all_lights if a["name"].lower() == light_name_input), None)
        
        if not selected_light:
            await update.message.reply_text(
                f"❌ Light '<b>{light_name_input}</b>' not found.\n\n"
                "Available lights: " + ", ".join([a["name"] for a in all_lights[:10]]) + "...",
                parse_mode="HTML",
                reply_markup=back_button
            )
            return
        
        # Check if user owns this light
        if selected_light["name"] not in user_data["inventory"] or user_data["inventory"][selected_light["name"]] == 0:
            await update.message.reply_text(
                f"❌ You don't own <b>{selected_light['name']}</b> yet!\n\n"
                "Roll to get this light first.",
                parse_mode="HTML",
                reply_markup=back_button
            )
            return
        
        # Equip the light
        equip_light(user_data, selected_light)
        await update.message.reply_text(
            f"✅ Successfully equipped {selected_light['icon']} <b>{selected_light['name']}</b> light!",
            parse_mode="HTML",
            reply_markup=back_button
        )
    except Exception as e:
        logging.error(f"Error in equip_light_command: {e}")
        try:
            await update.message.reply_text(
                "❌ An error occurred while equipping. Please try again.",
                reply_markup=back_button
            )
        except:
            pass

async def equip_gear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Equips a gear by command. Usage: /equip_gear <gear_name> <left|right>"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    try:
        user_id = update.effective_user.id
        user_data = get_user_data(user_id)
        update_activity(user_data)
        
        back_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]
        ])
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ <b>Usage:</b> /equip_gear &lt;gear_name&gt; &lt;left|right&gt;\n\n"
                "Examples:\n"
                "<code>/equip_gear jackpot left</code>\n"
                "<code>/equip_gear demon right</code>\n"
                "<code>/equip_gear clover left</code>",
                parse_mode="HTML",
                reply_markup=back_button
            )
            return
        
        # Get hand (last argument)
        hand = context.args[-1].lower()
        if hand not in ["left", "right"]:
            await update.message.reply_text(
                "❌ Invalid hand! Use <b>left</b> or <b>right</b>.",
                parse_mode="HTML",
                reply_markup=back_button
            )
            return
        
        # Get gear name (all args except last one)
        gear_name_input = " ".join(context.args[:-1]).strip().lower()
        
        # Find gear (case-insensitive, partial match)
        selected_gear = None
        for gear_name in GEARS.keys():
            if gear_name_input in gear_name.lower():
                selected_gear = gear_name
                break
        
        if not selected_gear:
            await update.message.reply_text(
                f"❌ Gear containing '<b>{gear_name_input}</b>' not found.\n\n"
                "Available gears: " + ", ".join(GEARS.keys()),
                parse_mode="HTML",
                reply_markup=back_button
            )
            return
        
        # Check if user owns this gear
        if selected_gear not in user_data["gear_inventory"] or user_data["gear_inventory"][selected_gear] == 0:
            await update.message.reply_text(
                f"❌ You don't own <b>{selected_gear}</b> yet!\n\n"
                "Use /craft to craft this gear.",
                parse_mode="HTML",
                reply_markup=back_button
            )
            return
        
        # Equip the gear
        hand_slot = "left_hand" if hand == "left" else "right_hand"
        db_equip_gear(user_data, selected_gear, hand_slot)
        
        gear_data = GEARS[selected_gear]
        await update.message.reply_text(
            f"✅ Successfully equipped {gear_data['icon']} <b>{selected_gear}</b> on <b>{hand.upper()}</b> hand!\n\n"
            f"Luck Bonus: +{gear_data['stats']['luck']}",
            parse_mode="HTML",
            reply_markup=back_button
        )
    except Exception as e:
        logging.error(f"Error in equip_gear_command: {e}")
        try:
            await update.message.reply_text(
                "❌ An error occurred while equipping gear. Please try again.",
                reply_markup=back_button
            )
        except:
            pass

async def unequip_gear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unequips a gear by command. Usage: /unequip_gear <left|right>"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from database import unequip_gear
    
    try:
        user_id = update.effective_user.id
        user_data = get_user_data(user_id)
        update_activity(user_data)
        
        back_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]
        ])
        
        if not context.args:
            await update.message.reply_text(
                "❌ <b>Usage:</b> /unequip_gear &lt;left|right&gt;\n\n"
                "Examples:\n"
                "<code>/unequip_gear left</code>\n"
                "<code>/unequip_gear right</code>",
                parse_mode="HTML",
                reply_markup=back_button
            )
            return
        
        # Get hand argument
        hand = context.args[0].lower()
        if hand not in ["left", "right"]:
            await update.message.reply_text(
                "❌ Invalid hand! Use <b>left</b> or <b>right</b>.",
                parse_mode="HTML",
                reply_markup=back_button
            )
            return
        
        # Unequip the gear
        hand_slot = "left_hand" if hand == "left" else "right_hand"
        success, result = unequip_gear(user_data, hand_slot)
        
        if success:
            gear_data = GEARS[result]
            await update.message.reply_text(
                f"✅ Successfully unequipped {gear_data['icon']} <b>{result}</b> from <b>{hand.upper()}</b> hand!\n\n"
                f"💡 You can equip it again anytime with /equip_gear",
                parse_mode="HTML",
                reply_markup=back_button
            )
        else:
            await update.message.reply_text(
                f"❌ {result}",
                parse_mode="HTML",
                reply_markup=back_button
            )
    except Exception as e:
        logging.error(f"Error in unequip_gear_command: {e}")
        try:
            await update.message.reply_text(
                "❌ An error occurred while unequipping gear. Please try again.",
                reply_markup=back_button
            )
        except:
            pass

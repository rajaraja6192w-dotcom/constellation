"""Achievement command handler"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_user_data, save_user_data
from config import ACHIEVEMENTS, POTIONS
from utils.achievement_manager import (
    get_claimable_achievements, 
    claim_achievement_reward, 
    check_achievement,
    format_achievement_requirement,
    calculate_achievement_progress
)

async def achievement_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /achievement command."""
    try:
        user_id = update.effective_user.id
        user_data = get_user_data(user_id)
        
        # Update activity
        from database import update_activity
        update_activity(user_data)
        user_data = get_user_data(user_id)
        
        # Check if claiming
        if context.args and len(context.args) > 0 and context.args[0].lower() == "claim":
            await claim_achievements(update, context)
            return
        
        # Default to page 1
        page = 1
        if context.args and len(context.args) > 0:
            try:
                page = int(context.args[0])
                if page < 1 or page > 5:
                    page = 1
            except:
                page = 1
        
        page_key = f"page_{page}"
        
        if page_key not in ACHIEVEMENTS:
            await update.message.reply_text("❌ Invalid page number. Use 1-5.")
            return
        
        page_data = ACHIEVEMENTS[page_key]
        claimed = user_data.get("achievements_claimed", [])
        
        text = f"{page_data['title']}\n"
        text += "="*35 + "\n\n"
        
        for ach_id, ach_data in page_data["achievements"].items():
            is_claimed = ach_id in claimed
            is_complete = check_achievement(user_data, ach_id, ach_data)
            
            status = ""
            if is_claimed:
                status = "✅"
            elif is_complete:
                status = "🎁"
            else:
                status = "🔒"
            
            text += f"{status} {ach_data['icon']} <b>{ach_data['name']}</b>\n"
            text += f"   └ {ach_data['description']}\n"
            
            if not is_claimed:
                progress = format_achievement_requirement(ach_data, user_data)
                text += f"   └ {progress}\n"
            
            # Show reward
            reward = ach_data.get("reward", {})
            reward_text = []
            if "coins" in reward:
                reward_text.append(f"💰 {reward['coins']:,}")
            if "potions" in reward:
                for potion_id, amount in reward["potions"].items():
                    potion = POTIONS.get(potion_id, {})
                    icon = potion.get("icon", "🧪")
                    reward_text.append(f"{icon} x{amount}")
            
            if reward_text:
                text += f"   └ Reward: {', '.join(reward_text)}\n"
            
            text += "\n"
        
        text += "="*35 + "\n"
        
        # Show progress for page 5
        if page == 5:
            progress = calculate_achievement_progress(user_data)
            rolls = user_data.get("total_rolls", 0)
            text += f"\n📊 <b>Progress:</b> {progress:.1f}% | Rolls: {rolls:,}/10,000\n"
        
        # Check for claimable achievements
        claimable = get_claimable_achievements(user_data)
        claimable_count = len(claimable)
        
        if claimable_count > 0:
            text += f"\n🎁 <b>{claimable_count} achievement(s) ready to claim!</b>\n"
            text += "Use <code>/achievement claim</code> to claim all!\n"
        
        # Navigation
        text += f"\n📄 Page {page}/5"
        text += "\n💡 <code>/achievement &lt;1-5&gt;</code> - View page"
        
        keyboard = [[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]]
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        
    except Exception as e:
        logging.error(f"Error in achievement_command: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text(
            "❌ An error occurred. Please try again.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]])
        )

async def claim_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Claim all available achievements."""
    try:
        user_id = update.effective_user.id
        user_data = get_user_data(user_id)
        
        # Update activity
        from database import update_activity
        update_activity(user_data)
        user_data = get_user_data(user_id)
        
        claimable = get_claimable_achievements(user_data)
        
        if not claimable:
            text = "❌ No achievements to claim right now!\n\n"
            text += "<i>Complete more achievements to earn rewards.</i>"
            keyboard = [[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]]
            await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        # Initialize claimed list if not exists
        if "achievements_claimed" not in user_data:
            user_data["achievements_claimed"] = []
        
        total_coins = 0
        total_potions = {}
        claimed_names = []
        
        for page_key, ach_id, ach_data in claimable:
            # Claim reward
            reward_summary = claim_achievement_reward(user_data, ach_data)
            
            # Track for summary
            if "coins" in reward_summary:
                total_coins += reward_summary["coins"]
            if "potions" in reward_summary:
                for potion_id, amount in reward_summary["potions"].items():
                    total_potions[potion_id] = total_potions.get(potion_id, 0) + amount
            
            # Mark as claimed
            user_data["achievements_claimed"].append(ach_id)
            claimed_names.append(f"{ach_data['icon']} {ach_data['name']}")
        
        # Save
        save_user_data(user_data)
        
        # Build response
        text = "🎉 <b>ACHIEVEMENTS CLAIMED!</b> 🎉\n"
        text += "="*35 + "\n\n"
        
        for name in claimed_names:
            text += f"✅ {name}\n"
        
        text += "\n" + "="*35 + "\n"
        text += "<b>📦 REWARDS RECEIVED:</b>\n\n"
        
        if total_coins > 0:
            text += f"💰 <b>{total_coins:,} Coins</b>\n"
        
        for potion_id, amount in total_potions.items():
            potion = POTIONS.get(potion_id, {})
            icon = potion.get("icon", "🧪")
            name = potion.get("name", potion_id)
            text += f"{icon} <b>{name}</b> x{amount}\n"
        
        text += "\n<i>Congratulations! Keep progressing!</i>"
        
        keyboard = [[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]]
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        
    except Exception as e:
        logging.error(f"Error in claim_achievements: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text(
            "❌ An error occurred. Please try again.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]])
        )

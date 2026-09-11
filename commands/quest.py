"""Daily quest command handler"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_user_data, save_user_data
from config import POTIONS, DAILY_QUESTS_DATA
from utils.quest_manager import (
    should_reset_daily_quests,
    reset_daily_quests,
    check_quest_completion,
    get_quest_progress,
    claim_quest_reward,
    claim_completion_reward,
    update_playtime,
    get_time_until_reset
)

async def quest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /quest command."""
    try:
        user_id = update.effective_user.id
        user_data = get_user_data(user_id)
        
        # Update activity
        from database import update_activity
        update_activity(user_data)
        user_data = get_user_data(user_id)
        
        # Check if claiming
        if context.args and len(context.args) > 0 and context.args[0].lower() == "claim":
            await claim_quests(update, context)
            return
        
        # Update playtime before checking
        update_playtime(user_data)
        
        # Check if needs reset
        if should_reset_daily_quests(user_data):
            reset_daily_quests(user_data)
            save_user_data(user_data)
        
        quest_data = user_data.get("daily_quests", {})
        quests = quest_data.get("quests", [])
        completed = quest_data.get("completed", [])
        claimed_completion = quest_data.get("claimed_completion_reward", False)
        
        if not quests:
            # Initialize if somehow missing
            reset_daily_quests(user_data)
            save_user_data(user_data)
            quest_data = user_data.get("daily_quests", {})
            quests = quest_data.get("quests", [])
            completed = quest_data.get("completed", [])
        
        text = "📋 <b>DAILY QUESTS</b> 📋\n"
        text += "="*35 + "\n\n"
        
        all_complete = True
        
        for idx, quest in enumerate(quests):
            quest_id = quest["id"]
            is_completed = check_quest_completion(user_data, quest)
            is_claimed = quest_id in completed
            
            if not is_completed:
                all_complete = False
            
            # Status icon
            if is_claimed:
                status = "✅"
            elif is_completed:
                status = "🎁"
            else:
                status = "⏳"
                all_complete = False
            
            text += f"{status} {quest['icon']} <b>{quest['name']}</b>\n"
            text += f"   └ {quest['description']}\n"
            
            if not is_claimed:
                progress = get_quest_progress(user_data, quest)
                text += f"   └ Progress: {progress}\n"
            
            # Show reward
            reward = quest.get("reward", {})
            reward_text = []
            if "coins" in reward:
                coins_range = reward["coins"]
                if isinstance(coins_range, list):
                    reward_text.append(f"💰 {coins_range[0]}-{coins_range[1]}")
                else:
                    reward_text.append(f"💰 {coins_range}")
            if "potions" in reward:
                for potion_id, amount in reward["potions"].items():
                    potion = POTIONS.get(potion_id, {})
                    icon = potion.get("icon", "🧪")
                    reward_text.append(f"{icon} x{amount}")
            
            if reward_text and not is_claimed:
                text += f"   └ Reward: {', '.join(reward_text)}\n"
            
            text += "\n"
        
        text += "="*35 + "\n"
        
        # Show time until reset
        time_until_reset = get_time_until_reset()
        text += f"\n🕐 <b>Reset in:</b> {time_until_reset}\n"
        
        # Completion reward
        if all_complete and not claimed_completion:
            text += "\n🎉 <b>ALL QUESTS COMPLETE!</b> 🎉\n"
            text += "Claim your completion bonus:\n\n"
            
            completion_data = DAILY_QUESTS_DATA["completion_reward"]
            reward = completion_data["reward"]
            
            text += "🏆 <b>Completion Bonus:</b>\n"
            if "coins" in reward:
                coins_range = reward["coins"]
                text += f"   💰 {coins_range[0]:,}-{coins_range[1]:,} Coins\n"
            if "potions" in reward:
                for potion_id, amount in reward["potions"].items():
                    potion = POTIONS.get(potion_id, {})
                    icon = potion.get("icon", "🧪")
                    name = potion.get("name", potion_id)
                    text += f"   {icon} {name} x{amount}\n"
            if "effect" in reward:
                effect = reward["effect"]
                text += f"   {effect['icon']} {effect['name']} (+{effect['amount']}% luck for 24h)\n"
            
            text += "\nUse <code>/quest claim</code> to claim all rewards!\n"
        
        elif claimed_completion:
            text += "\n✅ <b>Daily quests completed!</b>\n"
            text += "<i>Come back tomorrow for new quests.</i>\n"
        
        else:
            completed_count = len([q for q in quests if check_quest_completion(user_data, q)])
            text += f"\n📊 Progress: {completed_count}/4 quests completed\n"
            text += "<i>Complete quests to earn rewards!</i>\n"
        
        text += "\n💡 <code>/quest claim</code> - Claim completed quest rewards"
        
        keyboard = [[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]]
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        
    except Exception as e:
        logging.error(f"Error in quest_command: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text(
            "❌ An error occurred. Please try again.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]])
        )

async def claim_quests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Claim completed quest rewards."""
    try:
        user_id = update.effective_user.id
        user_data = get_user_data(user_id)
        
        # Update activity
        from database import update_activity
        update_activity(user_data)
        user_data = get_user_data(user_id)
        
        # Update playtime
        update_playtime(user_data)
        
        # Check if needs reset
        if should_reset_daily_quests(user_data):
            reset_daily_quests(user_data)
            save_user_data(user_data)
        
        quest_data = user_data.get("daily_quests", {})
        quests = quest_data.get("quests", [])
        completed = quest_data.get("completed", [])
        claimed_completion = quest_data.get("claimed_completion_reward", False)
        
        # Find claimable quests
        claimable = []
        for quest in quests:
            quest_id = quest["id"]
            if quest_id not in completed and check_quest_completion(user_data, quest):
                claimable.append(quest)
        
        if not claimable and claimed_completion:
            text = "❌ No quests to claim!\n\n"
            text += "<i>You've already claimed all rewards for today.</i>"
            keyboard = [[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]]
            await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        total_coins = 0
        total_potions = {}
        claimed_names = []
        
        # Claim individual quest rewards
        for quest in claimable:
            reward_summary = claim_quest_reward(user_data, quest)
            
            if "coins" in reward_summary:
                total_coins += reward_summary["coins"]
            if "potions" in reward_summary:
                for potion_id, amount in reward_summary["potions"].items():
                    total_potions[potion_id] = total_potions.get(potion_id, 0) + amount
            
            # Mark as completed
            quest_data["completed"].append(quest["id"])
            claimed_names.append(f"{quest['icon']} {quest['name']}")
        
        # Check if all 4 complete and not claimed completion reward
        all_complete = len(quest_data["completed"]) >= 4
        completion_reward_summary = None
        
        if all_complete and not claimed_completion:
            completion_reward_summary = claim_completion_reward(user_data)
            quest_data["claimed_completion_reward"] = True
            
            if "coins" in completion_reward_summary:
                total_coins += completion_reward_summary["coins"]
            if "potions" in completion_reward_summary:
                for potion_id, amount in completion_reward_summary["potions"].items():
                    total_potions[potion_id] = total_potions.get(potion_id, 0) + amount
        
        # Save
        user_data["daily_quests"] = quest_data
        save_user_data(user_data)
        
        # Build response
        text = "🎉 <b>QUEST REWARDS CLAIMED!</b> 🎉\n"
        text += "="*35 + "\n\n"
        
        if claimed_names:
            text += "<b>✅ Completed Quests:</b>\n"
            for name in claimed_names:
                text += f"  • {name}\n"
            text += "\n"
        
        text += "<b>📦 REWARDS RECEIVED:</b>\n\n"
        
        if total_coins > 0:
            text += f"💰 <b>{total_coins:,} Coins</b>\n"
        
        for potion_id, amount in total_potions.items():
            potion = POTIONS.get(potion_id, {})
            icon = potion.get("icon", "🧪")
            name = potion.get("name", potion_id)
            text += f"{icon} <b>{name}</b> x{amount}\n"
        
        if completion_reward_summary and "effect" in completion_reward_summary:
            effect = completion_reward_summary["effect"]
            text += f"\n✨ <b>DAILY BLESSING ACTIVATED!</b>\n"
            text += f"   {effect['icon']} +{effect['amount']}% luck for 24 hours!\n"
        
        text += "\n<i>Great job! Come back tomorrow for more quests!</i>"
        
        keyboard = [[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]]
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        
    except Exception as e:
        logging.error(f"Error in claim_quests: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text(
            "❌ An error occurred. Please try again.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="action_main")]])
        )

"""Help command - Complete guide to all commands"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_user_data, update_activity

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display comprehensive help information."""
    try:
        user_id = update.effective_user.id
        user_data = get_user_data(user_id)
        update_activity(user_data)
        
        # Check server membership
        from utils.server_check import check_server_membership
        if not await check_server_membership(update, user_data):
            return
        
        text = (
            "📖 <b>CONSTELLATION RNG - COMMAND GUIDE</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            "🎮 <b>BASIC COMMANDS</b>\n"
            "• <b>/start</b> - Start bot & view main menu\n"
            "• <b>/roll</b> - Same as /start (quick access)\n"
            "• <b>/help</b> - Show this help guide\n\n"
            
            "🌐 <b>SERVER COMMANDS</b>\n"
            "• <b>/play</b> - Select or join a server (10 servers available)\n"
            "• <b>/changeserver</b> - Switch to a different server\n"
            "• <b>/serverinfo</b> - View current server information\n\n"
            
            "🎲 <b>ROLLING & INVENTORY</b>\n"
            "• <b>Roll Button</b> - Roll for rare Lights (3s cooldown)\n"
            "• <b>Auto-Roll</b> - Enable/disable automatic rolling\n"
            "• <b>Inventory</b> - View your Light collection\n"
            "• <b>/discard [light_name]</b> - Remove unwanted light\n"
            "• <b>/autodiscard [rarity]</b> - Auto-discard lights below rarity\n"
            "   Example: /autodiscard 1000 (discards ≤1 in 1000)\n\n"
            
            "🔨 <b>CRAFTING & GEAR</b>\n"
            "• <b>/craft</b> - Open crafting menu\n"
            "• <b>Craft Gear</b> - Combine lights into powerful gears\n"
            "• <b>Auto-Craft</b> - Enable/disable automatic crafting\n"
            "• <b>/equip_gear [gear_name]</b> - Equip gear for luck bonus\n"
            "• <b>/unequip_gear [slot]</b> - Remove gear from slot\n"
            "   Slots: left_hand, right_hand\n"
            "• <b>/equip_light [light_name]</b> - Showcase a light\n\n"
            
            "🧪 <b>POTIONS</b>\n"
            "• <b>/use [potion_name]</b> - Use a luck potion\n"
            "• <b>Potion Types</b>:\n"
            "   - Angelic: +25% luck (10 min)\n"
            "   - Divine: +50% luck (15 min)\n"
            "   - Mythical: +75% luck (20 min)\n"
            "   - Celestial: +100% luck (30 min)\n"
            "   - Ethereal: +150% luck (45 min)\n"
            "   - Null: Unlock Anomaly light (1 use)\n\n"
            
            "💰 <b>SHOP & ECONOMY</b>\n"
            "• <b>/buy</b> - Open shop menu\n"
            "• <b>Buy Coins</b> - Purchase coins with real money\n"
            "• <b>Buy Potions</b> - Purchase luck potions\n"
            "• <b>Premium Discount</b> - Pro members get 30% off!\n\n"
            
            "💎 <b>PREMIUM SUBSCRIPTION</b>\n"
            "• <b>/premium</b> - View premium plans\n"
            "• <b>Basic ($1.99/mo)</b>:\n"
            "   - 100k coins/month\n"
            "   - 150 luck potions/month\n"
            "   - +250% permanent luck\n"
            "   - 2x coins & exp\n"
            "   - Auto-roll permanent\n"
            "• <b>Pro ($3.99/mo)</b>:\n"
            "   - 200k coins/month (2x Basic)\n"
            "   - 300 luck potions/month (2x Basic)\n"
            "   - +500% permanent luck (2x Basic)\n"
            "   - 2x coins & exp\n"
            "   - 3 Exclusive Lights (get 2 random)\n"
            "   - 30% shop discount\n"
            "   - Light preview access\n\n"
            
            "🏆 <b>PROGRESSION</b>\n"
            "• <b>/leaderboard</b> - View server rankings\n"
            "   - Level, Coins, Playtime, Rolls\n"
            "• <b>/achievement</b> - Check your achievements\n"
            "• <b>/quest</b> - View daily quests\n"
            "• <b>Profile</b> - View your stats & progress\n\n"
            
            "🌍 <b>WORLD SYSTEM</b>\n"
            "• <b>Weather</b> - 6 types, each gives luck bonus\n"
            "• <b>Events</b> - Special events with huge bonuses:\n"
            "   - Normal (0% bonus)\n"
            "   - Eclipse (50% bonus, Eclipse light)\n"
            "   - Meteor Fall (100% bonus, Burnt effect)\n"
            "   - Thunder Wrath (300% bonus)\n"
            "   - None Event (1500% bonus, Anomaly chance)\n"
            "   - Heaven Approach (2000% bonus, Exclusive lights)\n"
            "   - Poseidon Fury (800% bonus, Kraken/Whale)\n"
            "• <b>Time Periods</b>:\n"
            "   - Night: Moonlight exclusive (+25%)\n"
            "   - Morning: Sunrise exclusive (+25%)\n\n"
            
            "✨ <b>EXCLUSIVE LIGHTS (PRO ONLY)</b>\n"
            "• 🌆 <b>Cybernight</b> - 1 in Exclusive\n"
            "• 🎸 <b>O'Sound</b> - 1 in Exclusive\n"
            "• 🎻 <b>Remembrance</b> - 1 in Exclusive\n"
            "• Drops during Heaven Approach (0.5%, 15% rate)\n"
            "• Get 2 random on Pro purchase!\n\n"
            
            "📊 <b>STATS & INFO</b>\n"
            "• <b>Total Lights</b>: 117+ (including specials)\n"
            "• <b>Gears</b>: 5 craftable tiers\n"
            "• <b>Potions</b>: 6 types + Null (drop-only)\n"
            "• <b>Achievements</b>: 28+ unlockable\n"
            "• <b>Daily Quests</b>: 5 active quests\n"
            "• <b>Servers</b>: 10 servers (100 players each)\n\n"
            
            "💡 <b>PRO TIPS</b>\n"
            "• Use potions during rare events for max luck\n"
            "• Auto-craft saves lights for gear recipes\n"
            "• Higher luck = better rare light chances\n"
            "• Join friends on same server for competitions\n"
            "• Premium auto-roll never stops rolling!\n"
            "• Pro exclusive lights only drop in Heaven Approach\n\n"
            
            "📞 <b>NEED HELP?</b>\n"
            "Contact admin: @YourAdminUsername\n"
            "Support group: [Link]\n"
            "Updates channel: [Link]\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌟 <b>Good luck rolling!</b> 🌟"
        )
        
        keyboard = [
            [InlineKeyboardButton("💎 Premium Plans", callback_data="action_premium")],
            [InlineKeyboardButton("🎮 Back to Main", callback_data="action_main")]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logging.error(f"Error in help_command: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text("❌ An error occurred. Please try again.")

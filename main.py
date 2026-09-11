"""
Constellation RNG Bot - Main Entry Point
A modular Telegram bot for rolling rare lights and crafting gear
"""

import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler

# Import configuration
from config import BOT_TOKEN

# Import command handlers
from commands.start import start_command
from commands.craft import craft_command
from commands.equip import equip_light_command, equip_gear_command, unequip_gear_command
from commands.use_potion import use_potion_command
from commands.shop import buy_command
from commands.leaderboard import leaderboard_command
from commands.achievement import achievement_command
from commands.quest import quest_command
from commands.discard import discard_command, autodiscard_command
from commands.server import play_command, changeserver_command, server_info_command
from commands.help import help_command
from commands.premium import premium_command

# Import callback handler
from handlers.callbacks import button_callback

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    """Main function to start the bot"""
    # Build application
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Register command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("roll", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("premium", premium_command))
    app.add_handler(CommandHandler("craft", craft_command))
    app.add_handler(CommandHandler("equip_light", equip_light_command))
    app.add_handler(CommandHandler("equip_gear", equip_gear_command))
    app.add_handler(CommandHandler("unequip_gear", unequip_gear_command))
    app.add_handler(CommandHandler("use", use_potion_command))
    app.add_handler(CommandHandler("buy", buy_command))
    app.add_handler(CommandHandler("leaderboard", leaderboard_command))
    app.add_handler(CommandHandler("achievement", achievement_command))
    app.add_handler(CommandHandler("quest", quest_command))
    app.add_handler(CommandHandler("discard", discard_command))
    app.add_handler(CommandHandler("autodiscard", autodiscard_command))
    app.add_handler(CommandHandler("play", play_command))
    app.add_handler(CommandHandler("changeserver", changeserver_command))
    app.add_handler(CommandHandler("serverinfo", server_info_command))
    
    # Register callback handler
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # Start bot
    print("⚡ Constellation RNG Bot V1.3.3 is live...")
    print("=" * 50)
    print("📊 Total Lights: 102 (3 Exclusive + 15 New!)")
    print("🔨 Total Gears: 8 (2 New Tier 1!)")
    print("🧪 Total Potions: 6 (Null Potion drop-only)")
    print("🏆 Achievements: 28+")
    print("📋 Daily Quests: Active")
    print("🌦️ Weather System: 6 types")
    print("🌍 Event System: 7 types (Poseidon Fury NEW!)")
    print("🌅 Time Periods: 2 (Night/Morning)")
    print("👾 Null Potion: 0.1% drop chance")
    print("🔥 Burnt Effect: 1% during Meteor Fall")
    print("✨ Heaven Approach: 0.5% event (Exclusive lights!)")
    print("🌊 Poseidon Fury: 2% event (Kraken & Whale!)")
    print("💎 Premium System: Basic & Pro tiers")
    print("🗑️ Auto-Discard: Threshold system")
    print("🎨 Auto-Craft: Reserve & Priority system")
    print("🌐 Server System: 10 servers (100 players each)")
    print("=" * 50)
    print("🎮 Ready to roll with multi-server system!")
    print("📖 Use /play to select your server")
    print("📊 Use /leaderboard to see rankings")
    print("💎 Use /premium to see subscription plans")
    
    app.run_polling()

if __name__ == '__main__':
    main()

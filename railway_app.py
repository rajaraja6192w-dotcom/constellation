"""
Railway deployment app - Combines bot and webhook in one process
"""

import os
import logging
import asyncio
from threading import Thread
from flask import Flask, request, jsonify
import json
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# Import bot components
from config import BOT_TOKEN
from database import get_user_data, activate_premium, claim_monthly_premium_rewards

# Import commands individually (MATCHING main.py EXACTLY)
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

# Import callback handler (MATCHING main.py EXACTLY)
from handlers.callbacks import button_callback

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask app for Ko-fi webhook
app = Flask(__name__)

# Store bot instance globally
bot_instance = None
telegram_app = None

@app.route('/kofi-webhook', methods=['POST'])
def kofi_webhook():
    """Handle Ko-fi webhook for subscription payments."""
    try:
        # Get form data
        data_str = request.form.get('data')
        
        if not data_str:
            logger.error("No data field in webhook")
            return jsonify({"status": "error", "message": "No data"}), 400
        
        # Parse JSON data
        data = json.loads(data_str)
        
        # Log webhook data for debugging
        logger.info(f"Ko-fi Webhook received: {data}")
        
        # Extract important fields
        payment_type = data.get('type')
        is_subscription = data.get('is_subscription_payment', False)
        is_first_payment = data.get('is_first_subscription_payment', False)
        tier_name = data.get('tier_name', '')
        message_id = data.get('message_id', '')
        
        # Extract Telegram ID from message
        message = data.get('message', '')
        telegram_id = None
        
        if 'telegram_id:' in message.lower():
            try:
                parts = message.lower().split('telegram_id:')
                id_part = parts[1].strip().split()[0]
                telegram_id = int(id_part)
            except:
                pass
        
        # Also check from_name for ID
        from_name = data.get('from_name', '')
        if telegram_id is None and from_name.isdigit():
            telegram_id = int(from_name)
        
        if telegram_id is None:
            logger.error(f"Could not extract Telegram ID from webhook data")
            return jsonify({
                "status": "error", 
                "message": "Telegram ID not found in message"
            }), 200
        
        # Process subscription payment
        if is_subscription and tier_name:
            # Determine tier (basic or pro)
            tier = None
            if 'basic' in tier_name.lower():
                tier = 'basic'
            elif 'pro' in tier_name.lower():
                tier = 'pro'
            
            if tier is None:
                logger.error(f"Unknown tier name: {tier_name}")
                return jsonify({"status": "error", "message": "Unknown tier"}), 200
            
            # Get user data
            user_data = get_user_data(telegram_id)
            
            if user_data is None:
                logger.error(f"User {telegram_id} not found in database")
                return jsonify({"status": "error", "message": "User not found"}), 200
            
            # Activate premium
            success = activate_premium(user_data, tier, 30)
            
            if not success:
                logger.error(f"Failed to activate premium for user {telegram_id}")
                return jsonify({"status": "error", "message": "Activation failed"}), 200
            
            # Claim monthly rewards
            rewards = claim_monthly_premium_rewards(user_data)
            
            # Send notification to user (using asyncio in thread)
            tier_display = "Constellation | Basic" if tier == "basic" else "Constellation | Pro"
            icon = "🌟" if tier == "basic" else "⭐"
            
            notification = (
                f"{icon} <b>PREMIUM ACTIVATED!</b> {icon}\n\n"
                f"Your <b>{tier_display}</b> subscription is now active!\n\n"
                f"<b>🎁 Welcome Rewards:</b>\n"
            )
            
            if rewards.get('success'):
                notification += (
                    f"• 💰 <b>{rewards['coins']:,} Coins</b>\n"
                    f"• 🧪 <b>{rewards['potions']} Luck Potions</b>\n"
                )
            
            notification += "\n<b>✨ Your Premium Benefits:</b>\n"
            
            if tier == "basic":
                notification += (
                    "• 🔄 Permanent Auto-Roll\n"
                    "• 💰 100k Coins/month\n"
                    "• 🧪 150 Luck Potions/month\n"
                    "• 🍀 +250% Permanent Luck\n"
                    "• 💎 2x Coins & EXP\n"
                )
            else:
                notification += (
                    "• 🔄 Permanent Auto-Roll\n"
                    "• 💰 200k Coins/month (2x Basic!)\n"
                    "• 🧪 300 Luck Potions/month (2x Basic!)\n"
                    "• 🍀 +500% Permanent Luck (2x Basic!)\n"
                    "• 💎 2x Coins & EXP\n"
                    "• ✨ 2 Random Exclusive Lights\n"
                    "• 🔮 Light Preview Access\n"
                    "• 💸 30% Shop Discount\n"
                )
            
            notification += (
                "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "💡 Your premium is active for <b>30 days</b>\n"
                "Use /premium to check your status anytime!\n\n"
                "🌟 <b>Thank you for supporting Constellation!</b> 🌟"
            )
            
            # Send notification asynchronously
            try:
                asyncio.run_coroutine_threadsafe(
                    bot_instance.send_message(
                        chat_id=telegram_id,
                        text=notification,
                        parse_mode='HTML'
                    ),
                    telegram_app.bot._async_runner.loop
                )
                logger.info(f"Premium notification sent to user {telegram_id}")
            except Exception as e:
                logger.error(f"Failed to send notification to {telegram_id}: {e}")
            
            return jsonify({
                "status": "success",
                "message": f"Premium {tier} activated for user {telegram_id}",
                "tier": tier,
                "telegram_id": telegram_id,
                "first_payment": is_first_payment
            }), 200
        
        return jsonify({"status": "success", "message": "Webhook received"}), 200
        
    except Exception as e:
        logger.error(f"Error processing Ko-fi webhook: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "bot": "running" if telegram_app and telegram_app.running else "stopped"
    }), 200

@app.route('/', methods=['GET'])
def home():
    """Root endpoint."""
    return jsonify({
        "name": "Constellation RNG Bot",
        "version": "1.3.4",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "webhook": "/kofi-webhook"
        }
    }), 200

def run_bot():
    """Run Telegram bot in background."""
    global bot_instance, telegram_app
    
    try:
        # Create application
        telegram_app = Application.builder().token(BOT_TOKEN).build()
        bot_instance = telegram_app.bot
        
        # Register command handlers (matching main.py exactly)
        telegram_app.add_handler(CommandHandler("start", start_command))
        telegram_app.add_handler(CommandHandler("roll", start_command))  # roll uses start_command
        telegram_app.add_handler(CommandHandler("help", help_command))
        telegram_app.add_handler(CommandHandler("premium", premium_command))
        telegram_app.add_handler(CommandHandler("craft", craft_command))
        telegram_app.add_handler(CommandHandler("equip_light", equip_light_command))
        telegram_app.add_handler(CommandHandler("equip_gear", equip_gear_command))
        telegram_app.add_handler(CommandHandler("unequip_gear", unequip_gear_command))
        telegram_app.add_handler(CommandHandler("use", use_potion_command))
        telegram_app.add_handler(CommandHandler("buy", buy_command))
        telegram_app.add_handler(CommandHandler("leaderboard", leaderboard_command))
        telegram_app.add_handler(CommandHandler("achievement", achievement_command))
        telegram_app.add_handler(CommandHandler("quest", quest_command))
        telegram_app.add_handler(CommandHandler("discard", discard_command))
        telegram_app.add_handler(CommandHandler("autodiscard", autodiscard_command))
        telegram_app.add_handler(CommandHandler("play", play_command))
        telegram_app.add_handler(CommandHandler("changeserver", changeserver_command))
        telegram_app.add_handler(CommandHandler("serverinfo", server_info_command))
        
        # Register callback handler (MATCHING main.py EXACTLY)
        telegram_app.add_handler(CallbackQueryHandler(button_callback))
        
        logger.info("🤖 Bot started successfully!")
        
        # Run polling
        telegram_app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        import traceback
        traceback.print_exc()

# Start bot thread immediately when module loads (for Gunicorn)
logger.info("🚀 Initializing bot thread...")
bot_thread = Thread(target=run_bot, daemon=True)
bot_thread.start()
logger.info("✅ Bot thread started!")

if __name__ == '__main__':
    # Start bot in background thread
    bot_thread = Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Run Flask app
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🌐 Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port)

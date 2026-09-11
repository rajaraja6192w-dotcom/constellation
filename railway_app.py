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
from commands import start, premium, shop, leaderboard, achievement, quest, help_command, server, craft, equip, discard, use_potion
from handlers.callbacks import button_handler
from handlers.server_callbacks import server_button_handler

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
        
        # Register command handlers
        telegram_app.add_handler(CommandHandler("start", start.start))
        telegram_app.add_handler(CommandHandler("stats", start.stats))
        telegram_app.add_handler(CommandHandler("inventory", start.inventory))
        telegram_app.add_handler(CommandHandler("roll", start.roll))
        telegram_app.add_handler(CommandHandler("premium", premium.premium_command))
        telegram_app.add_handler(CommandHandler("shop", shop.shop_command))
        telegram_app.add_handler(CommandHandler("buy", shop.buy_command))
        telegram_app.add_handler(CommandHandler("leaderboard", leaderboard.leaderboard_command))
        telegram_app.add_handler(CommandHandler("achievement", achievement.achievement_command))
        telegram_app.add_handler(CommandHandler("quest", quest.quest_command))
        telegram_app.add_handler(CommandHandler("help", help_command.help_command))
        telegram_app.add_handler(CommandHandler("server", server.server_command))
        telegram_app.add_handler(CommandHandler("craft", craft.craft_command))
        telegram_app.add_handler(CommandHandler("equip", equip.equip_command))
        telegram_app.add_handler(CommandHandler("discard", discard.discard_command))
        telegram_app.add_handler(CommandHandler("use_potion", use_potion.use_potion_command))
        
        # Register callback handlers
        telegram_app.add_handler(CallbackQueryHandler(button_handler, pattern=r'^(action|craft|inv|gear|toggle|roll|buy|use|view|renew)'))
        telegram_app.add_handler(CallbackQueryHandler(server_button_handler, pattern=r'^server_'))
        
        logger.info("🤖 Bot started successfully!")
        
        # Run polling
        telegram_app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # Start bot in background thread
    bot_thread = Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Run Flask app
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🌐 Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port)

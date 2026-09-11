"""Ko-fi Webhook Handler for Premium Subscriptions"""

import json
import logging
from flask import Flask, request, jsonify
from telegram import Bot
from database import get_user_data, activate_premium, claim_monthly_premium_rewards
from config import BOT_TOKEN

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

@app.route('/kofi-webhook', methods=['POST'])
async def kofi_webhook():
    """Handle Ko-fi webhook for subscription payments."""
    try:
        # Get form data
        data_str = request.form.get('data')
        
        if not data_str:
            logging.error("No data field in webhook")
            return jsonify({"status": "error", "message": "No data"}), 400
        
        # Parse JSON data
        data = json.loads(data_str)
        
        # Log webhook data for debugging
        logging.info(f"Ko-fi Webhook received: {data}")
        
        # Extract important fields
        payment_type = data.get('type')  # Tip, Subscription, Commission, Shop Order
        is_subscription = data.get('is_subscription_payment', False)
        is_first_payment = data.get('is_first_subscription_payment', False)
        tier_name = data.get('tier_name', '')
        message_id = data.get('message_id', '')
        
        # Extract user info from message or email
        # Ko-fi doesn't send Telegram ID directly, so we need user to include it
        # Users should include their Telegram ID in the message/note
        message = data.get('message', '')
        
        # Try to extract Telegram ID from message
        telegram_id = None
        if 'telegram_id:' in message.lower():
            try:
                # Format: "telegram_id: 123456789" or similar
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
            logging.error(f"Could not extract Telegram ID from webhook data")
            # Still return 200 to acknowledge receipt
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
                logging.error(f"Unknown tier name: {tier_name}")
                return jsonify({"status": "error", "message": "Unknown tier"}), 200
            
            # Get user data
            user_data = get_user_data(telegram_id)
            
            if user_data is None:
                logging.error(f"User {telegram_id} not found in database")
                return jsonify({"status": "error", "message": "User not found"}), 200
            
            # Activate premium
            success = activate_premium(user_data, tier, 30)  # 30 days
            
            if not success:
                logging.error(f"Failed to activate premium for user {telegram_id}")
                return jsonify({"status": "error", "message": "Activation failed"}), 200
            
            # Claim monthly rewards
            rewards = claim_monthly_premium_rewards(user_data)
            
            # Send notification to user
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
            
            notification += (
                "\n<b>✨ Your Premium Benefits:</b>\n"
            )
            
            if tier == "basic":
                notification += (
                    "• 🔄 Permanent Auto-Roll\n"
                    "• 💰 100k Coins/month\n"
                    "• 🧪 150 Luck Potions/month\n"
                    "• 🍀 +250% Permanent Luck\n"
                    "• 💎 2x Coins & EXP\n"
                )
            else:  # pro
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
            
            try:
                await bot.send_message(
                    chat_id=telegram_id,
                    text=notification,
                    parse_mode='HTML'
                )
                logging.info(f"Premium notification sent to user {telegram_id}")
            except Exception as e:
                logging.error(f"Failed to send notification to {telegram_id}: {e}")
            
            # Return 200 to confirm receipt
            return jsonify({
                "status": "success",
                "message": f"Premium {tier} activated for user {telegram_id}",
                "tier": tier,
                "telegram_id": telegram_id,
                "first_payment": is_first_payment
            }), 200
        
        # For other payment types, just acknowledge
        return jsonify({"status": "success", "message": "Webhook received"}), 200
        
    except Exception as e:
        logging.error(f"Error processing Ko-fi webhook: {e}")
        import traceback
        traceback.print_exc()
        # Still return 200 to acknowledge receipt
        return jsonify({"status": "error", "message": str(e)}), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    # Run webhook server
    app.run(host='0.0.0.0', port=5000)

"""Premium subscription command handler"""

import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Load premium tiers with UTF-8 encoding
with open("data/premium_tiers.json", "r", encoding="utf-8") as f:
    PREMIUM_TIERS = json.load(f)

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display premium subscription information."""
    try:
        user_id = update.effective_user.id
        
        # Determine if this is from command or callback
        is_callback = update.callback_query is not None
        message = update.callback_query.message if is_callback else update.message
        
        # Update activity
        from database import get_user_data, update_activity, get_premium_status
        user_data = get_user_data(user_id)
        update_activity(user_data)
        
        # Get current premium status
        premium_info = get_premium_status(user_data)
        
        # Build premium info text
        text = (
            "💎 <b>CONSTELLATION PREMIUM</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        
        # Show current status
        if premium_info and premium_info.get("active"):
            tier = premium_info.get("tier", "none")
            days_left = premium_info.get("days_left", 0)
            
            tier_data = PREMIUM_TIERS.get(tier, {})
            tier_name = tier_data.get("name", "Unknown")
            tier_icon = tier_data.get("icon", "⭐")
            
            text += (
                f"{tier_icon} <b>Current Status: ACTIVE</b>\n"
                f"• <b>Tier:</b> {tier_name}\n"
                f"• <b>Days Remaining:</b> {days_left} days\n"
                f"• <b>Auto-Renew:</b> {'✅ Enabled' if premium_info.get('auto_renew') else '❌ Disabled'}\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            )
        else:
            text += (
                "⚪ <b>Current Status: FREE</b>\n"
                "Upgrade to premium for amazing benefits!\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            )
        
        # Basic Tier
        basic = PREMIUM_TIERS["basic"]
        text += (
            f"{basic['icon']} <b>{basic['name']}</b>\n"
            f"💵 <b>Price:</b> ${basic['price_usd']:.2f}/month\n\n"
            "<b>🎁 Benefits:</b>\n"
            f"• 🔄 <b>Auto-Roll Permanent</b> (Always ON!)\n"
            f"• 💰 <b>{basic['benefits']['monthly_coins']:,} Coins/month</b>\n"
            f"• 🧪 <b>{basic['benefits']['monthly_luck_potions']} Luck Potions/month</b>\n"
            f"• 🍀 <b>+{basic['benefits']['luck_boost_percent']}% Permanent Luck Boost</b>\n"
            f"• 💰 <b>{basic['benefits']['coins_multiplier']:.0f}x Coins Multiplier</b>\n"
            f"• ⭐ <b>{basic['benefits']['exp_multiplier']:.0f}x EXP Multiplier</b>\n"
            f"• 🏷️ <b>Exclusive Title</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        
        # Pro Tier
        pro = PREMIUM_TIERS["pro"]
        text += (
            f"{pro['icon']} <b>{pro['name']}</b>\n"
            f"💵 <b>Price:</b> ${pro['price_usd']:.2f}/month\n"
            f"<i>🎉 2x ALL Basic Rewards!</i>\n\n"
            "<b>🎁 Benefits:</b>\n"
            f"• 🔄 <b>Auto-Roll Permanent</b> (Always ON!)\n"
            f"• 💰 <b>{pro['benefits']['monthly_coins']:,} Coins/month</b> (2x Basic)\n"
            f"• 🧪 <b>{pro['benefits']['monthly_luck_potions']} Luck Potions/month</b> (2x Basic)\n"
            f"• 🍀 <b>+{pro['benefits']['luck_boost_percent']}% Permanent Luck Boost</b> (2x Basic)\n"
            f"• 💰 <b>{pro['benefits']['coins_multiplier']:.0f}x Coins Multiplier</b>\n"
            f"• ⭐ <b>{pro['benefits']['exp_multiplier']:.0f}x EXP Multiplier</b>\n\n"
            f"<b>✨ PRO EXCLUSIVE FEATURES:</b>\n"
            f"• 🌆🎸🎻 <b>Exclusive Lights Access</b>\n"
            f"   └ Get 2 random from: Cybernight 🌆, O'Sound 🎸, Remembrance 🎻\n"
            f"   └ Drops during Heaven Approach event ✨👼 (0.5% chance, 15% drop rate)\n"
            f"• 🔮 <b>New Light Preview</b> (See upcoming lights before release!)\n"
            f"• 💸 <b>{pro['benefits']['shop_discount_percent']}% Shop Discount</b>\n"
            f"• 🏷️ <b>Elite Title</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        
        text += (
            "<b>💡 Why Go Premium?</b>\n"
            "• Never stop rolling with permanent auto-roll!\n"
            "• Massive luck boost for better drops\n"
            "• Double your coins and EXP gain\n"
            "• Monthly rewards keep you ahead\n"
            "• Pro exclusive: Light preview & discounts!\n\n"
            "<b>🔐 Secure Payment</b>\n"
            "All payments are processed securely.\n"
            "Cancel anytime, no hidden fees!\n\n"
            "<b>📞 How to Subscribe?</b>\n"
            "Contact bot admin or use payment buttons below.\n"
            "Payment methods: PayPal, Crypto, Bank Transfer"
        )
        
        # Build keyboard
        keyboard = []
        
        if not premium_info or not premium_info.get("active"):
            # Show purchase buttons for non-premium users
            keyboard.append([
                InlineKeyboardButton(f"{basic['icon']} Buy Basic (${basic['price_usd']:.2f})", callback_data="buy_premium_basic")
            ])
            keyboard.append([
                InlineKeyboardButton(f"{pro['icon']} Buy Pro (${pro['price_usd']:.2f})", callback_data="buy_premium_pro")
            ])
        else:
            # Show management buttons for premium users
            keyboard.append([
                InlineKeyboardButton("🔄 Renew Subscription", callback_data=f"renew_premium_{premium_info.get('tier')}")
            ])
            keyboard.append([
                InlineKeyboardButton("⬆️ Upgrade Tier", callback_data="upgrade_premium")
            ])
            if premium_info.get('auto_renew'):
                keyboard.append([
                    InlineKeyboardButton("❌ Cancel Auto-Renew", callback_data="cancel_autorenew")
                ])
            else:
                keyboard.append([
                    InlineKeyboardButton("✅ Enable Auto-Renew", callback_data="enable_autorenew")
                ])
        
        keyboard.append([
            InlineKeyboardButton("🌐 Visit Premium Website", url="https://constellation-premium.space")
        ])
        keyboard.append([
            InlineKeyboardButton("📊 Compare Tiers", callback_data="compare_premium")
        ])
        keyboard.append([
            InlineKeyboardButton("💬 Contact Admin", url="https://t.me/YourAdminUsername")
        ])
        keyboard.append([
            InlineKeyboardButton("❌ Close", callback_data="close_menu")
        ])
        
        # Send or edit message based on source
        if is_callback:
            await message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await message.reply_text(
                text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
    except Exception as e:
        logging.error(f"Error in premium_command: {e}")
        import traceback
        traceback.print_exc()
        
        # Handle error based on source
        try:
            if update.callback_query:
                await update.callback_query.message.edit_text("❌ An error occurred. Please try again.")
            elif update.message:
                await update.message.reply_text("❌ An error occurred. Please try again.")
        except:
            pass  # Fail silently if can't send error message

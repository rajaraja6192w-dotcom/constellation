"""Test script for Ko-fi webhook integration"""

import requests
import json

def test_health():
    """Test webhook health check"""
    print("🔍 Testing webhook health...")
    try:
        response = requests.get("http://localhost:5000/health")
        if response.status_code == 200:
            print("✅ Health check passed:", response.json())
            return True
        else:
            print("❌ Health check failed:", response.status_code)
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to webhook server!")
        print("   Make sure kofi_webhook.py is running")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_webhook(telegram_id):
    """Test webhook with simulated Ko-fi payment"""
    print(f"\n🔍 Testing webhook with Telegram ID: {telegram_id}")
    print("   Simulating Ko-fi 'Constellation | Basic' purchase...")
    
    # Simulate Ko-fi webhook data
    webhook_data = {
        "type": "Subscription",
        "is_subscription_payment": True,
        "is_first_subscription_payment": True,
        "tier_name": "Constellation | Basic",
        "message": f"telegram_id: {telegram_id}",
        "message_id": "test_" + str(int(time.time())),
        "from_name": "Test User",
        "amount": "1.99",
        "currency": "USD"
    }
    
    try:
        response = requests.post(
            "http://localhost:5000/kofi-webhook",
            data={"data": json.dumps(webhook_data)}
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📊 Response Body: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                print("\n✅ WEBHOOK TEST PASSED!")
                print(f"   ✓ Premium activated for user {telegram_id}")
                print(f"   ✓ Tier: {result.get('tier')}")
                print(f"   ✓ Check your Telegram for notification!")
                return True
            else:
                print("\n⚠️ Webhook returned error:", result.get("message"))
                return False
        else:
            print("\n❌ Webhook test failed!")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during webhook test: {e}")
        return False

if __name__ == "__main__":
    import time
    
    print("=" * 60)
    print("   KO-FI WEBHOOK TEST SCRIPT")
    print("=" * 60)
    print()
    
    # Test 1: Health check
    health_ok = test_health()
    
    if not health_ok:
        print("\n❌ Webhook server is not running!")
        print("   Please start it first: python kofi_webhook.py")
        exit(1)
    
    # Test 2: Webhook with payment simulation
    print("\n" + "=" * 60)
    telegram_id = input("Enter your Telegram ID to test (from /start): ")
    
    if not telegram_id.isdigit():
        print("❌ Invalid Telegram ID! Must be numbers only.")
        exit(1)
    
    telegram_id = int(telegram_id)
    
    print("\n⚠️ WARNING:")
    print("   This will activate Basic premium for this user!")
    print("   Make sure the user exists in the database (has used /start)")
    
    confirm = input("\n   Continue? (yes/no): ")
    
    if confirm.lower() not in ["yes", "y"]:
        print("❌ Test cancelled.")
        exit(0)
    
    # Run webhook test
    success = test_webhook(telegram_id)
    
    # Summary
    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED!")
        print("\n📋 What happened:")
        print("   1. Webhook received payment data")
        print("   2. Premium 'basic' activated for 30 days")
        print("   3. User received 100k coins + 150 potions")
        print("   4. Telegram notification sent")
        print("   5. Auto-roll enabled permanently")
        print("\n💡 User should now see:")
        print("   • Premium status in /stats")
        print("   • 'See Premium' button in main menu")
        print("   • +250% permanent luck boost")
        print("   • 2x coins & exp multiplier")
    else:
        print("❌ TESTS FAILED!")
        print("\n🔍 Check:")
        print("   • Is main bot running? (python main.py)")
        print("   • Is webhook running? (python kofi_webhook.py)")
        print("   • Does user exist in database? (used /start)")
        print("   • Check server logs for errors")
    print("=" * 60)

#!/usr/bin/env python3
"""
Test sending message to potential group chat IDs
"""

import requests

# Your bot token
BOT_TOKEN = '8468875074:AAEeCH6H5NfNzHFobMAaw4epxa2v8nZvw_8'

# Common group chat ID patterns to test
# Group chat IDs are usually negative numbers
potential_group_ids = [
    '-1001234567890',  # Replace with your actual group ID
    '-1002000000000',
    '-1003000000000'
]

def test_group_message(chat_id):
    """Test sending a message to a specific chat ID"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": f"🧪 Test message to chat ID: {chat_id}\n\nIf you see this, this is the correct group!",
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, data=data, timeout=10)
        result = response.json()
        
        if result['ok']:
            print(f"✅ SUCCESS! Message sent to chat ID: {chat_id}")
            print(f"📝 Message ID: {result['result']['message_id']}")
            return True
        else:
            print(f"❌ Failed for chat ID {chat_id}: {result.get('description', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error for chat ID {chat_id}: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing potential group chat IDs...")
    print("📋 Instructions:")
    print("1. Edit this script and replace the potential_group_ids with your actual group ID")
    print("2. Run this script to test which chat ID works")
    print("=" * 60)
    
    for chat_id in potential_group_ids:
        print(f"\n🧪 Testing chat ID: {chat_id}")
        if test_group_message(chat_id):
            print(f"🎯 Found working group chat ID: {chat_id}")
            break
        print("-" * 40)
    
    print("\n💡 If none worked, you need to:")
    print("1. Send a message in your group")
    print("2. Visit: https://api.telegram.org/bot8468875074:AAEeCH6H5NfNzHFobMAaw4epxa2v8nZvw_8/getUpdates")
    print("3. Find the negative number (group chat ID) in the response")
    print("4. Update this script with the correct ID")



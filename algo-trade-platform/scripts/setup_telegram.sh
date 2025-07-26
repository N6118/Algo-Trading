#!/bin/bash

# Setup script for Telegram notifications
# This script helps configure the Telegram bot for IBKR notifications

echo "🔧 Setting up Telegram notifications for IBKR IBC service..."

# Check if config file exists
CONFIG_FILE="config/telegram_config.json"
SERVICE_FILE="server/ibkr-streamdata.service"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Configuration file not found: $CONFIG_FILE"
    exit 1
fi

if [ ! -f "$SERVICE_FILE" ]; then
    echo "❌ Service file not found: $SERVICE_FILE"
    exit 1
fi

echo ""
echo "📋 To set up Telegram notifications, you need:"
echo "1. A Telegram bot token (get from @BotFather)"
echo "2. A chat/group ID where notifications will be sent"
echo ""

# Get bot token
read -p "Enter your Telegram bot token: " BOT_TOKEN

if [ -z "$BOT_TOKEN" ]; then
    echo "❌ Bot token is required"
    exit 1
fi

# Get chat ID
read -p "Enter your Telegram chat/group ID: " CHAT_ID

if [ -z "$CHAT_ID" ]; then
    echo "❌ Chat ID is required"
    exit 1
fi

echo ""
echo "🔧 Updating configuration files..."

# Update config file
sed -i "s/your_telegram_bot_token_here/$BOT_TOKEN/g" "$CONFIG_FILE"
sed -i "s/your_telegram_chat_id_here/$CHAT_ID/g" "$CONFIG_FILE"

# Update service file
sed -i "s/your_bot_token_here/$BOT_TOKEN/g" "$SERVICE_FILE"
sed -i "s/your_chat_id_here/$CHAT_ID/g" "$SERVICE_FILE"

echo "✅ Configuration updated successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Copy the service file to systemd:"
echo "   sudo cp server/ibkr-streamdata.service /etc/systemd/system/"
echo ""
echo "2. Reload systemd and enable the service:"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable ibkr-streamdata.service"
echo ""
echo "3. Start the service:"
echo "   sudo systemctl start ibkr-streamdata.service"
echo ""
echo "4. Check service status:"
echo "   sudo systemctl status ibkr-streamdata.service"
echo ""
echo "5. View logs:"
echo "   sudo journalctl -u ibkr-streamdata.service -f"
echo ""

# Test the configuration
echo "🧪 Testing Telegram configuration..."
python3 -c "
import sys
import os
sys.path.append('.')
from backend.app.services.telegram_notifier import get_telegram_notifier

notifier = get_telegram_notifier()
if notifier:
    success = notifier.send_message('🧪 Test message from IBKR setup script')
    if success:
        print('✅ Telegram test message sent successfully!')
    else:
        print('❌ Failed to send test message')
else:
    print('❌ Telegram notifier not configured properly')
" 
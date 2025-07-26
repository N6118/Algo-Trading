import requests
import logging
import os
from datetime import datetime
from typing import Optional

class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram notifier.
        
        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat/group ID
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.logger = logging.getLogger(__name__)
        
    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Send a message to the Telegram group.
        
        Args:
            message: Message to send
            parse_mode: Message format (HTML or Markdown)
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"✅ Telegram message sent successfully")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Failed to send Telegram message: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Unexpected error sending Telegram message: {e}")
            return False
    
    def send_server_start_notification(self) -> bool:
        """Send notification when server starts."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"""
🚀 <b>IBKR IBC Server Started</b>

⏰ <b>Time:</b> {timestamp}
📡 <b>Status:</b> Server is now running and ready to receive market data

<i>Waiting for first market data entry...</i>
        """.strip()
        
        return self.send_message(message)
    
    def send_server_stop_notification(self) -> bool:
        """Send notification when server stops."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"""
🛑 <b>IBKR IBC Server Stopped</b>

⏰ <b>Time:</b> {timestamp}
📡 <b>Status:</b> Server has been stopped

<i>Market data collection ended.</i>
        """.strip()
        
        return self.send_message(message)
    
    def send_first_entry_notification(self, symbol: str, price: float, volume: int) -> bool:
        """Send notification for the first market data entry after server start."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"""
📊 <b>First Market Data Entry</b>

⏰ <b>Time:</b> {timestamp}
📈 <b>Symbol:</b> {symbol}
💰 <b>Price:</b> {price}
📦 <b>Volume:</b> {volume}

<i>Market data streaming has begun!</i>
        """.strip()
        
        return self.send_message(message)
    
    def send_last_entry_notification(self, symbol: str, price: float, volume: int) -> bool:
        """Send notification for the last market data entry before server stop."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"""
📊 <b>Last Market Data Entry</b>

⏰ <b>Time:</b> {timestamp}
📈 <b>Symbol:</b> {symbol}
💰 <b>Price:</b> {price}
📦 <b>Volume:</b> {volume}

<i>Final market data entry before shutdown.</i>
        """.strip()
        
        return self.send_message(message)
    
    def send_connection_status(self, status: str, error_msg: Optional[str] = None) -> bool:
        """Send connection status notification."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if status == "connected":
            message = f"""
✅ <b>TWS Connection Established</b>

⏰ <b>Time:</b> {timestamp}
📡 <b>Status:</b> Successfully connected to Interactive Brokers TWS
🔗 <b>Connection:</b> Active and ready for market data
            """.strip()
        elif status == "disconnected":
            message = f"""
❌ <b>TWS Connection Lost</b>

⏰ <b>Time:</b> {timestamp}
📡 <b>Status:</b> Connection to Interactive Brokers TWS lost
🔗 <b>Connection:</b> Disconnected
            """.strip()
        elif status == "error":
            message = f"""
⚠️ <b>TWS Connection Error</b>

⏰ <b>Time:</b> {timestamp}
📡 <b>Status:</b> Failed to connect to Interactive Brokers TWS
❌ <b>Error:</b> {error_msg or "Unknown error"}
            """.strip()
        else:
            return False
        
        return self.send_message(message)

# Global notifier instance
_telegram_notifier = None

def get_telegram_notifier() -> Optional[TelegramNotifier]:
    """Get the global Telegram notifier instance."""
    global _telegram_notifier
    
    if _telegram_notifier is None:
        # Get configuration from environment variables
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if bot_token and chat_id:
            _telegram_notifier = TelegramNotifier(bot_token, chat_id)
            logging.info("✅ Telegram notifier initialized")
        else:
            logging.warning("⚠️ Telegram notifier not configured - missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
    
    return _telegram_notifier

def send_server_start_notification() -> bool:
    """Send server start notification."""
    notifier = get_telegram_notifier()
    if notifier:
        return notifier.send_server_start_notification()
    return False

def send_server_stop_notification() -> bool:
    """Send server stop notification."""
    notifier = get_telegram_notifier()
    if notifier:
        return notifier.send_server_stop_notification()
    return False

def send_first_entry_notification(symbol: str, price: float, volume: int) -> bool:
    """Send first entry notification."""
    notifier = get_telegram_notifier()
    if notifier:
        return notifier.send_first_entry_notification(symbol, price, volume)
    return False

def send_last_entry_notification(symbol: str, price: float, volume: int) -> bool:
    """Send last entry notification."""
    notifier = get_telegram_notifier()
    if notifier:
        return notifier.send_last_entry_notification(symbol, price, volume)
    return False

def send_connection_status(status: str, error_msg: Optional[str] = None) -> bool:
    """Send connection status notification."""
    notifier = get_telegram_notifier()
    if notifier:
        return notifier.send_connection_status(status, error_msg)
    return False 
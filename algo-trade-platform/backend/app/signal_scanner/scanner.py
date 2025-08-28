"""
Signal Scanner Service

This module implements the signal scanning logic, which periodically checks
for trading signals based on configured strategies and conditions.
"""

import os
import sys
import time
import logging
import threading
import schedule
import pytz
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from urllib.parse import quote_plus as urlquote
from tenacity import retry, stop_after_attempt, wait_exponential
from sqlalchemy.orm import joinedload

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import database models and correlation strategy
from backend.app.signal_scanner.db_schema import (
    SignalConfig, SignalSymbol, SignalEntryRule, SignalExitRule,
    GeneratedSignal, SignalCondition, Base
)
from backend.app.signal_scanner.correlation_strategy import CorrelationStrategy

# Import Telegram notifier
from backend.app.services.telegram_notifier import get_telegram_notifier

# Set up logging
logger = logging.getLogger(__name__)

class SignalScanner:
    """
    Signal Scanner Service that periodically checks for trading signals
    based on configured strategies and conditions.
    """
    
    def __init__(self):
        """Initialize the signal scanner with database connection and scheduling."""
        self.setup_database()
        self.setup_schedule()
        self.correlation_strategy = None
        self.running = False
        self.thread = None
    
    def setup_database(self):
        """Set up database connection with connection pooling."""
        try:
            password = os.getenv("DB_PASSWORD", "password")
            encoded_password = urlquote(password)
            uri = os.getenv("DB_URI", f"postgresql://postgres:{encoded_password}@localhost:5432/theodb")
            
            # Create engine with connection pooling
            self.engine = create_engine(
                uri,
                poolclass=QueuePool,
                pool_size=5,  # Maximum number of connections
                max_overflow=10,  # Maximum number of connections that can be created beyond pool_size
                pool_timeout=30,  # Seconds to wait before giving up on getting a connection
                pool_recycle=1800,  # Recycle connections after 30 minutes
                pool_pre_ping=True  # Enable connection health checks
            )
            
            # Create session factory
            self.Session = sessionmaker(bind=self.engine)
            
            # Ensure tables exist
            Base.metadata.create_all(self.engine)
            
            logger.info("Database connection established with connection pooling")
        
        except Exception as e:
            logger.error(f"Error setting up database connection: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def get_market_data(self, symbol, timeframe, lookback=20):
        """
        Get market data for a symbol with retry mechanism.
        
        Args:
            symbol: The symbol to get data for
            timeframe: The timeframe (e.g., '5min', '15min', '1h')
            lookback: Number of periods to look back
            
        Returns:
            DataFrame with market data or None if error
        """
        session = None
        try:
            session = self.Session()
            
            # Map timeframe to table name
            timeframe_map = {
                '5min': 'stock_ohlc_5min',
                '15min': 'tbl_ohlc_fifteen_output',  # or 'stock_ohlc_15min' if you want raw OHLC
                '30min': 'tbl_ohlc_thirty_output',   # if you have this
                '1h': 'stock_ohlc_60min'
            }
            
            table_name = timeframe_map.get(timeframe)
            if not table_name:
                raise ValueError(f"Invalid timeframe: {timeframe}")
            
            # Construct query
            query = text(f"""
                SELECT timestamp, open, high, low, close, volume,
                       sh_price, sl_price, sh_status, sl_status
                FROM {table_name}
                WHERE symbol = :symbol
                ORDER BY timestamp DESC
                LIMIT :limit
            """)
            
            result = session.execute(query, {'symbol': symbol, 'limit': lookback})
            rows = result.fetchall()
            
            if not rows:
                logger.warning(f"No data found for {symbol} in {timeframe} timeframe")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(rows)
            df = df.sort_values('timestamp')  # Sort by timestamp ascending
            
            # Validate data
            if len(df) < lookback:
                logger.warning(f"Insufficient data for {symbol} in {timeframe} timeframe: {len(df)} < {lookback}")
                return None
            
            # Check for missing values
            if df.isnull().any().any():
                logger.warning(f"Missing values found in data for {symbol}")
                return None
            
            # Remove timezone conversion logic here; handled in correlation_strategy.py
            return df
        
        except Exception as e:
            logger.error(f"Error getting market data for {symbol} in {timeframe} timeframe: {str(e)}")
            raise
        
        finally:
            if session:
                session.close()
    
    def validate_market_data(self, df, symbol, timeframe):
        """
        Validate market data for completeness and quality.
        
        Args:
            df: DataFrame with market data
            symbol: Symbol being checked
            timeframe: Timeframe being checked
            
        Returns:
            bool: Whether the data is valid
        """
        if df is None or df.empty:
            logger.warning(f"No data available for {symbol} in {timeframe} timeframe")
            return False
        
        # Check for missing values
        if df.isnull().any().any():
            logger.warning(f"Missing values found in data for {symbol}")
            return False
        
        # Check for zero or negative prices
        if (df['close'] <= 0).any():
            logger.warning(f"Invalid prices found in data for {symbol}")
            return False
        
        # Check for reasonable price movements
        price_changes = df['close'].pct_change().abs()
        if (price_changes > 0.5).any():  # More than 50% price change
            logger.warning(f"Unusual price movements found in data for {symbol}")
            return False
        
        return True
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def cleanup_old_signals(self):
        """Clean up old signals based on configuration."""
        session = self.Session()
        try:
            # Get all active configurations
            configs = session.query(SignalConfig).filter(SignalConfig.is_active == True).all()
            
            for config in configs:
                # Determine retention period based on expiry
                if config.expiry == 'Daily':
                    retention_days = 1
                elif config.expiry == 'Weekly':
                    retention_days = 7
                else:  # Monthly
                    retention_days = 30
                
                # Calculate cutoff date
                cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
                
                # Delete old signals
                query = text("""
                    DELETE FROM generated_signals
                    WHERE config_id = :config_id
                    AND signal_time < :cutoff_date
                    AND status IN ('Executed', 'Rejected', 'Expired')
                """)
                
                result = session.execute(query, {
                    'config_id': config.id,
                    'cutoff_date': cutoff_date
                })
                
                deleted_count = result.rowcount
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old signals for config {config.name}")
            
            session.commit()
        
        except Exception as e:
            logger.error(f"Error cleaning up old signals: {str(e)}")
            session.rollback()
            raise
        
        finally:
            session.close()

    def mark_old_signals_expired(self):
        """Mark old signals as expired to prevent blocking new signals."""
        session = self.Session()
        try:
            # Mark signals older than 2 hours as expired
            cutoff_time = datetime.utcnow() - timedelta(hours=2)
            
            query = text("""
                UPDATE generated_signals
                SET status = 'Expired'
                WHERE status IN ('New', 'Pending')
                AND signal_time < :cutoff_time
            """)
            
            result = session.execute(query, {'cutoff_time': cutoff_time})
            updated_count = result.rowcount
            
            if updated_count > 0:
                logger.info(f"Marked {updated_count} old signals as expired")
            
            session.commit()
        
        except Exception as e:
            logger.error(f"Error marking old signals as expired: {str(e)}")
            session.rollback()
            raise
        
        finally:
            session.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def check_duplicate_signals(self, config, symbol, direction, price, timeframe):
        """
        Check for duplicate signals within a time window.
        
        Args:
            config: SignalConfig object
            symbol: Symbol to check
            direction: Signal direction
            price: Signal price
            timeframe: Signal timeframe
            
        Returns:
            bool: Whether a duplicate signal exists
        """
        session = self.Session()
        try:
            # Define time window (e.g., 5 minutes)
            time_window = timedelta(minutes=5)
            cutoff_time = datetime.utcnow() - time_window
            
            # Check for similar signals
            query = text("""
                SELECT COUNT(*) FROM generated_signals
                WHERE config_id = :config_id
                AND symbol = :symbol
                AND direction = :direction
                AND timeframe = :timeframe
                AND signal_time > :cutoff_time
                AND ABS(price - :price) / :price < 0.01  -- Within 1% price difference
            """)
            
            result = session.execute(query, {
                'config_id': config.id,
                'symbol': symbol,
                'direction': direction,
                'timeframe': timeframe,
                'cutoff_time': cutoff_time,
                'price': price
            })
            
            count = result.scalar()
            return count > 0
        
        except Exception as e:
            logger.error(f"Error checking duplicate signals: {str(e)}")
            raise
        
        finally:
            session.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def scan_for_signals(self, config):
        """
        Scan for signals based on a configuration.
        
        Args:
            config: SignalConfig object
            
        Returns:
            list: Generated signals
        """
        session = self.Session()
        try:
            # Eagerly load all relationships for config
            config = session.query(SignalConfig)\
                .options(
                    joinedload(SignalConfig.entry_rules),
                    joinedload(SignalConfig.symbols),
                    joinedload(SignalConfig.exit_rules)
                )\
                .filter(SignalConfig.id == config.id).first()
            
            # Check if we should run this config
            if not self.should_run_config(config):
                return []
            
            # Initialize correlation strategy if not already done
            if self.correlation_strategy is None:
                self.correlation_strategy = CorrelationStrategy(config)
            
            # Generate signals using correlation strategy
            signals = self.correlation_strategy.generate_signal(config)
            
            # Filter out duplicate signals
            filtered_signals = []
            for signal in signals:
                if not self.check_duplicate_signals(
                    config, signal.symbol, signal.direction,
                    signal.price, signal.timeframe
                ):
                    filtered_signals.append(signal)
                else:
                    logger.info(f"Skipping duplicate signal for {signal.symbol}")
            
            # Log results and send Telegram notifications
            if filtered_signals:
                logger.info(f"Generated {len(filtered_signals)} signals for config {config.name}")
                
                # Send Telegram notifications for each signal
                notifier = get_telegram_notifier()
                if notifier:
                    for signal in filtered_signals:
                        message = f"🚨 **SIGNAL GENERATED** 🚨\n\n"
                        message += f"**Symbol:** {signal.symbol}\n"
                        message += f"**Direction:** {signal.direction}\n"
                        message += f"**Price:** ${signal.price:.2f}\n"
                        message += f"**Timeframe:** {signal.timeframe}\n"
                        message += f"**Strategy:** {config.name}\n"
                        message += f"**Generated:** {signal.generated_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                        message += f"**Entry Rules:**\n"
                        for rule in signal.entry_rules:
                            message += f"• {rule.condition}\n"
                        
                        try:
                            notifier.send_message(message)
                            logger.info(f"Telegram notification sent for signal {signal.id}")
                        except Exception as e:
                            logger.error(f"Failed to send Telegram notification: {e}")
                else:
                    logger.warning("Telegram notifier not available")
            else:
                logger.info(f"No signals generated for config {config.name}")
            
            return filtered_signals
        
        except Exception as e:
            logger.error(f"Error scanning for signals: {str(e)}")
            raise
        
        finally:
            session.close()
    
    def should_run_config(self, config):
        """
        Check if a configuration should be run based on time and market conditions.
        
        Args:
            config: SignalConfig object
            
        Returns:
            bool: Whether the config should be run
        """
        try:
            # Check if config is active
            if not config.is_active:
                return False
            
            # Get current time in ET
            et = pytz.timezone('US/Eastern')
            current_time = datetime.now(et)
            
            # Check if it's a trading day
            trading_days = config.trading_days.split(',')
            if current_time.strftime('%a') not in trading_days:
                logger.info(f"Not a trading day for config {config.name}")
                return False
            
            # Parse market hours
            try:
                start_time = datetime.strptime(config.start_time, '%H:%M').time()
                end_time = datetime.strptime(config.end_time, '%H:%M').time()
            except ValueError as e:
                logger.error(f"Invalid time format in config {config.name}: {str(e)}")
                return False
            
            # Convert times to ET
            start_dt = et.localize(datetime.combine(current_time.date(), start_time))
            end_dt = et.localize(datetime.combine(current_time.date(), end_time))
            current_dt = current_time
            
            # Check if within market hours
            if not (start_dt <= current_dt <= end_dt):
                logger.info(f"Outside market hours for config {config.name}")
                return False
            
            # Check for market holidays
            if self.is_market_holiday(current_time.date()):
                logger.info(f"Market holiday for config {config.name}")
                return False
            
            # Pre/post market hours as datetime
            pre_market_start_dt = et.localize(datetime.combine(current_time.date(), datetime.strptime('04:00', '%H:%M').time()))
            post_market_end_dt = et.localize(datetime.combine(current_time.date(), datetime.strptime('20:00', '%H:%M').time()))

            if not (pre_market_start_dt <= current_dt <= post_market_end_dt):
                logger.info(f"Outside pre/post market hours for config {config.name}")
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error checking if config should run: {str(e)}")
            return False
    
    def is_market_holiday(self, date):
        """
        Check if a date is a market holiday.
        
        Args:
            date: Date to check
            
        Returns:
            bool: Whether the date is a market holiday
        """
        try:
            # Get holidays from database or cache
            session = self.Session()
            query = text("""
                SELECT date FROM market_holidays
                WHERE date = :date
            """)
            result = session.execute(query, {'date': date})
            is_holiday = result.scalar() is not None
            session.close()
            return is_holiday
        except Exception as e:
            logger.error(f"Error checking market holiday: {str(e)}")
            return False
    
    def setup_schedule(self):
        """Set up the scanning schedule."""
        try:
            # Get active configurations
            session = self.Session()
            configs = session.query(SignalConfig).filter(SignalConfig.is_active == True).all()
            
            # Schedule each config
            for config in configs:
                interval = config.scan_interval_minutes
                schedule.every(interval).minutes.do(self.scan_for_signals, config)
            
            # Schedule cleanup job (run daily at midnight)
            schedule.every().day.at("00:00").do(self.cleanup_old_signals)
            
            logger.info(f"Scheduled {len(configs)} active configurations")
        
        except Exception as e:
            logger.error(f"Error setting up schedule: {str(e)}")
        
        finally:
            session.close()
    
    def start(self):
        """Start the signal scanner in a separate thread."""
        if self.running:
            logger.warning("Signal scanner is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Signal scanner started")
    
    def stop(self):
        """Stop the signal scanner."""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Signal scanner stopped")
    
    def _run(self):
        """Main loop for the signal scanner."""
        while self.running:
            try:
                # Mark old signals as expired to prevent blocking new signals
                self.mark_old_signals_expired()
                
                # Run scheduled tasks
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in signal scanner main loop: {str(e)}")
                time.sleep(5)  # Wait before retrying


def load_config():
    """Load configuration from file."""
    config_path = os.getenv('SCANNER_CONFIG_PATH', 'config/scanner_config.json')
    try:
        import json
        with open(config_path, 'r') as json_file:
            return json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load config from {config_path}: {str(e)}")
        logger.warning("Using default configuration")
        return {}


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load configuration
    config = load_config()
    
    # Create and start the scanner
    scanner = SignalScanner()
    scanner.start()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scanner.stop()

"""
Multi-Symbol Correlation Strategy

This module implements the correlation-based trading strategy that analyzes relationships
between multiple symbols to generate trading signals.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus as urlquote
from scipy import stats
from sklearn.preprocessing import StandardScaler
import pytz
from sqlalchemy.orm import joinedload

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import database models
from backend.app.signal_scanner.db_schema import (
    SignalConfig, SignalSymbol, SignalEntryRule, SignalExitRule,
    GeneratedSignal, SignalCondition, Base
)

# Set up logging
logger = logging.getLogger(__name__)

class CorrelationStrategy:
    """
    Correlation-based trading strategy that analyzes relationships between
    multiple symbols to generate trading signals.
    """
    
    def __init__(self, config):
        """
        Initialize the correlation strategy.
        
        Args:
            config: SignalConfig object containing strategy configuration
        """
        self.config = config
        self.setup_database()
        self.scaler = StandardScaler()
    
    def setup_database(self):
        """Set up database connection."""
        try:
            password = os.getenv("DB_PASSWORD", "password")
            encoded_password = urlquote(password)
            uri = os.getenv("DB_URI", f"postgresql://postgres:{encoded_password}@100.121.186.86:5432/theodb")
            
            self.engine = create_engine(uri)
            self.Session = sessionmaker(bind=self.engine)
            
            logger.info("Database connection established for correlation strategy")
        
        except Exception as e:
            logger.error(f"Error setting up database connection: {str(e)}")
            raise
    
    def get_market_data(self, symbol, timeframe, lookback=25):
        """
        Get market data for a symbol.
        
        Args:
            symbol: The symbol to get data for
            timeframe: The timeframe (e.g., '5min', '15min', '1h')
            lookback: Number of periods to look back
            
        Returns:
            DataFrame with market data or None if error
        """
        session = self.Session()
        try:
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
            
            # Construct query with timezone handling
            query = text(f"""
                SELECT 
                    created,  -- fetch as naive, localize in pandas
                    open, high, low, close, volume
                FROM {table_name}
                WHERE symbol = :symbol
                ORDER BY created DESC
                LIMIT :limit
            """)
            
            result = session.execute(query, {'symbol': symbol, 'limit': lookback})
            rows = result.fetchall()
            
            if not rows:
                logger.warning(f"No data found for {symbol} in {timeframe} timeframe")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(rows)
            # Localize 'created' as Asia/Singapore if naive, else just convert
            dt = pd.to_datetime(df['created'])
            if dt.dt.tz is None:
                df['timestamp'] = dt.dt.tz_localize('Asia/Singapore').dt.tz_convert('America/New_York')
            else:
                df['timestamp'] = dt.dt.tz_convert('America/New_York')
            df = df.sort_values('timestamp')  # Sort by timestamp ascending
            
            # Validate data
            if not self.validate_market_data(df, symbol, timeframe):
                return None
            
            return df
        
        except Exception as e:
            logger.error(f"Error getting market data for {symbol} in {timeframe} timeframe: {str(e)}")
            return None
        
        finally:
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
        
        # Check for data gaps
        expected_interval = pd.Timedelta(timeframe)
        time_diffs = df['timestamp'].diff()
        if (time_diffs > expected_interval * 2).any():
            logger.warning(f"Data gaps found in {symbol} data")
            return False
        
        # Check for market hours
        et = pytz.timezone('America/New_York')
        # Use datetime objects for market start and end
        market_start_time = datetime.strptime('09:30', '%H:%M').time()
        market_end_time = datetime.strptime('16:00', '%H:%M').time()
        # For each row, compare the timestamp as a datetime
        df['in_market_hours'] = df['timestamp'].apply(lambda ts: market_start_time <= ts.time() <= market_end_time)
        if not df['in_market_hours'].all():
            logger.warning(f"Data outside market hours found for {symbol}")
            return False
        # Remove the helper column
        df.drop(columns=['in_market_hours'], inplace=True)
        return True
    
    def calculate_correlation(self, symbol1_data, symbol2_data, method='pearson', window=None):
        """
        Calculate correlation between two symbols using various methods.
        
        Args:
            symbol1_data: DataFrame with first symbol's data
            symbol2_data: DataFrame with second symbol's data
            method: Correlation method ('pearson', 'spearman', 'kendall')
            window: Rolling window size for dynamic correlation
            
        Returns:
            float or Series: Correlation coefficient(s)
        """
        try:
            # Validate minimum data points
            min_data_points = 20  # Minimum required for reliable correlation
            if len(symbol1_data) < min_data_points or len(symbol2_data) < min_data_points:
                logger.warning(f"Insufficient data points for correlation calculation (minimum {min_data_points} required)")
                return None
            
            # Align the data by timestamp
            merged = pd.merge(
                symbol1_data[['timestamp', 'close']].rename(columns={'close': 'close_1'}),
                symbol2_data[['timestamp', 'close']].rename(columns={'close': 'close_2'}),
                on='timestamp', how='inner'
            )
            
            if len(merged) < min_data_points:
                logger.warning("Insufficient overlapping data points for correlation calculation")
                return None
            
            # Calculate returns
            merged['returns_1'] = merged['close_1'].pct_change()
            merged['returns_2'] = merged['close_2'].pct_change()
            
            # Remove NaN values
            merged = merged.dropna()
            
            if len(merged) < min_data_points:
                logger.warning("Insufficient valid data points after removing NaN values")
                return None
            
            # Check for zero or constant returns
            if merged['returns_1'].std() == 0 or merged['returns_2'].std() == 0:
                logger.warning("Zero or constant returns detected, correlation cannot be calculated")
                return None
            
            # Check for outliers using z-score
            z_scores_1 = np.abs(stats.zscore(merged['returns_1']))
            z_scores_2 = np.abs(stats.zscore(merged['returns_2']))
            outlier_mask = (z_scores_1 > 3) | (z_scores_2 > 3)
            if outlier_mask.any():
                logger.warning(f"Outliers detected in returns data, removing {outlier_mask.sum()} points")
                merged = merged[~outlier_mask]
            
            if len(merged) < min_data_points:
                logger.warning("Insufficient data points after removing outliers")
                return None
            
            if window:
                # Calculate rolling correlation
                if method == 'pearson':
                    correlation = merged['returns_1'].rolling(window).corr(merged['returns_2'])
                elif method == 'spearman':
                    correlation = merged['returns_1'].rolling(window).corr(merged['returns_2'], method='spearman')
                elif method == 'kendall':
                    correlation = merged['returns_1'].rolling(window).corr(merged['returns_2'], method='kendall')
                else:
                    raise ValueError(f"Unsupported correlation method: {method}")
                
                return correlation.iloc[-1]  # Return the latest correlation
            
            else:
                # Calculate static correlation
                if method == 'pearson':
                    correlation = merged['returns_1'].corr(merged['returns_2'])
                elif method == 'spearman':
                    correlation = merged['returns_1'].corr(merged['returns_2'], method='spearman')
                elif method == 'kendall':
                    correlation = merged['returns_1'].corr(merged['returns_2'], method='kendall')
                else:
                    raise ValueError(f"Unsupported correlation method: {method}")
                
                return correlation
        
        except Exception as e:
            logger.error(f"Error calculating correlation: {str(e)}")
            return None
    
    def calculate_correlation_matrix(self, symbols_data):
        """
        Calculate correlation matrix for multiple symbols.
        
        Args:
            symbols_data: Dict of symbol to DataFrame mappings
            
        Returns:
            DataFrame: Correlation matrix
        """
        try:
            # Prepare returns data
            returns_data = {}
            for symbol, data in symbols_data.items():
                returns = data['close'].pct_change()
                returns_data[symbol] = returns
            
            # Create DataFrame of returns
            returns_df = pd.DataFrame(returns_data)
            returns_df = returns_df.dropna()
            
            # Calculate correlation matrix
            correlation_matrix = returns_df.corr(method='pearson')
            
            return correlation_matrix
        
        except Exception as e:
            logger.error(f"Error calculating correlation matrix: {str(e)}")
            return None
    
    def check_buy_conditions(self, primary_data, correlated_data):
        """
        Check conditions for generating a buy signal.
        
        Args:
            primary_data: DataFrame with primary symbol's data
            correlated_data: DataFrame with correlated symbol's data
            
        Returns:
            (bool, str): Whether conditions are met and description
        """
        try:
            if primary_data is None or correlated_data is None:
                return False, "Missing market data"
            
            # Validate minimum data points
            min_data_points = 20  # Minimum required for reliable correlation
            if len(primary_data) < min_data_points or len(correlated_data) < min_data_points:
                return False, f"Insufficient data points (minimum {min_data_points} required)"
            
            # Get latest data points
            primary_latest = primary_data.iloc[-1]
            correlated_latest = correlated_data.iloc[-1]
            
            # Calculate correlation
            correlation = self.calculate_correlation(primary_data, correlated_data)
            if correlation is None:
                return False, "Failed to calculate correlation"
            
            # Debug: log the correlation value
            logger.info(f"[DEBUG] Correlation value: {correlation}")
            
            # Restore correlation threshold check
            correlation_threshold = None
            for rule in self.config.entry_rules:
                if rule.rule_type == 'Correlation' and rule.correlation_threshold:
                    correlation_threshold = rule.correlation_threshold
                    break
            if correlation_threshold is None:
                correlation_threshold = 0.7  # Default threshold
            if correlation < correlation_threshold:
                return False, f"Correlation {correlation:.2f} below threshold {correlation_threshold}"
            
            # Get price conditions
            primary_price = primary_latest['close']
            correlated_price = correlated_latest['close']
            
            # Get Swing High/Low levels
            primary_sh = primary_data['high'].rolling(20).max().iloc[-1]
            primary_sl = primary_data['low'].rolling(20).min().iloc[-1]
            correlated_sh = correlated_data['high'].rolling(20).max().iloc[-1]
            correlated_sl = correlated_data['low'].rolling(20).min().iloc[-1]
            
            # Check buy conditions
            if primary_price > primary_sh and correlated_price < correlated_sl:
                return True, f"Buy signal: Primary price {primary_price:.2f} > SH {primary_sh:.2f}, Correlated price {correlated_price:.2f} < SL {correlated_sl:.2f} (correlation: {correlation:.2f})"
            
            return False, "Buy conditions not met"
        
        except Exception as e:
            logger.error(f"Error checking buy conditions: {str(e)}")
            return False, f"Error: {str(e)}"
    
    def check_sell_conditions(self, primary_data, correlated_data):
        """
        Check conditions for generating a sell signal.
        
        Args:
            primary_data: DataFrame with primary symbol's data
            correlated_data: DataFrame with correlated symbol's data
            
        Returns:
            (bool, str): Whether conditions are met and description
        """
        try:
            if primary_data is None or correlated_data is None:
                return False, "Missing market data"
            
            # Validate minimum data points
            min_data_points = 20  # Minimum required for reliable correlation
            if len(primary_data) < min_data_points or len(correlated_data) < min_data_points:
                return False, f"Insufficient data points (minimum {min_data_points} required)"
            
            # Get latest data points
            primary_latest = primary_data.iloc[-1]
            correlated_latest = correlated_data.iloc[-1]
            
            # Calculate correlation
            correlation = self.calculate_correlation(primary_data, correlated_data)
            if correlation is None:
                return False, "Failed to calculate correlation"
            
            # Debug: log the correlation value
            logger.info(f"[DEBUG] Correlation value: {correlation}")
            
            # Restore correlation threshold check
            correlation_threshold = None
            for rule in self.config.entry_rules:
                if rule.rule_type == 'Correlation' and rule.correlation_threshold:
                    correlation_threshold = rule.correlation_threshold
                    break
            if correlation_threshold is None:
                correlation_threshold = 0.7  # Default threshold
            if correlation < correlation_threshold:
                return False, f"Correlation {correlation:.2f} below threshold {correlation_threshold}"
            
            # Check price conditions
            primary_price = primary_latest['close']
            correlated_price = correlated_latest['close']
            
            # Get Swing High/Low levels
            primary_sh = primary_data['high'].rolling(20).max().iloc[-1]
            primary_sl = primary_data['low'].rolling(20).min().iloc[-1]
            correlated_sh = correlated_data['high'].rolling(20).max().iloc[-1]
            correlated_sl = correlated_data['low'].rolling(20).min().iloc[-1]
            
            # Check sell conditions
            if primary_price < primary_sl and correlated_price > correlated_sh:
                return True, f"Sell signal: Primary price {primary_price:.2f} < SL {primary_sl:.2f}, Correlated price {correlated_price:.2f} > SH {correlated_sh:.2f} (correlation: {correlation:.2f})"
            
            return False, "Sell conditions not met"
        
        except Exception as e:
            logger.error(f"Error checking sell conditions: {str(e)}")
            return False, f"Error: {str(e)}"
    
    def generate_signal(self, config, check_duplicate_signals=None):
        session = self.Session()
        try:
            # Get symbols
            symbols = session.query(SignalSymbol).filter(SignalSymbol.config_id == config.id).all()
            if not symbols:
                logger.warning(f"No symbols found for config {config.name}")
                return []
            # Find primary and correlated symbols
            primary_symbol = next((s for s in symbols if s.is_primary), None)
            correlated_symbol = next((s for s in symbols if not s.is_primary), None)
            if not primary_symbol or not correlated_symbol:
                logger.warning("Missing primary or correlated symbol")
                return []
            # Get market data
            primary_data = self.get_market_data(primary_symbol.symbol, primary_symbol.timeframe, lookback=25)
            correlated_data = self.get_market_data(correlated_symbol.symbol, correlated_symbol.timeframe, lookback=25)
            if primary_data is None or correlated_data is None:
                return []
            signals = []
            # Check for buy signals
            if config.signal_direction in ['Long', 'Both']:
                buy_condition, buy_description = self.check_buy_conditions(primary_data, correlated_data)
                if buy_condition:
                    # Prevent duplicate signals
                    duplicate = False
                    if check_duplicate_signals:
                        duplicate = check_duplicate_signals(
                            config, primary_symbol.symbol, 'Long', primary_data.iloc[-1]['close'], primary_symbol.timeframe
                        )
                    else:
                        # Fallback: check in DB for same config/symbol/direction/price/timeframe in last 15min
                        cutoff_time = datetime.utcnow() - timedelta(minutes=15)
                        existing = session.query(GeneratedSignal).filter(
                            GeneratedSignal.config_id == config.id,
                            GeneratedSignal.symbol == primary_symbol.symbol,
                            GeneratedSignal.direction == 'Long',
                            GeneratedSignal.price == primary_data.iloc[-1]['close'],
                            GeneratedSignal.timeframe == primary_symbol.timeframe,
                            GeneratedSignal.signal_time > cutoff_time
                        ).first()
                        duplicate = existing is not None
                    if not duplicate:
                        signal = GeneratedSignal(
                            config_id=config.id,
                            symbol=primary_symbol.symbol,
                            token=primary_symbol.token,
                            direction='Long',
                            price=primary_data.iloc[-1]['close'],
                            timeframe=primary_symbol.timeframe,
                            status='New'
                        )
                        session.add(signal)
                        signals.append(signal)
                        logger.info(f"Generated buy signal: {buy_description}")
                    else:
                        logger.info(f"Duplicate buy signal detected, skipping.")
            # Check for sell signals
            if config.signal_direction in ['Short', 'Both']:
                sell_condition, sell_description = self.check_sell_conditions(primary_data, correlated_data)
                if sell_condition:
                    duplicate = False
                    if check_duplicate_signals:
                        duplicate = check_duplicate_signals(
                            config, primary_symbol.symbol, 'Short', primary_data.iloc[-1]['close'], primary_symbol.timeframe
                        )
                    else:
                        cutoff_time = datetime.utcnow() - timedelta(minutes=15)
                        existing = session.query(GeneratedSignal).filter(
                            GeneratedSignal.config_id == config.id,
                            GeneratedSignal.symbol == primary_symbol.symbol,
                            GeneratedSignal.direction == 'Short',
                            GeneratedSignal.price == primary_data.iloc[-1]['close'],
                            GeneratedSignal.timeframe == primary_symbol.timeframe,
                            GeneratedSignal.signal_time > cutoff_time
                        ).first()
                        duplicate = existing is not None
                    if not duplicate:
                        signal = GeneratedSignal(
                            config_id=config.id,
                            symbol=primary_symbol.symbol,
                            token=primary_symbol.token,
                            direction='Short',
                            price=primary_data.iloc[-1]['close'],
                            timeframe=primary_symbol.timeframe,
                            status='New'
                        )
                        session.add(signal)
                        signals.append(signal)
                        logger.info(f"Generated sell signal: {sell_description}")
                    else:
                        logger.info(f"Duplicate sell signal detected, skipping.")
            if signals:
                session.commit()
            return signals
        except Exception as e:
            logger.error(f"Error generating signals: {str(e)}")
            session.rollback()
            return []
        finally:
            session.close()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test the strategy
    strategy = CorrelationStrategy()
    # Add test code here 
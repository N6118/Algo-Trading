import time
import logging
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.signal_scanner.db_schema import GeneratedSignal, SignalConfig
from app.models.signal_generation import SignalGeneration, ExchangeType, OrderType, ProductType, OrderSide, SignalStatus, MarketSession
from app.database import Base

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection (adjust as needed)
DB_URI = 'postgresql://postgres:password@100.121.186.86:5432/theodb'  # Update with your actual URI
engine = create_engine(DB_URI)
Session = sessionmaker(bind=engine)

POLL_INTERVAL = 10  # seconds

# Sensible defaults (customize as needed)
DEFAULT_USER_ID = 1
DEFAULT_EXCHANGE = ExchangeType.SMART
DEFAULT_ORDER_TYPE = OrderType.MARKET
DEFAULT_PRODUCT_TYPE = ProductType.MARGIN
DEFAULT_CONTRACT_SIZE = 1
DEFAULT_QUANTITY = 1
DEFAULT_MARKET_SESSION = MarketSession.REGULAR


def promote_signals():
    session = Session()
    try:
        # Fetch new signals
        new_signals = session.query(GeneratedSignal).filter(GeneratedSignal.status == 'New').all()
        for gs in new_signals:
            try:
                # Fetch config for additional info if needed
                config = session.query(SignalConfig).filter(SignalConfig.id == gs.config_id).first()
                # Map direction to side
                side = OrderSide.BUY if gs.direction == 'Long' else OrderSide.SELL
                # Map or use defaults for required fields
                signal = SignalGeneration(
                    user_id=DEFAULT_USER_ID,  # TODO: Map from config/user if available
                    strategy_id=gs.config_id,
                    symbol=gs.symbol,
                    exchange=DEFAULT_EXCHANGE,
                    order_type=DEFAULT_ORDER_TYPE,
                    product_type=DEFAULT_PRODUCT_TYPE,
                    side=side,
                    contract_size=DEFAULT_CONTRACT_SIZE,
                    quantity=DEFAULT_QUANTITY,
                    entry_price=gs.price,
                    stop_loss=gs.stop_loss,
                    take_profit=gs.take_profit,
                    status=SignalStatus.PENDING,
                    market_session=DEFAULT_MARKET_SESSION,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    is_active=True
                )
                session.add(signal)
                session.commit()
                # Mark original signal as promoted
                gs.status = 'Promoted'
                session.commit()
                logger.info(f"Promoted GeneratedSignal {gs.id} ({gs.symbol}, {gs.direction}) to SignalGeneration {signal.id}")
            except Exception as e:
                logger.error(f"Error promoting GeneratedSignal {gs.id}: {e}")
                session.rollback()
    except Exception as e:
        logger.error(f"Error in promotion loop: {e}")
    finally:
        session.close()


def main():
    logger.info("Starting automated signal promotion service...")
    while True:
        promote_signals()
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main() 
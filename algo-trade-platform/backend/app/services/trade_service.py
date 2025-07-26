import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.trade import Trade, TradeStatus
from app.models.signal_generation import ExchangeType, OrderSide
from app.models.risk_settings import RiskSettings
from app.services.market_data_service import MarketDataService
from app.services.order_service import OrderService

logger = logging.getLogger("trade-service")

class RiskException(Exception):
    pass

class ComplianceException(Exception):
    pass

class TechnicalException(Exception):
    pass

class TradeService:
    def __init__(self, db: Session):
        self.db = db
        self.market_data_service = MarketDataService(db)
        self.order_service = OrderService(db)

    def _get_risk_settings(self, db: Session, user_id: int, strategy_id: int):
        """Fetch risk settings for user+strategy, user, strategy, or global (in that order)."""
        settings = (
            db.query(RiskSettings)
            .filter(RiskSettings.user_id == user_id, RiskSettings.strategy_id == strategy_id)
            .first()
        )
        if settings:
            logger.info(f"Using user+strategy risk settings: {settings}")
            return settings
        settings = (
            db.query(RiskSettings)
            .filter(RiskSettings.user_id == user_id, RiskSettings.strategy_id == None)
            .first()
        )
        if settings:
            logger.info(f"Using user risk settings: {settings}")
            return settings
        settings = (
            db.query(RiskSettings)
            .filter(RiskSettings.user_id == None, RiskSettings.strategy_id == strategy_id)
            .first()
        )
        if settings:
            logger.info(f"Using strategy risk settings: {settings}")
            return settings
        settings = (
            db.query(RiskSettings)
            .filter(RiskSettings.user_id == None, RiskSettings.strategy_id == None)
            .first()
        )
        if settings:
            logger.info(f"Using global risk settings: {settings}")
            return settings
        logger.info("No risk settings found, using hardcoded defaults.")
        return None

    def create_trade(self, user_id, strategy_id, signal_id, symbol, exchange, side, quantity, entry_price, stop_loss=None, take_profit=None):
        # Fetch risk settings
        risk_settings = self._get_risk_settings(self.db, user_id, strategy_id)
        max_active_trades = risk_settings.max_active_trades if risk_settings else 10
        max_trades_per_day = risk_settings.max_trades_per_day if risk_settings else 20
        max_risk_pct = risk_settings.max_risk_per_trade_pct if risk_settings else 0.02
        max_total_risk_pct = risk_settings.max_total_risk_pct if risk_settings else 0.05
        # Use these in all relevant checks below

        # 1. Number of active trades
        active_trades = self.db.query(Trade).filter(Trade.user_id == user_id, Trade.status == TradeStatus.RUNNING, Trade.is_active == True).count()
        if active_trades >= max_active_trades:
            logger.warning(f"User {user_id} has too many active trades.")
            raise RiskException("Too many active trades.")

        # 2. Number of trades per day
        today = datetime.utcnow().date()
        trades_today = self.db.query(Trade).filter(Trade.user_id == user_id, Trade.created_at >= datetime(today.year, today.month, today.day)).count()
        if trades_today >= max_trades_per_day:
            logger.warning(f"User {user_id} exceeded daily trade limit.")
            raise RiskException("Exceeded daily trade limit.")

        # 3. PDT rule check (use OrderService logic)
        if not self.order_service._check_pdt_rules():
            logger.warning(f"User {user_id} violates PDT rule.")
            raise ComplianceException("Pattern Day Trader rule violation.")

        # 4. Initial profit target and 5. Initial stop-loss price (basic validation)
        if stop_loss is not None and stop_loss >= entry_price:
            raise RiskException("Stop loss must be below entry price for BUY, above for SELL.")
        if take_profit is not None and take_profit <= entry_price:
            raise RiskException("Take profit must be above entry price for BUY, below for SELL.")

        # 6. Account risk percentage (fetch real equity)
        try:
            account_equity = self.market_data_service.get_account_equity()
        except Exception as e:
            logger.error(f"Failed to fetch account equity: {e}")
            raise TechnicalException("Failed to fetch account equity.")
        max_risk = account_equity * max_risk_pct

        # 7. Calculate number of shares based on risk (placeholder logic)
        risk_per_share = abs(entry_price - stop_loss) if stop_loss else 1
        if risk_per_share == 0:
            raise RiskException("Invalid stop loss or entry price.")
        max_shares = int(max_risk / risk_per_share)
        if quantity > max_shares:
            raise RiskException(f"Quantity exceeds allowed risk. Max: {max_shares}")

        # 8. Calculate trade risk
        trade_risk = risk_per_share * quantity
        if trade_risk > max_risk:
            raise RiskException("Trade risk exceeds allowed per-trade risk.")

        # 9. Calculate total risk percentage (placeholder, sum of all open trades)
        open_trades = self.db.query(Trade).filter(Trade.user_id == user_id, Trade.status == TradeStatus.RUNNING, Trade.is_active == True).all()
        total_risk = sum(abs(t.entry_price - (t.stop_loss or t.entry_price)) * t.quantity for t in open_trades) + trade_risk
        if total_risk > account_equity * max_total_risk_pct:
            raise RiskException("Total risk exceeds allowed account risk.")

        # 10. Adjust stop loss (optional, placeholder)
        # Could auto-adjust stop loss here if needed

        # 11. Reg-T margin check (use OrderService logic)
        order_value = quantity * entry_price
        if not self.order_service._check_reg_t_margin(order_value):
            raise RiskException("Insufficient margin for order.")

        # 8. Place order and persist trade atomically
        from sqlalchemy.exc import SQLAlchemyError
        try:
            with self.db.begin():
                order_params = {
                    "symbol": symbol,
                    "exchange": exchange,
                    "order_type": self._get_order_type(stop_loss, take_profit),
                    "side": side,
                    "quantity": quantity,
                    "entry_price": entry_price,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit
                }
                if stop_loss and take_profit:
                    order_result = self.order_service.create_bracket_order(order_params)
                else:
                    order_result = self.order_service.create_order(order_params)
                if not order_result or order_result.get("status") not in ("Submitted", "PreSubmitted", "Filled"):
                    logger.error(f"Order not placed successfully: {order_result}")
                    raise ComplianceException("Order not placed successfully.")
                trade = Trade(
                    user_id=user_id,
                    strategy_id=strategy_id,
                    signal_id=signal_id,
                    symbol=symbol,
                    exchange=exchange.value if hasattr(exchange, 'value') else str(exchange),
                    side=side.value if hasattr(side, 'value') else str(side),
                    quantity=quantity,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    status=TradeStatus.RUNNING,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    order_id=order_result.get("id"),
                    order_status=order_result.get("status")
                )
                self.db.add(trade)
                logger.info(f"Trade created and order placed atomically: Trade ID (pending) Order ID {order_result.get('id')}")
            self.db.refresh(trade)
            logger.info(f"Trade committed: Trade ID {trade.id}, Order ID {order_result.get('id')}")
            return trade
        except (SQLAlchemyError, RiskException, ComplianceException, TechnicalException) as e:
            logger.error(f"Atomic trade/order transaction failed: {e}")
            self.db.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error in atomic trade/order transaction: {e}")
            self.db.rollback()
            raise TechnicalException(f"Unexpected error: {e}")

    def _get_order_type(self, stop_loss, take_profit):
        if stop_loss and take_profit:
            return self.order_service.OrderType.BRACKET if hasattr(self.order_service, 'OrderType') else "BRACKET"
        return self.order_service.OrderType.MARKET if hasattr(self.order_service, 'OrderType') else "MARKET" 
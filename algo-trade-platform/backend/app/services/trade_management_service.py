import threading
import time
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.trade import Trade, TradeStatus
from app.services.market_data_service import MarketDataService

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("trade-management-service")

class TradeManagementService:
    def __init__(self, db: Session):
        self.db = db
        self.market_data_service = MarketDataService(db)
        self.active = False
        self.monitor_thread = None
        self.interval = 5  # seconds

    def start(self):
        if self.active:
            logger.info("Trade monitoring already running.")
            return
        self.active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("✅ Trade monitoring started.")

    def stop(self):
        self.active = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("✅ Trade monitoring stopped.")

    def _monitor_loop(self):
        while self.active:
            try:
                self._monitor_trades()
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"❌ Error in trade monitoring loop: {e}")

    def _monitor_trades(self):
        RR_TRIGGER = 2.0  # Risk-reward ratio to trigger reduction
        REDUCTION_PCT = 0.5  # Sell 50% of position
        running_trades = self.db.query(Trade).filter(Trade.status == TradeStatus.RUNNING, Trade.is_active == True).all()
        now_utc = datetime.utcnow()
        market_close_utc = now_utc.replace(hour=20, minute=0, second=0, microsecond=0)  # 20:00 UTC (16:00 ET)

        # --- BEGIN DRAWNDOWN ENFORCEMENT ---
        # Group trades by user
        from app.models.risk_settings import RiskSettings
        user_ids = set([t.user_id for t in running_trades])
        for user_id in user_ids:
            # Get risk settings for user (global if not found)
            risk_settings = (
                self.db.query(RiskSettings)
                .filter(RiskSettings.user_id == user_id)
                .first()
            )
            if not risk_settings:
                risk_settings = self.db.query(RiskSettings).filter(RiskSettings.user_id == None).first()
            rm_max_sp = risk_settings.rm_max_sp if risk_settings else 0.2
            # Calculate realized P&L (closed trades)
            realized_pnl = sum(
                t.pnl or 0 for t in self.db.query(Trade).filter(Trade.user_id == user_id, Trade.status == TradeStatus.CLOSED).all()
            )
            # Calculate unrealized P&L (open trades)
            user_running_trades = [t for t in running_trades if t.user_id == user_id]
            unrealized_pnl = 0
            for t in user_running_trades:
                current_price = self.market_data_service.get_current_price(t.symbol)
                if t.side.name == "BUY":
                    unrealized_pnl += (current_price - t.entry_price) * t.quantity
                else:
                    unrealized_pnl += (t.entry_price - current_price) * t.quantity
            # Fetch account equity (assume method exists)
            try:
                account_equity = self.market_data_service.get_account_equity()
            except Exception:
                account_equity = 1  # fallback to avoid division by zero
            total_pnl = realized_pnl + unrealized_pnl
            drawdown_pct = -total_pnl / account_equity if account_equity > 0 else 0
            # If drawdown exceeds limit, close all open trades for user
            if drawdown_pct >= rm_max_sp:
                for t in user_running_trades:
                    current_price = self.market_data_service.get_current_price(t.symbol)
                    self._close_trade(t, current_price, reason=f"Drawdown limit {rm_max_sp*100:.1f}% exceeded")
                logger.warning(f"User {user_id} drawdown {drawdown_pct*100:.2f}% exceeded limit {rm_max_sp*100:.2f}%. All trades closed.")
                self.db.commit()
                continue  # skip further processing for this user
            # If drawdown approaches 80% of limit, tighten stop losses
            if drawdown_pct >= 0.8 * rm_max_sp:
                for t in user_running_trades:
                    current_price = self.market_data_service.get_current_price(t.symbol)
                    if t.side.name == "BUY":
                        new_stop = max(t.stop_loss or t.entry_price, current_price * 0.995)
                        if not t.stop_loss or new_stop > t.stop_loss:
                            logger.info(f"Tightening stop loss for trade {t.id} due to drawdown risk: {new_stop}")
                            t.stop_loss = new_stop
                    else:
                        new_stop = min(t.stop_loss or t.entry_price, current_price * 1.005)
                        if not t.stop_loss or new_stop < t.stop_loss:
                            logger.info(f"Tightening stop loss for trade {t.id} due to drawdown risk: {new_stop}")
                            t.stop_loss = new_stop
        # --- END DRAWNDOWN ENFORCEMENT ---

        for trade in running_trades:
            try:
                current_price = self.market_data_service.get_current_price(trade.symbol)
                if current_price is None:
                    logger.warning(f"No price for {trade.symbol}, skipping trade {trade.id}")
                    continue
                # 1. Time-based closure
                if now_utc >= market_close_utc:
                    self._close_trade(trade, current_price, reason="Time-based Closure (Market Close)")
                    continue
                # 2. Exit rule monitoring (placeholder)
                # TODO: Implement custom exit rules per strategy
                # if self._check_exit_rule(trade, current_price):
                #     self._close_trade(trade, current_price, reason="Exit Rule Triggered")
                #     continue
                # 3. Trailing stop-loss (dynamic adjustment)
                if trade.side.name == "BUY" and trade.take_profit and current_price > trade.entry_price:
                    new_stop = max(trade.stop_loss or trade.entry_price, current_price * 0.99)
                    if not trade.stop_loss or new_stop > trade.stop_loss:
                        logger.info(f"Adjusting stop loss for trade {trade.id} to {new_stop}")
                        trade.stop_loss = new_stop
                elif trade.side.name == "SELL" and trade.take_profit and current_price < trade.entry_price:
                    new_stop = min(trade.stop_loss or trade.entry_price, current_price * 1.01)
                    if not trade.stop_loss or new_stop < trade.stop_loss:
                        logger.info(f"Adjusting stop loss for trade {trade.id} to {new_stop}")
                        trade.stop_loss = new_stop
                # 4. RR-triggered risk reduction (partial sell)
                if not trade.risk_reduced and trade.stop_loss and trade.quantity > 1:
                    initial_risk = abs(trade.entry_price - trade.stop_loss)
                    if initial_risk > 0:
                        rr = abs(current_price - trade.entry_price) / initial_risk
                        if rr >= RR_TRIGGER:
                            reduction_qty = int(trade.quantity * REDUCTION_PCT)
                            if reduction_qty < 1:
                                reduction_qty = 1
                            logger.info(f"RR-triggered risk reduction for trade {trade.id}: RR={rr:.2f}, selling {reduction_qty}")
                            # Place market sell order for reduction_qty
                            from app.services.order_service import OrderService, OrderSide
                            order_service = OrderService(self.db)
                            side = OrderSide.SELL if trade.side.name == "BUY" else OrderSide.BUY
                            order_params = {
                                "symbol": trade.symbol,
                                "exchange": trade.exchange,
                                "order_type": "MARKET",
                                "side": side,
                                "quantity": reduction_qty,
                                "entry_price": current_price
                            }
                            try:
                                order_result = order_service.create_order(order_params)
                                if order_result and order_result.get("status") in ("Submitted", "PreSubmitted", "Filled"):
                                    trade.quantity -= reduction_qty
                                    trade.risk_reduced = True
                                    trade.risk_reduction_qty = reduction_qty
                                    # Move stop-loss to entry price (break-even)
                                    trade.stop_loss = trade.entry_price
                                    logger.info(f"Risk reduction executed for trade {trade.id}. New qty: {trade.quantity}, stop_loss moved to entry.")
                                else:
                                    logger.error(f"Risk reduction order failed for trade {trade.id}: {order_result}")
                            except Exception as e:
                                logger.error(f"Risk reduction order error for trade {trade.id}: {e}")
                # Check stop loss
                if trade.stop_loss and ((trade.side.name == "BUY" and current_price <= trade.stop_loss) or (trade.side.name == "SELL" and current_price >= trade.stop_loss)):
                    self._close_trade(trade, current_price, reason="Stop Loss Hit")
                # Check take profit
                elif trade.take_profit and ((trade.side.name == "BUY" and current_price >= trade.take_profit) or (trade.side.name == "SELL" and current_price <= trade.take_profit)):
                    self._close_trade(trade, current_price, reason="Take Profit Hit")
            except Exception as e:
                logger.error(f"Error monitoring trade {trade.id}: {e}")
        self.db.commit()

    def _close_trade(self, trade, exit_price, reason="Closed"):
        trade.exit_price = exit_price
        trade.closed_at = datetime.utcnow()
        trade.status = TradeStatus.CLOSED
        trade.is_active = False
        if trade.side.name == "BUY":
            trade.pnl = (exit_price - trade.entry_price) * trade.quantity
        else:
            trade.pnl = (trade.entry_price - exit_price) * trade.quantity
        logger.info(f"Closed trade {trade.id} ({trade.symbol}) at {exit_price} due to {reason}. PnL: {trade.pnl}")

# Background entry point for main.py
_service_instance = None

def start_trade_monitoring():
    global _service_instance
    from app.database import get_db
    db = next(get_db())
    _service_instance = TradeManagementService(db)
    _service_instance.start() 
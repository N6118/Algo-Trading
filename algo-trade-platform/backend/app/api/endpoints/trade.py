from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from app.database import get_db
from app.services.trade_service import TradeService, RiskException, ComplianceException, TechnicalException
from app.models.signal_generation import ExchangeType, OrderSide
from app.models.trade import TradeStatus
import logging

router = APIRouter()
logger = logging.getLogger("trade-endpoint")

class TradeCreateRequest(BaseModel):
    user_id: int
    strategy_id: int
    signal_id: Optional[int] = None
    symbol: str
    exchange: ExchangeType
    side: OrderSide
    quantity: int
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

class TradeResponse(BaseModel):
    id: int
    user_id: int
    strategy_id: int
    signal_id: Optional[int]
    symbol: str
    exchange: ExchangeType
    side: OrderSide
    quantity: int
    entry_price: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    status: TradeStatus
    created_at: str
    updated_at: str

@router.post("/trades", response_model=TradeResponse)
def create_trade(request: TradeCreateRequest, db: Session = Depends(get_db)):
    try:
        trade = TradeService(db).create_trade(
            user_id=request.user_id,
            strategy_id=request.strategy_id,
            signal_id=request.signal_id,
            symbol=request.symbol,
            exchange=request.exchange,
            side=request.side,
            quantity=request.quantity,
            entry_price=request.entry_price,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit
        )
        return TradeResponse.from_orm(trade)
    except RiskException as e:
        logger.warning(f"Risk error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ComplianceException as e:
        logger.warning(f"Compliance error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except TechnicalException as e:
        logger.error(f"Technical error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred.") 
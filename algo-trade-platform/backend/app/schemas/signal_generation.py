from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.signal_generation import ExchangeType, OrderType, ProductType

class SignalGenerationBase(BaseModel):
    user_id: int
    strategy_id: int
    symbol: str
    exchange: ExchangeType
    order_type: OrderType
    product_type: ProductType
    contract_size: int
    quantity: int
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

class SignalGenerationCreate(SignalGenerationBase):
    pass

class SignalGenerationUpdate(BaseModel):
    symbol: Optional[str] = None
    exchange: Optional[ExchangeType] = None
    order_type: Optional[OrderType] = None
    product_type: Optional[ProductType] = None
    contract_size: Optional[int] = None
    quantity: Optional[int] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None

class SignalGeneration(SignalGenerationBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        orm_mode = True 
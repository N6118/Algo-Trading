from fastapi import APIRouter
from app.api.endpoints import signal_generation
from app.api.endpoints import trade

api_router = APIRouter()

# ... existing code ...

# Add signal generation endpoints
api_router.include_router(
    signal_generation.router,
    prefix="/signals",
    tags=["signals"]
)

app.include_router(trade.router, prefix="/api", tags=["Trades"]) 
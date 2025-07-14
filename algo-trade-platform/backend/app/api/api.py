from fastapi import APIRouter
from app.api.endpoints import signal_generation

api_router = APIRouter()

# ... existing code ...

# Add signal generation endpoints
api_router.include_router(
    signal_generation.router,
    prefix="/signals",
    tags=["signals"]
) 
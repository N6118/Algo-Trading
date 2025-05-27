from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from datetime import datetime
import time
import threading

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"logs/api_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("algo-trade-api")

# Create FastAPI app
app = FastAPI(
    title="Algorithmic Trading Platform API",
    description="API for managing algorithmic trading strategies and executions",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers after app creation
from app.api.routes import market_data, strategies, trades, settings

# Register routers
app.include_router(market_data.router, prefix="/api/market-data", tags=["Market Data"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["Strategies"])
app.include_router(trades.router, prefix="/api/trades", tags=["Trades"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])

# Background services
background_services = []

@app.on_event("startup")
async def startup_event():
    """Start background services when the application starts"""
    from app.services.market_data_service import start_market_data_collection
    from app.services.signal_service import start_signal_scanning
    from app.services.trade_monitor_service import start_trade_monitoring
    
    logger.info("Starting background services...")
    
    # Start market data collection in background
    market_data_thread = threading.Thread(
        target=start_market_data_collection,
        daemon=True
    )
    market_data_thread.start()
    background_services.append(market_data_thread)
    
    # Start signal scanning in background (15-minute intervals)
    signal_thread = threading.Thread(
        target=start_signal_scanning,
        daemon=True
    )
    signal_thread.start()
    background_services.append(signal_thread)
    
    # Start trade monitoring in background (5-second intervals)
    monitor_thread = threading.Thread(
        target=start_trade_monitoring,
        daemon=True
    )
    monitor_thread.start()
    background_services.append(monitor_thread)
    
    logger.info("All background services started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup when the application shuts down"""
    logger.info("Shutting down application...")
    # Any cleanup code goes here

@app.get("/")
async def root():
    """Root endpoint to check if API is running"""
    return {
        "status": "online",
        "name": "Algorithmic Trading Platform API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "market_data": "running" if any(t.name == "market_data" for t in background_services) else "stopped",
            "signal_scanning": "running" if any(t.name == "signal_scanning" for t in background_services) else "stopped",
            "trade_monitoring": "running" if any(t.name == "trade_monitoring" for t in background_services) else "stopped"
        },
        "timestamp": datetime.now().isoformat()
    }

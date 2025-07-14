from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.signal_generation import (
    SignalGeneration,
    SignalGenerationCreate,
    SignalGenerationUpdate
)
from app.services.signal_generation_service import SignalGenerationService

router = APIRouter()

@router.post("/", response_model=SignalGeneration)
def create_signal(
    signal: SignalGenerationCreate,
    db: Session = Depends(get_db)
):
    """Create a new signal generation entry"""
    service = SignalGenerationService(db)
    return service.create_signal(signal)

@router.get("/{signal_id}", response_model=SignalGeneration)
def get_signal(
    signal_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific signal by ID"""
    service = SignalGenerationService(db)
    signal = service.get_signal(signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return signal

@router.get("/user/{user_id}", response_model=List[SignalGeneration])
def get_user_signals(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all signals for a specific user"""
    service = SignalGenerationService(db)
    return service.get_user_signals(user_id, skip, limit)

@router.get("/active/", response_model=List[SignalGeneration])
def get_active_signals(
    db: Session = Depends(get_db)
):
    """Get all active signals"""
    service = SignalGenerationService(db)
    return service.get_active_signals()

@router.put("/{signal_id}", response_model=SignalGeneration)
def update_signal(
    signal_id: int,
    signal: SignalGenerationUpdate,
    db: Session = Depends(get_db)
):
    """Update a signal"""
    service = SignalGenerationService(db)
    updated_signal = service.update_signal(signal_id, signal)
    if not updated_signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return updated_signal

@router.delete("/{signal_id}", response_model=SignalGeneration)
def deactivate_signal(
    signal_id: int,
    db: Session = Depends(get_db)
):
    """Deactivate a signal"""
    service = SignalGenerationService(db)
    signal = service.deactivate_signal(signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return signal

@router.post("/{signal_id}/process", response_model=bool)
def process_signal(
    signal_id: int,
    db: Session = Depends(get_db)
):
    """Process a signal and generate orders"""
    service = SignalGenerationService(db)
    success = service.process_signal(signal_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to process signal")
    return success 
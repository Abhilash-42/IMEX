from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from database.session import get_db
from database.models import Event, Port, Supplier, User, RiskReport
from services.auth import (
    get_current_active_user,
    get_current_manager_or_admin,
    get_current_admin_user,
)

router = APIRouter()

# Pydantic schemas
class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    event_type: str
    severity: float = Field(0.0, ge=0, le=100)
    location: Optional[str] = None
    country: Optional[str] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    estimated_duration_days: Optional[int] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    is_active: bool = True

class EventCreate(EventBase):
    port_id: Optional[int] = None
    supplier_id: Optional[int] = None

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[str] = None
    severity: Optional[float] = Field(None, ge=0, le=100)
    location: Optional[str] = None
    country: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    estimated_duration_days: Optional[int] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    is_active: Optional[bool] = None
    port_id: Optional[int] = None
    supplier_id: Optional[int] = None

class EventResponse(EventBase):
    id: int
    port_id: Optional[int]
    supplier_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class EventDetailResponse(EventResponse):
    port: Optional[dict] = None
    supplier: Optional[dict] = None
    risk_reports: List[dict] = []

class EventListResponse(BaseModel):
    total: int
    events: List[EventResponse]

@router.get("/", response_model=EventListResponse)
async def get_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    event_type: Optional[str] = None,
    min_severity: Optional[float] = Query(None, ge=0, le=100),
    is_active: Optional[bool] = None,
    country: Optional[str] = None,
    start_date_from: Optional[datetime] = None,
    start_date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all events with filtering and pagination"""
    query = db.query(Event)
    
    # Apply filters
    if search:
        query = query.filter(
            or_(
                Event.title.ilike(f"%{search}%"),
                Event.description.ilike(f"%{search}%"),
                Event.location.ilike(f"%{search}%")
            )
        )
    
    if event_type:
        query = query.filter(Event.event_type == event_type)
    
    if min_severity is not None:
        query = query.filter(Event.severity >= min_severity)
    
    if is_active is not None:
        query = query.filter(Event.is_active == is_active)
    
    if country:
        query = query.filter(Event.country == country)
    
    if start_date_from:
        query = query.filter(Event.start_date >= start_date_from)
    
    if start_date_to:
        query = query.filter(Event.start_date <= start_date_to)
    
    total = query.count()
    events = query.order_by(Event.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "events": events
    }

@router.get("/{event_id}", response_model=EventDetailResponse)
async def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get event by ID with related data"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Get related data
    port = None
    if event.port_id:
        port = db.query(Port).filter(Port.id == event.port_id).first()
    
    supplier = None
    if event.supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == event.supplier_id).first()
    
    # Get risk reports
    risk_reports = db.query(RiskReport).filter(
        RiskReport.event_id == event.id
    ).order_by(RiskReport.created_at.desc()).all()
    
    response = EventDetailResponse.from_orm(event)
    response.port = {"id": port.id, "name": port.name, "country": port.country} if port else None
    response.supplier = {"id": supplier.id, "name": supplier.name} if supplier else None
    response.risk_reports = [
        {
            "id": r.id,
            "risk_score": r.risk_score,
            "revenue_exposure": r.revenue_exposure,
            "created_at": r.created_at
        }
        for r in risk_reports
    ]
    
    return response

@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager_or_admin)
):
    """Create a new event"""
    # Check if event already exists
    existing = db.query(Event).filter(
        Event.title == event.title,
        Event.source == event.source
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Event with this title and source already exists"
        )
    
    # Validate port if provided
    if event.port_id:
        port = db.query(Port).filter(Port.id == event.port_id).first()
        if not port:
            raise HTTPException(status_code=400, detail="Port not found")
    
    # Validate supplier if provided
    if event.supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == event.supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=400, detail="Supplier not found")
    
    # Create event
    db_event = Event(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    return db_event

@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_update: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager_or_admin)
):
    """Update event by ID"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Update fields
    update_data = event_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)
    
    event.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(event)
    
    return event

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete event by ID (Admin only)"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Delete associated risk reports first
    db.query(RiskReport).filter(RiskReport.event_id == event_id).delete()
    
    db.delete(event)
    db.commit()

@router.get("/stats/summary")
async def get_event_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get event statistics"""
    query = db.query(Event)
    
    total = query.count()
    active = query.filter(Event.is_active == True).count()
    
    # Average severity
    avg_severity = db.query(db.func.avg(Event.severity)).scalar() or 0
    
    # Events by type
    event_types = db.query(
        Event.event_type, 
        db.func.count(Event.id).label('count')
    ).group_by(Event.event_type).all()
    
    # Recent events (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent = query.filter(Event.created_at >= week_ago).count()
    
    # High severity events
    high_severity = query.filter(Event.severity >= 70).count()
    
    return {
        "total": total,
        "active": active,
        "avg_severity": avg_severity,
        "recent_events": recent,
        "high_severity_events": high_severity,
        "event_types": [{"type": et[0], "count": et[1]} for et in event_types]
    }

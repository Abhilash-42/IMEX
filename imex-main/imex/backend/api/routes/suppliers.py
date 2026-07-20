from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from database.session import get_db
from database.models import Supplier, Component, Company, User
from database.neo4j_client import neo4j_client
from services.auth import (
    get_current_active_user,
    get_current_manager_or_admin,
    get_current_admin_user,
)

router = APIRouter()

# Pydantic schemas
class SupplierBase(BaseModel):
    name: str
    country: Optional[str] = None
    city: Optional[str] = None
    criticality_score: float = Field(0.0, ge=0, le=100)
    reliability_score: float = Field(0.0, ge=0, le=100)
    is_active: bool = True

class SupplierCreate(SupplierBase):
    company_id: Optional[int] = None

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    criticality_score: Optional[float] = Field(None, ge=0, le=100)
    reliability_score: Optional[float] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None

class SupplierResponse(SupplierBase):
    id: int
    company_id: Optional[int]
    neo4j_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class SupplierDetailResponse(SupplierResponse):
    components: List[dict] = []
    events: List[dict] = []

class SupplierListResponse(BaseModel):
    total: int
    suppliers: List[SupplierResponse]

@router.get("/", response_model=SupplierListResponse)
async def get_suppliers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    country: Optional[str] = None,
    min_criticality: Optional[float] = Query(None, ge=0, le=100),
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all suppliers with filtering and pagination"""
    query = db.query(Supplier)
    
    # Apply company filter for non-admin users
    if current_user.role != "admin" and current_user.company_id:
        query = query.filter(Supplier.company_id == current_user.company_id)
    
    # Apply filters
    if search:
        query = query.filter(
            or_(
                Supplier.name.ilike(f"%{search}%"),
                Supplier.city.ilike(f"%{search}%"),
                Supplier.country.ilike(f"%{search}%")
            )
        )
    
    if country:
        query = query.filter(Supplier.country == country)
    
    if min_criticality is not None:
        query = query.filter(Supplier.criticality_score >= min_criticality)
    
    if is_active is not None:
        query = query.filter(Supplier.is_active == is_active)
    
    total = query.count()
    suppliers = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "suppliers": suppliers
    }

@router.get("/{supplier_id}", response_model=SupplierDetailResponse)
async def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get supplier by ID with related data"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Check permissions
    if current_user.role != "admin" and supplier.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get components
    components = db.query(Component).filter(Component.supplier_id == supplier.id).all()
    
    # Get events (if any)
    events = []
    if supplier.neo4j_id:
        # This would be expanded to fetch events from Neo4j
        pass
    
    response = SupplierDetailResponse.from_orm(supplier)
    response.components = [
        {"id": c.id, "name": c.name, "criticality": c.criticality}
        for c in components
    ]
    response.events = events
    
    return response

@router.post("/", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    supplier: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager_or_admin)
):
    """Create a new supplier"""
    # Set company_id if not provided
    if not supplier.company_id:
        if current_user.company_id:
            supplier.company_id = current_user.company_id
        else:
            raise HTTPException(
                status_code=400, 
                detail="Company ID is required for supplier creation"
            )
    
    # Check if supplier already exists
    existing = db.query(Supplier).filter(
        Supplier.name == supplier.name,
        Supplier.company_id == supplier.company_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Supplier with this name already exists for this company"
        )
    
    # Create supplier
    db_supplier = Supplier(
        name=supplier.name,
        country=supplier.country,
        city=supplier.city,
        criticality_score=supplier.criticality_score,
        reliability_score=supplier.reliability_score,
        is_active=supplier.is_active,
        company_id=supplier.company_id
    )
    
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    
    # Create Neo4j node
    if neo4j_client.driver:
        try:
            neo4j_data = {
                "id": str(db_supplier.id),
                "name": db_supplier.name,
                "country": db_supplier.country or "",
                "city": db_supplier.city or "",
                "criticality_score": db_supplier.criticality_score,
                "reliability_score": db_supplier.reliability_score,
                "is_active": db_supplier.is_active
            }
            result = neo4j_client.create_supplier(neo4j_data)
            if result:
                db_supplier.neo4j_id = str(db_supplier.id)
                db.commit()
                db.refresh(db_supplier)
        except Exception as e:
            # Log error but don't fail the request
            print(f"Error creating Neo4j node: {e}")
    
    return db_supplier

@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: int,
    supplier_update: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager_or_admin)
):
    """Update supplier by ID"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Check permissions
    if current_user.role != "admin" and supplier.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update fields
    update_data = supplier_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)
    
    supplier.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(supplier)
    
    # Update Neo4j if needed
    if neo4j_client.driver and supplier.neo4j_id:
        try:
            # This would update the Neo4j node
            pass
        except Exception as e:
            print(f"Error updating Neo4j node: {e}")
    
    return supplier

@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete supplier by ID (Admin only)"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Check if supplier has components
    components = db.query(Component).filter(Component.supplier_id == supplier.id).first()
    if components:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete supplier with associated components. Remove components first."
        )
    
    # Delete from Neo4j
    if neo4j_client.driver and supplier.neo4j_id:
        try:
            with neo4j_client.driver.session() as session:
                session.run(
                    "MATCH (s:Supplier {id: $id}) DETACH DELETE s",
                    id=supplier.neo4j_id
                )
        except Exception as e:
            print(f"Error deleting Neo4j node: {e}")
    
    db.delete(supplier)
    db.commit()

@router.get("/stats/summary")
async def get_supplier_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get supplier statistics"""
    query = db.query(Supplier)
    if current_user.role != "admin" and current_user.company_id:
        query = query.filter(Supplier.company_id == current_user.company_id)
    
    total = query.count()
    active = query.filter(Supplier.is_active == True).count()
    critical = query.filter(Supplier.criticality_score >= 70).count()
    
    # Get top countries
    countries = db.query(Supplier.country, db.func.count(Supplier.id).label('count'))\
        .filter(Supplier.country.isnot(None))\
        .group_by(Supplier.country)\
        .order_by(db.desc('count'))\
        .limit(10).all()
    
    return {
        "total": total,
        "active": active,
        "critical": critical,
        "top_countries": [{"country": c[0], "count": c[1]} for c in countries]
    }

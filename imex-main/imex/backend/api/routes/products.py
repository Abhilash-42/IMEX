from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from database.session import get_db
from database.models import Product, Component, Company, User
from database.neo4j_client import neo4j_client
from services.auth import (
    get_current_active_user,
    get_current_manager_or_admin,
    get_current_admin_user,
)

router = APIRouter()

# Pydantic schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    revenue_per_unit: float = Field(0.0, ge=0)
    monthly_sales: int = Field(0, ge=0)
    business_unit: Optional[str] = None

class ProductCreate(ProductBase):
    company_id: Optional[int] = None
    component_ids: Optional[List[int]] = []

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    revenue_per_unit: Optional[float] = Field(None, ge=0)
    monthly_sales: Optional[int] = Field(None, ge=0)
    business_unit: Optional[str] = None
    component_ids: Optional[List[int]] = None

class ProductResponse(ProductBase):
    id: int
    company_id: Optional[int]
    neo4j_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class ProductDetailResponse(ProductResponse):
    components: List[dict] = []

class ProductListResponse(BaseModel):
    total: int
    products: List[ProductResponse]

@router.get("/", response_model=ProductListResponse)
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    country: Optional[str] = None,
    min_criticality: Optional[float] = Query(None, ge=0, le=100),
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get all products with filtering and pagination"""
    query = db.query(Product)
    
    # Apply filters
    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%"),
                Product.business_unit.ilike(f"%{search}%")
            )
        )
    
    if business_unit:
        query = query.filter(Product.business_unit == business_unit)
    
    if min_revenue is not None:
        query = query.filter(Product.revenue_per_unit >= min_revenue)
    
    total = query.count()
    products = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "products": products
    }

@router.get("/{product_id}", response_model=ProductDetailResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get product by ID with related data"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check permissions
    if current_user.role != "admin" and product.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get components
    components = db.query(Component).join(
        Product.components
    ).filter(Product.id == product.id).all()
    
    response = ProductDetailResponse.from_orm(product)
    response.components = [
        {"id": c.id, "name": c.name, "supplier_id": c.supplier_id}
        for c in components
    ]
    
    return response

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager_or_admin)
):
    """Create a new product"""
    # Set company_id if not provided
    if not product.company_id:
        if current_user.company_id:
            product.company_id = current_user.company_id
        else:
            raise HTTPException(
                status_code=400, 
                detail="Company ID is required for product creation"
            )
    
    # Check if product already exists
    existing = db.query(Product).filter(
        Product.name == product.name,
        Product.company_id == product.company_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Product with this name already exists for this company"
        )
    
    # Create product
    db_product = Product(
        name=product.name,
        description=product.description,
        revenue_per_unit=product.revenue_per_unit,
        monthly_sales=product.monthly_sales,
        business_unit=product.business_unit,
        company_id=product.company_id
    )
    
    # Add components
    if product.component_ids:
        components = db.query(Component).filter(
            Component.id.in_(product.component_ids)
        ).all()
        db_product.components.extend(components)
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # Create Neo4j node
    if neo4j_client.driver:
        try:
            neo4j_data = {
                "id": str(db_product.id),
                "name": db_product.name,
                "description": db_product.description or "",
                "revenue_per_unit": db_product.revenue_per_unit,
                "monthly_sales": db_product.monthly_sales,
                "business_unit": db_product.business_unit or ""
            }
            result = neo4j_client.create_product(neo4j_data)
            if result:
                db_product.neo4j_id = str(db_product.id)
                
                # Create relationships with components
                for component in db_product.components:
                    if component.neo4j_id:
                        neo4j_client.create_relationship(
                            component.neo4j_id,
                            db_product.neo4j_id,
                            "USED_IN"
                        )
                
                db.commit()
                db.refresh(db_product)
        except Exception as e:
            print(f"Error creating Neo4j node: {e}")
    
    return db_product

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager_or_admin)
):
    """Update product by ID"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check permissions
    if current_user.role != "admin" and product.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update fields
    update_data = product_update.dict(exclude_unset=True)
    
    # Handle components separately
    component_ids = update_data.pop("component_ids", None)
    
    for field, value in update_data.items():
        setattr(product, field, value)
    
    # Update components if provided
    if component_ids is not None:
        components = db.query(Component).filter(
            Component.id.in_(component_ids)
        ).all()
        product.components = components
    
    product.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(product)
    
    # Update Neo4j if needed
    if neo4j_client.driver and product.neo4j_id:
        try:
            # This would update the Neo4j node and relationships
            pass
        except Exception as e:
            print(f"Error updating Neo4j node: {e}")
    
    return product

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete product by ID (Admin only)"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Delete from Neo4j
    if neo4j_client.driver and product.neo4j_id:
        try:
            with neo4j_client.driver.session() as session:
                session.run(
                    "MATCH (p:Product {id: $id}) DETACH DELETE p",
                    id=product.neo4j_id
                )
        except Exception as e:
            print(f"Error deleting Neo4j node: {e}")
    
    db.delete(product)
    db.commit()

@router.get("/stats/summary")
async def get_product_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get product statistics"""
    query = db.query(Product)
    if current_user.role != "admin" and current_user.company_id:
        query = query.filter(Product.company_id == current_user.company_id)
    
    total = query.count()
    
    # Calculate revenue metrics
    products = query.all()
    total_monthly_revenue = sum(p.revenue_per_unit * p.monthly_sales for p in products)
    avg_revenue_per_product = total_monthly_revenue / total if total > 0 else 0
    
    # Get top business units
    business_units = db.query(
        Product.business_unit, 
        db.func.count(Product.id).label('count'),
        db.func.sum(Product.revenue_per_unit * Product.monthly_sales).label('revenue')
    ).filter(Product.business_unit.isnot(None))\
     .group_by(Product.business_unit)\
     .order_by(db.desc('revenue'))\
     .limit(10).all()
    
    return {
        "total": total,
        "total_monthly_revenue": total_monthly_revenue,
        "avg_revenue_per_product": avg_revenue_per_product,
        "top_business_units": [
            {"unit": bu[0], "count": bu[1], "revenue": bu[2]} 
            for bu in business_units
        ]
    }

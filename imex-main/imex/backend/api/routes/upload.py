from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict
import csv
import io
import logging
from datetime import datetime

from database.session import get_db
from database.models import Supplier, Component, Product, Company, User
from database.neo4j_client import neo4j_client
from services.auth import get_current_active_user, get_current_manager_or_admin

router = APIRouter()
logger = logging.getLogger(__name__)

class UploadResult(BaseModel):
    success: bool
    message: str
    created_count: int
    updated_count: int
    errors: List[str]

@router.post("/suppliers", response_model=UploadResult)
async def upload_suppliers(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager_or_admin)
):
    """Upload suppliers from CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be CSV format")
    
    created_count = 0
    updated_count = 0
    errors = []
    
    try:
        content = await file.read()
        csv_reader = csv.DictReader(io.StringIO(content.decode('utf-8')))
        
        # Required columns
        required_cols = ['name']
        if not all(col in csv_reader.fieldnames for col in required_cols):
            raise HTTPException(
                status_code=400, 
                detail=f"CSV must contain columns: {', '.join(required_cols)}"
            )
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Validate required fields
                if not row.get('name'):
                    errors.append(f"Row {row_num}: Missing 'name' field")
                    continue
                
                # Check if supplier exists
                supplier = db.query(Supplier).filter(
                    Supplier.name == row['name'].strip(),
                    Supplier.company_id == current_user.company_id
                ).first()
                
                if supplier:
                    # Update existing supplier
                    supplier.country = row.get('country', supplier.country)
                    supplier.city = row.get('city', supplier.city)
                    if row.get('criticality_score'):
                        try:
                            supplier.criticality_score = float(row['criticality_score'])
                        except ValueError:
                            errors.append(f"Row {row_num}: Invalid criticality_score")
                            continue
                    if row.get('reliability_score'):
                        try:
                            supplier.reliability_score = float(row['reliability_score'])
                        except ValueError:
                            errors.append(f"Row {row_num}: Invalid reliability_score")
                            continue
                    supplier.is_active = row.get('is_active', 'true').lower() == 'true'
                    supplier.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    # Create new supplier
                    new_supplier = Supplier(
                        name=row['name'].strip(),
                        country=row.get('country'),
                        city=row.get('city'),
                        criticality_score=float(row.get('criticality_score', 0)),
                        reliability_score=float(row.get('reliability_score', 0)),
                        is_active=row.get('is_active', 'true').lower() == 'true',
                        company_id=current_user.company_id
                    )
                    db.add(new_supplier)
                    created_count += 1
                
                db.commit()
                
            except Exception as e:
                db.rollback()
                errors.append(f"Row {row_num}: {str(e)}")
                logger.error(f"Error processing supplier row {row_num}: {e}")
        
        # Create Neo4j nodes for new suppliers
        if created_count > 0 and neo4j_client.driver:
            try:
                new_suppliers = db.query(Supplier).filter(
                    Supplier.company_id == current_user.company_id
                ).order_by(Supplier.id.desc()).limit(created_count).all()
                
                for supplier in new_suppliers:
                    if not supplier.neo4j_id:
                        neo4j_data = {
                            "id": str(supplier.id),
                            "name": supplier.name,
                            "country": supplier.country or "",
                            "city": supplier.city or "",
                            "criticality_score": supplier.criticality_score,
                            "reliability_score": supplier.reliability_score,
                            "is_active": supplier.is_active
                        }
                        result = neo4j_client.create_supplier(neo4j_data)
                        if result:
                            supplier.neo4j_id = str(supplier.id)
                            db.commit()
            except Exception as e:
                logger.error(f"Error creating Neo4j nodes: {e}")
        
        return UploadResult(
            success=True,
            message=f"Processed {created_count + updated_count} suppliers",
            created_count=created_count,
            updated_count=updated_count,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Error processing upload: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.post("/components", response_model=UploadResult)
async def upload_components(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager_or_admin)
):
    """Upload components from CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be CSV format")
    
    created_count = 0
    updated_count = 0
    errors = []
    
    try:
        content = await file.read()
        csv_reader = csv.DictReader(io.StringIO(content.decode('utf-8')))
        
        # Required columns
        required_cols = ['name', 'supplier_name']
        if not all(col in csv_reader.fieldnames for col in required_cols):
            raise HTTPException(
                status_code=400, 
                detail=f"CSV must contain columns: {', '.join(required_cols)}"
            )
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Find supplier
                supplier = db.query(Supplier).filter(
                    Supplier.name == row['supplier_name'].strip(),
                    Supplier.company_id == current_user.company_id
                ).first()
                
                if not supplier:
                    errors.append(f"Row {row_num}: Supplier '{row['supplier_name']}' not found")
                    continue
                
                # Check if component exists
                component = db.query(Component).filter(
                    Component.name == row['name'].strip(),
                    Component.supplier_id == supplier.id
                ).first()
                
                if component:
                    # Update existing component
                    component.description = row.get('description', component.description)
                    component.criticality = row.get('criticality', component.criticality)
                    if row.get('lead_time_days'):
                        try:
                            component.lead_time_days = int(row['lead_time_days'])
                        except ValueError:
                            errors.append(f"Row {row_num}: Invalid lead_time_days")
                            continue
                    if row.get('cost_per_unit'):
                        try:
                            component.cost_per_unit = float(row['cost_per_unit'])
                        except ValueError:
                            errors.append(f"Row {row_num}: Invalid cost_per_unit")
                            continue
                    component.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    # Create new component
                    new_component = Component(
                        name=row['name'].strip(),
                        description=row.get('description'),
                        supplier_id=supplier.id,
                        criticality=row.get('criticality', 'medium'),
                        lead_time_days=int(row.get('lead_time_days', 0)),
                        cost_per_unit=float(row.get('cost_per_unit', 0))
                    )
                    db.add(new_component)
                    created_count += 1
                
                db.commit()
                
                # Create Neo4j relationships
                if neo4j_client.driver and supplier.neo4j_id:
                    try:
                        component_id = new_component.id if not component else component.id
                        neo4j_data = {
                            "id": str(component_id),
                            "name": row['name'].strip(),
                            "description": row.get('description', ''),
                            "criticality": row.get('criticality', 'medium'),
                            "lead_time_days": int(row.get('lead_time_days', 0)),
                            "cost_per_unit": float(row.get('cost_per_unit', 0))
                        }
                        neo4j_client.create_component(neo4j_data)
                        neo4j_client.create_relationship(
                            supplier.neo4j_id,
                            str(component_id),
                            "PROVIDES"
                        )
                    except Exception as e:
                        logger.error(f"Error creating Neo4j relationship: {e}")
                
            except Exception as e:
                db.rollback()
                errors.append(f"Row {row_num}: {str(e)}")
                logger.error(f"Error processing component row {row_num}: {e}")
        
        return UploadResult(
            success=True,
            message=f"Processed {created_count + updated_count} components",
            created_count=created_count,
            updated_count=updated_count,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Error processing upload: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.post("/products", response_model=UploadResult)
async def upload_products(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager_or_admin)
):
    """Upload products from CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be CSV format")
    
    created_count = 0
    updated_count = 0
    errors = []
    
    try:
        content = await file.read()
        csv_reader = csv.DictReader(io.StringIO(content.decode('utf-8')))
        
        # Required columns
        required_cols = ['name']
        if not all(col in csv_reader.fieldnames for col in required_cols):
            raise HTTPException(
                status_code=400, 
                detail=f"CSV must contain columns: {', '.join(required_cols)}"
            )
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Check if product exists
                product = db.query(Product).filter(
                    Product.name == row['name'].strip(),
                    Product.company_id == current_user.company_id
                ).first()
                
                if product:
                    # Update existing product
                    product.description = row.get('description', product.description)
                    if row.get('revenue_per_unit'):
                        try:
                            product.revenue_per_unit = float(row['revenue_per_unit'])
                        except ValueError:
                            errors.append(f"Row {row_num}: Invalid revenue_per_unit")
                            continue
                    if row.get('monthly_sales'):
                        try:
                            product.monthly_sales = int(row['monthly_sales'])
                        except ValueError:
                            errors.append(f"Row {row_num}: Invalid monthly_sales")
                            continue
                    product.business_unit = row.get('business_unit', product.business_unit)
                    product.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    # Create new product
                    new_product = Product(
                        name=row['name'].strip(),
                        description=row.get('description'),
                        company_id=current_user.company_id,
                        revenue_per_unit=float(row.get('revenue_per_unit', 0)),
                        monthly_sales=int(row.get('monthly_sales', 0)),
                        business_unit=row.get('business_unit')
                    )
                    db.add(new_product)
                    created_count += 1
                
                db.commit()
                
                # Create Neo4j node
                if neo4j_client.driver:
                    try:
                        product_id = new_product.id if not product else product.id
                        neo4j_data = {
                            "id": str(product_id),
                            "name": row['name'].strip(),
                            "description": row.get('description', ''),
                            "revenue_per_unit": float(row.get('revenue_per_unit', 0)),
                            "monthly_sales": int(row.get('monthly_sales', 0)),
                            "business_unit": row.get('business_unit', '')
                        }
                        neo4j_client.create_product(neo4j_data)
                    except Exception as e:
                        logger.error(f"Error creating Neo4j product: {e}")
                
                # Handle component relationships if provided
                if row.get('component_names'):
                    component_names = [c.strip() for c in row['component_names'].split(';')]
                    components = db.query(Component).filter(
                        Component.name.in_(component_names),
                        Component.supplier.has(Supplier.company_id == current_user.company_id)
                    ).all()
                    
                    if components:
                        product_obj = product or new_product
                        product_obj.components.extend(components)
                        db.commit()
                        
                        # Create Neo4j relationships
                        if neo4j_client.driver and product_obj.neo4j_id:
                            for component in components:
                                if component.neo4j_id:
                                    neo4j_client.create_relationship(
                                        component.neo4j_id,
                                        product_obj.neo4j_id,
                                        "USED_IN"
                                    )
                
            except Exception as e:
                db.rollback()
                errors.append(f"Row {row_num}: {str(e)}")
                logger.error(f"Error processing product row {row_num}: {e}")
        
        return UploadResult(
            success=True,
            message=f"Processed {created_count + updated_count} products",
            created_count=created_count,
            updated_count=updated_count,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Error processing upload: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.get("/template/{data_type}")
async def download_template(
    data_type: str,
    current_user: User = Depends(get_current_active_user)
):
    """Download CSV template for data upload"""
    if data_type not in ['suppliers', 'components', 'products']:
        raise HTTPException(status_code=400, detail="Invalid data type")
    
    templates = {
        'suppliers': [
            ['name', 'country', 'city', 'criticality_score', 'reliability_score', 'is_active'],
            ['Example Supplier', 'USA', 'New York', '75', '80', 'true']
        ],
        'components': [
            ['name', 'description', 'supplier_name', 'criticality', 'lead_time_days', 'cost_per_unit'],
            ['Example Component', 'High-quality part', 'Example Supplier', 'high', '15', '25.50']
        ],
        'products': [
            ['name', 'description', 'revenue_per_unit', 'monthly_sales', 'business_unit', 'component_names'],
            ['Example Product', 'Finished good', '100.00', '500', 'Electronics', 'Example Component 1;Example Component 2']
        ]
    }
    
    template = templates.get(data_type, [])
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(template)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={data_type}_template.csv"
        }
    )

@router.get("/status/{job_id}")
async def get_upload_status(
    job_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get upload job status (placeholder for async processing)"""
    # This would be implemented with a job queue system like Celery
    # For now, return a placeholder
    return {
        "job_id": job_id,
        "status": "completed",
        "progress": 100,
        "message": "Upload processed successfully"
    }

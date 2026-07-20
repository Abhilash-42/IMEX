from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import io

from database.session import get_db
from database.models import RiskReport, Event, User
from services.reports import pdf_generator
from services.auth import get_current_active_user, get_current_manager_or_admin

router = APIRouter()

# Pydantic schemas
class ReportResponse(BaseModel):
    id: int
    event_id: int
    risk_score: float
    revenue_exposure: float
    affected_suppliers: List[dict]
    affected_products: List[dict]
    recommendations: List[str]
    executive_summary: str
    pdf_url: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ReportListResponse(BaseModel):
    total: int
    reports: List[ReportResponse]

class GenerateReportRequest(BaseModel):
    event_id: int
    include_details: bool = True

@router.get("/", response_model=ReportListResponse)
async def get_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    min_risk_score: Optional[float] = Query(None, ge=0, le=100),
    max_risk_score: Optional[float] = Query(None, ge=0, le=100),
    event_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all risk reports with filtering"""
    query = db.query(RiskReport)
    
    # Apply filters
    if min_risk_score is not None:
        query = query.filter(RiskReport.risk_score >= min_risk_score)
    
    if max_risk_score is not None:
        query = query.filter(RiskReport.risk_score <= max_risk_score)
    
    if event_id:
        query = query.filter(RiskReport.event_id == event_id)
    
    total = query.count()
    reports = query.order_by(RiskReport.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "reports": reports
    }

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get report by ID"""
    report = db.query(RiskReport).filter(RiskReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return report

@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: GenerateReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager_or_admin)
):
    """Generate a new risk report"""
    # Get event
    event = db.query(Event).filter(Event.id == request.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Get associated risk data (this would come from the risk assessment agent)
    # For now, we'll create a simple report
    from agents.risk_assessment import risk_assessment_agent
    risk_data = risk_assessment_agent.assess_event_risk(db, request.event_id)
    
    # Create report
    report = RiskReport(
        event_id=request.event_id,
        risk_score=risk_data.get("risk_score", 0),
        revenue_exposure=risk_data.get("revenue_exposure", 0),
        affected_suppliers=risk_data.get("affected_suppliers", []),
        affected_products=risk_data.get("affected_products", []),
        recommendations=risk_data.get("recommendations", []),
        executive_summary=risk_data.get("executive_summary", "")
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return report

@router.get("/pdf/{report_id}")
async def download_pdf_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Download PDF version of a report"""
    report = db.query(RiskReport).filter(RiskReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Prepare data for PDF
    risk_data = {
        "risk_score": report.risk_score,
        "revenue_exposure": report.revenue_exposure,
        "affected_suppliers": report.affected_suppliers,
        "affected_products": report.affected_products,
        "recommendations": report.recommendations,
        "executive_summary": report.executive_summary,
        "event_severity": db.query(Event).filter(Event.id == report.event_id).first().severity if report.event_id else 0
    }
    
    # Generate PDF
    pdf_bytes = pdf_generator.generate_risk_report(risk_data)
    
    # Create streaming response
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=risk_report_{report_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        }
    )

@router.post("/generate-pdf", response_class=StreamingResponse)
async def generate_and_download_pdf(
    request: GenerateReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager_or_admin)
):
    """Generate and download PDF report in one step"""
    # Generate report first
    from agents.risk_assessment import risk_assessment_agent
    risk_data = risk_assessment_agent.assess_event_risk(db, request.event_id)
    
    # Generate PDF
    pdf_bytes = pdf_generator.generate_risk_report(risk_data)
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=risk_report_{request.event_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        }
    )

@router.get("/stats/summary")
async def get_report_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get report statistics"""
    total = db.query(RiskReport).count()
    
    # Average risk score
    avg_risk = db.query(db.func.avg(RiskReport.risk_score)).scalar() or 0
    
    # Total revenue exposure
    total_revenue = db.query(db.func.sum(RiskReport.revenue_exposure)).scalar() or 0
    
    # Reports by risk level
    low_risk = db.query(RiskReport).filter(RiskReport.risk_score < 30).count()
    medium_risk = db.query(RiskReport).filter(
        RiskReport.risk_score >= 30, 
        RiskReport.risk_score < 70
    ).count()
    high_risk = db.query(RiskReport).filter(RiskReport.risk_score >= 70).count()
    
    # Recent reports
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent = db.query(RiskReport).filter(RiskReport.created_at >= week_ago).count()
    
    return {
        "total": total,
        "avg_risk_score": avg_risk,
        "total_revenue_exposure": total_revenue,
        "low_risk_reports": low_risk,
        "medium_risk_reports": medium_risk,
        "high_risk_reports": high_risk,
        "recent_reports": recent
    }

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel

from database.session import get_db
from database.models import Event, RiskReport
from agents.risk_assessment import risk_assessment_agent
from services.auth import get_current_active_user, get_current_manager_or_admin

router = APIRouter()

class RiskAnalysisRequest(BaseModel):
    event_id: int
    include_details: bool = True

class RiskAnalysisResponse(BaseModel):
    event_id: int
    event_title: str
    risk_score: float
    revenue_exposure: float
    affected_suppliers: List[Dict]
    affected_products: List[Dict]
    recommendations: List[str]
    executive_summary: str

@router.post("/analyze", response_model=RiskAnalysisResponse)
async def analyze_risk(
    request: RiskAnalysisRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Analyze risk for a specific event"""
    try:
        risk_data = risk_assessment_agent.assess_event_risk(db, request.event_id)
        return RiskAnalysisResponse(**risk_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing risk: {str(e)}"
        )

@router.get("/reports")
async def get_risk_reports(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get all risk reports"""
    reports = db.query(RiskReport).order_by(RiskReport.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "event_id": r.event_id,
            "risk_score": r.risk_score,
            "revenue_exposure": r.revenue_exposure,
            "created_at": r.created_at,
            "executive_summary": r.executive_summary
        }
        for r in reports
    ]

@router.get("/report/{report_id}")
async def get_risk_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get detailed risk report by ID"""
    report = db.query(RiskReport).filter(RiskReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {
        "id": report.id,
        "event_id": report.event_id,
        "risk_score": report.risk_score,
        "revenue_exposure": report.revenue_exposure,
        "affected_suppliers": report.affected_suppliers,
        "affected_products": report.affected_products,
        "recommendations": report.recommendations,
        "executive_summary": report.executive_summary,
        "created_at": report.created_at
    }

@router.get("/dashboard")
async def get_risk_dashboard(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get dashboard summary of risks"""
    # Count active disruptions
    active_events = db.query(Event).filter(Event.is_active == True).count()
    
    # Get highest risk report
    top_risk = db.query(RiskReport).order_by(RiskReport.risk_score.desc()).first()
    
    # Calculate total revenue at risk
    total_revenue = 0
    reports = db.query(RiskReport).all()
    for report in reports:
        total_revenue += report.revenue_exposure
    
    # Get recent alerts
    recent_events = db.query(Event).filter(
        Event.is_active == True
    ).order_by(Event.created_at.desc()).limit(5).all()
    
    return {
        "active_disruptions": active_events,
        "top_risk_score": top_risk.risk_score if top_risk else 0,
        "total_revenue_exposure": total_revenue,
        "recent_events": [
            {
                "id": e.id,
                "title": e.title,
                "severity": e.severity,
                "created_at": e.created_at
            }
            for e in recent_events
        ]
    }
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from database.session import SessionLocal
from services.rss_ingestion import rss_service
from agents.risk_assessment import risk_assessment_agent
from services.alerts import alert_service
from database.models import Event, RiskReport

logger = logging.getLogger(__name__)

def check_news_feeds():
    """Background job to check RSS feeds"""
    logger.info("Checking news feeds for supply chain disruptions")
    
    db = SessionLocal()
    try:
        # Process RSS feeds
        events = rss_service.process_articles(db)
        
        # Check weather events
        rss_service.ingest_weather_events(db)
        
        # Assess risk for new high-severity events
        high_risk_events = db.query(Event).filter(
            Event.severity > 50,
            Event.is_active == True
        ).all()
        
        for event in high_risk_events:
            # Check if risk assessment exists
            existing = db.query(RiskReport).filter(
                RiskReport.event_id == event.id
            ).first()
            
            if not existing:
                # Perform risk assessment
                risk_data = risk_assessment_agent.assess_event_risk(db, event.id)
                
                # Create risk report
                report = RiskReport(
                    event_id=event.id,
                    risk_score=risk_data["risk_score"],
                    revenue_exposure=risk_data["revenue_exposure"],
                    affected_suppliers=risk_data["affected_suppliers"],
                    affected_products=risk_data["affected_products"],
                    recommendations=risk_data["recommendations"],
                    executive_summary=risk_data["executive_summary"]
                )
                db.add(report)
                db.commit()
                
                # Send alerts if risk is high
                if risk_data["risk_score"] > 70:
                    alert_service.send_risk_alert(risk_data)
        
        logger.info(f"Processed {len(events)} new events")
    except Exception as e:
        logger.error(f"Error in news feed processing: {e}")
    finally:
        db.close()

def start_scheduler():
    """Start the background scheduler"""
    scheduler = BackgroundScheduler()
    
    # Schedule feed checking every 30 minutes
    scheduler.add_job(
        check_news_feeds,
        trigger=IntervalTrigger(minutes=30),
        id="check_news_feeds",
        next_run_time=datetime.now()  # Run immediately on start
    )
    
    logger.info("Scheduler started with 30-minute interval")
    return scheduler
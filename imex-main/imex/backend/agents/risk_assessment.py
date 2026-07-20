import logging
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from database.models import Event, Supplier, Component, Product, Port
from database.neo4j_client import neo4j_client
from services.risk_engine import RiskEngine

logger = logging.getLogger(__name__)

class RiskAssessmentAgent:
    def __init__(self):
        self.risk_engine = RiskEngine()
    
    def assess_event_risk(self, db: Session, event_id: int) -> Dict:
        """Assess risk for a specific event"""
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            return {"error": "Event not found"}
        
        affected_suppliers = []
        affected_products = []
        recommendations = []
        
        # Get affected suppliers from Neo4j
        if event.port_id:
            port = db.query(Port).filter(Port.id == event.port_id).first()
            if port and port.neo4j_id:
                suppliers = neo4j_client.get_affected_suppliers(port.neo4j_id)
                for supplier_data in suppliers:
                    supplier = db.query(Supplier).filter(
                        Supplier.neo4j_id == supplier_data["id"]
                    ).first()
                    if supplier:
                        affected_suppliers.append(supplier)
        
        # Get affected products for each supplier
        for supplier in affected_suppliers:
            if supplier.neo4j_id:
                products = neo4j_client.get_affected_products(supplier.neo4j_id)
                for product_data in products:
                    product = db.query(Product).filter(
                        Product.neo4j_id == product_data["id"]
                    ).first()
                    if product:
                        affected_products.append(product)
        
        # Calculate risk metrics
        metrics = self.risk_engine.calculate_risk(
            event=event,
            suppliers=affected_suppliers,
            products=affected_products,
            db=db
        )
        
        # Generate recommendations
        recommendations = self.generate_recommendations(
            event=event,
            suppliers=affected_suppliers,
            products=affected_products,
            risk_score=metrics["risk_score"]
        )
        
        return {
            "event_id": event.id,
            "event_title": event.title,
            "risk_score": metrics["risk_score"],
            "revenue_exposure": metrics["revenue_exposure"],
            "affected_suppliers": [
                {"id": s.id, "name": s.name, "criticality": s.criticality_score}
                for s in affected_suppliers
            ],
            "affected_products": [
                {"id": p.id, "name": p.name, "revenue": p.revenue_per_unit * p.monthly_sales}
                for p in affected_products
            ],
            "recommendations": recommendations,
            "executive_summary": self.generate_executive_summary(
                event, affected_suppliers, affected_products, metrics
            )
        }
    
    def generate_recommendations(self, event: Event, suppliers: List[Supplier], 
                                 products: List[Product], risk_score: float) -> List[str]:
        """Generate mitigation recommendations"""
        recommendations = []
        
        if risk_score > 70:
            recommendations.append("Immediate action required: Consider alternative suppliers")
            recommendations.append("Implement emergency procurement plan")
            recommendations.append("Notify key stakeholders and customers")
        
        if risk_score > 50:
            recommendations.append("Evaluate alternative logistics routes")
            recommendations.append("Increase safety stock levels")
            recommendations.append("Monitor situation closely and update daily")
        
        if event.event_type == "port":
            recommendations.append("Consider routing shipments through alternate ports")
            recommendations.append("Contact freight forwarders for alternative solutions")
        
        if event.event_type == "weather":
            recommendations.append("Review weather patterns and adjust delivery schedules")
            recommendations.append("Assess insurance coverage for weather-related disruptions")
        
        if event.event_type == "geopolitical":
            recommendations.append("Review sanctions and compliance requirements")
            recommendations.append("Evaluate political risk exposure")
            recommendations.append("Consider supply chain diversification strategies")
        
        # Supplier-specific recommendations
        for supplier in suppliers:
            if supplier.criticality_score > 70:
                recommendations.append(f"Critical supplier {supplier.name}: Establish backup supplier relationships")
        
        return recommendations[:5]  # Return top 5 recommendations
    
    def generate_executive_summary(self, event: Event, suppliers: List[Supplier],
                                    products: List[Product], metrics: Dict) -> str:
        """Generate executive summary"""
        total_revenue = metrics["revenue_exposure"]
        supplier_count = len(suppliers)
        product_count = len(products)
        
        if supplier_count == 0 and product_count == 0:
            return f"Event '{event.title}' has been detected but no immediate supply chain impact has been identified."
        
        summary = f"{event.title} may impact {supplier_count} supplier{'s' if supplier_count > 1 else ''}, "
        summary += f"{product_count} product{'s' if product_count > 1 else ''}, "
        summary += f"and place approximately ${total_revenue:,.0f}M revenue at risk. "
        summary += f"Risk score: {metrics['risk_score']:.0f}/100. "
        
        if metrics['risk_score'] > 70:
            summary += "Immediate mitigation action is recommended."
        elif metrics['risk_score'] > 50:
            summary += "Increased monitoring and contingency planning advised."
        else:
            summary += "Situation is being monitored. Continue standard operations."
        
        return summary

# Singleton instance
risk_assessment_agent = RiskAssessmentAgent()
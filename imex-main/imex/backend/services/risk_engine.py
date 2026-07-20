import logging
from typing import Dict, List
from sqlalchemy.orm import Session

from database.models import Event, Supplier, Component, Product

logger = logging.getLogger(__name__)

class RiskEngine:
    def __init__(self):
        self.weights = {
            "supplier_criticality": 0.25,
            "port_severity": 0.20,
            "component_dependency": 0.25,
            "revenue_exposure": 0.30
        }
    
    def calculate_risk(self, event: Event, suppliers: List[Supplier], 
                       products: List[Product], db: Session) -> Dict:
        """Calculate comprehensive risk score"""
        
        # 1. Supplier Criticality Score (0-100)
        supplier_score = self.calculate_supplier_criticality(suppliers)
        
        # 2. Port Severity Score (0-100)
        port_score = self.calculate_port_severity(event)
        
        # 3. Component Dependency Score (0-100)
        component_score = self.calculate_component_dependency(suppliers, db)
        
        # 4. Revenue Exposure Score (0-100)
        revenue_score = self.calculate_revenue_exposure(products)
        
        # Weighted risk score
        risk_score = (
            supplier_score * self.weights["supplier_criticality"] +
            port_score * self.weights["port_severity"] +
            component_score * self.weights["component_dependency"] +
            revenue_score * self.weights["revenue_exposure"]
        )
        
        # Calculate revenue exposure
        total_revenue = sum(
            p.revenue_per_unit * p.monthly_sales for p in products
        )
        
        return {
            "risk_score": risk_score,
            "revenue_exposure": total_revenue,
            "supplier_score": supplier_score,
            "port_score": port_score,
            "component_score": component_score,
            "revenue_score": revenue_score
        }
    
    def calculate_supplier_criticality(self, suppliers: List[Supplier]) -> float:
        """Calculate average supplier criticality"""
        if not suppliers:
            return 0
        
        total_criticality = sum(s.criticality_score for s in suppliers)
        avg_criticality = total_criticality / len(suppliers)
        
        # Apply amplification for number of suppliers
        supplier_count_factor = min(1.0, len(suppliers) / 10)
        
        return min(100, avg_criticality * (1 + supplier_count_factor * 0.2))
    
    def calculate_port_severity(self, event: Event) -> float:
        """Calculate port severity score"""
        if not event.port_id:
            return 0
        
        # Base severity from event
        base_severity = event.severity
        
        # Adjust for duration
        duration_factor = min(1.0, event.estimated_duration_days / 30)
        
        # Adjust for event type
        event_type_multipliers = {
            "port": 1.5,
            "weather": 1.2,
            "geopolitical": 1.3,
            "labor": 1.1,
            "supply": 1.0
        }
        multiplier = event_type_multipliers.get(event.event_type, 1.0)
        
        return min(100, base_severity * multiplier * (1 + duration_factor * 0.3))
    
    def calculate_component_dependency(self, suppliers: List[Supplier], db: Session) -> float:
        """Calculate component dependency score"""
        if not suppliers:
            return 0
        
        total_components = 0
        critical_components = 0
        
        for supplier in suppliers:
            components = db.query(Component).filter(
                Component.supplier_id == supplier.id
            ).all()
            
            total_components += len(components)
            
            for component in components:
                if component.criticality in ["high", "critical"]:
                    critical_components += 1
        
        if total_components == 0:
            return 0
        
        critical_ratio = critical_components / total_components
        component_density = min(1.0, total_components / 50)
        
        return min(100, (critical_ratio * 70 + component_density * 30))
    
    def calculate_revenue_exposure(self, products: List[Product]) -> float:
        """Calculate revenue exposure score"""
        if not products:
            return 0
        
        total_monthly_revenue = sum(
            p.revenue_per_unit * p.monthly_sales for p in products
        )
        
        # Score based on revenue tiers (in millions)
        if total_monthly_revenue == 0:
            return 0
        
        # Scale to 0-100 with logarithmic progression
        import math
        score = min(100, math.log10(total_monthly_revenue * 12) * 25)
        
        return score
    
    def calculate_business_unit_impact(self, products: List[Product]) -> Dict:
        """Calculate impact per business unit"""
        impact = {}
        
        for product in products:
            unit = product.business_unit or "Uncategorized"
            if unit not in impact:
                impact[unit] = {
                    "product_count": 0,
                    "revenue": 0
                }
            
            impact[unit]["product_count"] += 1
            impact[unit]["revenue"] += product.revenue_per_unit * product.monthly_sales
        
        return impact
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Table
from database.session import Base
import enum
from datetime import datetime

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    VIEWER = "viewer"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.VIEWER)
    full_name = Column(String(255))
    company_id = Column(Integer, ForeignKey("companies.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    company = relationship("Company", back_populates="users")
    alerts = relationship("Alert", back_populates="user")

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    website = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    users = relationship("User", back_populates="company")
    products = relationship("Product", back_populates="company")
    suppliers = relationship("Supplier", back_populates="company")

class Supplier(Base):
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    country = Column(String(100))
    city = Column(String(100))
    criticality_score = Column(Float, default=0.0)
    reliability_score = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    neo4j_id = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    company = relationship("Company", back_populates="suppliers")
    components = relationship("Component", back_populates="supplier")
    events = relationship("Event", secondary="supplier_events")

class Component(Base):
    __tablename__ = "components"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    criticality = Column(String(50))
    lead_time_days = Column(Integer)
    cost_per_unit = Column(Float)
    neo4j_id = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    supplier = relationship("Supplier", back_populates="components")
    products = relationship("Product", secondary="component_products")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    company_id = Column(Integer, ForeignKey("companies.id"))
    revenue_per_unit = Column(Float)
    monthly_sales = Column(Integer)
    business_unit = Column(String(100))
    neo4j_id = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    company = relationship("Company", back_populates="products")
    components = relationship("Component", secondary="component_products")

class Port(Base):
    __tablename__ = "ports"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    country = Column(String(100))
    city = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)
    is_active = Column(Boolean, default=True)
    neo4j_id = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    events = relationship("Event", back_populates="port")

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    event_type = Column(String(100))
    severity = Column(Float, default=0.0)  # 0-100
    location = Column(String(255))
    country = Column(String(100))
    start_date = Column(DateTime)
    end_date = Column(DateTime, nullable=True)
    estimated_duration_days = Column(Integer)
    source = Column(String(100))
    source_url = Column(String(500))
    port_id = Column(Integer, ForeignKey("ports.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    port = relationship("Port", back_populates="events")
    supplier = relationship("Supplier", back_populates="events")
    risk_reports = relationship("RiskReport", back_populates="event")

class RiskReport(Base):
    __tablename__ = "risk_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    risk_score = Column(Float, default=0.0)
    revenue_exposure = Column(Float, default=0.0)
    affected_suppliers = Column(JSON)
    affected_products = Column(JSON)
    recommendations = Column(JSON)
    executive_summary = Column(Text)
    pdf_url = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())
    
    event = relationship("Event", back_populates="risk_reports")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_id = Column(Integer, ForeignKey("events.id"))
    alert_type = Column(String(50))
    severity = Column(String(50))
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="alerts")
    event = relationship("Event")

# Association tables
supplier_events = Table(
    "supplier_events",
    Base.metadata,
    Column("supplier_id", Integer, ForeignKey("suppliers.id")),
    Column("event_id", Integer, ForeignKey("events.id"))
)

component_products = Table(
    "component_products",
    Base.metadata,
    Column("component_id", Integer, ForeignKey("components.id")),
    Column("product_id", Integer, ForeignKey("products.id"))
)

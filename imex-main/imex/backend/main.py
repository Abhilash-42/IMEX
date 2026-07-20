from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging
from contextlib import asynccontextmanager

from api.routes import auth, suppliers, products, events, risk, reports, upload
from database.session import engine, Base
from services.scheduler import start_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    logger.info("Starting chainSol AI Backend...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # Start background scheduler
    scheduler = start_scheduler()
    scheduler.start()
    logger.info("Background scheduler started")
    
    yield
    
    # Shutdown
    scheduler.shutdown()
    logger.info("Shutting down chainSol AI Backend...")

app = FastAPI(
    title="chainSol AI",
    description="Real-Time Supply Chain Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://chainsol-ai.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(suppliers.router, prefix="/api/suppliers", tags=["Suppliers"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(events.router, prefix="/api/events", tags=["Events"])
app.include_router(risk.router, prefix="/api/risk", tags=["Risk Analysis"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(upload.router, prefix="/api/upload", tags=["Uploads"])

@app.get("/")
async def root():
    return {"message": "chainSol AI API", "version": "1.0.0"}
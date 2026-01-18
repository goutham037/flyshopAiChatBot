"""
FlyShop AI ChatBot - MVP Query API
FastAPI application entry point with CORS, logging, and route registration.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
import sys
import os

from app.api.query import router as query_router
from app.api.debug import router as debug_router
from app.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="FlyShop AI ChatBot",
    description="""
## MVP Customer Query API

A natural language query interface for FlyShop CRM customers to access their:
- Flight bookings and confirmations
- Quotations and pricing
- Payment status and schedules
- Activity bookings
- Admin contact information

### Authentication
All queries require a registered mobile number in format `+91XXXXXXXXXX`.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware - configure for your frontend domain in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Proxy headers middleware - essential for devtunnels/proxies
app.add_middleware(
    ProxyHeadersMiddleware,
    trusted_hosts="*"
)


# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Register routers
app.include_router(query_router, tags=["Query"])
app.include_router(debug_router, tags=["Debug"])


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("FlyShop AI ChatBot starting up...")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    logger.info(f"Max query limit: {settings.MAX_LIMIT}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("FlyShop AI ChatBot shutting down...")


# Chat UI route
@app.get("/chat")
async def chat_ui():
    """Serve the chat UI."""
    html_path = os.path.join(static_dir, "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"error": "Chat UI not found"}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "FlyShop AI ChatBot",
        "version": "1.0.0",
        "description": "MVP Customer Query API",
        "chat_ui": "/chat",
        "docs": "/docs",
        "endpoints": {
            "query": "POST /mvp/query",
            "chat_ui": "GET /chat",
            "health": "GET /health",
            "intents": "GET /intents"
        }
    }


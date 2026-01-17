"""
FastAPI main application entry point
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import Database
from app.routes import auth, projects, websocket, assertions, chat
from app.middleware.error_handler import error_handling_middleware
from app.middleware.sanitization import SanitizationMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.https_redirect import HTTPSRedirectMiddleware
from app.config import settings
from app.utils.structured_logging import (
    setup_structured_logging,
    log_api_request,
    set_request_id,
    clear_request_id
)
from app.utils.metrics import track_api_request, track_agent_execution
import logging
import time
import uuid
from datetime import datetime

# Setup structured logging
setup_structured_logging(
    log_level="INFO" if not settings.debug else "DEBUG",
    log_file="server.log"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    # Startup
    logger.info("Starting SVA-Chatbot API...")
    await Database.connect_db()
    logger.info("Database connected")
    
    # Start background job queue
    from app.utils.background_jobs import start_job_queue
    await start_job_queue()
    logger.info("Background job queue started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SVA-Chatbot API...")
    
    # Stop background job queue
    from app.utils.background_jobs import stop_job_queue
    await stop_job_queue()
    logger.info("Background job queue stopped")
    
    await Database.close_db()
    logger.info("Database connection closed")


app = FastAPI(
    title="SVA-Chatbot API",
    description="AI-powered SystemVerilog Assertion generation system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration - Requirements 20.5
# MUST be added FIRST before any other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",  # Additional frontend port
        "http://localhost:5173",  # Vite default port
        "http://127.0.0.1:5173",  # Alternative localhost
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# HTTPS enforcement - Requirements 20.5
# Disabled in development, enabled in production
enforce_https = settings.environment == "production"
app.add_middleware(HTTPSRedirectMiddleware, enforce_https=enforce_https)

# Rate limiting middleware - Requirements 17.4
app.add_middleware(RateLimitMiddleware)

# Input sanitization middleware - Requirements 20.3
app.add_middleware(SanitizationMiddleware)

# Include routers AFTER middleware
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(assertions.router)
app.include_router(chat.router)
app.include_router(websocket.router)


# Error handling middleware - Requirements 19.1, 19.2, 19.5
@app.middleware("http")
async def error_handler(request: Request, call_next):
    """Global error handling middleware"""
    # Skip error handling for OPTIONS requests (CORS preflight)
    if request.method == "OPTIONS":
        return await call_next(request)
    return await error_handling_middleware(request, call_next)


# Request logging middleware - Requirements 19.5, 20.5
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming requests with timing information and structured data
    
    Validates: Requirement 19.5 - Log all API requests
    Validates: Requirement 16.5 - Track API response times
    """
    # Skip detailed logging for OPTIONS requests (CORS preflight)
    if request.method == "OPTIONS":
        return await call_next(request)
    
    # Generate and set request ID
    request_id = str(uuid.uuid4())
    set_request_id(request_id)
    
    start_time = time.time()
    
    # Log request start
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            "extra_data": {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_host": request.client.host if request.client else None
            }
        }
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Track metrics
    track_api_request(
        method=request.method,
        path=request.url.path,
        duration=process_time
    )
    
    # Log request completion with structured data
    log_api_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=process_time,
        request_id=request_id,
        client_host=request.client.host if request.client else None
    )
    
    # Add custom headers
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = request_id
    
    # Clear request ID
    clear_request_id()
    
    return response


@app.get("/")
async def root():
    return {"message": "SVA-Chatbot API is running"}


@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint
    
    Checks:
    - Database connectivity
    - LLM API availability
    - Service status
    
    Returns:
        dict: Health status with component details
        
    Validates: Requirements - Health check endpoint with all components
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # Check database
    db_healthy = await Database.health_check()
    health_status["components"]["database"] = {
        "status": "healthy" if db_healthy else "unhealthy",
        "message": "Connected" if db_healthy else "Connection failed"
    }
    
    # Check LLM API availability
    try:
        from app.clients.groq_client import GroqClient
        groq_client = GroqClient()
        await groq_client._ensure_session()
        
        # Simple test to check if we can reach the API
        # We don't actually make a call, just check if session is ready
        llm_healthy = groq_client.session is not None and not groq_client.session.closed
        
        health_status["components"]["llm_api"] = {
            "status": "healthy" if llm_healthy else "unhealthy",
            "message": "Available" if llm_healthy else "Unavailable",
            "primary_model": settings.groq_primary_model,
            "fallback_model": settings.groq_fallback_model
        }
        
        await groq_client.close()
        
    except Exception as e:
        health_status["components"]["llm_api"] = {
            "status": "unhealthy",
            "message": f"Error: {str(e)}"
        }
        llm_healthy = False
    
    # Check background job queue
    try:
        from app.utils.background_jobs import job_queue
        job_queue_healthy = job_queue.running
        
        health_status["components"]["job_queue"] = {
            "status": "healthy" if job_queue_healthy else "unhealthy",
            "message": "Running" if job_queue_healthy else "Stopped",
            "workers": job_queue.max_workers,
            "queue_size": job_queue.queue.qsize()
        }
    except Exception as e:
        health_status["components"]["job_queue"] = {
            "status": "unknown",
            "message": f"Error: {str(e)}"
        }
        job_queue_healthy = True  # Don't fail health check if job queue check fails
    
    # Overall status
    if not db_healthy or not llm_healthy:
        health_status["status"] = "degraded"
    
    if not db_healthy and not llm_healthy:
        health_status["status"] = "unhealthy"
    
    return health_status


@app.get("/health/live")
async def liveness_check():
    """
    Liveness probe for Kubernetes/container orchestration
    
    Returns 200 if the application is running
    
    Returns:
        dict: Simple liveness status
    """
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness_check():
    """
    Readiness probe for Kubernetes/container orchestration
    
    Returns 200 if the application is ready to serve traffic
    
    Returns:
        dict: Readiness status with critical components
    """
    # Check critical components
    db_healthy = await Database.health_check()
    
    if db_healthy:
        return {"status": "ready"}
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Service not ready")


@app.get("/cache/stats")
async def cache_stats():
    """
    Get cache statistics for monitoring performance
    
    Returns:
        dict: Cache statistics for all cache instances
        
    Validates: Requirement 17.4 - Cache monitoring
    """
    from app.utils.cache import get_cache_stats
    
    return {
        "cache_stats": get_cache_stats()
    }


@app.get("/jobs/{job_id}")
async def get_job_status_endpoint(job_id: str):
    """
    Get status of a background job
    
    Args:
        job_id: Job identifier
        
    Returns:
        dict: Job status information
        
    Validates: Requirements 1.1, 1.2, 1.3, 1.4, 2.1 - Background job tracking
    """
    from app.utils.background_jobs import get_job_status
    
    status = get_job_status(job_id)
    
    if status is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    
    return status


@app.get("/metrics")
async def get_metrics():
    """
    Get performance metrics for monitoring
    
    Returns:
        dict: Performance metrics for all tracked operations
        
    Validates: Requirement 16.5 - Performance metrics tracking
    """
    from app.utils.metrics import get_all_metrics
    
    return {
        "metrics": get_all_metrics()
    }

"""
Sanitization middleware for FastAPI

Automatically sanitizes request inputs to prevent injection attacks.

Validates: Requirement 20.3
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from app.utils.sanitization import (
    detect_sql_injection,
    detect_xss,
    detect_path_traversal,
    sanitize_string
)

logger = logging.getLogger(__name__)


class SanitizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to sanitize and validate all incoming requests
    
    Validates: Requirement 20.3
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and sanitize inputs
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response
        """
        # Skip sanitization for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            logger.info(f"Skipping sanitization for OPTIONS request to {request.url.path}")
            return await call_next(request)
        
        logger.info(f"Processing {request.method} request to {request.url.path}")
        
        # Check query parameters for injection attempts
        for key, value in request.query_params.items():
            if isinstance(value, str):
                if detect_sql_injection(value):
                    logger.warning(
                        f"SQL injection attempt detected in query param '{key}': {value}"
                    )
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid input detected"}
                    )
                
                if detect_xss(value):
                    logger.warning(
                        f"XSS attempt detected in query param '{key}': {value}"
                    )
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid input detected"}
                    )
                
                if detect_path_traversal(value):
                    logger.warning(
                        f"Path traversal attempt detected in query param '{key}': {value}"
                    )
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid input detected"}
                    )
        
        # Check path parameters for injection attempts
        for key, value in request.path_params.items():
            if isinstance(value, str):
                if detect_path_traversal(value):
                    logger.warning(
                        f"Path traversal attempt detected in path param '{key}': {value}"
                    )
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid input detected"}
                    )
        
        # Process the request
        response = await call_next(request)
        
        return response

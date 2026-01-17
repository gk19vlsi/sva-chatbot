"""
HTTPS enforcement middleware

Redirects HTTP requests to HTTPS and sets secure cookie flags.

Validates: Requirement 20.5
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
import logging

logger = logging.getLogger(__name__)


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce HTTPS in production
    
    Validates: Requirement 20.5
    """
    
    def __init__(self, app, enforce_https: bool = True):
        """
        Initialize HTTPS redirect middleware
        
        Args:
            app: FastAPI application
            enforce_https: Whether to enforce HTTPS (disable for local development)
        """
        super().__init__(app)
        self.enforce_https = enforce_https
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and enforce HTTPS
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response or redirect to HTTPS
            
        Validates: Requirement 20.5
        """
        # Skip for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Skip HTTPS enforcement if disabled (e.g., local development)
        if not self.enforce_https:
            response = await call_next(request)
            return self._add_security_headers(response)
        
        # Check if request is HTTP (not HTTPS)
        if request.url.scheme == "http":
            # Build HTTPS URL
            https_url = request.url.replace(scheme="https")
            
            logger.info(f"Redirecting HTTP to HTTPS: {request.url} -> {https_url}")
            
            # Redirect to HTTPS
            return RedirectResponse(url=str(https_url), status_code=301)
        
        # Process the request
        response = await call_next(request)
        
        # Add security headers
        return self._add_security_headers(response)
    
    def _add_security_headers(self, response):
        """
        Add security headers to response
        
        Args:
            response: Response object
            
        Returns:
            Response with security headers
            
        Validates: Requirement 20.5
        """
        # Strict-Transport-Security (HSTS)
        # Tells browsers to only use HTTPS for this site
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # X-Content-Type-Options
        # Prevents MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options
        # Prevents clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-XSS-Protection
        # Enables XSS filter in browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content-Security-Policy
        # Restricts resource loading
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'"
        )
        
        # Referrer-Policy
        # Controls referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy
        # Controls browser features
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=()"
        )
        
        return response


def configure_secure_cookies(app):
    """
    Configure secure cookie settings
    
    Args:
        app: FastAPI application
        
    Validates: Requirement 20.5
    """
    # This would be used when setting cookies
    # Example configuration for session cookies:
    secure_cookie_config = {
        "httponly": True,  # Prevents JavaScript access
        "secure": True,    # Only sent over HTTPS
        "samesite": "lax", # CSRF protection
        "max_age": 3600    # 1 hour expiration
    }
    
    return secure_cookie_config

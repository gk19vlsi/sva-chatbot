"""
Rate limiting middleware for FastAPI

Implements rate limiting per user/IP to prevent abuse.

Validates: Requirement 17.4
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
from collections import defaultdict
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter using token bucket algorithm
    
    Validates: Requirement 17.4
    """
    
    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        """
        Initialize rate limiter
        
        Args:
            requests_per_minute: Maximum requests per minute
            requests_per_hour: Maximum requests per hour
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        
        # Store request timestamps per client
        # Format: {client_id: [(timestamp1, timestamp2, ...)]}
        self.request_history: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> Tuple[bool, str]:
        """
        Check if a request is allowed for the client
        
        Args:
            client_id: Client identifier (user_id or IP)
            
        Returns:
            Tuple of (is_allowed, reason)
            
        Validates: Requirement 17.4
        """
        current_time = time.time()
        
        # Get request history for this client
        history = self.request_history[client_id]
        
        # Remove requests older than 1 hour
        cutoff_hour = current_time - 3600
        history = [ts for ts in history if ts > cutoff_hour]
        self.request_history[client_id] = history
        
        # Check hourly limit
        if len(history) >= self.requests_per_hour:
            return False, f"Hourly rate limit exceeded ({self.requests_per_hour} requests/hour)"
        
        # Check minute limit
        cutoff_minute = current_time - 60
        recent_requests = [ts for ts in history if ts > cutoff_minute]
        
        if len(recent_requests) >= self.requests_per_minute:
            return False, f"Rate limit exceeded ({self.requests_per_minute} requests/minute)"
        
        # Allow the request and record it
        history.append(current_time)
        
        return True, ""
    
    def get_remaining(self, client_id: str) -> Dict[str, int]:
        """
        Get remaining requests for a client
        
        Args:
            client_id: Client identifier
            
        Returns:
            Dict with remaining requests per minute and hour
        """
        current_time = time.time()
        history = self.request_history.get(client_id, [])
        
        # Count recent requests
        cutoff_minute = current_time - 60
        cutoff_hour = current_time - 3600
        
        minute_requests = len([ts for ts in history if ts > cutoff_minute])
        hour_requests = len([ts for ts in history if ts > cutoff_hour])
        
        return {
            "remaining_per_minute": max(0, self.requests_per_minute - minute_requests),
            "remaining_per_hour": max(0, self.requests_per_hour - hour_requests),
            "limit_per_minute": self.requests_per_minute,
            "limit_per_hour": self.requests_per_hour
        }
    
    def reset(self, client_id: str):
        """Reset rate limit for a client"""
        if client_id in self.request_history:
            del self.request_history[client_id]


# Global rate limiter instance
_rate_limiter: RateLimiter = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance"""
    global _rate_limiter
    
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(
            requests_per_minute=60,
            requests_per_hour=1000
        )
    
    return _rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce rate limiting
    
    Validates: Requirement 17.4
    """
    
    def __init__(self, app, rate_limiter: RateLimiter = None):
        """
        Initialize rate limit middleware
        
        Args:
            app: FastAPI application
            rate_limiter: Optional RateLimiter instance
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter or get_rate_limiter()
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and enforce rate limiting
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response or 429 error
            
        Validates: Requirement 17.4
        """
        # Skip rate limiting for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Skip rate limiting for health check
        if request.url.path == "/health":
            return await call_next(request)
        
        # Get client identifier (user_id from auth or IP address)
        client_id = self._get_client_id(request)
        
        # Check rate limit
        is_allowed, reason = self.rate_limiter.is_allowed(client_id)
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for client {client_id}: {reason}")
            
            # Get remaining limits for headers
            remaining = self.rate_limiter.get_remaining(client_id)
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": reason,
                    "retry_after": 60  # seconds
                },
                headers={
                    "X-RateLimit-Limit-Minute": str(remaining["limit_per_minute"]),
                    "X-RateLimit-Limit-Hour": str(remaining["limit_per_hour"]),
                    "X-RateLimit-Remaining-Minute": str(remaining["remaining_per_minute"]),
                    "X-RateLimit-Remaining-Hour": str(remaining["remaining_per_hour"]),
                    "Retry-After": "60"
                }
            )
        
        # Process the request
        response = await call_next(request)
        
        # Add rate limit headers to response
        remaining = self.rate_limiter.get_remaining(client_id)
        response.headers["X-RateLimit-Limit-Minute"] = str(remaining["limit_per_minute"])
        response.headers["X-RateLimit-Limit-Hour"] = str(remaining["limit_per_hour"])
        response.headers["X-RateLimit-Remaining-Minute"] = str(remaining["remaining_per_minute"])
        response.headers["X-RateLimit-Remaining-Hour"] = str(remaining["remaining_per_hour"])
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """
        Get client identifier from request
        
        Args:
            request: FastAPI request
            
        Returns:
            Client identifier (user_id or IP)
        """
        # Try to get user_id from request state (set by auth middleware)
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"
        
        # Fall back to IP address
        if request.client:
            return f"ip:{request.client.host}"
        
        # Default fallback
        return "unknown"

"""
Error handling middleware for FastAPI application

This middleware catches all unhandled exceptions, returns appropriate HTTP status codes,
and logs errors with stack traces for debugging.

Validates: Requirements 19.1, 19.2, 19.5
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback
from datetime import datetime
from typing import Union

logger = logging.getLogger(__name__)


class ErrorLogger:
    """
    Centralized error logging with structured format
    
    Validates: Requirement 19.5
    """
    
    @staticmethod
    async def log_error(
        error: Exception,
        request: Request,
        status_code: int,
        error_type: str = "UnhandledException"
    ) -> dict:
        """
        Log error with complete context and stack trace
        
        Args:
            error: The exception that occurred
            request: FastAPI request object
            status_code: HTTP status code to return
            error_type: Type/category of error
            
        Returns:
            dict: Error log entry
            
        Validates: Requirement 19.5 - Error Logging Completeness
        """
        # Get stack trace
        stack_trace = traceback.format_exc()
        
        # Build error log entry
        error_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": error_type,
            "error_class": error.__class__.__name__,
            "message": str(error),
            "status_code": status_code,
            "request": {
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_host": request.client.host if request.client else None,
            },
            "stack_trace": stack_trace
        }
        
        # Log with appropriate level
        if status_code >= 500:
            logger.error(
                f"Server Error [{status_code}]: {error_type} - {str(error)}\n"
                f"Request: {request.method} {request.url.path}\n"
                f"Stack Trace:\n{stack_trace}"
            )
        elif status_code >= 400:
            logger.warning(
                f"Client Error [{status_code}]: {error_type} - {str(error)}\n"
                f"Request: {request.method} {request.url.path}"
            )
        else:
            logger.info(
                f"Error [{status_code}]: {error_type} - {str(error)}"
            )
        
        return error_log


async def error_handling_middleware(request: Request, call_next):
    """
    Global error handling middleware
    
    Catches all unhandled exceptions and returns appropriate HTTP responses
    with detailed error information and logging.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/route handler in chain
        
    Returns:
        Response with error details or successful response
        
    Validates: Requirements 19.1, 19.2, 19.5
    """
    try:
        # Process request
        response = await call_next(request)
        return response
        
    except StarletteHTTPException as exc:
        # Handle HTTP exceptions (raised by FastAPI)
        await ErrorLogger.log_error(
            error=exc,
            request=request,
            status_code=exc.status_code,
            error_type="HTTPException"
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    except RequestValidationError as exc:
        # Handle validation errors (Pydantic)
        await ErrorLogger.log_error(
            error=exc,
            request=request,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_type="ValidationError"
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation error",
                "details": exc.errors(),
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    except ValueError as exc:
        # Handle value errors (invalid input)
        await ErrorLogger.log_error(
            error=exc,
            request=request,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_type="ValueError"
        )
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Invalid input",
                "message": str(exc),
                "status_code": status.HTTP_400_BAD_REQUEST,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    except FileNotFoundError as exc:
        # Handle file not found errors
        await ErrorLogger.log_error(
            error=exc,
            request=request,
            status_code=status.HTTP_404_NOT_FOUND,
            error_type="FileNotFoundError"
        )
        
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "Resource not found",
                "message": str(exc),
                "status_code": status.HTTP_404_NOT_FOUND,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    except PermissionError as exc:
        # Handle permission errors
        await ErrorLogger.log_error(
            error=exc,
            request=request,
            status_code=status.HTTP_403_FORBIDDEN,
            error_type="PermissionError"
        )
        
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": "Permission denied",
                "message": str(exc),
                "status_code": status.HTTP_403_FORBIDDEN,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    except TimeoutError as exc:
        # Handle timeout errors
        await ErrorLogger.log_error(
            error=exc,
            request=request,
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            error_type="TimeoutError"
        )
        
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={
                "error": "Request timeout",
                "message": "The operation took too long to complete",
                "status_code": status.HTTP_504_GATEWAY_TIMEOUT,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    except ConnectionError as exc:
        # Handle connection errors (database, external APIs)
        await ErrorLogger.log_error(
            error=exc,
            request=request,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_type="ConnectionError"
        )
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "Service unavailable",
                "message": "Unable to connect to required service",
                "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    except Exception as exc:
        # Catch all other unhandled exceptions
        await ErrorLogger.log_error(
            error=exc,
            request=request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_type="UnhandledException"
        )
        
        # Return generic error message (don't expose internal details)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred. Please try again later.",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


class DatabaseError(Exception):
    """Custom exception for database-related errors"""
    pass


class FileProcessingError(Exception):
    """Custom exception for file processing errors"""
    
    def __init__(self, file_type: str, error_details: str, line_number: int = None):
        self.file_type = file_type
        self.error_details = error_details
        self.line_number = line_number
        super().__init__(self.to_message())
    
    def to_message(self) -> str:
        """Convert to error message"""
        msg = f"File processing failed for {self.file_type}: {self.error_details}"
        if self.line_number:
            msg += f" (line {self.line_number})"
        return msg
    
    def to_response(self) -> dict:
        """Convert to API response dict"""
        return {
            "error": "file_processing_failed",
            "file_type": self.file_type,
            "details": self.error_details,
            "line_number": self.line_number
        }


class AgentExecutionError(Exception):
    """Custom exception for agent execution errors"""
    
    def __init__(self, agent_name: str, error_details: str):
        self.agent_name = agent_name
        self.error_details = error_details
        super().__init__(f"Agent {agent_name} failed: {error_details}")

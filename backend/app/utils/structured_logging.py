"""
Structured Logging Utilities

Provides structured logging in JSON format for better log analysis and monitoring.
Logs all API requests, agent executions, and errors with context.

Implements Requirement 19.5: Error logging completeness
"""
import logging
import json
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar

# Context variable for request ID tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs in JSON format
    
    Validates: Requirement 19.5 - Structured logging format (JSON)
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        # Base log data
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add request ID if available
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields from record
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data)


class StructuredLogger:
    """
    Wrapper for structured logging with context
    
    Validates: Requirement 19.5 - Log errors with context
    """
    
    def __init__(self, name: str):
        """
        Initialize structured logger
        
        Args:
            name: Logger name
        """
        self.logger = logging.getLogger(name)
    
    def _log(self, level: int, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """
        Internal log method with extra data support
        
        Args:
            level: Log level
            message: Log message
            extra_data: Additional structured data
        """
        if extra_data:
            # Create a log record with extra data
            record = self.logger.makeRecord(
                self.logger.name,
                level,
                "(unknown file)",
                0,
                message,
                (),
                None
            )
            record.extra_data = extra_data
            self.logger.handle(record)
        else:
            self.logger.log(level, message)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional structured data"""
        self._log(logging.DEBUG, message, kwargs if kwargs else None)
    
    def info(self, message: str, **kwargs):
        """Log info message with optional structured data"""
        self._log(logging.INFO, message, kwargs if kwargs else None)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional structured data"""
        self._log(logging.WARNING, message, kwargs if kwargs else None)
    
    def error(self, message: str, **kwargs):
        """Log error message with optional structured data"""
        self._log(logging.ERROR, message, kwargs if kwargs else None)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with optional structured data"""
        self._log(logging.CRITICAL, message, kwargs if kwargs else None)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback and optional structured data"""
        kwargs['exc_info'] = True
        self._log(logging.ERROR, message, kwargs if kwargs else None)


def setup_structured_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None
):
    """
    Set up structured logging for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        
    Validates: Requirement 19.5 - Structured logging setup
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create structured formatter
    formatter = StructuredFormatter()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    logging.info("Structured logging initialized", extra={
        "extra_data": {
            "log_level": log_level,
            "log_file": log_file
        }
    })


def log_api_request(
    method: str,
    path: str,
    status_code: int,
    duration: float,
    user_id: Optional[str] = None,
    **kwargs
):
    """
    Log API request with structured data
    
    Args:
        method: HTTP method
        path: Request path
        status_code: Response status code
        duration: Request duration in seconds
        user_id: Optional user ID
        **kwargs: Additional context
        
    Validates: Requirement 19.5 - Log all API requests
    """
    logger = StructuredLogger("api")
    
    log_data = {
        "event_type": "api_request",
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_seconds": duration,
        "user_id": user_id,
        **kwargs
    }
    
    logger.info(f"API Request: {method} {path}", **log_data)


def log_agent_execution(
    agent_name: str,
    project_id: str,
    status: str,
    duration: float,
    error: Optional[str] = None,
    **kwargs
):
    """
    Log agent execution with structured data
    
    Args:
        agent_name: Name of the agent
        project_id: Project ID
        status: Execution status (success/failure)
        duration: Execution duration in seconds
        error: Optional error message
        **kwargs: Additional context
        
    Validates: Requirement 19.5 - Log agent executions
    """
    logger = StructuredLogger("agent")
    
    log_data = {
        "event_type": "agent_execution",
        "agent_name": agent_name,
        "project_id": project_id,
        "status": status,
        "duration_seconds": duration,
        "error": error,
        **kwargs
    }
    
    if status == "success":
        logger.info(f"Agent execution completed: {agent_name}", **log_data)
    else:
        logger.error(f"Agent execution failed: {agent_name}", **log_data)


def log_error(
    error_type: str,
    error_message: str,
    context: Optional[Dict[str, Any]] = None,
    exc_info: bool = True
):
    """
    Log error with full context and stack trace
    
    Args:
        error_type: Type of error
        error_message: Error message
        context: Additional context information
        exc_info: Whether to include exception info
        
    Validates: Requirement 19.5 - Log errors with context
    """
    logger = StructuredLogger("error")
    
    log_data = {
        "event_type": "error",
        "error_type": error_type,
        "error_message": error_message,
        "context": context or {}
    }
    
    if exc_info:
        logger.exception(f"Error occurred: {error_type}", **log_data)
    else:
        logger.error(f"Error occurred: {error_type}", **log_data)


def log_database_operation(
    operation: str,
    collection: str,
    duration: float,
    success: bool,
    document_count: Optional[int] = None,
    **kwargs
):
    """
    Log database operation with structured data
    
    Args:
        operation: Database operation (insert, update, delete, find)
        collection: Collection name
        duration: Operation duration in seconds
        success: Whether operation succeeded
        document_count: Number of documents affected
        **kwargs: Additional context
    """
    logger = StructuredLogger("database")
    
    log_data = {
        "event_type": "database_operation",
        "operation": operation,
        "collection": collection,
        "duration_seconds": duration,
        "success": success,
        "document_count": document_count,
        **kwargs
    }
    
    logger.info(f"Database operation: {operation} on {collection}", **log_data)


def log_llm_request(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    duration: float,
    success: bool,
    project_id: Optional[str] = None,
    **kwargs
):
    """
    Log LLM API request with structured data
    
    Args:
        model: Model name
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
        total_tokens: Total tokens used
        duration: Request duration in seconds
        success: Whether request succeeded
        project_id: Optional project ID
        **kwargs: Additional context
    """
    logger = StructuredLogger("llm")
    
    log_data = {
        "event_type": "llm_request",
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "duration_seconds": duration,
        "success": success,
        "project_id": project_id,
        **kwargs
    }
    
    logger.info(f"LLM request: {model}", **log_data)


def set_request_id(request_id: str):
    """
    Set request ID for current context
    
    Args:
        request_id: Request identifier
    """
    request_id_var.set(request_id)


def get_request_id() -> Optional[str]:
    """
    Get request ID from current context
    
    Returns:
        Request ID or None
    """
    return request_id_var.get()


def clear_request_id():
    """Clear request ID from current context"""
    request_id_var.set(None)

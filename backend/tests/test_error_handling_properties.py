"""
Property-based tests for error handling and logging

Tests comprehensive error handling middleware and logging functionality.

Validates: Requirements 19.1, 19.2, 19.5
"""
import pytest
from hypothesis import given, strategies as st, settings
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import logging
from datetime import datetime

from app.middleware.error_handler import (
    error_handling_middleware,
    ErrorLogger,
    DatabaseError,
    FileProcessingError,
    AgentExecutionError
)


# Test application setup
def create_test_app():
    """Create a test FastAPI application with error handling"""
    app = FastAPI()
    
    @app.middleware("http")
    async def error_handler(request: Request, call_next):
        return await error_handling_middleware(request, call_next)
    
    @app.get("/test/success")
    async def success_endpoint():
        return {"status": "ok"}
    
    @app.get("/test/http_error")
    async def http_error_endpoint():
        raise HTTPException(status_code=404, detail="Not found")
    
    @app.get("/test/value_error")
    async def value_error_endpoint():
        raise ValueError("Invalid value provided")
    
    @app.get("/test/file_not_found")
    async def file_not_found_endpoint():
        raise FileNotFoundError("File does not exist")
    
    @app.get("/test/permission_error")
    async def permission_error_endpoint():
        raise PermissionError("Access denied")
    
    @app.get("/test/timeout_error")
    async def timeout_error_endpoint():
        raise TimeoutError("Operation timed out")
    
    @app.get("/test/connection_error")
    async def connection_error_endpoint():
        raise ConnectionError("Connection failed")
    
    @app.get("/test/unhandled_error")
    async def unhandled_error_endpoint():
        raise RuntimeError("Unexpected error")
    
    @app.get("/test/database_error")
    async def database_error_endpoint():
        raise DatabaseError("Database operation failed")
    
    @app.get("/test/file_processing_error")
    async def file_processing_error_endpoint():
        raise FileProcessingError("pdf", "Corrupted file", 42)
    
    @app.get("/test/agent_error")
    async def agent_error_endpoint():
        raise AgentExecutionError("spec_parser", "Parsing failed")
    
    return app


@pytest.fixture
def test_client():
    """Create test client"""
    app = create_test_app()
    return TestClient(app)


@pytest.fixture
def mock_logger():
    """Create mock logger for testing"""
    with patch('app.middleware.error_handler.logger') as mock_log:
        yield mock_log


# Property 47: Error Logging Completeness
@given(
    error_message=st.text(min_size=1, max_size=200),
    status_code=st.integers(min_value=400, max_value=599)
)
@settings(max_examples=100, deadline=None)
def test_error_logging_completeness(error_message, status_code):
    """
    Feature: sva-chatbot, Property 47: Error Logging Completeness
    
    For any error that occurs in the system, an error log entry should be created
    containing the error type, message, stack trace, and timestamp.
    
    Validates: Requirement 19.5
    """
    # Create mock request
    mock_request = Mock(spec=Request)
    mock_request.method = "GET"
    mock_request.url = Mock()
    mock_request.url.path = "/test/endpoint"
    mock_request.url.__str__ = Mock(return_value="http://test/endpoint")
    mock_request.query_params = {}
    mock_request.client = Mock()
    mock_request.client.host = "127.0.0.1"
    
    # Create test exception
    test_error = Exception(error_message)
    
    # Create error logger
    error_logger = ErrorLogger()
    
    # Log the error (synchronous wrapper for async function)
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        error_log = loop.run_until_complete(
            error_logger.log_error(
                error=test_error,
                request=mock_request,
                status_code=status_code,
                error_type="TestError"
            )
        )
    finally:
        loop.close()
    
    # Verify error log contains all required fields
    assert "timestamp" in error_log, "Error log must contain timestamp"
    assert "error_type" in error_log, "Error log must contain error_type"
    assert "error_class" in error_log, "Error log must contain error_class"
    assert "message" in error_log, "Error log must contain message"
    assert "status_code" in error_log, "Error log must contain status_code"
    assert "request" in error_log, "Error log must contain request details"
    assert "stack_trace" in error_log, "Error log must contain stack_trace"
    
    # Verify field values
    assert error_log["error_type"] == "TestError"
    assert error_log["error_class"] == "Exception"
    assert error_log["message"] == error_message
    assert error_log["status_code"] == status_code
    
    # Verify request details
    assert error_log["request"]["method"] == "GET"
    assert error_log["request"]["path"] == "/test/endpoint"
    assert error_log["request"]["client_host"] == "127.0.0.1"
    
    # Verify timestamp format
    try:
        datetime.fromisoformat(error_log["timestamp"])
    except ValueError:
        pytest.fail("Timestamp must be in ISO format")
    
    # Verify stack trace is not empty
    assert len(error_log["stack_trace"]) > 0, "Stack trace must not be empty"


def test_http_error_handling(test_client, mock_logger):
    """Test that HTTP errors are handled correctly"""
    response = test_client.get("/test/http_error")
    
    assert response.status_code == 404
    data = response.json()
    # HTTPException returns 'detail' or 'error' depending on middleware processing
    assert "detail" in data or "error" in data
    
    # Verify logging was called
    assert mock_logger.warning.called or mock_logger.error.called


def test_value_error_handling(test_client, mock_logger):
    """Test that ValueError is handled with 400 status"""
    response = test_client.get("/test/value_error")
    
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "Invalid input"
    assert "message" in data
    assert "timestamp" in data


def test_file_not_found_handling(test_client, mock_logger):
    """Test that FileNotFoundError is handled with 404 status"""
    response = test_client.get("/test/file_not_found")
    
    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "Resource not found"
    assert "timestamp" in data


def test_permission_error_handling(test_client, mock_logger):
    """Test that PermissionError is handled with 403 status"""
    response = test_client.get("/test/permission_error")
    
    assert response.status_code == 403
    data = response.json()
    assert data["error"] == "Permission denied"
    assert "timestamp" in data


def test_timeout_error_handling(test_client, mock_logger):
    """Test that TimeoutError is handled with 504 status"""
    response = test_client.get("/test/timeout_error")
    
    assert response.status_code == 504
    data = response.json()
    assert data["error"] == "Request timeout"
    assert "timestamp" in data


def test_connection_error_handling(test_client, mock_logger):
    """Test that ConnectionError is handled with 503 status"""
    response = test_client.get("/test/connection_error")
    
    assert response.status_code == 503
    data = response.json()
    assert data["error"] == "Service unavailable"
    assert "timestamp" in data


def test_unhandled_error_handling(test_client, mock_logger):
    """Test that unhandled exceptions are caught with 500 status"""
    response = test_client.get("/test/unhandled_error")
    
    assert response.status_code == 500
    data = response.json()
    assert data["error"] == "Internal server error"
    assert "timestamp" in data
    
    # Verify error was logged
    assert mock_logger.error.called


def test_database_error_handling(test_client, mock_logger):
    """Test that DatabaseError is handled correctly"""
    response = test_client.get("/test/database_error")
    
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert "timestamp" in data


def test_file_processing_error_handling(test_client, mock_logger):
    """Test that FileProcessingError is handled correctly"""
    response = test_client.get("/test/file_processing_error")
    
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert "timestamp" in data


def test_agent_execution_error_handling(test_client, mock_logger):
    """Test that AgentExecutionError is handled correctly"""
    response = test_client.get("/test/agent_error")
    
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert "timestamp" in data


def test_success_endpoint_no_error(test_client, mock_logger):
    """Test that successful requests don't trigger error handling"""
    response = test_client.get("/test/success")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    
    # Verify no error logging occurred
    assert not mock_logger.error.called


@given(
    method=st.sampled_from(["GET", "POST", "PUT", "DELETE"]),
    path=st.text(min_size=1, max_size=50).map(lambda x: f"/{x.replace('/', '_')}"),
)
@settings(max_examples=50, deadline=None)
def test_error_log_includes_request_details(method, path):
    """
    Test that error logs include complete request details
    
    Validates: Requirement 19.5
    """
    # Create mock request
    mock_request = Mock(spec=Request)
    mock_request.method = method
    mock_request.url = Mock()
    mock_request.url.path = path
    mock_request.url.__str__ = Mock(return_value=f"http://test{path}")
    mock_request.query_params = {"test": "value"}
    mock_request.client = Mock()
    mock_request.client.host = "192.168.1.1"
    
    # Create test exception
    test_error = RuntimeError("Test error")
    
    # Create error logger
    error_logger = ErrorLogger()
    
    # Log the error
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        error_log = loop.run_until_complete(
            error_logger.log_error(
                error=test_error,
                request=mock_request,
                status_code=500,
                error_type="RuntimeError"
            )
        )
    finally:
        loop.close()
    
    # Verify request details are captured
    assert error_log["request"]["method"] == method
    assert error_log["request"]["path"] == path
    assert error_log["request"]["client_host"] == "192.168.1.1"
    assert "query_params" in error_log["request"]


def test_file_processing_error_response_format():
    """Test FileProcessingError response format"""
    error = FileProcessingError("pdf", "Corrupted header", 10)
    
    response = error.to_response()
    
    assert response["error"] == "file_processing_failed"
    assert response["file_type"] == "pdf"
    assert response["details"] == "Corrupted header"
    assert response["line_number"] == 10


def test_file_processing_error_message():
    """Test FileProcessingError message generation"""
    error = FileProcessingError("docx", "Invalid format", 25)
    
    message = error.to_message()
    
    assert "docx" in message
    assert "Invalid format" in message
    assert "line 25" in message


def test_agent_execution_error_message():
    """Test AgentExecutionError message generation"""
    error = AgentExecutionError("rtl_analyzer", "Parse failed")
    
    message = str(error)
    
    assert "rtl_analyzer" in message
    assert "Parse failed" in message

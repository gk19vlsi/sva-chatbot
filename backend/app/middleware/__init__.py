"""
Middleware modules for FastAPI application
"""
from .error_handler import error_handling_middleware

__all__ = ["error_handling_middleware"]

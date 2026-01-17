"""
Input sanitization utilities for security hardening

Provides functions to sanitize user inputs, validate file uploads,
and prevent injection attacks.

Validates: Requirement 20.3
"""
import re
import html
from typing import Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


# Allowed file extensions for uploads
ALLOWED_SPEC_EXTENSIONS = {'.pdf', '.docx', '.doc', '.md', '.txt'}
ALLOWED_RTL_EXTENSIONS = {'.sv', '.v', '.svh', '.vh'}

# Maximum file sizes (in bytes)
MAX_SPEC_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_RTL_FILE_SIZE = 10 * 1024 * 1024   # 10 MB

# Dangerous patterns to detect
SQL_INJECTION_PATTERNS = [
    r"(\bUNION\b.*\bSELECT\b)",
    r"(\bDROP\b.*\bTABLE\b)",
    r"(\bINSERT\b.*\bINTO\b)",
    r"(\bDELETE\b.*\bFROM\b)",
    r"(\bUPDATE\b.*\bSET\b)",
    r"(--\s*$)",
    r"(;\s*DROP\b)",
    r"('\s*OR\s*'1'\s*=\s*'1)",
    r"(\bEXEC\b.*\()",
]

XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",
    r"<iframe[^>]*>",
    r"<object[^>]*>",
    r"<embed[^>]*>",
]

PATH_TRAVERSAL_PATTERNS = [
    r"\.\./",
    r"\.\.",
    r"~",
    r"/etc/",
    r"/proc/",
    r"/sys/",
    r"C:\\",
    r"\\\\",
]


def sanitize_string(input_str: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize a string input by removing dangerous characters
    
    Args:
        input_str: Input string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
        
    Validates: Requirement 20.3
    """
    if not isinstance(input_str, str):
        raise ValueError("Input must be a string")
    
    # Trim whitespace
    sanitized = input_str.strip()
    
    # Enforce max length
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    # HTML escape to prevent XSS
    sanitized = html.escape(sanitized)
    
    # Remove null bytes
    sanitized = sanitized.replace('\x00', '')
    
    # Remove control characters except newlines and tabs
    sanitized = ''.join(char for char in sanitized 
                       if char == '\n' or char == '\t' or not char.iscntrl())
    
    return sanitized


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal attacks
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
        
    Raises:
        ValueError: If filename is invalid
        
    Validates: Requirement 20.3
    """
    if not filename:
        raise ValueError("Filename cannot be empty")
    
    # Remove path components
    filename = Path(filename).name
    
    # Check for path traversal attempts
    for pattern in PATH_TRAVERSAL_PATTERNS:
        if re.search(pattern, filename, re.IGNORECASE):
            raise ValueError(f"Invalid filename: contains path traversal pattern")
    
    # Remove dangerous characters
    sanitized = re.sub(r'[^\w\s\-\.]', '', filename)
    
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    
    if not sanitized:
        raise ValueError("Filename contains only invalid characters")
    
    return sanitized


def validate_file_upload(
    filename: str,
    file_size: int,
    file_type: str,
    content: Optional[bytes] = None
) -> tuple[bool, Optional[str]]:
    """
    Validate a file upload for security
    
    Args:
        filename: Name of the uploaded file
        file_size: Size of the file in bytes
        file_type: Type of file ('specification' or 'rtl')
        content: Optional file content for additional validation
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Validates: Requirement 20.3
    """
    # Sanitize filename
    try:
        sanitized_filename = sanitize_filename(filename)
    except ValueError as e:
        return False, str(e)
    
    # Get file extension
    ext = Path(sanitized_filename).suffix.lower()
    
    # Validate extension based on file type
    if file_type == 'specification':
        if ext not in ALLOWED_SPEC_EXTENSIONS:
            return False, f"Invalid file type. Allowed: {', '.join(ALLOWED_SPEC_EXTENSIONS)}"
        max_size = MAX_SPEC_FILE_SIZE
    elif file_type == 'rtl':
        if ext not in ALLOWED_RTL_EXTENSIONS:
            return False, f"Invalid file type. Allowed: {', '.join(ALLOWED_RTL_EXTENSIONS)}"
        max_size = MAX_RTL_FILE_SIZE
    else:
        return False, "Invalid file type specified"
    
    # Validate file size
    if file_size <= 0:
        return False, "File is empty"
    
    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        return False, f"File too large. Maximum size: {max_mb:.0f} MB"
    
    # Additional content validation if provided
    if content:
        # Check for null bytes (potential binary exploit)
        if b'\x00' in content[:1024]:  # Check first 1KB
            return False, "File contains invalid binary data"
        
        # For text files, validate encoding
        if ext in {'.txt', '.md', '.sv', '.v', '.svh', '.vh'}:
            try:
                content[:1024].decode('utf-8')
            except UnicodeDecodeError:
                return False, "File encoding is not valid UTF-8"
    
    return True, None


def detect_sql_injection(input_str: str) -> bool:
    """
    Detect potential SQL injection attempts
    
    Args:
        input_str: Input string to check
        
    Returns:
        True if potential SQL injection detected
        
    Validates: Requirement 20.3
    """
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, input_str, re.IGNORECASE):
            logger.warning(f"Potential SQL injection detected: {pattern}")
            return True
    return False


def detect_xss(input_str: str) -> bool:
    """
    Detect potential XSS (Cross-Site Scripting) attempts
    
    Args:
        input_str: Input string to check
        
    Returns:
        True if potential XSS detected
        
    Validates: Requirement 20.3
    """
    for pattern in XSS_PATTERNS:
        if re.search(pattern, input_str, re.IGNORECASE):
            logger.warning(f"Potential XSS detected: {pattern}")
            return True
    return False


def detect_path_traversal(input_str: str) -> bool:
    """
    Detect potential path traversal attempts
    
    Args:
        input_str: Input string to check
        
    Returns:
        True if potential path traversal detected
        
    Validates: Requirement 20.3
    """
    for pattern in PATH_TRAVERSAL_PATTERNS:
        if re.search(pattern, input_str, re.IGNORECASE):
            logger.warning(f"Potential path traversal detected: {pattern}")
            return True
    return False


def sanitize_project_name(name: str) -> str:
    """
    Sanitize a project name
    
    Args:
        name: Project name
        
    Returns:
        Sanitized project name
        
    Raises:
        ValueError: If name is invalid
        
    Validates: Requirement 20.3
    """
    if not name or not name.strip():
        raise ValueError("Project name cannot be empty")
    
    # Sanitize basic string
    sanitized = sanitize_string(name, max_length=100)
    
    # Check for injection attempts
    if detect_sql_injection(sanitized):
        raise ValueError("Project name contains invalid characters")
    
    if detect_xss(sanitized):
        raise ValueError("Project name contains invalid characters")
    
    # Ensure reasonable length
    if len(sanitized) < 1:
        raise ValueError("Project name too short")
    
    if len(sanitized) > 100:
        raise ValueError("Project name too long (max 100 characters)")
    
    return sanitized


def sanitize_description(description: str) -> str:
    """
    Sanitize a description field
    
    Args:
        description: Description text
        
    Returns:
        Sanitized description
        
    Validates: Requirement 20.3
    """
    if not description:
        return ""
    
    # Sanitize basic string
    sanitized = sanitize_string(description, max_length=1000)
    
    # Check for injection attempts
    if detect_xss(sanitized):
        logger.warning("XSS attempt detected in description")
        # Remove the dangerous content
        for pattern in XSS_PATTERNS:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
    
    return sanitized


def validate_object_id(obj_id: str) -> bool:
    """
    Validate a MongoDB ObjectId format
    
    Args:
        obj_id: Object ID string
        
    Returns:
        True if valid ObjectId format
        
    Validates: Requirement 20.3
    """
    if not obj_id or not isinstance(obj_id, str):
        return False
    
    # ObjectId should be 24 hex characters
    if len(obj_id) != 24:
        return False
    
    # Check if all characters are hexadecimal
    try:
        int(obj_id, 16)
        return True
    except ValueError:
        return False


def sanitize_search_query(query: str) -> str:
    """
    Sanitize a search query
    
    Args:
        query: Search query string
        
    Returns:
        Sanitized query
        
    Validates: Requirement 20.3
    """
    if not query:
        return ""
    
    # Sanitize basic string
    sanitized = sanitize_string(query, max_length=200)
    
    # Remove special regex characters that could cause issues
    special_chars = r'[\[\]{}()*+?.,\\^$|#]'
    sanitized = re.sub(special_chars, ' ', sanitized)
    
    # Collapse multiple spaces
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    return sanitized


def sanitize_email(email: str) -> str:
    """
    Sanitize and validate an email address
    
    Args:
        email: Email address
        
    Returns:
        Sanitized email
        
    Raises:
        ValueError: If email is invalid
        
    Validates: Requirement 20.3
    """
    if not email:
        raise ValueError("Email cannot be empty")
    
    # Basic sanitization
    sanitized = email.strip().lower()
    
    # Basic email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, sanitized):
        raise ValueError("Invalid email format")
    
    # Check length
    if len(sanitized) > 254:  # RFC 5321
        raise ValueError("Email too long")
    
    return sanitized


class InputSanitizer:
    """
    Centralized input sanitization class
    
    Validates: Requirement 20.3
    """
    
    @staticmethod
    def sanitize_all_inputs(data: dict) -> dict:
        """
        Sanitize all string inputs in a dictionary
        
        Args:
            data: Dictionary of inputs
            
        Returns:
            Dictionary with sanitized inputs
        """
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # Sanitize string values
                sanitized[key] = sanitize_string(value)
            elif isinstance(value, dict):
                # Recursively sanitize nested dictionaries
                sanitized[key] = InputSanitizer.sanitize_all_inputs(value)
            elif isinstance(value, list):
                # Sanitize list items
                sanitized[key] = [
                    sanitize_string(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                # Keep other types as-is
                sanitized[key] = value
        
        return sanitized
    
    @staticmethod
    def validate_and_sanitize_project_data(data: dict) -> dict:
        """
        Validate and sanitize project creation data
        
        Args:
            data: Project data dictionary
            
        Returns:
            Sanitized project data
            
        Raises:
            ValueError: If validation fails
        """
        if 'name' not in data:
            raise ValueError("Project name is required")
        
        sanitized = {
            'name': sanitize_project_name(data['name']),
            'description': sanitize_description(data.get('description', '')),
        }
        
        # Preserve other fields if present
        for key in ['user_id', 'created_at', 'updated_at']:
            if key in data:
                sanitized[key] = data[key]
        
        return sanitized

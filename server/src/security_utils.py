# -*- coding: utf-8 -*-
"""
Security Utilities for Tatou Server
Fixes for fuzzing vulnerabilities discovered in Phase III
"""

import re
import html
from typing import Any, Dict, Optional
from functools import wraps
from flask import request, jsonify
import time

# ============================================================================
# Input Validation
# ============================================================================

def sanitize_string(value: str, max_length: int = 255, allow_html: bool = False) -> str:
    """
    Sanitize a string input to prevent XSS and injection attacks.
    
    Args:
        value: The input string to sanitize
        max_length: Maximum allowed length
        allow_html: If False, HTML entities will be escaped
        
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return ""
    
    # Truncate to max length
    value = value[:max_length]
    
    # Escape HTML if not allowed
    if not allow_html:
        value = html.escape(value)
    
    return value


def validate_username(username: str) -> tuple[bool, Optional[str]]:
    """
    Validate username format.
    
    Rules:
    - 3-50 characters
    - Alphanumeric, underscore, hyphen only
    - No HTML/script tags
    
    Returns:
        (is_valid, error_message)
    """
    if not username or not isinstance(username, str):
        return False, "Username is required"
    
    username = username.strip()
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    if len(username) > 50:
        return False, "Username must be at most 50 characters"
    
    # Check for dangerous patterns
    dangerous_patterns = [
        r'<script',
        r'javascript:',
        r'onerror=',
        r'onload=',
        r'<iframe',
        r'\.\./',  # Path traversal
        r'<?xml',  # XXE
        r'<!DOCTYPE',  # XXE
        r'<!ENTITY',  # XXE
    ]
    
    username_lower = username.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, username_lower, re.IGNORECASE):
            return False, "Username contains invalid characters"
    
    # Allow alphanumeric, underscore, hyphen only
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscore, and hyphen"
    
    return True, None


def validate_email(email: str) -> tuple[bool, Optional[str]]:
    """
    Validate email format.
    
    Returns:
        (is_valid, error_message)
    """
    if not email or not isinstance(email, str):
        return False, "Email is required"
    
    email = email.strip()
    
    if len(email) < 5 or len(email) > 255:
        return False, "Invalid email length"
    
    # Check for XSS/injection patterns
    dangerous_patterns = [
        r'<script',
        r'javascript:',
        r'\.\./',
        r'<?xml',
    ]
    
    email_lower = email.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, email_lower, re.IGNORECASE):
            return False, "Email contains invalid characters"
    
    # Basic email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "Invalid email format"
    
    return True, None


def validate_identity(identity: str) -> tuple[bool, Optional[str]]:
    """
    Validate RMAP identity string.
    
    Rules:
    - Must be from allowed group list
    - No path traversal
    - No XXE patterns
    
    Returns:
        (is_valid, error_message)
    """
    if not identity or not isinstance(identity, str):
        return False, "Identity is required"
    
    identity = identity.strip()
    
    # Check for path traversal
    if '..' in identity or '/' in identity or '\\' in identity:
        return False, "Invalid identity format"
    
    # Check for XXE patterns
    xxe_patterns = [
        r'<?xml',
        r'<!DOCTYPE',
        r'<!ENTITY',
        r'SYSTEM',
        r'PUBLIC',
        r'<script',
        r'javascript:',
    ]
    
    identity_lower = identity.lower()
    for pattern in xxe_patterns:
        if re.search(pattern, identity_lower, re.IGNORECASE):
            return False, "Invalid identity format"
    
    # Must match GROUP_XX pattern or allowed names
    if not re.match(r'^[A-Z_][A-Z0-9_]{0,20}$', identity.upper()):
        return False, "Invalid identity format"
    
    return True, None


def sanitize_error_message(error: Exception, debug: bool = False) -> str:
    """
    Sanitize error messages to prevent information disclosure.
    
    Args:
        error: The exception object
        debug: If True, return detailed error (only for development)
        
    Returns:
        Safe error message
    """
    if debug:
        return str(error)
    
    # Map exception types to generic messages
    error_type = type(error).__name__
    
    generic_messages = {
        'IntegrityError': 'Data conflict occurred',
        'OperationalError': 'Database temporarily unavailable',
        'ValueError': 'Invalid input provided',
        'TypeError': 'Invalid data type',
        'KeyError': 'Required field missing',
        'FileNotFoundError': 'Resource not found',
        'PermissionError': 'Access denied',
    }
    
    return generic_messages.get(error_type, 'Internal server error')


# ============================================================================
# Rate Limiting
# ============================================================================

# Simple in-memory rate limiting (for production, use Redis)
_rate_limit_store: Dict[str, list] = {}

def rate_limit(max_requests: int = 5, window_seconds: int = 60):
    """
    Rate limiting decorator.
    
    Args:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds
        
    Usage:
        @rate_limit(max_requests=5, window_seconds=60)
        def my_endpoint():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Get client identifier (IP address)
            client_id = request.remote_addr or 'unknown'
            key = f"{f.__name__}:{client_id}"
            
            current_time = time.time()
            
            # Initialize if not exists
            if key not in _rate_limit_store:
                _rate_limit_store[key] = []
            
            # Remove old timestamps outside the window
            _rate_limit_store[key] = [
                ts for ts in _rate_limit_store[key]
                if current_time - ts < window_seconds
            ]
            
            # Check if limit exceeded
            if len(_rate_limit_store[key]) >= max_requests:
                return jsonify({
                    "error": "Rate limit exceeded. Please try again later."
                }), 429
            
            # Add current timestamp
            _rate_limit_store[key].append(current_time)
            
            return f(*args, **kwargs)
        return wrapped
    return decorator


# ============================================================================
# Safe Response Wrapper
# ============================================================================

def safe_jsonify(data: Dict[str, Any], sanitize_output: bool = True) -> Any:
    """
    Create a JSON response with sanitized output.
    
    Args:
        data: Dictionary to jsonify
        sanitize_output: If True, escape HTML in string values
        
    Returns:
        Flask jsonify response
    """
    if sanitize_output:
        sanitized_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized_data[key] = html.escape(value)
            else:
                sanitized_data[key] = value
        return jsonify(sanitized_data)
    return jsonify(data)


# ============================================================================
# File Upload Validation
# ============================================================================

ALLOWED_EXTENSIONS = {'.pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_file_upload(file) -> tuple[bool, Optional[str]]:
    """
    Validate uploaded file.
    
    Returns:
        (is_valid, error_message)
    """
    if not file or not file.filename:
        return False, "No file provided"
    
    # Check file extension
    filename = file.filename.lower()
    if not any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        return False, "Only PDF files are allowed"
    
    # Check for path traversal in filename
    if '..' in filename or '/' in filename or '\\' in filename:
        return False, "Invalid filename"
    
    # Check file size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Seek back to start
    
    if size > MAX_FILE_SIZE:
        return False, f"File too large (max {MAX_FILE_SIZE // (1024*1024)}MB)"
    
    if size == 0:
        return False, "File is empty"
    
    return True, None


# ============================================================================
# Security Headers
# ============================================================================

def add_security_headers(response):
    """
    Add security headers to response.
    
    Usage in Flask:
        @app.after_request
        def after_request(response):
            return add_security_headers(response)
    """
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response




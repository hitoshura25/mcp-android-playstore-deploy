"""
Security utilities for hitoshura25-mcp-android-playstore-deploy.

This module provides security functions to protect against common vulnerabilities
including input validation, path traversal, command injection, and more.

See SECURITY.md for comprehensive security guidelines.
"""

import re
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from functools import wraps
from collections import defaultdict
from threading import Lock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Input Validation
# ============================================================================

def validate_string_input(
    value: str,
    max_length: int = 1000,
    min_length: int = 0,
    allowed_pattern: Optional[str] = None,
    field_name: str = "input"
) -> str:
    """
    Validate and sanitize string input.

    Args:
        value: Input string to validate
        max_length: Maximum allowed length
        min_length: Minimum required length
        allowed_pattern: Optional regex pattern for allowed characters
        field_name: Name of field for error messages

    Returns:
        Validated string

    Raises:
        ValueError: If validation fails
    """
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    if len(value) < min_length:
        raise ValueError(f"{field_name} must be at least {min_length} characters")

    if len(value) > max_length:
        raise ValueError(f"{field_name} exceeds maximum length of {max_length}")

    if allowed_pattern:
        if not re.match(allowed_pattern, value):
            raise ValueError(f"{field_name} contains invalid characters")

    return value


def validate_numeric_input(
    value: int,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
    field_name: str = "input"
) -> int:
    """
    Validate numeric input.

    Args:
        value: Input number to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        field_name: Name of field for error messages

    Returns:
        Validated number

    Raises:
        ValueError: If validation fails
    """
    # Check for bool first (bool is a subclass of int in Python)
    # isinstance(True, int) returns True, so we must explicitly reject booleans
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")

    if min_value is not None and value < min_value:
        raise ValueError(f"{field_name} must be at least {min_value}")

    if max_value is not None and value > max_value:
        raise ValueError(f"{field_name} must not exceed {max_value}")

    return value


# ============================================================================
# Path Traversal Protection
# ============================================================================

def validate_safe_path(
    requested_path: str,
    allowed_directory: Path,
    must_exist: bool = False
) -> Path:
    """
    Validate that a file path is within allowed directory.

    Protects against path traversal attacks like ../../../../etc/passwd
    Also handles symlinks and case-insensitive filesystems correctly.

    Args:
        requested_path: User-provided path
        allowed_directory: Base directory that must contain the path
        must_exist: Whether the path must already exist

    Returns:
        Validated absolute Path object

    Raises:
        ValueError: If path is outside allowed directory
        FileNotFoundError: If must_exist=True and path doesn't exist
    """
    # Resolve to absolute paths
    allowed_dir = Path(allowed_directory).resolve()
    target_path = (allowed_dir / requested_path).resolve()

    # Check if resolved path is within allowed directory
    # Using relative_to() is more robust than string comparison
    # as it properly handles symlinks and case-insensitive filesystems
    try:
        target_path.relative_to(allowed_dir)
    except ValueError:
        logger.warning(f"Path traversal attempt blocked: {requested_path}")
        raise ValueError("Access denied: path outside allowed directory")

    # Check existence if required
    if must_exist and not target_path.exists():
        raise FileNotFoundError(f"Path not found: {requested_path}")

    return target_path


# ============================================================================
# Command Injection Protection
# ============================================================================

def validate_safe_command(
    command_name: str,
    args: Optional[List[str]],
    allowed_commands: Dict[str, List[str]],
    allowed_arg_pattern: Optional[str] = None
) -> List[str]:
    """
    Validate command against whitelist and check arguments for injection.

    Uses both negative validation (checking for dangerous characters) and
    positive validation (ensuring only safe characters are present).

    Args:
        command_name: Name of command to execute
        args: Optional list of arguments
        allowed_commands: Dict mapping command names to their base command lists
        allowed_arg_pattern: Optional regex pattern for allowed argument characters.
                           Default: alphanumeric, dash, underscore, dot, slash, space

    Returns:
        Complete command list ready for subprocess.run

    Raises:
        ValueError: If command not allowed or arguments are invalid
    """
    if command_name not in allowed_commands:
        logger.warning(f"Blocked disallowed command: {command_name}")
        raise ValueError(f"Command not allowed: {command_name}")

    cmd = allowed_commands[command_name].copy()

    if args:
        # Check for shell metacharacters that could enable injection
        # This is a comprehensive list including glob characters and escape sequences
        dangerous_chars = [
            ';', '&', '|', '$', '`', '\n', '(', ')', '{', '}',
            '<', '>', '*', '?', '[', ']', '"', "'", '\\'
        ]

        # Default pattern: alphanumeric, dash, underscore, dot, slash, space
        # Adjust this pattern based on your specific command's needs
        if allowed_arg_pattern is None:
            allowed_arg_pattern = r'^[a-zA-Z0-9\-_./ ]+$'

        for arg in args:
            # Negative validation: check for dangerous characters
            if any(char in arg for char in dangerous_chars):
                logger.warning(f"Blocked command injection attempt (dangerous char): {arg}")
                raise ValueError(f"Invalid argument contains shell metacharacters: {arg}")

            # Positive validation: ensure only allowed characters
            if not re.match(allowed_arg_pattern, arg):
                logger.warning(f"Blocked command injection attempt (invalid chars): {arg}")
                raise ValueError(f"Argument contains disallowed characters: {arg}")

        cmd.extend(args)

    return cmd


# ============================================================================
# Rate Limiting
# ============================================================================

class RateLimiter:
    """Simple in-memory rate limiter for protecting against high-speed attacks."""

    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = Lock()

    def is_allowed(
        self,
        key: str,
        max_requests: int = 100,
        window_seconds: int = 60
    ) -> bool:
        """
        Check if request is within rate limits.

        Args:
            key: Identifier for rate limit (e.g., function name, user ID)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            True if allowed, False if rate limit exceeded
        """
        with self.lock:
            now = time.time()

            # Remove requests outside the current window
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if now - req_time < window_seconds
            ]

            # Check if limit exceeded
            if len(self.requests[key]) >= max_requests:
                logger.warning(
                    f"Rate limit exceeded for {key}: "
                    f"{len(self.requests[key])} requests in {window_seconds}s"
                )
                return False

            # Record this request
            self.requests[key].append(now)
            return True


# Global rate limiter instance
_rate_limiter = RateLimiter()


def with_rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """
    Decorator to add rate limiting to functions.

    Args:
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds

    Example:
        @with_rate_limit(max_requests=50, window_seconds=60)
        def my_tool(param: str) -> Dict[str, Any]:
            # This tool is limited to 50 calls per minute
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = func.__name__

            if not _rate_limiter.is_allowed(key, max_requests, window_seconds):
                raise ValueError(
                    f"Rate limit exceeded. Maximum {max_requests} requests "
                    f"per {window_seconds} seconds."
                )

            return func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# Audit Logging
# ============================================================================

def audit_log(func):
    """
    Decorator to log all function calls for security auditing.

    Logs function calls with parameters, automatically redacting sensitive
    parameter names to prevent accidental disclosure of secrets.

    Example:
        @audit_log
        def my_tool(user_id: str, data: str) -> Dict[str, Any]:
            # All calls will be logged with sensitive params redacted
            pass
    """
    # Parameter names that should never be logged
    SENSITIVE_PARAM_NAMES = {
        'password', 'token', 'api_key', 'secret', 'credential',
        'auth', 'authorization', 'apikey', 'access_token',
        'refresh_token', 'private_key', 'passphrase'
    }

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Redact sensitive parameter values
        safe_kwargs = {
            k: '[REDACTED]' if k.lower() in SENSITIVE_PARAM_NAMES else str(v)[:100]
            for k, v in kwargs.items()
        }

        # Truncate args to avoid logging large data
        safe_args = str(args)[:100]

        logger.info(f"Tool called: {func.__name__} args={safe_args} kwargs={safe_kwargs}")

        try:
            result = func(*args, **kwargs)
            logger.info(f"Tool {func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool {func.__name__} failed: {type(e).__name__}: {str(e)}")
            raise

    return wrapper


# ============================================================================
# Sensitive Data Redaction
# ============================================================================

def redact_sensitive_data(text: str) -> str:
    """
    Redact common sensitive patterns from text.

    This helps prevent accidental exposure of PII, credentials, etc.

    NOTE: These are basic patterns and may produce false positives/negatives.
    Adjust patterns based on your specific security requirements.

    Args:
        text: Text potentially containing sensitive data

    Returns:
        Text with sensitive patterns redacted
    """
    patterns = [
        # Email addresses (fixed: [A-Za-z] instead of [A-Z|a-z])
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', '[EMAIL_REDACTED]'),
        # US SSN
        (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]'),
        # Credit card numbers (basic pattern - may have false positives)
        # NOTE: This is a simple pattern that matches 16-digit numbers.
        # For production, consider:
        # - Using Luhn algorithm validation
        # - Handling 13, 14, 15, and 19-digit card numbers
        # - Being more specific about separators
        # This pattern may match transaction IDs and other non-card numbers.
        (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[CARD_REDACTED]'),
        # API keys (common patterns)
        (r'api[_-]?key[_-]?[=:]?\s*["\']?([a-zA-Z0-9_\-]{20,})', 'api_key=[REDACTED]'),
        # Passwords in various formats
        (r'password[_-]?[=:]?\s*["\']?([^\s"\']+)', 'password=[REDACTED]'),
        # Stripe-style keys
        (r'(sk|pk|rk)_(?:live|test)_[a-zA-Z0-9]{20,}', '[API_KEY_REDACTED]'),
        # AWS keys
        (r'AKIA[0-9A-Z]{16}', '[AWS_KEY_REDACTED]'),
        # JWT tokens (fixed: use + instead of * to require at least one character)
        (r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+', '[JWT_REDACTED]'),
        # IP addresses (if you want to redact them)
        # (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP_REDACTED]'),
    ]

    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result


# ============================================================================
# Combined Security Wrapper
# ============================================================================

def secure_tool(
    rate_limit_requests: int = 100,
    rate_limit_window: int = 60,
    enable_audit_log: bool = True
):
    """
    Combined decorator for common security measures.

    Applies rate limiting and audit logging in one decorator.

    Args:
        rate_limit_requests: Maximum requests in window
        rate_limit_window: Time window in seconds
        enable_audit_log: Whether to enable audit logging

    Example:
        @secure_tool(rate_limit_requests=50, rate_limit_window=60)
        def my_tool(param: str) -> Dict[str, Any]:
            # This tool has rate limiting and audit logging
            pass
    """
    def decorator(func):
        wrapped = func

        # Apply audit logging if enabled
        if enable_audit_log:
            wrapped = audit_log(wrapped)

        # Apply rate limiting
        wrapped = with_rate_limit(rate_limit_requests, rate_limit_window)(wrapped)

        return wrapped
    return decorator
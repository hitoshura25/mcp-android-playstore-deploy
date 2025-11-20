"""Custom exceptions for MCP Android Play Store Deploy."""


class MCPPlayStoreError(Exception):
    """Base exception for all MCP Play Store errors."""
    pass


class ConfigurationError(MCPPlayStoreError):
    """Configuration is invalid or incomplete."""
    pass


class AuthenticationError(MCPPlayStoreError):
    """Authentication failed (invalid credentials)."""
    pass


class PermissionError(MCPPlayStoreError):
    """Insufficient permissions."""
    pass


class NotFoundError(MCPPlayStoreError):
    """Resource not found."""
    pass


class ValidationError(MCPPlayStoreError):
    """Input validation failed."""
    pass


class APIError(MCPPlayStoreError):
    """External API error."""
    pass


class NetworkError(MCPPlayStoreError):
    """Network connectivity issue."""
    pass


class RateLimitError(MCPPlayStoreError):
    """API rate limit exceeded."""
    pass


class DependencyError(MCPPlayStoreError):
    """Required system dependency missing."""
    pass


class CommandError(MCPPlayStoreError):
    """System command execution failed."""
    pass


class SecurityError(MCPPlayStoreError):
    """Security-related issue (permissions, etc.)."""
    pass


class TimeoutError(MCPPlayStoreError):
    """Operation timed out."""
    pass


class ServiceError(MCPPlayStoreError):
    """External service error."""
    pass

# Security Guidelines for MCP Server Generator

> **Important**: This document addresses security considerations in light of emerging threats, including AI-orchestrated cyber espionage campaigns that exploit MCP tools for malicious purposes.

## Table of Contents

- [Threat Model](#threat-model)
- [For Generator Users](#for-generator-users)
- [For Generated MCP Servers](#for-generated-mcp-servers)
- [Security Best Practices](#security-best-practices)
- [Incident Response](#incident-response)

## Threat Model

### Known Attack Vectors

Based on [Anthropic's research on AI-orchestrated cyber espionage](https://www.anthropic.com/news/disrupting-AI-espionage), MCP servers can be exploited for:

1. **Reconnaissance**: Infrastructure scanning, vulnerability discovery
2. **Credential Harvesting**: Extracting authentication tokens, API keys, passwords
3. **Data Exfiltration**: Accessing and transmitting sensitive data
4. **Exploit Development**: Automated vulnerability testing and exploitation
5. **High-Speed Automation**: Thousands of malicious requests per second

### Attack Methodology

Attackers may:
- **Jailbreak AI systems** by breaking malicious tasks into innocent-seeming steps
- **Chain multiple tools** to perform complex attacks with minimal human oversight
- **Exploit lack of rate limiting** to execute attacks at unprecedented speed
- **Use legitimate-looking requests** to bypass simple keyword-based filters

## For Generator Users

### Before Generating an MCP Server

#### 1. Validate Tool Purpose

**⚠️ Critical**: Carefully consider what capabilities your MCP server will expose.

**High-risk tool patterns** to avoid or secure carefully:
- File system access (read/write/delete operations)
- Network operations (HTTP requests, socket connections)
- Command/shell execution
- Database access with write permissions
- Authentication/credential management
- Code execution or evaluation
- System information disclosure

**Example - Dangerous Tool Definition**:
```json
{
  "tools": [
    {
      "name": "execute_command",
      "description": "Execute shell command",
      "parameters": [
        {"name": "command", "type": "string", "required": true}
      ]
    }
  ]
}
```

**❌ This tool is extremely dangerous** - it allows arbitrary command execution.

**✅ Better approach**: Create specific, limited-scope tools:
```json
{
  "tools": [
    {
      "name": "check_service_status",
      "description": "Check if a specific whitelisted service is running",
      "parameters": [
        {"name": "service_name", "type": "string", "required": true}
      ]
    }
  ]
}
```

#### 2. Principle of Least Privilege

Design tools that:
- Perform **specific, limited functions** rather than general operations
- Have **explicit whitelists** rather than blacklists
- Require **validation** before performing sensitive operations
- Return **minimal necessary data** to the model

#### 3. Security Review Checklist

Before generating, ask:

- [ ] Could this tool access sensitive files or data?
- [ ] Could this tool modify system state?
- [ ] Could this tool be used for network reconnaissance?
- [ ] Could this tool execute arbitrary code?
- [ ] Does this tool validate all inputs?
- [ ] Does this tool have rate limiting?
- [ ] Does this tool log security-relevant actions?

## For Generated MCP Servers

### Essential Security Measures to Implement

When implementing the TODO stubs in `generator.py`, **always include**:

#### 1. Input Validation

```python
def validate_input(value: str, max_length: int = 1000, allowed_pattern: str = None) -> str:
    """Validate and sanitize user input."""
    if not value:
        raise ValueError("Input cannot be empty")

    if len(value) > max_length:
        raise ValueError(f"Input exceeds maximum length of {max_length}")

    if allowed_pattern:
        import re
        if not re.match(allowed_pattern, value):
            raise ValueError(f"Input does not match allowed pattern")

    return value
```

**Use in your tools**:
```python
def my_tool(user_input: str) -> Dict[str, Any]:
    # Validate input
    user_input = validate_input(
        user_input,
        max_length=500,
        allowed_pattern=r'^[a-zA-Z0-9\s\-_\.]+$'  # Alphanumeric only
    )

    # Now safe to use
    # ... implementation ...
```

#### 2. Path Traversal Protection

**❌ Vulnerable**:
```python
def read_file(filename: str) -> str:
    with open(filename) as f:  # Allows ../../../../etc/passwd
        return f.read()
```

**✅ Secure**:
```python
from pathlib import Path
import os

ALLOWED_DIR = Path("/safe/data/directory")

def read_file(filename: str) -> str:
    # Resolve to absolute path and check it's within allowed directory
    requested_path = (ALLOWED_DIR / filename).resolve()

    if not str(requested_path).startswith(str(ALLOWED_DIR.resolve())):
        raise ValueError("Access denied: path traversal detected")

    if not requested_path.exists():
        raise FileNotFoundError(f"File not found: {filename}")

    with open(requested_path) as f:
        return f.read()
```

#### 3. Command Injection Protection

**❌ Vulnerable**:
```python
import subprocess

def run_command(cmd: str) -> str:
    result = subprocess.run(cmd, shell=True, capture_output=True)  # Dangerous!
    return result.stdout.decode()
```

**✅ Secure**:
```python
import re
import subprocess
from typing import List, Optional

ALLOWED_COMMANDS = {
    'git_status': ['git', 'status'],
    'list_files': ['ls', '-la'],
}

def run_safe_command(
    command_name: str,
    args: List[str] = None,
    allowed_arg_pattern: Optional[str] = None
) -> str:
    """
    Run only whitelisted commands with validated arguments.

    Uses both negative validation (checking for dangerous characters) and
    positive validation (ensuring only safe characters are present).
    """
    if command_name not in ALLOWED_COMMANDS:
        raise ValueError(f"Command not allowed: {command_name}")

    cmd = ALLOWED_COMMANDS[command_name].copy()

    if args:
        # Comprehensive list of dangerous shell metacharacters
        dangerous_chars = [
            ';', '&', '|', '$', '`', '\n', '(', ')', '{', '}',
            '<', '>', '*', '?', '[', ']', '"', "'", '\\'
        ]

        # Default: allow alphanumeric, dash, underscore, dot, slash, space
        if allowed_arg_pattern is None:
            allowed_arg_pattern = r'^[a-zA-Z0-9\-_./ ]+$'

        for arg in args:
            # Negative validation: check for dangerous characters
            if any(c in arg for c in dangerous_chars):
                raise ValueError(f"Invalid argument contains shell metacharacters: {arg}")

            # Positive validation: ensure only allowed characters
            if not re.match(allowed_arg_pattern, arg):
                raise ValueError(f"Argument contains disallowed characters: {arg}")

        cmd.extend(args)

    result = subprocess.run(
        cmd,
        shell=False,  # NEVER use shell=True with user-supplied input
        capture_output=True,
        timeout=10  # Prevent hanging
    )
    return result.stdout.decode()
```

**Note on `shell=True`**: While the guidance "NEVER use shell=True" is the safest default, the critical issue is whether user input reaches the shell unsanitized. If you must use `shell=True` for legitimate reasons (e.g., complex shell pipelines), ensure all arguments are from trusted sources and properly quoted/escaped. However, in almost all cases, you should use `shell=False` with a list of arguments.

#### 4. Rate Limiting and Audit Logging

```python
import time
import logging
from functools import wraps
from collections import defaultdict
from threading import Lock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Simple in-memory rate limiter (for production, use Redis or similar)
class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = Lock()

    def is_allowed(self, key: str, max_requests: int = 100, window_seconds: int = 60) -> bool:
        """Check if request is within rate limits."""
        with self.lock:
            now = time.time()
            # Clean old requests
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if now - req_time < window_seconds
            ]

            if len(self.requests[key]) >= max_requests:
                return False

            self.requests[key].append(now)
            return True

rate_limiter = RateLimiter()

def with_rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """Decorator to add rate limiting to functions."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use function name as key (in production, use user/session ID)
            key = func.__name__

            if not rate_limiter.is_allowed(key, max_requests, window_seconds):
                logger.warning(f"Rate limit exceeded for {key}")
                raise ValueError(f"Rate limit exceeded. Max {max_requests} requests per {window_seconds}s")

            return func(*args, **kwargs)
        return wrapper
    return decorator

def audit_log(func):
    """Decorator to log all function calls for security auditing."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Log the call (excluding sensitive parameters)
        logger.info(f"Tool called: {func.__name__} with args: {args}, kwargs: {kwargs}")

        try:
            result = func(*args, **kwargs)
            logger.info(f"Tool {func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool {func.__name__} failed: {str(e)}")
            raise

    return wrapper

# Usage in your tools:
@audit_log
@with_rate_limit(max_requests=50, window_seconds=60)
def my_sensitive_tool(param: str) -> Dict[str, Any]:
    """This tool is rate-limited and logged."""
    # ... implementation ...
    return {'success': True}
```

#### 5. Sensitive Data Protection

```python
import re

def redact_sensitive_data(text: str) -> str:
    """Redact common sensitive patterns from text."""
    patterns = [
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),  # Email
        (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),  # SSN
        (r'\b\d{16}\b', '[CARD]'),  # Credit card
        (r'api[_-]?key[_-]?=?["\']?([a-zA-Z0-9_\-]+)', 'api_key=[REDACTED]'),  # API keys
        (r'password[_-]?=?["\']?([^"\s]+)', 'password=[REDACTED]'),  # Passwords
        (r'(sk|pk)_[a-zA-Z0-9]{20,}', '[API_KEY]'),  # Stripe-like keys
    ]

    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result

def my_tool_with_pii(user_data: str) -> Dict[str, Any]:
    """Tool that handles potentially sensitive data."""
    # Process data
    result = process_data(user_data)

    # Redact before returning to model
    safe_result = redact_sensitive_data(str(result))

    return {'success': True, 'data': safe_result}
```

#### 6. Timeout Protection

**For async operations (recommended)**:
```python
import asyncio

async def potentially_slow_operation(data: str) -> Dict[str, Any]:
    """Async operation with timeout (works on all platforms)."""
    try:
        result = await asyncio.wait_for(
            expensive_async_computation(data),
            timeout=30.0  # 30 second timeout
        )
        return {'success': True, 'result': result}
    except asyncio.TimeoutError:
        return {'success': False, 'error': 'Operation timed out'}
```

**For synchronous operations with threading**:
```python
import threading
from typing import Dict, Any, Optional

def potentially_slow_operation(data: str) -> Dict[str, Any]:
    """
    Synchronous operation with timeout using threading.

    Cross-platform compatible (works on Windows and Unix).
    Thread-safe alternative to signal.SIGALRM.
    """
    result_container = {'result': None, 'error': None}

    def worker():
        try:
            result_container['result'] = expensive_computation(data)
        except Exception as e:
            result_container['error'] = str(e)

    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()
    thread.join(timeout=30.0)  # 30 second timeout

    if thread.is_alive():
        # Thread is still running - timeout occurred
        # Note: thread will continue running in background
        return {'success': False, 'error': 'Operation timed out'}

    if result_container['error']:
        return {'success': False, 'error': result_container['error']}

    return {'success': True, 'result': result_container['result']}
```

**Note**: The `signal.SIGALRM` approach only works on Unix-like systems, is not thread-safe, and doesn't work with async code. For production code, use `asyncio.wait_for()` for async operations or the threading approach for synchronous code.

## Security Best Practices

### Development Phase

1. **Security Review**: Review all tool implementations for security issues
2. **Dependency Scanning**: Run `pip-audit` to check for vulnerable dependencies
3. **Static Analysis**: Use tools like `bandit` for Python security linting
4. **Testing**: Write tests for security scenarios (invalid inputs, path traversal, etc.)

```bash
# Install security tools
pip install bandit pip-audit safety

# Run security checks
bandit -r your_package_name/
pip-audit
safety check
```

### Deployment Phase

1. **Principle of Least Privilege**: Run MCP servers with minimal permissions
2. **Environment Isolation**: Use virtual environments or containers
3. **Secret Management**: Never hardcode credentials; use environment variables or secret managers
4. **Monitor Logs**: Review audit logs regularly for suspicious patterns
5. **Update Dependencies**: Keep all packages updated to patch security vulnerabilities

### Runtime Security

```bash
# Use restricted user (not root)
useradd -m -s /bin/bash mcp-user

# Run with limited permissions
sudo -u mcp-user hitoshura25-mcp-server-generator

# Use environment variables for secrets
export API_KEY=$(cat /secure/path/to/key)
export DATABASE_URL="postgresql://user:pass@localhost/db"
```

### Configuration Security

**Claude Desktop Configuration** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "your-mcp-server": {
      "command": "uvx",
      "args": ["your-package-name"],
      "env": {
        "LOG_LEVEL": "INFO",
        "RATE_LIMIT_ENABLED": "true",
        "ALLOWED_PATHS": "/safe/data/directory"
      }
    }
  }
}
```

**❌ Don't put secrets in config**:
```json
{
  "env": {
    "API_KEY": "sk_live_abc123..."  // Never do this!
  }
}
```

**✅ Use environment or secret files**:
```json
{
  "env": {
    "API_KEY_FILE": "/home/user/.secrets/api_key"
  }
}
```

## Detecting Malicious Use

### Suspicious Patterns to Monitor

Watch for:
- **High request rates** (thousands per minute)
- **Sequential file access** across directory structures
- **Network scanning patterns** (sequential IP/port access)
- **Authentication failures** followed by successes
- **Large data transfers** or exports
- **Unusual time patterns** (activity at odd hours)
- **Error patterns** that suggest automated probing

### Implementing Detection

```python
from collections import Counter
from datetime import datetime, timedelta

class AnomalyDetector:
    def __init__(self):
        self.request_times = []
        self.error_counts = Counter()

    def check_request_rate(self, threshold: int = 100) -> bool:
        """Detect suspiciously high request rates."""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)

        # Remove old requests
        self.request_times = [
            t for t in self.request_times if t > one_minute_ago
        ]

        self.request_times.append(now)

        if len(self.request_times) > threshold:
            logger.warning(f"Suspicious request rate: {len(self.request_times)} requests/minute")
            return True

        return False

    def check_error_patterns(self, tool_name: str, threshold: int = 10) -> bool:
        """Detect suspicious error patterns that might indicate probing."""
        self.error_counts[tool_name] += 1

        if self.error_counts[tool_name] > threshold:
            logger.warning(f"High error count for {tool_name}: {self.error_counts[tool_name]}")
            return True

        return False

detector = AnomalyDetector()

def monitored_tool(param: str) -> Dict[str, Any]:
    """Tool with anomaly detection."""
    if detector.check_request_rate(threshold=100):
        raise ValueError("Suspicious activity detected: high request rate")

    try:
        result = process(param)
        return result
    except Exception as e:
        if detector.check_error_patterns('monitored_tool'):
            logger.error("Possible attack: high error rate detected")
        raise
```

## Incident Response

### If You Suspect Compromise

1. **Immediately disable the MCP server**
   - Stop the Claude Desktop application
   - Remove the server from `claude_desktop_config.json`
   - Kill any running server processes

2. **Review audit logs**
   - Check for suspicious access patterns
   - Identify potentially compromised data
   - Note timestamps of suspicious activity

3. **Assess impact**
   - What data could have been accessed?
   - Were any credentials exposed?
   - Were any systems modified?

4. **Remediate**
   - Rotate any credentials that may have been exposed
   - Patch vulnerabilities in your tool implementations
   - Update dependencies
   - Strengthen input validation

5. **Report**
   - For MCP-related security issues: [Report to Anthropic](https://www.anthropic.com/security)
   - For this generator: [GitHub Security Advisories](https://github.com/hitoshura25/mcp-server-generator/security/advisories)

## Security Checklist for Generated MCP Servers

Use this checklist before deploying:

- [ ] All inputs are validated and sanitized
- [ ] File operations use path traversal protection
- [ ] No command execution with shell=True
- [ ] Sensitive data is redacted from outputs
- [ ] Rate limiting is implemented
- [ ] Audit logging is configured
- [ ] Timeouts prevent hanging operations
- [ ] Dependencies have been scanned for vulnerabilities
- [ ] Secrets are not hardcoded
- [ ] Server runs with minimal privileges
- [ ] Error messages don't leak sensitive information
- [ ] All async operations have proper error handling

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [Anthropic's MCP Security Documentation](https://modelcontextprotocol.io/docs/security)
- [Common Weakness Enumeration (CWE)](https://cwe.mitre.org/)

## Reporting Security Issues

If you discover a security vulnerability in:
- **This generator**: Email security@anthropic.com or create a [private security advisory](https://github.com/hitoshura25/mcp-server-generator/security/advisories/new)
- **Generated servers**: Responsible disclosure to the server maintainer
- **MCP protocol**: Report to Anthropic's security team

---

**Remember**: Security is not a one-time checklist but an ongoing process. Regularly review and update your security measures as threats evolve.
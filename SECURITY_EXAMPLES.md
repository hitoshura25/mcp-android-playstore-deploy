# Security Implementation Examples

This file provides concrete examples of secure tool implementations for hitoshura25-mcp-android-playstore-deploy.

## Table of Contents

- [Input Validation](#input-validation)
- [File Operations](#file-operations)
- [Command Execution](#command-execution)
- [API Calls](#api-calls)
- [Database Operations](#database-operations)
- [Complete Secure Tool Example](#complete-secure-tool-example)

## Input Validation

### Basic String Validation

```python
from .security_utils import validate_string_input

def process_text(text: str, max_length: int = None) -> Dict[str, Any]:
    """Process text with input validation."""
    # Validate input
    validated_text = validate_string_input(
        text,
        max_length=max_length or 1000,
        allowed_pattern=r'^[a-zA-Z0-9\s\-_\.!?,]+$',  # Alphanumeric + common punctuation
        field_name='text'
    )

    # Your logic here
    result = validated_text.upper()

    return {'success': True, 'result': result}
```

### Numeric Validation

```python
from .security_utils import validate_numeric_input

def calculate(amount: int) -> Dict[str, Any]:
    """Calculate with numeric validation."""
    # Validate numeric input
    validated_amount = validate_numeric_input(
        amount,
        min_value=0,
        max_value=1000000,
        field_name='amount'
    )

    result = validated_amount * 2

    return {'success': True, 'result': result}
```

## File Operations

### Secure File Reading

```python
from pathlib import Path
from .security_utils import validate_safe_path, redact_sensitive_data

# Define allowed directory
SAFE_DATA_DIR = Path("/safe/data/directory")

def read_file(filename: str) -> Dict[str, Any]:
    """Securely read a file from allowed directory."""
    try:
        # Validate path to prevent directory traversal
        safe_path = validate_safe_path(
            filename,
            allowed_directory=SAFE_DATA_DIR,
            must_exist=True
        )

        # Read file
        content = safe_path.read_text()

        # Redact sensitive data before returning
        safe_content = redact_sensitive_data(content)

        return {'success': True, 'content': safe_content}

    except FileNotFoundError:
        return {'success': False, 'error': 'File not found'}
    except ValueError as e:
        return {'success': False, 'error': f'Security violation: {e}'}
```

### Secure File Writing

```python
from pathlib import Path
from .security_utils import validate_safe_path, validate_string_input

SAFE_OUTPUT_DIR = Path("/safe/output/directory")

def write_file(filename: str, content: str) -> Dict[str, Any]:
    """Securely write a file to allowed directory."""
    try:
        # Validate filename (no path traversal)
        safe_path = validate_safe_path(
            filename,
            allowed_directory=SAFE_OUTPUT_DIR,
            must_exist=False
        )

        # Validate content
        validated_content = validate_string_input(
            content,
            max_length=100000,  # 100KB limit
            field_name='content'
        )

        # Write file
        safe_path.write_text(validated_content)

        return {'success': True, 'path': str(safe_path)}

    except ValueError as e:
        return {'success': False, 'error': str(e)}
```

## Command Execution

### Secure Command Execution with Whitelist

```python
import subprocess
from typing import List, Optional
from .security_utils import validate_safe_command

# Define allowed commands with their base arguments
ALLOWED_COMMANDS = {
    'git_status': ['git', 'status'],
    'git_diff': ['git', 'diff'],
    'list_dir': ['ls', '-la'],
    'disk_usage': ['du', '-sh'],
}

def run_command(command_name: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
    """Execute whitelisted commands safely."""
    try:
        # Validate command against whitelist
        cmd = validate_safe_command(
            command_name,
            args,
            allowed_commands=ALLOWED_COMMANDS
        )

        # Execute without shell
        result = subprocess.run(
            cmd,
            shell=False,  # NEVER use shell=True with user-supplied input
            capture_output=True,
            timeout=30,  # Timeout to prevent hanging
            text=True
        )

        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }

    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Command timed out'}
    except ValueError as e:
        return {'success': False, 'error': f'Security violation: {e}'}
```

## API Calls

### Secure API Call with Rate Limiting and Validation

```python
import httpx
from .security_utils import (
    validate_string_input,
    with_rate_limit,
    audit_log,
    redact_sensitive_data
)

@audit_log  # Log all API calls for security auditing
@with_rate_limit(max_requests=100, window_seconds=60)  # Limit to 100 calls/minute
async def fetch_data(api_endpoint: str, query: str) -> Dict[str, Any]:
    """Fetch data from API with security measures."""
    try:
        # Validate API endpoint against whitelist
        allowed_endpoints = [
            'https://api.example.com/v1/data',
            'https://api.example.com/v1/search',
        ]

        if api_endpoint not in allowed_endpoints:
            return {'success': False, 'error': 'API endpoint not allowed'}

        # Validate query parameter
        validated_query = validate_string_input(
            query,
            max_length=200,
            allowed_pattern=r'^[a-zA-Z0-9\s\-_]+$',
            field_name='query'
        )

        # Make API call with timeout
        MAX_RESPONSE_SIZE = 1_000_000  # 1MB limit to prevent memory issues
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                api_endpoint,
                params={'q': validated_query}
            )
            response.raise_for_status()

            # Check response size before processing
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > MAX_RESPONSE_SIZE:
                return {'success': False, 'error': 'Response too large'}

            data = response.json()

        # Apply redaction selectively to string fields
        # rather than converting entire structure to string
        def redact_dict_strings(obj):
            """Recursively redact string values in dict/list structures."""
            if isinstance(obj, dict):
                return {k: redact_dict_strings(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [redact_dict_strings(item) for item in obj]
            elif isinstance(obj, str):
                return redact_sensitive_data(obj)
            else:
                return obj

        safe_data = redact_dict_strings(data)

        return {'success': True, 'data': safe_data}

    except httpx.TimeoutException:
        return {'success': False, 'error': 'API request timed out'}
    except httpx.HTTPStatusError as e:
        return {'success': False, 'error': f'API error: {e.response.status_code}'}
    except Exception as e:
        # Log internal error details for debugging
        logger.error(f"Unexpected error in fetch_data: {type(e).__name__}: {e}", exc_info=True)
        # Don't leak internal error details to user
        return {'success': False, 'error': 'An error occurred'}
```

## Database Operations

### Secure Database Query with Parameterization

```python
import sqlite3
from .security_utils import (
    validate_string_input,
    validate_numeric_input,
    audit_log,
    with_rate_limit,
    redact_sensitive_data
)

@audit_log  # Log all database operations
@with_rate_limit(max_requests=50, window_seconds=60)
def query_user(user_id: int) -> Dict[str, Any]:
    """Query user data securely using parameterized queries."""
    conn = None
    try:
        # Validate input
        validated_id = validate_numeric_input(
            user_id,
            min_value=1,
            max_value=999999999,
            field_name='user_id'
        )

        # Use parameterized query to prevent SQL injection
        conn = sqlite3.connect('database.db', timeout=5.0)
        cursor = conn.cursor()

        # GOOD: Parameterized query
        cursor.execute(
            'SELECT username, email FROM users WHERE id = ?',
            (validated_id,)
        )

        # NEVER do this (SQL injection vulnerability):
        # cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')

        result = cursor.fetchone()

        if result:
            username, email = result
            # Redact sensitive data
            safe_email = redact_sensitive_data(email)

            return {
                'success': True,
                'user': {
                    'id': validated_id,
                    'username': username,
                    'email': safe_email
                }
            }
        else:
            return {'success': False, 'error': 'User not found'}

    except sqlite3.Error as e:
        # Log details internally for debugging
        logger.error(f"Database error in query_user: {e}", exc_info=True)
        # Don't leak database error details to user
        return {'success': False, 'error': 'Database error occurred'}
    finally:
        # Always close connection, even if an error occurred
        if conn:
            conn.close()
```

## Complete Secure Tool Example

### Production-Ready Secure Implementation

```python
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from .security_utils import (
    validate_string_input,
    validate_numeric_input,
    validate_safe_path,
    redact_sensitive_data,
    secure_tool,  # Combined decorator
    audit_log,
    with_rate_limit,
)

logger = logging.getLogger(__name__)

# Configuration
ALLOWED_DATA_DIR = Path('/safe/data')
MAX_FILE_SIZE = 1_000_000  # 1MB

@secure_tool(rate_limit_requests=50, rate_limit_window=60, enable_audit_log=True)
async def process_user_file(
    user_id: int,
    filename: str,
    operation: str
) -> Dict[str, Any]:
    """
    Process a user's file with comprehensive security measures.

    This example demonstrates:
    - Input validation
    - Path traversal protection
    - Rate limiting
    - Audit logging
    - Error handling without info leakage
    - Sensitive data redaction
    """
    try:
        # 1. Validate all inputs
        validated_user_id = validate_numeric_input(
            user_id,
            min_value=1,
            max_value=999999999,
            field_name='user_id'
        )

        validated_filename = validate_string_input(
            filename,
            max_length=255,
            allowed_pattern=r'^[a-zA-Z0-9\-_\.]+$',  # Only safe filename chars
            field_name='filename'
        )

        validated_operation = validate_string_input(
            operation,
            max_length=20,
            field_name='operation'
        )

        # 2. Validate operation against whitelist
        allowed_operations = ['read', 'analyze', 'summary']
        if validated_operation not in allowed_operations:
            return {
                'success': False,
                'error': f'Operation not allowed. Allowed: {allowed_operations}'
            }

        # 3. Build safe path with user isolation
        user_dir = ALLOWED_DATA_DIR / f"user_{validated_user_id}"
        safe_path = validate_safe_path(
            validated_filename,
            allowed_directory=user_dir,
            must_exist=True
        )

        # 4. Check file size to prevent resource exhaustion
        file_size = safe_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            return {
                'success': False,
                'error': f'File too large. Max size: {MAX_FILE_SIZE} bytes'
            }

        # 5. Read file (this is now safe)
        content = safe_path.read_text()

        # 6. Process based on operation
        if validated_operation == 'read':
            result = content
        elif validated_operation == 'analyze':
            result = f"File contains {len(content)} characters"
        elif validated_operation == 'summary':
            result = content[:200] + '...' if len(content) > 200 else content

        # 7. Redact sensitive data before returning
        safe_result = redact_sensitive_data(str(result))

        return {
            'success': True,
            'operation': validated_operation,
            'result': safe_result,
            'file_size': file_size
        }

    except FileNotFoundError:
        # Specific error without path leakage
        return {'success': False, 'error': 'File not found'}

    except ValueError as e:
        # Validation or security violation
        logger.warning(f"Security violation in process_user_file: {e}")
        return {'success': False, 'error': str(e)}

    except Exception as e:
        # Catch-all: log details internally, return generic error
        logger.error(f"Unexpected error in process_user_file: {e}", exc_info=True)
        return {'success': False, 'error': 'An internal error occurred'}
```

## Anti-Patterns to Avoid

### ❌ DON'T: Command Injection Vulnerability

```python
# NEVER DO THIS
def bad_run_command(filename: str):
    import os
    os.system(f"cat {filename}")  # Command injection!
```

**Attack**: `filename = "file.txt; rm -rf /"`

### ❌ DON'T: Path Traversal Vulnerability

```python
# NEVER DO THIS
def bad_read_file(filename: str):
    with open(f"/data/{filename}") as f:  # Path traversal!
        return f.read()
```

**Attack**: `filename = "../../../../etc/passwd"`

### ❌ DON'T: SQL Injection Vulnerability

```python
# NEVER DO THIS
def bad_query(user_input: str):
    cursor.execute(f"SELECT * FROM users WHERE name = '{user_input}'")  # SQL injection!
```

**Attack**: `user_input = "' OR '1'='1"`

### ❌ DON'T: No Input Validation

```python
# NEVER DO THIS
def bad_process(data: str):
    # No validation - accepts any size/content
    result = expensive_operation(data)  # Could cause DoS
    return result
```

### ❌ DON'T: No Rate Limiting

```python
# NEVER DO THIS
def bad_api_call(endpoint: str):
    # No rate limit - can be abused for DoS
    return requests.get(endpoint).json()
```

## Security Checklist

Before deploying any tool, verify:

- [ ] All inputs are validated with appropriate constraints
- [ ] File operations use `validate_safe_path()`
- [ ] Commands use `validate_safe_command()` with whitelisting
- [ ] Sensitive data is redacted with `redact_sensitive_data()`
- [ ] Rate limiting is applied to prevent abuse
- [ ] Audit logging is enabled for security-relevant operations
- [ ] Errors don't leak sensitive information
- [ ] Timeouts prevent hanging operations
- [ ] SQL queries use parameterization (never string concatenation)
- [ ] No `shell=True` in subprocess calls
- [ ] No `eval()` or `exec()` with user input

## Additional Resources

- **SECURITY.md**: Comprehensive security guidelines
- **security_utils.py**: Security utility functions
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [Anthropic's AI Espionage Research](https://www.anthropic.com/news/disrupting-AI-espionage)
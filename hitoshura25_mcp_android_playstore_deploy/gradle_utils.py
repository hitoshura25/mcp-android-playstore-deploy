"""Gradle utilities for Android project configuration."""

import os
import secrets
import string
from pathlib import Path


def detect_gradle_user_home() -> Path:
    """
    Detect Gradle user home directory.

    Returns:
        Path to Gradle user home (e.g., ~/.gradle/)

    Priority:
        1. $GRADLE_USER_HOME environment variable
        2. ~/.gradle/ (default)

    Example:
        >>> gradle_home = detect_gradle_user_home()
        >>> print(gradle_home)
        /Users/username/.gradle
    """
    gradle_home_env = os.environ.get("GRADLE_USER_HOME")
    if gradle_home_env:
        return Path(gradle_home_env)
    return Path.home() / ".gradle"


def generate_secure_password(length: int = 16) -> str:
    """
    Generate cryptographically secure random password.

    Uses secrets module for cryptographic strength suitable for
    keystore passwords.

    Args:
        length: Password length (default: 16)

    Returns:
        Secure random password string

    Character set:
        - Uppercase letters (A-Z)
        - Lowercase letters (a-z)
        - Digits (0-9)
        - Safe symbols: !@#$%^&*-_=+

    Example:
        >>> password = generate_secure_password(length=20)
        >>> len(password)
        20
        >>> password = generate_secure_password()
        >>> len(password)
        16
    """
    charset = string.ascii_letters + string.digits + "!@#$%^&*-_=+"
    return "".join(secrets.choice(charset) for _ in range(length))

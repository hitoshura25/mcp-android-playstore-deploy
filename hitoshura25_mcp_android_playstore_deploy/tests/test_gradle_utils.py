"""Tests for Gradle utilities"""

import os
from pathlib import Path
from hitoshura25_mcp_android_playstore_deploy.gradle_utils import (
    detect_gradle_user_home,
    generate_secure_password,
)


def test_detect_gradle_user_home_default():
    """Test default Gradle home detection"""
    # Save and clear GRADLE_USER_HOME if it exists
    original_gradle_home = os.environ.get("GRADLE_USER_HOME")
    if "GRADLE_USER_HOME" in os.environ:
        del os.environ["GRADLE_USER_HOME"]

    try:
        gradle_home = detect_gradle_user_home()

        # Should return ~/.gradle
        assert gradle_home.name == ".gradle"
        assert gradle_home.is_absolute()
        assert str(gradle_home) == str(Path.home() / ".gradle")
    finally:
        # Restore original value
        if original_gradle_home:
            os.environ["GRADLE_USER_HOME"] = original_gradle_home


def test_detect_gradle_user_home_env_var(monkeypatch):
    """Test Gradle home detection with GRADLE_USER_HOME set"""
    custom_home = "/custom/gradle/home"
    monkeypatch.setenv("GRADLE_USER_HOME", custom_home)

    gradle_home = detect_gradle_user_home()
    assert str(gradle_home) == custom_home


def test_generate_secure_password_length():
    """Test password generation length"""
    # Test default length
    password_default = generate_secure_password()
    assert len(password_default) == 16

    # Test custom lengths
    password_20 = generate_secure_password(length=20)
    assert len(password_20) == 20

    password_32 = generate_secure_password(length=32)
    assert len(password_32) == 32

    password_8 = generate_secure_password(length=8)
    assert len(password_8) == 8


def test_generate_secure_password_uniqueness():
    """Test that passwords are unique"""
    # Generate 10 passwords and ensure they're all unique
    passwords = [generate_secure_password() for _ in range(10)]
    assert len(set(passwords)) == 10  # All unique

    # Generate 10 passwords with custom length and ensure uniqueness
    passwords_20 = [generate_secure_password(length=20) for _ in range(10)]
    assert len(set(passwords_20)) == 10  # All unique

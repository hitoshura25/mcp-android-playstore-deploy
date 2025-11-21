"""Tests for MCP tools in generator.py"""

import pytest
from pathlib import Path
from hitoshura25_mcp_android_playstore_deploy.generator import (
    analyze_android_project,
    generate_keystore,
    generate_signing_config,
    setup_service_account_guide,
    generate_github_workflow,
    create_github_secrets_guide,
)


def test_setup_service_account_guide():
    """Test that setup_service_account_guide returns proper structure"""
    result = setup_service_account_guide()

    assert result["success"] is True
    assert "steps" in result
    assert len(result["steps"]) == 7
    assert "validation_checklist" in result
    assert "troubleshooting" in result


def test_generate_signing_config():
    """Test that generate_signing_config generates proper Gradle config"""
    result = generate_signing_config(
        project_path="/fake/path", signing_strategy="environment_variables"
    )

    assert result["success"] is True
    assert "gradle_config_kotlin" in result
    assert "gradle_config_groovy" in result
    assert "signingConfigs" in result["gradle_config_kotlin"]
    assert "SIGNING_KEY_STORE_PATH" in result["gradle_config_kotlin"]


def test_create_github_secrets_guide():
    """Test that create_github_secrets_guide generates proper guide"""
    result = create_github_secrets_guide(repo_url="https://github.com/owner/repo")

    assert result["success"] is True
    assert "secrets" in result
    assert len(result["secrets"]) == 5
    assert (
        result["github_secrets_url"]
        == "https://github.com/owner/repo/settings/secrets/actions"
    )


def test_generate_github_workflow_defaults():
    """Test that generate_github_workflow uses proper defaults"""
    result = generate_github_workflow(
        project_path="/fake/path", package_name="com.example.app"
    )

    assert result["success"] is True
    assert "workflow_content" in result
    assert "internal" in result["workflow_path"]
    assert "workflow_dispatch" in result["workflow_content"]
    assert "com.example.app" in result["workflow_content"]


def test_generate_github_workflow_with_track():
    """Test that generate_github_workflow respects track parameter"""
    result = generate_github_workflow(
        project_path="/fake/path", package_name="com.example.app", track="beta"
    )

    assert result["success"] is True
    assert "beta" in result["workflow_path"]
    assert "Deploy to Play Store beta" in result["workflow_content"]


def test_analyze_android_project_nonexistent():
    """Test analyze_android_project with nonexistent path"""
    result = analyze_android_project(project_path="/nonexistent/path")

    assert result["success"] is False
    assert "error" in result


def test_analyze_android_project_test_fixture():
    """Test analyze_android_project with test fixture"""
    test_project = Path(__file__).parent / "fixtures" / "test-android-app"

    if not test_project.exists():
        pytest.skip("Test Android project not found")

    result = analyze_android_project(project_path=str(test_project))

    assert result["success"] is True
    assert result["package_name"] == "com.test.playstore"
    assert result["project_type"] == "native_android"
    assert result["build_system"] == "gradle"
    assert "recommendations" in result


def test_generate_keystore_invalid_path():
    """Test generate_keystore with parent directory that doesn't exist"""
    # This should create the parent directory
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "subdir", "test.jks")

        result = generate_keystore(
            output_path=output_path,
            alias="testkey",
            key_password="testpass123",
            store_password="storepass123",
        )

        # Should succeed and create the directory
        assert result["success"] is True
        assert "keystore_path" in result
        assert os.path.exists(output_path)


def test_generate_keystore_already_exists():
    """Test generate_keystore when file already exists"""
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test.jks")

        # Create first keystore
        result1 = generate_keystore(
            output_path=output_path,
            alias="testkey",
            key_password="testpass123",
            store_password="storepass123",
        )
        assert result1["success"] is True

        # Try to create again - should fail
        result2 = generate_keystore(
            output_path=output_path,
            alias="testkey",
            key_password="testpass123",
            store_password="storepass123",
        )
        assert result2["success"] is False
        assert "already exists" in result2["error"]

"""
Tests for MCP server implementation.
"""

import pytest
from hitoshura25_mcp_android_playstore_deploy.server import mcp

from hitoshura25_mcp_android_playstore_deploy.server import analyze_android_project

from hitoshura25_mcp_android_playstore_deploy.server import generate_keystore

from hitoshura25_mcp_android_playstore_deploy.server import generate_signing_config

from hitoshura25_mcp_android_playstore_deploy.server import setup_service_account_guide

from hitoshura25_mcp_android_playstore_deploy.server import generate_github_workflow

from hitoshura25_mcp_android_playstore_deploy.server import validate_github_secrets

from hitoshura25_mcp_android_playstore_deploy.server import create_github_secrets_guide

from hitoshura25_mcp_android_playstore_deploy.server import validate_play_store_setup

from hitoshura25_mcp_android_playstore_deploy.server import test_deployment_workflow


@pytest.mark.asyncio
async def test_server_initialization():
    """Test that the MCP server initializes correctly."""
    assert mcp.name == "hitoshura25_mcp_android_playstore_deploy"

    # Check that tools are registered
    tools = await mcp.list_tools()
    assert len(tools) == 9

    tool_names = [tool.name for tool in tools]

    assert "analyze_android_project" in tool_names

    assert "generate_keystore" in tool_names

    assert "generate_signing_config" in tool_names

    assert "setup_service_account_guide" in tool_names

    assert "generate_github_workflow" in tool_names

    assert "validate_github_secrets" in tool_names

    assert "create_github_secrets_guide" in tool_names

    assert "validate_play_store_setup" in tool_names

    assert "test_deployment_workflow" in tool_names


def test_analyze_android_project_function():
    """Test analyze_android_project tool function."""
    # Test the function directly
    result = analyze_android_project(project_path="test_value")

    # Result should be a string (FastMCP tools return strings)
    assert isinstance(result, str)
    assert len(result) > 0


def test_generate_keystore_function():
    """Test generate_keystore tool function."""
    # Test the function directly
    result = generate_keystore(
        output_path="test_value",
        alias="test_value",
        key_password="test_value",
        store_password="test_value",
        validity_days=42,
        key_size=42,
        dname="test_value",
    )

    # Result should be a string (FastMCP tools return strings)
    assert isinstance(result, str)
    assert len(result) > 0


def test_generate_signing_config_function():
    """Test generate_signing_config tool function."""
    # Test the function directly
    result = generate_signing_config(
        project_path="test_value", signing_strategy="test_value"
    )

    # Result should be a string (FastMCP tools return strings)
    assert isinstance(result, str)
    assert len(result) > 0


def test_setup_service_account_guide_function():
    """Test setup_service_account_guide tool function."""
    # Test the function directly
    result = setup_service_account_guide()

    # Result should be a string (FastMCP tools return strings)
    assert isinstance(result, str)
    assert len(result) > 0


def test_generate_github_workflow_function():
    """Test generate_github_workflow tool function."""
    # Test the function directly
    result = generate_github_workflow(
        project_path="test_value",
        package_name="test_value",
        track="test_value",
        trigger_strategy="test_value",
        branch_name="test_value",
        app_module_path="test_value",
        java_version="test_value",
    )

    # Result should be a string (FastMCP tools return strings)
    assert isinstance(result, str)
    assert len(result) > 0


def test_validate_github_secrets_function():
    """Test validate_github_secrets tool function."""
    # Test the function directly
    result = validate_github_secrets(
        repo_owner="test_value",
        repo_name="test_value",
        github_token="test_value",
        required_secrets="test",
    )

    # Result should be a string (FastMCP tools return strings)
    assert isinstance(result, str)
    assert len(result) > 0


def test_create_github_secrets_guide_function():
    """Test create_github_secrets_guide tool function."""
    # Test the function directly
    result = create_github_secrets_guide(
        repo_url="test_value", keystore_path="test_value"
    )

    # Result should be a string (FastMCP tools return strings)
    assert isinstance(result, str)
    assert len(result) > 0


def test_validate_play_store_setup_function():
    """Test validate_play_store_setup tool function."""
    # Test the function directly
    result = validate_play_store_setup(
        service_account_json_path="test_value", package_name="test_value"
    )

    # Result should be a string (FastMCP tools return strings)
    assert isinstance(result, str)
    assert len(result) > 0


def test_test_deployment_workflow_function():
    """Test test_deployment_workflow tool function."""
    # Test the function directly
    result = test_deployment_workflow(
        project_path="test_value",
        keystore_path="test_value",
        store_password="test_value",
        key_alias="test_value",
        key_password="test_value",
        dry_run=True,
    )

    # Result should be a string (FastMCP tools return strings)
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_all_tools_have_descriptions():
    """Test that all tools have proper descriptions."""
    tools = await mcp.list_tools()

    for tool in tools:
        assert hasattr(tool, "description")
        assert tool.description
        assert len(tool.description) > 0


@pytest.mark.asyncio
async def test_tool_schemas():
    """Test that all tools have proper input schemas."""
    tools = await mcp.list_tools()

    for tool in tools:
        assert hasattr(tool, "inputSchema")
        schema = tool.inputSchema

        # Check schema structure
        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema

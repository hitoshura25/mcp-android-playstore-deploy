"""
Tests for MCP server implementation.
"""

import pytest
from hitoshura25_mcp_android_playstore_deploy.server import mcp


@pytest.mark.asyncio
async def test_server_initialization():
    """Test that the MCP server initializes correctly."""
    assert mcp.name == "hitoshura25_mcp_android_playstore_deploy"

    # Check that tools are registered
    tools = await mcp.list_tools()
    assert len(tools) == 10

    tool_names = [tool.name for tool in tools]

    assert "analyze_android_project" in tool_names
    assert "generate_keystore" in tool_names
    assert "generate_signing_config" in tool_names
    assert "setup_local_development" in tool_names
    assert "setup_service_account_guide" in tool_names
    assert "generate_github_workflow" in tool_names
    assert "validate_github_secrets" in tool_names
    assert "create_github_secrets_guide" in tool_names
    assert "validate_play_store_setup" in tool_names
    assert "test_deployment_workflow" in tool_names

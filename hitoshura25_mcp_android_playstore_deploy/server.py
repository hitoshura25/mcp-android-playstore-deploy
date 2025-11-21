#!/usr/bin/env python3
"""
MCP Server for hitoshura25-mcp-android-playstore-deploy.

MCP server that helps developers set up automated Google Play Store deployment for Android apps
"""

import inspect
from mcp.server.fastmcp import FastMCP

from . import generator

# Initialize FastMCP server
mcp = FastMCP("hitoshura25_mcp_android_playstore_deploy")



@mcp.tool()
async def analyze_android_project(
    
    project_path: str
    
) -> str:
    """Analyze an Android project to understand its configuration and identify requirements for Play Store deployment


    Args:
        
        project_path: Absolute path to the Android project root directory
        


    Returns:
        Result from analyze_android_project
    """
    result = generator.analyze_android_project(
        
        project_path=project_path
        
    )
    # Handle both sync and async business logic
    if inspect.isawaitable(result):
        result = await result
    return str(result)


@mcp.tool()
async def generate_keystore(
    
    output_path: str,
    
    alias: str,
    
    key_password: str,
    
    store_password: str,
    
    validity_days: int = None,
    
    key_size: int = None,
    
    dname: str = None
    
) -> str:
    """Generate a new Android keystore file for app signing with secure parameters


    Args:
        
        output_path: Absolute path where the keystore will be saved
        
        alias: Key alias for the signing key
        
        key_password: Password for the signing key
        
        store_password: Password for the keystore
        
        validity_days: How many days the key should be valid
        
        key_size: Key size in bits
        
        dname: Distinguished name for the certificate
        


    Returns:
        Result from generate_keystore
    """
    result = generator.generate_keystore(
        
        output_path=output_path,
        
        alias=alias,
        
        key_password=key_password,
        
        store_password=store_password,
        
        validity_days=validity_days,
        
        key_size=key_size,
        
        dname=dname
        
    )
    # Handle both sync and async business logic
    if inspect.isawaitable(result):
        result = await result
    return str(result)


@mcp.tool()
async def generate_signing_config(
    
    project_path: str,
    
    signing_strategy: str = None
    
) -> str:
    """Generate Gradle signing configuration code to add to build.gradle.kts


    Args:
        
        project_path: Path to Android project
        
        signing_strategy: How to provide signing credentials (environment_variables or gradle_properties)
        


    Returns:
        Result from generate_signing_config
    """
    result = generator.generate_signing_config(
        
        project_path=project_path,
        
        signing_strategy=signing_strategy
        
    )
    # Handle both sync and async business logic
    if inspect.isawaitable(result):
        result = await result
    return str(result)


@mcp.tool()
async def setup_service_account_guide() -> str:
    """Provide interactive step-by-step guide for setting up Google Play Service Account


    Returns:
        Result from setup_service_account_guide
    """
    result = generator.setup_service_account_guide(
        
    )
    # Handle both sync and async business logic
    if inspect.isawaitable(result):
        result = await result
    return str(result)


@mcp.tool()
async def generate_github_workflow(
    
    project_path: str,
    
    package_name: str,
    
    track: str = None,
    
    trigger_strategy: str = None,
    
    branch_name: str = None,
    
    app_module_path: str = None,
    
    java_version: str = None
    
) -> str:
    """Generate a complete GitHub Actions workflow file for Play Store deployment


    Args:
        
        project_path: Path to Android project
        
        package_name: Android app package name
        
        track: Play Store release track (internal, alpha, beta, production)
        
        trigger_strategy: How to trigger the workflow (manual, branch, tag)
        
        branch_name: Branch name to trigger on if trigger_strategy is branch
        
        app_module_path: Path to app module relative to project root
        
        java_version: Java/JDK version to use for builds
        


    Returns:
        Result from generate_github_workflow
    """
    result = generator.generate_github_workflow(
        
        project_path=project_path,
        
        package_name=package_name,
        
        track=track,
        
        trigger_strategy=trigger_strategy,
        
        branch_name=branch_name,
        
        app_module_path=app_module_path,
        
        java_version=java_version
        
    )
    # Handle both sync and async business logic
    if inspect.isawaitable(result):
        result = await result
    return str(result)


@mcp.tool()
async def validate_github_secrets(
    
    repo_owner: str,
    
    repo_name: str,
    
    github_token: str,
    
    required_secrets: str = None
    
) -> str:
    """Validate that required GitHub Secrets are configured (checks existence only)


    Args:
        
        repo_owner: GitHub repository owner username or organization
        
        repo_name: GitHub repository name
        
        github_token: GitHub Personal Access Token with repo scope
        
        required_secrets: List of secret names to check for
        


    Returns:
        Result from validate_github_secrets
    """
    result = generator.validate_github_secrets(
        
        repo_owner=repo_owner,
        
        repo_name=repo_name,
        
        github_token=github_token,
        
        required_secrets=required_secrets
        
    )
    # Handle both sync and async business logic
    if inspect.isawaitable(result):
        result = await result
    return str(result)


@mcp.tool()
async def create_github_secrets_guide(
    
    repo_url: str,
    
    keystore_path: str = None
    
) -> str:
    """Generate a comprehensive guide for creating all required GitHub Secrets


    Args:
        
        repo_url: GitHub repository URL
        
        keystore_path: Optional path to keystore for encoding instructions
        


    Returns:
        Result from create_github_secrets_guide
    """
    result = generator.create_github_secrets_guide(
        
        repo_url=repo_url,
        
        keystore_path=keystore_path
        
    )
    # Handle both sync and async business logic
    if inspect.isawaitable(result):
        result = await result
    return str(result)


@mcp.tool()
async def validate_play_store_setup(
    
    service_account_json_path: str,
    
    package_name: str
    
) -> str:
    """Validate that Play Store app and API access are properly configured using service account


    Args:
        
        service_account_json_path: Path to service account JSON file
        
        package_name: Android app package name to validate
        


    Returns:
        Result from validate_play_store_setup
    """
    result = generator.validate_play_store_setup(
        
        service_account_json_path=service_account_json_path,
        
        package_name=package_name
        
    )
    # Handle both sync and async business logic
    if inspect.isawaitable(result):
        result = await result
    return str(result)


@mcp.tool()
async def test_deployment_workflow(
    
    project_path: str,
    
    keystore_path: str,
    
    store_password: str,
    
    key_alias: str,
    
    key_password: str,
    
    dry_run: bool = None
    
) -> str:
    """Test the deployment workflow locally without uploading to Play Store


    Args:
        
        project_path: Path to Android project
        
        keystore_path: Path to keystore file
        
        store_password: Keystore password
        
        key_alias: Key alias
        
        key_password: Key password
        
        dry_run: If true, skip actual Play Store upload
        


    Returns:
        Result from test_deployment_workflow
    """
    result = generator.test_deployment_workflow(
        
        project_path=project_path,
        
        keystore_path=keystore_path,
        
        store_password=store_password,
        
        key_alias=key_alias,
        
        key_password=key_password,
        
        dry_run=dry_run
        
    )
    # Handle both sync and async business logic
    if inspect.isawaitable(result):
        result = await result
    return str(result)



def main():
    """Main entry point for MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
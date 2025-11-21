"""
hitoshura25-mcp-android-playstore-deploy

MCP server that helps developers set up automated Google Play Store deployment for Android apps
"""

__version__ = "0.1.0"
__author__ = "Vinayak Menon"
__license__ = "Apache-2.0"

from .generator import (
    
    analyze_android_project,
    
    generate_keystore,
    
    generate_signing_config,
    
    setup_service_account_guide,
    
    generate_github_workflow,
    
    validate_github_secrets,
    
    create_github_secrets_guide,
    
    validate_play_store_setup,
    
    test_deployment_workflow,
    
)

__all__ = [
    
    'analyze_android_project',
    
    'generate_keystore',
    
    'generate_signing_config',
    
    'setup_service_account_guide',
    
    'generate_github_workflow',
    
    'validate_github_secrets',
    
    'create_github_secrets_guide',
    
    'validate_play_store_setup',
    
    'test_deployment_workflow',
    
]
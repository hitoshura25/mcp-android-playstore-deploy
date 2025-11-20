"""Tools for MCP Android Play Store Deploy server."""

from mcp.server import Server
from mcp.types import Tool, TextContent

from .analyze_project import analyze_android_project
from .keystore import generate_keystore
from .signing_config import generate_signing_config
from .service_account import setup_service_account_guide
from .github_workflow import generate_github_workflow
from .github_secrets import validate_github_secrets, create_github_secrets_guide
from .playstore_validation import validate_play_store_setup
from .deployment_test import test_deployment_workflow


def register_tools(server: Server):
    """Register all MCP tools with the server."""

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List all available tools."""
        return [
            Tool(
                name="analyze_android_project",
                description="Analyze an Android project to understand its configuration and identify requirements for Play Store deployment",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "Absolute path to the Android project root directory"
                        }
                    },
                    "required": ["project_path"]
                }
            ),
            Tool(
                name="generate_keystore",
                description="Generate a new Android keystore file for app signing with secure parameters",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "output_path": {
                            "type": "string",
                            "description": "Absolute path where the keystore will be saved"
                        },
                        "alias": {
                            "type": "string",
                            "description": "Key alias for the signing key"
                        },
                        "key_password": {
                            "type": "string",
                            "description": "Password for the signing key"
                        },
                        "store_password": {
                            "type": "string",
                            "description": "Password for the keystore"
                        },
                        "validity_days": {
                            "type": "number",
                            "description": "How many days the key should be valid",
                            "default": 10000
                        },
                        "key_size": {
                            "type": "number",
                            "description": "Key size in bits",
                            "default": 2048
                        },
                        "dname": {
                            "type": "string",
                            "description": "Distinguished name for the certificate",
                            "default": "CN=Android Developer"
                        }
                    },
                    "required": ["output_path", "alias", "key_password", "store_password"]
                }
            ),
            Tool(
                name="generate_signing_config",
                description="Generate Gradle signing configuration code to add to build.gradle.kts",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "Path to Android project"
                        },
                        "signing_strategy": {
                            "type": "string",
                            "description": "How to provide signing credentials (environment_variables or gradle_properties)",
                            "enum": ["environment_variables", "gradle_properties"],
                            "default": "environment_variables"
                        }
                    },
                    "required": ["project_path"]
                }
            ),
            Tool(
                name="setup_service_account_guide",
                description="Provide interactive step-by-step guide for setting up Google Play Service Account",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="generate_github_workflow",
                description="Generate a complete GitHub Actions workflow file for Play Store deployment",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "Path to Android project"
                        },
                        "package_name": {
                            "type": "string",
                            "description": "Android app package name"
                        },
                        "track": {
                            "type": "string",
                            "description": "Play Store release track",
                            "enum": ["internal", "alpha", "beta", "production"],
                            "default": "internal"
                        },
                        "trigger_strategy": {
                            "type": "string",
                            "description": "How to trigger the workflow",
                            "enum": ["manual", "branch", "tag"],
                            "default": "manual"
                        },
                        "branch_name": {
                            "type": "string",
                            "description": "Branch name to trigger on if trigger_strategy is branch",
                            "default": "release/internal"
                        },
                        "app_module_path": {
                            "type": "string",
                            "description": "Path to app module relative to project root",
                            "default": "app"
                        },
                        "java_version": {
                            "type": "string",
                            "description": "Java/JDK version to use for builds",
                            "default": "17"
                        }
                    },
                    "required": ["project_path", "package_name"]
                }
            ),
            Tool(
                name="validate_github_secrets",
                description="Validate that required GitHub Secrets are configured (checks existence only)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repo_owner": {
                            "type": "string",
                            "description": "GitHub repository owner username or organization"
                        },
                        "repo_name": {
                            "type": "string",
                            "description": "GitHub repository name"
                        },
                        "github_token": {
                            "type": "string",
                            "description": "GitHub Personal Access Token with repo scope"
                        },
                        "required_secrets": {
                            "type": "array",
                            "description": "List of secret names to check for",
                            "items": {"type": "string"},
                            "default": [
                                "SERVICE_ACCOUNT_JSON_PLAINTEXT",
                                "SIGNING_KEY_STORE_BASE64",
                                "SIGNING_KEY_ALIAS",
                                "SIGNING_KEY_PASSWORD",
                                "SIGNING_STORE_PASSWORD"
                            ]
                        }
                    },
                    "required": ["repo_owner", "repo_name", "github_token"]
                }
            ),
            Tool(
                name="create_github_secrets_guide",
                description="Generate a comprehensive guide for creating all required GitHub Secrets",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repo_url": {
                            "type": "string",
                            "description": "GitHub repository URL"
                        },
                        "keystore_path": {
                            "type": "string",
                            "description": "Optional path to keystore for encoding instructions"
                        }
                    },
                    "required": ["repo_url"]
                }
            ),
            Tool(
                name="validate_play_store_setup",
                description="Validate that Play Store app and API access are properly configured using service account",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "service_account_json_path": {
                            "type": "string",
                            "description": "Path to service account JSON file"
                        },
                        "package_name": {
                            "type": "string",
                            "description": "Android app package name to validate"
                        }
                    },
                    "required": ["service_account_json_path", "package_name"]
                }
            ),
            Tool(
                name="test_deployment_workflow",
                description="Test the deployment workflow locally without uploading to Play Store",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "Path to Android project"
                        },
                        "keystore_path": {
                            "type": "string",
                            "description": "Path to keystore file"
                        },
                        "store_password": {
                            "type": "string",
                            "description": "Keystore password"
                        },
                        "key_alias": {
                            "type": "string",
                            "description": "Key alias"
                        },
                        "key_password": {
                            "type": "string",
                            "description": "Key password"
                        },
                        "dry_run": {
                            "type": "boolean",
                            "description": "If true, skip actual Play Store upload",
                            "default": True
                        }
                    },
                    "required": ["project_path", "keystore_path", "store_password", "key_alias", "key_password"]
                }
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Handle tool calls."""
        import json

        try:
            if name == "analyze_android_project":
                result = analyze_android_project(arguments["project_path"])
            elif name == "generate_keystore":
                result = generate_keystore(
                    output_path=arguments["output_path"],
                    alias=arguments["alias"],
                    key_password=arguments["key_password"],
                    store_password=arguments["store_password"],
                    validity_days=arguments.get("validity_days", 10000),
                    key_size=arguments.get("key_size", 2048),
                    dname=arguments.get("dname", "CN=Android Developer")
                )
            elif name == "generate_signing_config":
                result = generate_signing_config(
                    project_path=arguments["project_path"],
                    signing_strategy=arguments.get("signing_strategy", "environment_variables")
                )
            elif name == "setup_service_account_guide":
                result = setup_service_account_guide()
            elif name == "generate_github_workflow":
                result = generate_github_workflow(
                    project_path=arguments["project_path"],
                    package_name=arguments["package_name"],
                    track=arguments.get("track", "internal"),
                    trigger_strategy=arguments.get("trigger_strategy", "manual"),
                    branch_name=arguments.get("branch_name", "release/internal"),
                    app_module_path=arguments.get("app_module_path", "app"),
                    java_version=arguments.get("java_version", "17")
                )
            elif name == "validate_github_secrets":
                result = validate_github_secrets(
                    repo_owner=arguments["repo_owner"],
                    repo_name=arguments["repo_name"],
                    github_token=arguments["github_token"],
                    required_secrets=arguments.get("required_secrets", [
                        "SERVICE_ACCOUNT_JSON_PLAINTEXT",
                        "SIGNING_KEY_STORE_BASE64",
                        "SIGNING_KEY_ALIAS",
                        "SIGNING_KEY_PASSWORD",
                        "SIGNING_STORE_PASSWORD"
                    ])
                )
            elif name == "create_github_secrets_guide":
                result = create_github_secrets_guide(
                    repo_url=arguments["repo_url"],
                    keystore_path=arguments.get("keystore_path")
                )
            elif name == "validate_play_store_setup":
                result = validate_play_store_setup(
                    service_account_json_path=arguments["service_account_json_path"],
                    package_name=arguments["package_name"]
                )
            elif name == "test_deployment_workflow":
                result = test_deployment_workflow(
                    project_path=arguments["project_path"],
                    keystore_path=arguments["keystore_path"],
                    store_password=arguments["store_password"],
                    key_alias=arguments["key_alias"],
                    key_password=arguments["key_password"],
                    dry_run=arguments.get("dry_run", True)
                )
            else:
                result = {"success": False, "error": f"Unknown tool: {name}"}

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            error_result = {
                "success": False,
                "error": {
                    "type": type(e).__name__,
                    "message": str(e)
                }
            }
            return [TextContent(type="text", text=json.dumps(error_result, indent=2))]

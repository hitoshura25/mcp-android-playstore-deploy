# MCP Android Play Store Deploy

[![PyPI version](https://badge.fury.io/py/mcp-android-playstore-deploy.svg)](https://badge.fury.io/py/mcp-android-playstore-deploy)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

An MCP (Model Context Protocol) server that helps developers automate Google Play Store deployment for Android applications. This tool provides AI agents like Claude Code with capabilities to guide developers through the complex process of setting up automated Play Store deployments.

## Features

- **Analyze Android Projects**: Detect project type, configuration, and deployment readiness
- **Generate Keystores**: Create Android signing keystores with secure parameters
- **Configure Signing**: Generate Gradle signing configurations
- **Service Account Setup**: Interactive guide for Google Play Service Account creation
- **GitHub Actions Workflows**: Generate complete CI/CD workflows for Play Store deployment
- **Secrets Management**: Validate and guide GitHub Secrets setup
- **Play Store Validation**: Verify API access and app configuration
- **Local Testing**: Test deployment workflow without uploading

## Installation

```bash
pip install mcp-android-playstore-deploy
```

## Quick Start

### Using with Claude Desktop

Add to your Claude Desktop MCP configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS or `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "android-playstore-deploy": {
      "command": "python",
      "args": ["-m", "mcp_android_playstore_deploy"],
      "description": "Helps set up automated Google Play Store deployment for Android apps"
    }
  }
}
```

Restart Claude Desktop to load the new MCP server.

### Using with Other MCP Clients

The server can be started with:

```bash
python -m mcp_android_playstore_deploy
```

## Available Tools

### 1. analyze_android_project

Analyzes an Android project to understand its configuration and identify requirements for Play Store deployment.

**Parameters:**
- `project_path` (string, required): Absolute path to the Android project root directory

**Returns:** Project type, build system, package name, version info, signing status, recommendations, and issues.

### 2. generate_keystore

Generates a new Android keystore file for app signing with secure parameters.

**Parameters:**
- `output_path` (string, required): Where to save the keystore
- `alias` (string, required): Key alias
- `key_password` (string, required): Key password
- `store_password` (string, required): Keystore password
- `validity_days` (number, optional): Validity period (default: 10000)
- `key_size` (number, optional): Key size in bits (default: 2048)
- `dname` (string, optional): Distinguished name (default: "CN=Android Developer")

**Returns:** Keystore path, base64-encoded keystore, GitHub secret instructions, and security warnings.

### 3. generate_signing_config

Generates Gradle signing configuration code to add to build.gradle.kts.

**Parameters:**
- `project_path` (string, required): Path to Android project
- `signing_strategy` (string, optional): "environment_variables" or "gradle_properties" (default: "environment_variables")

**Returns:** Kotlin DSL, Groovy DSL, build types config, instructions, and complete example.

### 4. setup_service_account_guide

Provides interactive step-by-step guide for setting up Google Play Service Account.

**Parameters:** None

**Returns:** 7-step guide with URLs, verification steps, troubleshooting tips, and validation checklist.

### 5. generate_github_workflow

Generates a complete GitHub Actions workflow file for Play Store deployment.

**Parameters:**
- `project_path` (string, required): Path to Android project
- `package_name` (string, required): Android app package name
- `track` (string, optional): Release track - "internal", "alpha", "beta", or "production" (default: "internal")
- `trigger_strategy` (string, optional): "manual", "branch", or "tag" (default: "manual")
- `branch_name` (string, optional): Branch to trigger on (default: "release/internal")
- `app_module_path` (string, optional): Path to app module (default: "app")
- `java_version` (string, optional): JDK version (default: "17")

**Returns:** Workflow YAML content, path, required secrets, and instructions.

### 6. validate_github_secrets

Validates that required GitHub Secrets are configured (checks existence only).

**Parameters:**
- `repo_owner` (string, required): GitHub repository owner
- `repo_name` (string, required): GitHub repository name
- `github_token` (string, required): GitHub Personal Access Token with repo scope
- `required_secrets` (array, optional): List of secret names to check

**Returns:** Validation status, missing/configured secrets, and setup instructions.

### 7. create_github_secrets_guide

Generates a comprehensive guide for creating all required GitHub Secrets.

**Parameters:**
- `repo_url` (string, required): GitHub repository URL
- `keystore_path` (string, optional): Path to keystore for encoding instructions

**Returns:** Step-by-step instructions, secret details, and security reminders.

### 8. validate_play_store_setup

Validates that Play Store app and API access are properly configured.

**Parameters:**
- `service_account_json_path` (string, required): Path to service account JSON file
- `package_name` (string, required): Android app package name

**Returns:** Validation checks, errors, warnings, and next steps.

### 9. test_deployment_workflow

Tests the deployment workflow locally without uploading to Play Store.

**Parameters:**
- `project_path` (string, required): Path to Android project
- `keystore_path` (string, required): Path to keystore file
- `store_password` (string, required): Keystore password
- `key_alias` (string, required): Key alias
- `key_password` (string, required): Key password
- `dry_run` (boolean, optional): Skip actual upload (default: true)

**Returns:** Build status, AAB path and size, errors, warnings, and readiness for deployment.

## Example Usage with Claude Code

```
User: Help me set up automated Play Store deployment for my Android app

Claude: I'll help you set up automated Play Store deployment. Let me start by analyzing your project.

[Uses analyze_android_project tool]

Claude: I've analyzed your project. I found:
- Package name: com.example.app
- No signing configuration
- Minification is disabled

Let me help you:
1. Generate a signing keystore
2. Add signing configuration
3. Create a GitHub Actions workflow
4. Set up Google Play Service Account

[Continues with guided setup using the various tools]
```

## Security

This tool follows security best practices:

- **Never logs credentials**: Passwords and keys are never written to logs
- **Environment variables**: Credentials are passed via environment variables in CI/CD
- **Secure file permissions**: Generated keystores have restrictive permissions (600)
- **No hardcoded secrets**: All secrets are externalized
- **Sanitized error messages**: API errors don't expose sensitive information

## Development

### Setup

```bash
git clone https://github.com/hitoshura25/mcp-android-playstore-deploy.git
cd mcp-android-playstore-deploy
pip install -e ".[dev]"
```

### Running Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# With coverage
pytest --cov --cov-report=html
```

### Code Quality

```bash
# Format code
black src/

# Lint
ruff check src/

# Type checking
mypy src/
```

## Project Structure

```
mcp-android-playstore-deploy/
├── src/
│   └── mcp_android_playstore_deploy/
│       ├── __init__.py
│       ├── __main__.py
│       ├── exceptions.py
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── analyze_project.py
│       │   ├── keystore.py
│       │   ├── signing_config.py
│       │   ├── service_account.py
│       │   ├── github_workflow.py
│       │   ├── github_secrets.py
│       │   ├── playstore_validation.py
│       │   ├── deployment_test.py
│       │   └── utils.py
│       └── templates/
│           └── github_workflow.yml.j2
├── tests/
│   ├── fixtures/
│   │   └── test-android-app/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── pyproject.toml
└── README.md
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/hitoshura25/mcp-android-playstore-deploy/issues)
- **Documentation**: See the [spec](specs/mcp-playstore-deploy-implementation.md) for detailed implementation information

## Acknowledgments

Built with:
- [MCP SDK](https://github.com/anthropics/model-context-protocol) - Model Context Protocol implementation
- [Google Play Developer API](https://developers.google.com/android-publisher) - For Play Store integration
- [Jinja2](https://jinja.palletsprojects.com/) - Template engine for workflow generation

## Roadmap

- [ ] Add support for App Bundle Explorer integration
- [ ] Implement automatic version bumping
- [ ] Add release notes generation
- [ ] Support for multiple flavors and build variants
- [ ] Integration with Fastlane
- [ ] Support for staged rollouts

---

Made with ❤️ for the Android development community

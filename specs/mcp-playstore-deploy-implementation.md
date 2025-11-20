# MCP Android Play Store Deploy - Implementation Specification

## Executive Summary

This specification outlines the step-by-step implementation plan for creating a reusable MCP (Model Context Protocol) server that helps developers automate Google Play Store deployment for Android applications. The implementation will use the `mcp-server-generator` tool to scaffold the project, followed by publishing to PyPI, and finally using the MCP server to set up Play Store publishing for the Health Sync App.

## Project Overview

**Project Name**: `mcp-android-playstore-deploy`

**Purpose**: Provide AI agents (like Claude Code) with tools to guide developers through the complex process of setting up automated Google Play Store deployment.

**Implementation Strategy**: 3-phase approach
1. Phase 1: Generate and implement MCP server
2. Phase 2: Publish to PyPI
3. Phase 3: Use the MCP server to set up Health Sync App deployment

---

## Phase 1: MCP Server Generation and Implementation

### 1.1 Tool Specifications

The MCP server will provide 9 tools to help developers set up Play Store automation. Below are the detailed specifications for each tool.

#### Tool 1: `analyze_android_project`

**Purpose**: Analyze an Android project to understand its current configuration and identify what's needed for Play Store deployment.

**Parameters**:
```json
{
  "name": "project_path",
  "type": "string",
  "description": "Absolute path to the Android project root directory",
  "required": true
}
```

**Returns**:
```json
{
  "project_type": "native_android|react_native|flutter|unknown",
  "build_system": "gradle|maven|unknown",
  "package_name": "com.example.app",
  "namespace": "com.example.app",
  "has_signing_config": false,
  "has_github_actions": false,
  "github_workflows": [],
  "current_version_code": 1,
  "current_version_name": "1.0",
  "gradle_jdk_version": "11",
  "target_sdk": 34,
  "min_sdk": 21,
  "build_gradle_path": "/path/to/app/build.gradle.kts",
  "is_minify_enabled": false,
  "dependencies": {
    "compose": true,
    "hilt": true,
    "room": true
  },
  "recommendations": [
    "Enable code minification for release builds",
    "Add signing configuration",
    "Create GitHub Actions workflow"
  ],
  "issues": [
    {
      "severity": "critical|high|medium|low",
      "message": "Description of issue",
      "fix": "Suggested fix"
    }
  ]
}
```

**Implementation Logic**:
1. Verify project_path exists and is a directory
2. Look for `build.gradle`, `build.gradle.kts`, `settings.gradle`, `settings.gradle.kts`
3. Parse build files to extract configuration
4. Check for `.github/workflows/` directory
5. Detect project type from structure and dependencies
6. Analyze signing configuration
7. Generate recommendations based on findings

---

#### Tool 2: `generate_keystore`

**Purpose**: Generate a new Android keystore file for app signing.

**Parameters**:
```json
{
  "output_path": {
    "type": "string",
    "description": "Absolute path where the keystore will be saved",
    "required": true
  },
  "alias": {
    "type": "string",
    "description": "Key alias for the signing key",
    "required": true
  },
  "key_password": {
    "type": "string",
    "description": "Password for the signing key",
    "required": true
  },
  "store_password": {
    "type": "string",
    "description": "Password for the keystore",
    "required": true
  },
  "validity_days": {
    "type": "number",
    "description": "How many days the key should be valid",
    "required": false,
    "default": 10000
  },
  "key_size": {
    "type": "number",
    "description": "Key size in bits",
    "required": false,
    "default": 2048
  },
  "dname": {
    "type": "string",
    "description": "Distinguished name (CN, OU, O, L, ST, C)",
    "required": false,
    "default": "CN=Android Developer"
  }
}
```

**Returns**:
```json
{
  "success": true,
  "keystore_path": "/path/to/keystore.jks",
  "alias": "my-key-alias",
  "base64_encoded": "base64_string_of_keystore",
  "instructions": [
    "Save the keystore file securely",
    "Back up the keystore to multiple locations",
    "Never commit the keystore to version control",
    "Store passwords in a secure password manager"
  ],
  "github_secret_instructions": {
    "SIGNING_KEY_STORE_BASE64": "Use the base64_encoded value above",
    "SIGNING_KEY_ALIAS": "my-key-alias",
    "SIGNING_KEY_PASSWORD": "Use the key_password you provided",
    "SIGNING_STORE_PASSWORD": "Use the store_password you provided"
  },
  "warning": "CRITICAL: Loss of this keystore will prevent you from updating your app on Google Play. Back it up securely."
}
```

**Implementation Logic**:
1. Validate parameters (passwords, paths)
2. Check if keytool is available (from JDK)
3. Generate keystore using keytool command
4. Read keystore file and encode to base64
5. Return structured response with instructions

**System Dependencies**: `keytool` (from JDK)

---

#### Tool 3: `generate_signing_config`

**Purpose**: Generate Gradle signing configuration code to add to `build.gradle.kts`.

**Parameters**:
```json
{
  "project_path": {
    "type": "string",
    "description": "Path to Android project",
    "required": true
  },
  "signing_strategy": {
    "type": "string",
    "description": "How to provide signing credentials",
    "required": false,
    "default": "environment_variables",
    "enum": ["environment_variables", "gradle_properties"]
  }
}
```

**Returns**:
```json
{
  "success": true,
  "gradle_config_kotlin": "kotlin DSL code snippet",
  "gradle_config_groovy": "groovy DSL code snippet",
  "insert_location": "Inside android { ... } block, before buildTypes",
  "instructions": [
    "Add the signingConfigs block to your app/build.gradle.kts",
    "Update your release buildType to use the signing config",
    "Set environment variables in your CI/CD pipeline"
  ],
  "required_env_vars": [
    "SIGNING_KEY_STORE_PATH",
    "SIGNING_STORE_PASSWORD",
    "SIGNING_KEY_ALIAS",
    "SIGNING_KEY_PASSWORD"
  ],
  "complete_example": "Full example of build.gradle.kts with signing config"
}
```

**Generated Kotlin DSL**:
```kotlin
signingConfigs {
    create("release") {
        storeFile = file(System.getenv("SIGNING_KEY_STORE_PATH") ?: "release.jks")
        storePassword = System.getenv("SIGNING_STORE_PASSWORD")
        keyAlias = System.getenv("SIGNING_KEY_ALIAS")
        keyPassword = System.getenv("SIGNING_KEY_PASSWORD")
    }
}

buildTypes {
    release {
        signingConfig = signingConfigs.getByName("release")
        isMinifyEnabled = true
        isShrinkResources = true
        proguardFiles(
            getDefaultProguardFile("proguard-android-optimize.txt"),
            "proguard-rules.pro"
        )
    }
}
```

---

#### Tool 4: `setup_service_account_guide`

**Purpose**: Provide interactive step-by-step guide for setting up Google Play Service Account.

**Parameters**: None

**Returns**:
```json
{
  "steps": [
    {
      "step_number": 1,
      "title": "Access Google Play Console",
      "description": "Navigate to Google Play Console and sign in with your developer account",
      "url": "https://play.google.com/console/",
      "action": "Open URL in browser",
      "verification": "You should see your app listed in the Play Console"
    },
    {
      "step_number": 2,
      "title": "Navigate to API Access",
      "description": "In the left sidebar, go to Setup > API access",
      "action": "Click through navigation",
      "verification": "You should see the API access page with service accounts section"
    },
    {
      "step_number": 3,
      "title": "Create Service Account",
      "description": "Click 'Create new service account' button",
      "action": "Follow link to Google Cloud Platform",
      "url": "https://console.cloud.google.com/",
      "details": "This will open Google Cloud Console in a new tab"
    },
    {
      "step_number": 4,
      "title": "Create Service Account in GCP",
      "description": "In Google Cloud Console, create a new service account",
      "action": "Fill in service account details",
      "required_fields": {
        "name": "playstore-deploy-bot",
        "description": "Service account for automated Play Store deployments"
      }
    },
    {
      "step_number": 5,
      "title": "Create JSON Key",
      "description": "Create and download a JSON key for the service account",
      "action": "Click 'Create Key' > Select JSON format > Download",
      "warning": "This key will only be shown once. Store it securely.",
      "verification": "You should have a JSON file downloaded"
    },
    {
      "step_number": 6,
      "title": "Grant Permissions in Play Console",
      "description": "Return to Play Console and grant permissions to the service account",
      "action": "Select 'Release Manager' role",
      "required_permissions": ["Release Manager"],
      "verification": "Service account should appear in the list with correct permissions"
    },
    {
      "step_number": 7,
      "title": "Enable Play Developer API",
      "description": "Ensure Google Play Developer API is enabled in your Google Cloud project",
      "url": "https://console.cloud.google.com/apis/library/androidpublisher.googleapis.com",
      "action": "Click 'Enable API'",
      "verification": "API should show as 'Enabled'"
    }
  ],
  "validation_checklist": [
    "Service account JSON key file downloaded",
    "Service account has Release Manager role in Play Console",
    "Google Play Developer API is enabled",
    "You have the service account email address"
  ],
  "troubleshooting": {
    "common_issues": [
      {
        "issue": "Cannot see 'API access' option",
        "solution": "You need to be the account owner or have Admin permissions"
      },
      {
        "issue": "Service account not appearing in Play Console",
        "solution": "Make sure you completed the linking step from Play Console to GCP"
      }
    ]
  },
  "next_steps": "After completing these steps, you'll use the JSON key file as a GitHub Secret"
}
```

---

#### Tool 5: `generate_github_workflow`

**Purpose**: Generate a complete GitHub Actions workflow file for Play Store deployment.

**Parameters**:
```json
{
  "project_path": {
    "type": "string",
    "description": "Path to Android project",
    "required": true
  },
  "package_name": {
    "type": "string",
    "description": "Android app package name",
    "required": true
  },
  "track": {
    "type": "string",
    "description": "Play Store release track",
    "required": false,
    "default": "internal",
    "enum": ["internal", "alpha", "beta", "production"]
  },
  "trigger_strategy": {
    "type": "string",
    "description": "How to trigger the workflow",
    "required": false,
    "default": "manual",
    "enum": ["manual", "branch", "tag"]
  },
  "branch_name": {
    "type": "string",
    "description": "Branch name to trigger on (if trigger_strategy=branch)",
    "required": false,
    "default": "release/internal"
  },
  "app_module_path": {
    "type": "string",
    "description": "Path to app module",
    "required": false,
    "default": "app"
  },
  "java_version": {
    "type": "string",
    "description": "Java/JDK version to use",
    "required": false,
    "default": "17"
  }
}
```

**Returns**:
```json
{
  "success": true,
  "workflow_path": ".github/workflows/deploy-internal.yml",
  "workflow_content": "Complete YAML content",
  "required_secrets": [
    {
      "name": "SERVICE_ACCOUNT_JSON_PLAINTEXT",
      "description": "Contents of the service account JSON file",
      "how_to_generate": "Download from Google Cloud Console when creating service account key"
    },
    {
      "name": "SIGNING_KEY_STORE_BASE64",
      "description": "Base64-encoded keystore file",
      "how_to_generate": "Run: base64 -w 0 your-keystore.jks"
    },
    {
      "name": "SIGNING_KEY_ALIAS",
      "description": "The alias of your signing key",
      "how_to_generate": "This is what you specified when creating the keystore"
    },
    {
      "name": "SIGNING_KEY_PASSWORD",
      "description": "Password for your signing key",
      "how_to_generate": "This is what you specified when creating the keystore"
    },
    {
      "name": "SIGNING_STORE_PASSWORD",
      "description": "Password for your keystore",
      "how_to_generate": "This is what you specified when creating the keystore"
    }
  ],
  "instructions": [
    "Create .github/workflows directory if it doesn't exist",
    "Save the workflow_content to the workflow_path",
    "Configure the required GitHub Secrets",
    "Commit and push the workflow file",
    "Test with a manual workflow dispatch"
  ],
  "estimated_build_time": "5-10 minutes",
  "github_actions_cost": "Free for public repos, 2000 minutes/month for private repos on free tier"
}
```

**Workflow Template**:
```yaml
name: Deploy to Play Store {{track}}

on:
  {{trigger_config}}

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up JDK {{java_version}}
        uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '{{java_version}}'
          cache: 'gradle'

      - name: Grant execute permission for gradlew
        run: chmod +x gradlew

      - name: Decode Keystore
        run: |
          echo "${{ secrets.SIGNING_KEY_STORE_BASE64 }}" | base64 --decode > ${{ github.workspace }}/release.jks

      - name: Build Release AAB
        run: ./gradlew bundleRelease
        env:
          SIGNING_KEY_ALIAS: ${{ secrets.SIGNING_KEY_ALIAS }}
          SIGNING_KEY_PASSWORD: ${{ secrets.SIGNING_KEY_PASSWORD }}
          SIGNING_STORE_PASSWORD: ${{ secrets.SIGNING_STORE_PASSWORD }}
          SIGNING_KEY_STORE_PATH: ${{ github.workspace }}/release.jks

      - name: Upload to Google Play {{track}} Track
        uses: r0adkll/upload-google-play@v1
        with:
          serviceAccountJsonPlainText: ${{ secrets.SERVICE_ACCOUNT_JSON_PLAINTEXT }}
          packageName: {{package_name}}
          releaseFiles: {{app_module_path}}/build/outputs/bundle/release/app-release.aab
          track: {{track}}
          status: completed

      - name: Clean up keystore
        if: always()
        run: rm -f ${{ github.workspace }}/release.jks
```

---

#### Tool 6: `validate_github_secrets`

**Purpose**: Validate that required GitHub Secrets are configured (checks existence, not values).

**Parameters**:
```json
{
  "repo_owner": {
    "type": "string",
    "description": "GitHub repository owner (username or org)",
    "required": true
  },
  "repo_name": {
    "type": "string",
    "description": "GitHub repository name",
    "required": true
  },
  "github_token": {
    "type": "string",
    "description": "GitHub Personal Access Token with repo scope",
    "required": true
  },
  "required_secrets": {
    "type": "array",
    "description": "List of secret names to check",
    "required": false,
    "default": [
      "SERVICE_ACCOUNT_JSON_PLAINTEXT",
      "SIGNING_KEY_STORE_BASE64",
      "SIGNING_KEY_ALIAS",
      "SIGNING_KEY_PASSWORD",
      "SIGNING_STORE_PASSWORD"
    ]
  }
}
```

**Returns**:
```json
{
  "all_secrets_present": false,
  "total_required": 5,
  "total_configured": 3,
  "missing_secrets": [
    "SERVICE_ACCOUNT_JSON_PLAINTEXT",
    "SIGNING_KEY_STORE_BASE64"
  ],
  "configured_secrets": [
    "SIGNING_KEY_ALIAS",
    "SIGNING_KEY_PASSWORD",
    "SIGNING_STORE_PASSWORD"
  ],
  "instructions_for_missing": {
    "SERVICE_ACCOUNT_JSON_PLAINTEXT": "Download the service account JSON from Google Cloud Console, then copy its entire contents into this secret",
    "SIGNING_KEY_STORE_BASE64": "Run 'base64 -w 0 your-keystore.jks' and paste the output here"
  },
  "github_secrets_url": "https://github.com/owner/repo/settings/secrets/actions",
  "validation_timestamp": "2025-11-20T10:30:00Z"
}
```

**Implementation**: Uses GitHub REST API `/repos/{owner}/{repo}/actions/secrets`

---

#### Tool 7: `create_github_secrets_guide`

**Purpose**: Generate a comprehensive guide for creating all required GitHub Secrets.

**Parameters**:
```json
{
  "repo_url": {
    "type": "string",
    "description": "GitHub repository URL (https://github.com/owner/repo)",
    "required": true
  },
  "keystore_path": {
    "type": "string",
    "description": "Path to keystore file for encoding instructions",
    "required": false
  }
}
```

**Returns**:
```json
{
  "github_secrets_url": "https://github.com/owner/repo/settings/secrets/actions",
  "secrets": [
    {
      "name": "SERVICE_ACCOUNT_JSON_PLAINTEXT",
      "description": "The complete contents of your Google Play service account JSON file",
      "how_to_get_value": [
        "Open the JSON file you downloaded from Google Cloud Console",
        "Copy the entire file contents (all the JSON)",
        "Paste it directly into the secret value field"
      ],
      "is_sensitive": true,
      "required": true
    },
    {
      "name": "SIGNING_KEY_STORE_BASE64",
      "description": "Your Android keystore file encoded as base64",
      "how_to_get_value": [
        "Open terminal/command prompt",
        "Navigate to the directory containing your keystore",
        "Run: base64 -w 0 your-keystore.jks (Linux/Mac)",
        "Or: certutil -encode your-keystore.jks keystore-base64.txt (Windows)",
        "Copy the output and paste as the secret value"
      ],
      "example_command": "base64 -w 0 release.jks",
      "is_sensitive": true,
      "required": true
    },
    {
      "name": "SIGNING_KEY_ALIAS",
      "description": "The alias you chose when creating your keystore",
      "how_to_get_value": [
        "This is the value you specified when creating the keystore",
        "If you forgot it, run: keytool -list -v -keystore your-keystore.jks"
      ],
      "is_sensitive": false,
      "required": true
    },
    {
      "name": "SIGNING_KEY_PASSWORD",
      "description": "The password for your signing key",
      "how_to_get_value": [
        "This is the password you set when creating the keystore key"
      ],
      "is_sensitive": true,
      "required": true
    },
    {
      "name": "SIGNING_STORE_PASSWORD",
      "description": "The password for your keystore file",
      "how_to_get_value": [
        "This is the password you set when creating the keystore"
      ],
      "is_sensitive": true,
      "required": true
    }
  ],
  "step_by_step_instructions": [
    "Navigate to your GitHub repository",
    "Click on Settings tab",
    "In left sidebar, click 'Secrets and variables' > 'Actions'",
    "Click 'New repository secret' button",
    "For each secret above:",
    "  - Enter the exact secret name (case-sensitive)",
    "  - Follow the 'how_to_get_value' instructions",
    "  - Paste the value",
    "  - Click 'Add secret'",
    "Verify all 5 secrets are listed"
  ],
  "security_reminders": [
    "Never commit secrets to your repository",
    "Never log or print secret values",
    "Store passwords in a secure password manager",
    "Back up your keystore and passwords securely",
    "Rotate service account keys periodically"
  ]
}
```

---

#### Tool 8: `validate_play_store_setup`

**Purpose**: Validate that Play Store app and API access are properly configured.

**Parameters**:
```json
{
  "service_account_json_path": {
    "type": "string",
    "description": "Path to service account JSON file",
    "required": true
  },
  "package_name": {
    "type": "string",
    "description": "Android app package name",
    "required": true
  }
}
```

**Returns**:
```json
{
  "overall_status": "success|partial|failure",
  "checks": {
    "service_account_valid": {
      "status": "pass|fail",
      "message": "Service account credentials are valid"
    },
    "api_enabled": {
      "status": "pass|fail",
      "message": "Google Play Developer API is enabled"
    },
    "app_exists": {
      "status": "pass|fail",
      "message": "App with package name exists in Play Console"
    },
    "permissions_sufficient": {
      "status": "pass|fail",
      "message": "Service account has Release Manager permissions",
      "details": "Required: Release Manager, Found: Release Manager"
    },
    "can_access_tracks": {
      "status": "pass|fail",
      "message": "Can access internal testing track",
      "available_tracks": ["internal", "alpha", "beta", "production"]
    }
  },
  "errors": [],
  "warnings": [
    "No releases found on internal track - this is expected for new apps"
  ],
  "next_steps": [
    "Your Play Store setup is complete",
    "You can now deploy to the internal track",
    "Make sure to add testers to your internal testing group"
  ]
}
```

**Implementation**: Uses Google Play Developer API
- Authenticates with service account
- Queries app details
- Checks available tracks
- Validates permissions

---

#### Tool 9: `test_deployment_workflow`

**Purpose**: Test the deployment workflow locally without actually uploading to Play Store.

**Parameters**:
```json
{
  "project_path": {
    "type": "string",
    "description": "Path to Android project",
    "required": true
  },
  "keystore_path": {
    "type": "string",
    "description": "Path to keystore file",
    "required": true
  },
  "store_password": {
    "type": "string",
    "description": "Keystore password",
    "required": true
  },
  "key_alias": {
    "type": "string",
    "description": "Key alias",
    "required": true
  },
  "key_password": {
    "type": "string",
    "description": "Key password",
    "required": true
  },
  "dry_run": {
    "type": "boolean",
    "description": "If true, skip the actual Play Store upload",
    "required": false,
    "default": true
  }
}
```

**Returns**:
```json
{
  "overall_status": "success|failure",
  "steps": [
    {
      "step": "Environment Setup",
      "status": "pass",
      "duration_seconds": 2,
      "message": "Gradle wrapper found and executable"
    },
    {
      "step": "Build AAB",
      "status": "pass",
      "duration_seconds": 120,
      "message": "Successfully built release AAB",
      "details": {
        "task": "bundleRelease",
        "output_file": "app/build/outputs/bundle/release/app-release.aab",
        "file_size_mb": 15.3
      }
    },
    {
      "step": "Verify Signing",
      "status": "pass",
      "duration_seconds": 1,
      "message": "AAB is properly signed",
      "details": {
        "signer": "CN=Android Developer",
        "algorithm": "SHA256withRSA"
      }
    },
    {
      "step": "Upload to Play Store",
      "status": "skipped",
      "message": "Skipped due to dry_run=true"
    }
  ],
  "total_duration_seconds": 123,
  "build_successful": true,
  "signing_successful": true,
  "aab_generated": true,
  "aab_path": "/path/to/app/build/outputs/bundle/release/app-release.aab",
  "aab_size_mb": 15.3,
  "errors": [],
  "warnings": [
    "ProGuard rules file is minimal - consider adding app-specific rules"
  ],
  "ready_for_deployment": true,
  "next_steps": [
    "Test the AAB on a real device",
    "Set dry_run=false to perform actual upload",
    "Monitor the GitHub Actions workflow"
  ]
}
```

---

### 1.2 Security Requirements

**CRITICAL**: All tools must implement secure credential handling to prevent security breaches.

#### Credential Management Principles

1. **Never Hardcode Credentials**:
   - No credentials in source code
   - No credentials in configuration files committed to version control
   - No credentials in logs or error messages

2. **Credential Sources** (in order of preference):
   - Environment variables (recommended)
   - Secure credential store (OS keychain)
   - File path provided by user (with restricted permissions)
   - Interactive prompt (masked input)

3. **Credential Handling in Tools**:

   **Tool: `validate_github_secrets`**
   - GitHub token MUST be read from:
     - Environment variable: `GITHUB_TOKEN`
     - OR passed as parameter (not logged)
   - Token MUST never appear in logs or error messages
   - Use token only for API authentication
   - Clear token from memory after use

   **Tool: `validate_play_store_setup`**
   - Service account JSON MUST be read from:
     - File path (verify file permissions: 600 or 400)
     - OR environment variable: `GOOGLE_APPLICATION_CREDENTIALS`
   - JSON contents MUST never be logged
   - Validate JSON structure before use
   - Clear sensitive data from memory after use

   **Tool: `generate_keystore`**
   - Passwords MUST be provided via:
     - Parameters (not logged)
     - OR interactive masked prompt
   - Set restrictive permissions on generated keystore: chmod 600
   - Warn user about backup requirements
   - Never echo passwords in shell commands

   **Tool: `test_deployment_workflow`**
   - Accept keystore passwords via:
     - Environment variables
     - OR parameters (not logged)
   - Clear passwords from memory after use
   - Never write passwords to temporary files

4. **Logging Security**:
   - Implement credential sanitization in all logs
   - Replace sensitive values with "[REDACTED]"
   - Log only success/failure, not credential values
   - Sanitize error messages from external APIs

5. **File Permission Checks**:
   ```python
   def validate_secure_file(file_path: str) -> bool:
       """Ensure file has secure permissions (600 or 400)"""
       import os
       import stat

       st = os.stat(file_path)
       mode = st.st_mode & 0o777

       if mode not in [0o600, 0o400]:
           raise SecurityError(
               f"Insecure file permissions: {oct(mode)}. "
               f"Expected 600 or 400. Run: chmod 600 {file_path}"
           )
       return True
   ```

6. **Environment Variable Documentation**:

   All tools that accept credentials must document environment variables:

   ```
   Environment Variables:
     GITHUB_TOKEN              GitHub Personal Access Token (repo scope)
     GOOGLE_APPLICATION_CREDENTIALS   Path to service account JSON
     SIGNING_STORE_PASSWORD    Keystore password (for testing)
     SIGNING_KEY_PASSWORD      Key password (for testing)

   Security Notes:
     - Never commit .env files with real credentials
     - Use .env.example with placeholder values
     - In production (GitHub Actions), use encrypted secrets
   ```

#### Security Testing Requirements

All credential-handling code must be tested for:
- [ ] Credentials never appear in logs
- [ ] Credentials never appear in error messages
- [ ] Environment variables are checked before file paths
- [ ] File permissions are validated
- [ ] Memory is cleared after credential use (where applicable)

---

### 1.3 Error Handling Requirements

All tools must implement robust error handling, especially for external API interactions.

#### Error Handling Patterns

1. **API Interaction Error Handling**:

   **Pattern for GitHub API**:
   ```python
   import requests
   from typing import Dict, Any

   def call_github_api(url: str, token: str) -> Dict[str, Any]:
       """Call GitHub API with comprehensive error handling"""
       try:
           response = requests.get(
               url,
               headers={"Authorization": f"token {token}"},
               timeout=30
           )

           # Handle specific HTTP errors
           if response.status_code == 401:
               raise AuthenticationError(
                   "GitHub token is invalid or expired. "
                   "Generate a new token at: https://github.com/settings/tokens"
               )
           elif response.status_code == 403:
               if "rate limit" in response.text.lower():
                   raise RateLimitError(
                       "GitHub API rate limit exceeded. "
                       "Wait an hour or use a token with higher limits."
                   )
               else:
                   raise PermissionError(
                       "GitHub token lacks required permissions. "
                       "Ensure token has 'repo' scope."
                   )
           elif response.status_code == 404:
               raise NotFoundError(
                   "Repository not found. Check owner/repo names and token permissions."
               )
           elif response.status_code >= 500:
               raise ServiceError(
                   f"GitHub API is experiencing issues (HTTP {response.status_code}). "
                   "Try again later."
               )

           response.raise_for_status()
           return response.json()

       except requests.exceptions.Timeout:
           raise TimeoutError(
               "GitHub API request timed out. Check your internet connection."
           )
       except requests.exceptions.ConnectionError:
           raise NetworkError(
               "Cannot connect to GitHub API. Check your internet connection."
           )
       except requests.exceptions.RequestException as e:
           raise APIError(f"GitHub API error: {str(e)}")
   ```

   **Pattern for Google Play API**:
   ```python
   from google.oauth2 import service_account
   from googleapiclient.discovery import build
   from googleapiclient.errors import HttpError

   def call_play_api(service_account_path: str, package_name: str):
       """Call Google Play API with comprehensive error handling"""
       try:
           # Authenticate
           credentials = service_account.Credentials.from_service_account_file(
               service_account_path,
               scopes=['https://www.googleapis.com/auth/androidpublisher']
           )

           service = build('androidpublisher', 'v3', credentials=credentials)

           # Make API call
           result = service.edits().insert(
               body={}, packageName=package_name
           ).execute()

           return result

       except FileNotFoundError:
           raise ConfigurationError(
               f"Service account file not found: {service_account_path}"
           )
       except ValueError as e:
           if "json" in str(e).lower():
               raise ConfigurationError(
                   "Invalid service account JSON format. "
                   "Re-download from Google Cloud Console."
               )
           raise
       except HttpError as e:
           if e.resp.status == 401:
               raise AuthenticationError(
                   "Service account credentials are invalid. "
                   "Verify the JSON file is correct and not expired."
               )
           elif e.resp.status == 403:
               raise PermissionError(
                   "Service account lacks permissions. "
                   "Ensure it has 'Release Manager' role in Play Console."
               )
           elif e.resp.status == 404:
               raise NotFoundError(
                   f"App with package name '{package_name}' not found. "
                   "Verify the package name and that the app exists in Play Console."
               )
           elif e.resp.status == 429:
               raise RateLimitError(
                   "Google Play API rate limit exceeded. Wait and try again."
               )
           else:
               raise APIError(f"Google Play API error: {e.resp.status} - {e._get_reason()}")
   ```

2. **File System Error Handling**:
   ```python
   import os
   from pathlib import Path

   def validate_project_path(project_path: str) -> Path:
       """Validate Android project path with helpful errors"""
       path = Path(project_path).resolve()

       if not path.exists():
           raise FileNotFoundError(
               f"Project path does not exist: {project_path}\n"
               "Provide an absolute path to your Android project root."
           )

       if not path.is_dir():
           raise NotADirectoryError(
               f"Path is not a directory: {project_path}"
           )

       # Check for Android project markers
       has_gradle = (path / "build.gradle").exists() or (path / "build.gradle.kts").exists()
       has_settings = (path / "settings.gradle").exists() or (path / "settings.gradle.kts").exists()

       if not (has_gradle and has_settings):
           raise ValidationError(
               f"Path does not appear to be an Android project: {project_path}\n"
               "Expected to find build.gradle(.kts) and settings.gradle(.kts)"
           )

       return path
   ```

3. **System Command Error Handling**:
   ```python
   import subprocess
   from typing import Tuple

   def run_command(cmd: list, cwd: str = None) -> Tuple[str, str]:
       """Run system command with comprehensive error handling"""
       try:
           result = subprocess.run(
               cmd,
               cwd=cwd,
               capture_output=True,
               text=True,
               timeout=300,  # 5 minutes
               check=False
           )

           if result.returncode != 0:
               # Parse common errors
               if "keytool" in cmd[0]:
                   if "command not found" in result.stderr:
                       raise DependencyError(
                           "keytool not found. Install JDK and ensure it's in PATH."
                       )
                   elif "keystore password was incorrect" in result.stderr:
                       raise AuthenticationError(
                           "Incorrect keystore password."
                       )

               raise CommandError(
                   f"Command failed: {' '.join(cmd)}\n"
                   f"Exit code: {result.returncode}\n"
                   f"Error: {result.stderr}"
               )

           return result.stdout, result.stderr

       except subprocess.TimeoutExpired:
           raise TimeoutError(
               f"Command timed out after 5 minutes: {' '.join(cmd)}"
           )
       except FileNotFoundError:
           raise DependencyError(
               f"Command not found: {cmd[0]}\n"
               "Ensure required tools are installed."
           )
   ```

4. **Custom Exception Hierarchy**:
   ```python
   class MCPPlayStoreError(Exception):
       """Base exception for all MCP Play Store errors"""
       pass

   class ConfigurationError(MCPPlayStoreError):
       """Configuration is invalid or incomplete"""
       pass

   class AuthenticationError(MCPPlayStoreError):
       """Authentication failed (invalid credentials)"""
       pass

   class PermissionError(MCPPlayStoreError):
       """Insufficient permissions"""
       pass

   class NotFoundError(MCPPlayStoreError):
       """Resource not found"""
       pass

   class ValidationError(MCPPlayStoreError):
       """Input validation failed"""
       pass

   class APIError(MCPPlayStoreError):
       """External API error"""
       pass

   class NetworkError(MCPPlayStoreError):
       """Network connectivity issue"""
       pass

   class RateLimitError(MCPPlayStoreError):
       """API rate limit exceeded"""
       pass

   class DependencyError(MCPPlayStoreError):
       """Required system dependency missing"""
       pass

   class CommandError(MCPPlayStoreError):
       """System command execution failed"""
       pass

   class SecurityError(MCPPlayStoreError):
       """Security-related issue (permissions, etc.)"""
       pass
   ```

5. **Error Response Format**:

   All tools must return errors in consistent format:
   ```json
   {
     "success": false,
     "error": {
       "type": "AuthenticationError",
       "message": "GitHub token is invalid or expired",
       "details": "Generate a new token at: https://github.com/settings/tokens",
       "code": "GITHUB_AUTH_FAILED",
       "recoverable": true,
       "suggested_action": "Create a new GitHub token with 'repo' scope and try again"
     }
   }
   ```

#### Error Handling Testing Requirements

- [ ] All API interaction paths have error handling
- [ ] Network failures are handled gracefully
- [ ] Invalid credentials produce helpful error messages
- [ ] File system errors include suggested fixes
- [ ] Timeout errors are caught and reported
- [ ] Rate limiting is handled with retry guidance

---

### 1.4 Testing Strategy

Comprehensive testing is essential for reliability and maintainability.

#### Unit Tests

**Test Each Tool Independently**:

1. **`analyze_android_project`**:
   - Test with valid native Android project
   - Test with React Native project structure
   - Test with Flutter project structure
   - Test with missing build files (error case)
   - Test with invalid path (error case)
   - Mock file system for deterministic tests

2. **`generate_keystore`**:
   - Test keystore creation with valid parameters
   - Test with invalid output path (error case)
   - Test with weak passwords (validation)
   - Mock `keytool` command
   - Verify base64 encoding correctness
   - Test file permission setting

3. **`generate_signing_config`**:
   - Test Kotlin DSL generation
   - Test Groovy DSL generation (if supported)
   - Test with different signing strategies
   - Verify output format is valid

4. **`setup_service_account_guide`**:
   - Test guide structure completeness
   - Verify all steps present
   - Check URLs are valid

5. **`generate_github_workflow`**:
   - Test workflow generation for each track
   - Test different trigger strategies
   - Verify YAML validity
   - Test template rendering

6. **`validate_github_secrets`**:
   - Mock GitHub API responses
   - Test with all secrets present
   - Test with missing secrets
   - Test authentication failure (401)
   - Test permission failure (403)
   - Test rate limiting (429)
   - Test network errors

7. **`create_github_secrets_guide`**:
   - Test guide completeness
   - Verify all required secrets covered
   - Check command examples are correct

8. **`validate_play_store_setup`**:
   - Mock Google Play API responses
   - Test with valid service account
   - Test with invalid JSON
   - Test with insufficient permissions
   - Test with non-existent app
   - Test API disabled scenario

9. **`test_deployment_workflow`**:
   - Mock Gradle execution
   - Test successful build
   - Test build failure
   - Test signing verification
   - Test dry_run mode

**Unit Test Framework**:
```python
# tests/test_tools.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from mcp_android_playstore_deploy.generator import (
    analyze_android_project,
    generate_keystore,
    validate_github_secrets
)

class TestAnalyzeProject:
    def test_valid_native_android_project(self, tmp_path):
        # Create test project structure
        (tmp_path / "build.gradle.kts").write_text("// build file")
        (tmp_path / "settings.gradle.kts").write_text("// settings")
        app_dir = tmp_path / "app"
        app_dir.mkdir()
        (app_dir / "build.gradle.kts").write_text("""
            android {
                namespace = "com.example.app"
                defaultConfig {
                    applicationId = "com.example.app"
                    versionCode = 1
                    versionName = "1.0"
                }
            }
        """)

        result = analyze_android_project(str(tmp_path))

        assert result["success"] == True
        assert result["project_type"] == "native_android"
        assert result["package_name"] == "com.example.app"

    def test_invalid_path(self):
        with pytest.raises(FileNotFoundError):
            analyze_android_project("/nonexistent/path")

class TestValidateGitHubSecrets:
    @patch('requests.get')
    def test_all_secrets_present(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "secrets": [
                {"name": "SERVICE_ACCOUNT_JSON_PLAINTEXT"},
                {"name": "SIGNING_KEY_STORE_BASE64"},
                {"name": "SIGNING_KEY_ALIAS"},
                {"name": "SIGNING_KEY_PASSWORD"},
                {"name": "SIGNING_STORE_PASSWORD"}
            ]
        }
        mock_get.return_value = mock_response

        result = validate_github_secrets(
            repo_owner="test",
            repo_name="repo",
            github_token="fake_token"
        )

        assert result["all_secrets_present"] == True
        assert len(result["missing_secrets"]) == 0

    @patch('requests.get')
    def test_authentication_failure(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        with pytest.raises(AuthenticationError):
            validate_github_secrets(
                repo_owner="test",
                repo_name="repo",
                github_token="invalid_token"
            )
```

#### Integration Tests

**Test Tool Interactions**:

1. **End-to-End Project Analysis**:
   - Use real Android project as test fixture
   - Verify all fields extracted correctly
   - Test with different project types

2. **Workflow Generation + Validation**:
   - Generate workflow file
   - Parse and validate YAML
   - Verify all placeholders filled

3. **Keystore Generation + Signing Config**:
   - Generate keystore
   - Generate signing config
   - Verify config references keystore correctly

#### End-to-End Tests

**Full Workflow Tests**:

1. **Setup Test Android Project**:
   - Create minimal test Android project
   - Include in test fixtures

2. **Run Complete Setup Flow**:
   - Analyze project
   - Generate keystore
   - Generate signing config
   - Generate workflow
   - Validate (with mocked APIs)

3. **Verify Outputs**:
   - All files created
   - Files have correct content
   - Configuration is valid

#### Test Coverage Requirements

- **Minimum**: 80% code coverage
- **Target**: 90% code coverage
- **Critical paths**: 100% coverage
  - Credential handling
  - API authentication
  - Error handling

#### Continuous Integration Tests

**GitHub Actions Test Workflow**:
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.10', '3.11', '3.12']

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"

    - name: Run unit tests
      run: pytest tests/unit/ -v --cov

    - name: Run integration tests
      run: pytest tests/integration/ -v

    - name: Check code coverage
      run: pytest --cov --cov-report=xml --cov-report=term

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

### 1.5 Using mcp-server-generator

**Command to Generate Project**:

```bash
# Using the MCP server generator tool
```

**Tool Call Parameters**:
```json
{
  "project_name": "mcp-android-playstore-deploy",
  "description": "MCP server that helps developers set up automated Google Play Store deployment for Android apps",
  "author": "Vinayak Menon",
  "author_email": "your-email@example.com",
  "tools": [
    {
      "name": "analyze_android_project",
      "description": "Analyze an Android project to understand its configuration and identify requirements for Play Store deployment",
      "parameters": [
        {
          "name": "project_path",
          "type": "string",
          "description": "Absolute path to the Android project root directory",
          "required": true
        }
      ]
    },
    {
      "name": "generate_keystore",
      "description": "Generate a new Android keystore file for app signing with secure parameters",
      "parameters": [
        {
          "name": "output_path",
          "type": "string",
          "description": "Absolute path where the keystore will be saved",
          "required": true
        },
        {
          "name": "alias",
          "type": "string",
          "description": "Key alias for the signing key",
          "required": true
        },
        {
          "name": "key_password",
          "type": "string",
          "description": "Password for the signing key",
          "required": true
        },
        {
          "name": "store_password",
          "type": "string",
          "description": "Password for the keystore",
          "required": true
        },
        {
          "name": "validity_days",
          "type": "number",
          "description": "How many days the key should be valid",
          "required": false
        },
        {
          "name": "key_size",
          "type": "number",
          "description": "Key size in bits",
          "required": false
        },
        {
          "name": "dname",
          "type": "string",
          "description": "Distinguished name for the certificate",
          "required": false
        }
      ]
    },
    {
      "name": "generate_signing_config",
      "description": "Generate Gradle signing configuration code to add to build.gradle.kts",
      "parameters": [
        {
          "name": "project_path",
          "type": "string",
          "description": "Path to Android project",
          "required": true
        },
        {
          "name": "signing_strategy",
          "type": "string",
          "description": "How to provide signing credentials (environment_variables or gradle_properties)",
          "required": false
        }
      ]
    },
    {
      "name": "setup_service_account_guide",
      "description": "Provide interactive step-by-step guide for setting up Google Play Service Account",
      "parameters": []
    },
    {
      "name": "generate_github_workflow",
      "description": "Generate a complete GitHub Actions workflow file for Play Store deployment",
      "parameters": [
        {
          "name": "project_path",
          "type": "string",
          "description": "Path to Android project",
          "required": true
        },
        {
          "name": "package_name",
          "type": "string",
          "description": "Android app package name",
          "required": true
        },
        {
          "name": "track",
          "type": "string",
          "description": "Play Store release track (internal, alpha, beta, production)",
          "required": false
        },
        {
          "name": "trigger_strategy",
          "type": "string",
          "description": "How to trigger the workflow (manual, branch, tag)",
          "required": false
        },
        {
          "name": "branch_name",
          "type": "string",
          "description": "Branch name to trigger on if trigger_strategy is branch",
          "required": false
        },
        {
          "name": "app_module_path",
          "type": "string",
          "description": "Path to app module relative to project root",
          "required": false
        },
        {
          "name": "java_version",
          "type": "string",
          "description": "Java/JDK version to use for builds",
          "required": false
        }
      ]
    },
    {
      "name": "validate_github_secrets",
      "description": "Validate that required GitHub Secrets are configured (checks existence only)",
      "parameters": [
        {
          "name": "repo_owner",
          "type": "string",
          "description": "GitHub repository owner username or organization",
          "required": true
        },
        {
          "name": "repo_name",
          "type": "string",
          "description": "GitHub repository name",
          "required": true
        },
        {
          "name": "github_token",
          "type": "string",
          "description": "GitHub Personal Access Token with repo scope",
          "required": true
        },
        {
          "name": "required_secrets",
          "type": "array",
          "description": "List of secret names to check for",
          "required": false
        }
      ]
    },
    {
      "name": "create_github_secrets_guide",
      "description": "Generate a comprehensive guide for creating all required GitHub Secrets",
      "parameters": [
        {
          "name": "repo_url",
          "type": "string",
          "description": "GitHub repository URL",
          "required": true
        },
        {
          "name": "keystore_path",
          "type": "string",
          "description": "Optional path to keystore for encoding instructions",
          "required": false
        }
      ]
    },
    {
      "name": "validate_play_store_setup",
      "description": "Validate that Play Store app and API access are properly configured using service account",
      "parameters": [
        {
          "name": "service_account_json_path",
          "type": "string",
          "description": "Path to service account JSON file",
          "required": true
        },
        {
          "name": "package_name",
          "type": "string",
          "description": "Android app package name to validate",
          "required": true
        }
      ]
    },
    {
      "name": "test_deployment_workflow",
      "description": "Test the deployment workflow locally without uploading to Play Store",
      "parameters": [
        {
          "name": "project_path",
          "type": "string",
          "description": "Path to Android project",
          "required": true
        },
        {
          "name": "keystore_path",
          "type": "string",
          "description": "Path to keystore file",
          "required": true
        },
        {
          "name": "store_password",
          "type": "string",
          "description": "Keystore password",
          "required": true
        },
        {
          "name": "key_alias",
          "type": "string",
          "description": "Key alias",
          "required": true
        },
        {
          "name": "key_password",
          "type": "string",
          "description": "Key password",
          "required": true
        },
        {
          "name": "dry_run",
          "type": "boolean",
          "description": "If true, skip actual Play Store upload",
          "required": false
        }
      ]
    }
  ],
  "output_dir": "~/projects",
  "python_version": "3.10"
}
```

### 1.3 Implementation Tasks

After generating the project skeleton, the following implementations are needed:

**File: `src/mcp_android_playstore_deploy/generator.py`**

Implement the business logic for each tool:

1. **`analyze_android_project`**:
   - Parse `build.gradle.kts` / `build.gradle` files
   - Extract package name, version codes, SDK versions
   - Check for signing configuration
   - Detect project type (native, React Native, Flutter)
   - Generate recommendations

2. **`generate_keystore`**:
   - Validate parameters
   - Execute `keytool` command
   - Encode keystore to base64
   - Return instructions

3. **`generate_signing_config`**:
   - Generate Kotlin/Groovy DSL snippets
   - Provide insertion instructions
   - Include security best practices

4. **`setup_service_account_guide`**:
   - Return structured guide data
   - Include URLs, verification steps
   - Provide troubleshooting tips

5. **`generate_github_workflow`**:
   - Use Jinja2 templates for workflow generation
   - Support different trigger strategies
   - Include all required secrets documentation

6. **`validate_github_secrets`**:
   - Use GitHub API to check secret existence
   - Handle authentication
   - Provide helpful error messages

7. **`create_github_secrets_guide`**:
   - Generate structured guide
   - Include platform-specific commands
   - Provide security reminders

8. **`validate_play_store_setup`**:
   - Use Google Play Developer API
   - Authenticate with service account
   - Check app existence and permissions
   - Return detailed status

9. **`test_deployment_workflow`**:
   - Execute Gradle build locally
   - Verify signing
   - Check AAB validity
   - Report detailed status

### 1.4 Dependencies

**Add to `pyproject.toml` or `requirements.txt`**:

```toml
[project]
dependencies = [
    "mcp>=1.0.0",
    "google-auth>=2.0.0",
    "google-api-python-client>=2.0.0",
    "pyyaml>=6.0",
    "jinja2>=3.0",
    "requests>=2.28.0",
    "packaging>=23.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "mypy>=1.0.0"
]
```

### 1.5 Testing Strategy

**Unit Tests** (for each tool):
- Test with mock data
- Validate parameter validation
- Test error handling

**Integration Tests**:
- Test with real Android project (test fixture)
- Test keystore generation
- Test workflow generation
- Mock external APIs (GitHub, Google Play)

**End-to-End Tests**:
- Test complete workflow with test project
- Verify generated files are valid
- Test with Claude Code locally

---

### 1.6 Test Android Project

**IMPORTANT**: Include a barebones Android project within the MCP server repository for testing generated workflows and artifacts.

#### Purpose

The test project serves multiple purposes:
1. **Validation**: Verify generated workflows and configs actually work
2. **Testing**: Use as fixture for integration and E2E tests
3. **Documentation**: Provide a working example for users
4. **Development**: Quick iteration without external project dependency

#### Project Structure

```
mcp-android-playstore-deploy/
├── src/
│   └── mcp_android_playstore_deploy/
│       └── ... (MCP server code)
├── tests/
│   ├── fixtures/
│   │   └── test-android-app/          # Test Android project
│   │       ├── app/
│   │       │   ├── build.gradle.kts
│   │       │   └── src/
│   │       │       └── main/
│   │       │           ├── AndroidManifest.xml
│   │       │           └── java/
│   │       │               └── com/
│   │       │                   └── test/
│   │       │                       └── playstore/
│   │       │                           └── MainActivity.kt
│   │       ├── build.gradle.kts
│   │       ├── settings.gradle.kts
│   │       ├── gradle.properties
│   │       ├── gradlew
│   │       └── gradlew.bat
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── examples/
│   └── example-setup.md              # Shows how to use with real project
└── ...
```

#### Test Android Project Specifications

**Minimal but Complete**:

1. **`settings.gradle.kts`**:
```kotlin
rootProject.name = "TestPlayStoreApp"
include(":app")
```

2. **Root `build.gradle.kts`**:
```kotlin
plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.kotlin.android) apply false
}
```

3. **`app/build.gradle.kts`** (Minimal):
```kotlin
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.test.playstore"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.test.playstore"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        release {
            // Note: No signing config initially
            // Tests will add it
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.6.1")
}
```

4. **`AndroidManifest.xml`** (Minimal):
```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application
        android:label="Test PlayStore App"
        android:theme="@style/Theme.AppCompat">
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
```

5. **`MainActivity.kt`** (Minimal):
```kotlin
package com.test.playstore

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
    }
}
```

#### Using Test Project in Tests

**Integration Test Example**:
```python
# tests/integration/test_workflow_generation.py
import pytest
from pathlib import Path
from mcp_android_playstore_deploy.generator import (
    analyze_android_project,
    generate_signing_config,
    generate_github_workflow
)

@pytest.fixture
def test_android_project():
    """Return path to test Android project"""
    return Path(__file__).parent.parent / "fixtures" / "test-android-app"

class TestWorkflowGeneration:
    def test_analyze_test_project(self, test_android_project):
        """Test analyzing the test Android project"""
        result = analyze_android_project(str(test_android_project))

        assert result["success"] == True
        assert result["project_type"] == "native_android"
        assert result["package_name"] == "com.test.playstore"
        assert result["has_signing_config"] == False

    def test_generate_and_apply_signing_config(self, test_android_project, tmp_path):
        """Test generating signing config for test project"""
        # Generate signing config
        config_result = generate_signing_config(
            project_path=str(test_android_project)
        )

        assert config_result["success"] == True
        assert "signingConfigs" in config_result["gradle_config_kotlin"]

        # Copy test project to temp directory
        import shutil
        test_project_copy = tmp_path / "test-android-app"
        shutil.copytree(test_android_project, test_project_copy)

        # Apply config (in real implementation)
        build_gradle = test_project_copy / "app" / "build.gradle.kts"
        # ... apply signing config ...

        # Re-analyze to verify
        result = analyze_android_project(str(test_project_copy))
        # Would now show has_signing_config: true

    def test_build_test_project(self, test_android_project):
        """Test that test project can be built"""
        import subprocess

        result = subprocess.run(
            ["./gradlew", "assembleDebug"],
            cwd=test_android_project,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert (test_android_project / "app" / "build" / "outputs" / "apk" / "debug").exists()
```

#### Test Project Maintenance

**Keep It Minimal**:
- Only essential dependencies
- No complex features
- No UI beyond empty activity
- Fast to build (< 30 seconds)

**Regular Updates**:
- Update SDK versions annually
- Update dependencies when tools require newer versions
- Keep in sync with current Android best practices

**Documentation**:
Add `tests/fixtures/test-android-app/README.md`:
```markdown
# Test Android Project

This is a minimal Android project used for testing the mcp-android-playstore-deploy tools.

## Purpose
- Integration testing
- E2E testing
- Example for documentation

## Building
```bash
cd tests/fixtures/test-android-app
./gradlew assembleDebug
```

## Updating
When updating Android SDK versions or dependencies:
1. Update `compileSdk` and `targetSdk` in `app/build.gradle.kts`
2. Update dependencies to latest stable versions
3. Test that all MCP server tools still work correctly
4. Run full test suite
```

#### Benefits of Including Test Project

1. **Self-Contained Testing**:
   - No dependency on external projects
   - Consistent test environment
   - Fast test execution

2. **Validation**:
   - Verify generated configs actually work
   - Test actual Gradle builds
   - Catch compatibility issues early

3. **Documentation**:
   - Show real example of how tools modify projects
   - Provide working reference for users

4. **Development Speed**:
   - Quick iteration during development
   - No need to set up external test project
   - Easy to reproduce issues

5. **CI/CD Integration**:
   - Test project builds in CI
   - Verify generated workflows
   - Catch breaking changes

#### Testing Strategy with Test Project

**Unit Tests**: Mock file operations
**Integration Tests**: Use test project as fixture
**E2E Tests**:
1. Start with clean copy of test project
2. Run all tools in sequence
3. Verify project builds successfully
4. Verify generated workflow is valid YAML
5. Verify signing config works (with test keystore)

---

## Phase 2: Publishing to PyPI

### 2.1 Prerequisites

Before publishing:

1. **PyPI Account**:
   - Create account at https://pypi.org
   - Create account at https://test.pypi.org (for testing)
   - Generate API token with upload scope

2. **Package Completeness**:
   - All tools implemented
   - Tests passing
   - Documentation complete
   - README.md with usage examples
   - LICENSE file (recommend MIT or Apache 2.0)

3. **Version Management**:
   - Initial version: `0.1.0`
   - Follow semantic versioning

### 2.2 Pre-Publishing Checklist

- [ ] All 9 tools implemented and tested
- [ ] Test Android project created in `tests/fixtures/test-android-app/`
- [ ] Test Android project builds successfully
- [ ] Unit tests passing (>80% coverage)
- [ ] Integration tests passing (using test Android project)
- [ ] E2E tests passing (complete workflow with test project)
- [ ] README.md complete with examples
- [ ] MCP-USAGE.md explains how to configure with Claude Code
- [ ] LICENSE file present
- [ ] CHANGELOG.md with initial entry
- [ ] pyproject.toml metadata complete (description, keywords, classifiers)
- [ ] Test locally: `pip install -e .`
- [ ] Test MCP server startup: `python -m mcp_android_playstore_deploy`

### 2.3 PyPI Publishing Workflow (Automated)

**IMPORTANT**: The `mcp-server-generator` uses `pypi-workflow-generator` to automatically create the PyPI publishing workflow. You don't need to manually configure this.

**What mcp-server-generator Provides**:

The generated project will include:
- `.github/workflows/publish.yml` - Automated PyPI publishing on release
- Complete package configuration in `pyproject.toml`
- Proper versioning setup
- TestPyPI and PyPI publishing support

**GitHub Actions Workflow (Auto-Generated)**:

The generator creates a workflow that:
1. Triggers on GitHub Release creation
2. Builds the package automatically
3. Publishes to PyPI using trusted publishing (no API token needed if configured)
4. Or publishes using `PYPI_API_TOKEN` secret

**Your Only Setup Requirements**:

1. **Configure PyPI Trusted Publishing** (Recommended):
   - Go to PyPI project settings (after first manual upload)
   - Add GitHub repository as trusted publisher
   - No API tokens needed for future releases

   **OR**

2. **Add PyPI API Token**:
   - Generate token at https://pypi.org/manage/account/token/
   - Add as GitHub Secret: `PYPI_API_TOKEN`

**Initial Manual Upload**:

For the very first release to PyPI (to create the project):
```bash
cd mcp-android-playstore-deploy
python -m pip install --upgrade build twine
python -m build
python -m twine upload dist/*
```

After the initial upload, all future releases are automated via GitHub Actions.

### 2.4 Release Process

**To Publish a New Version**:

1. **Update Version**:
   - Version is managed in `pyproject.toml`
   - Follow semantic versioning (e.g., `0.1.0` → `0.1.1` or `0.2.0`)

2. **Create Git Tag**:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

3. **Create GitHub Release**:
   - Go to GitHub repository → Releases → Create new release
   - Select the tag you just created
   - Add release notes
   - Publish release

4. **Automated Publishing**:
   - GitHub Actions automatically builds and publishes to PyPI
   - Monitor the workflow run
   - Verify package appears on PyPI

### 2.5 Testing on TestPyPI (Optional)

If you want to test before publishing to PyPI:

**TestPyPI Setup** (one-time):
- Create account at https://test.pypi.org
- Configure in workflow or use manual upload

**Manual Test Upload**:
```bash
python -m twine upload --repository testpypi dist/*
```

**Test Installation**:
```bash
pip install --index-url https://test.pypi.org/simple/ mcp-android-playstore-deploy
```

### 2.6 Post-Publishing Tasks

- [ ] Verify package on PyPI
- [ ] Test installation: `pip install mcp-android-playstore-deploy`
- [ ] Update documentation with installation instructions
- [ ] Create announcement (if desired)
- [ ] Add badge to README: `[![PyPI version](https://badge.fury.io/py/mcp-android-playstore-deploy.svg)](https://badge.fury.io/py/mcp-android-playstore-deploy)`

---

## Phase 3: Using MCP Server to Set Up Health Sync App

### 3.1 Installation and Configuration

**Install the MCP Server**:
```bash
pip install mcp-android-playstore-deploy
```

**Configure in Claude Code**:

Add to Claude Code's MCP configuration file (typically `~/.config/claude/mcp.json` or similar):

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

**Restart Claude Code** to load the new MCP server.

### 3.2 Guided Setup Workflow

**Step 1: Analyze Health Sync App**

User asks Claude Code:
> "Help me set up automated Play Store deployment for my Health Sync App"

Claude Code uses MCP server:
```
Tool: analyze_android_project
Parameters:
  project_path: /Users/vinayakmenon/health-sync-app
```

Expected findings:
- Project type: native_android
- Build system: gradle
- Package name: io.github.hitoshura25.healthsyncapp
- No signing config present
- No GitHub Actions workflows
- isMinifyEnabled: false (security issue)

**Step 2: Generate Keystore**

Claude Code suggests:
> "I'll help you create a signing keystore. Please provide a strong password for your keystore and key."

User provides passwords (or Claude generates secure ones).

```
Tool: generate_keystore
Parameters:
  output_path: /Users/vinayakmenon/health-sync-app/release.jks
  alias: healthsync-key
  key_password: <user-provided>
  store_password: <user-provided>
  validity_days: 10000
  key_size: 2048
  dname: "CN=Health Sync App"
```

Claude Code receives:
- Keystore file created
- Base64 encoded version
- Instructions for backing up

**Step 3: Add Signing Configuration**

```
Tool: generate_signing_config
Parameters:
  project_path: /Users/vinayakmenon/health-sync-app
  signing_strategy: environment_variables
```

Claude Code:
- Receives Kotlin DSL snippet
- Uses Edit tool to update `app/build.gradle.kts`
- Adds signing configuration
- **Fixes security issue**: Changes `isMinifyEnabled = false` to `true`
- Adds `isShrinkResources = true`

**Step 4: Service Account Setup Guide**

Claude Code asks:
> "Next, we need to set up a Google Play Service Account. Have you done this before?"

If no:
```
Tool: setup_service_account_guide
Parameters: {}
```

Claude Code presents the 7-step guide interactively, waiting for user confirmation at each step.

**Step 5: Generate GitHub Workflow**

```
Tool: generate_github_workflow
Parameters:
  project_path: /Users/vinayakmenon/health-sync-app
  package_name: io.github.hitoshura25.healthsyncapp
  track: internal
  trigger_strategy: manual
  java_version: "17"
```

Claude Code:
- Creates `.github/workflows/` directory
- Writes workflow file
- Lists required GitHub Secrets

**Step 6: GitHub Secrets Setup**

```
Tool: create_github_secrets_guide
Parameters:
  repo_url: https://github.com/hitoshura25/health-sync-app
  keystore_path: /Users/vinayakmenon/health-sync-app/release.jks
```

Claude Code provides detailed instructions for each secret.

User manually adds secrets to GitHub (Claude Code cannot do this).

**Step 7: Validate Setup**

```
Tool: validate_github_secrets
Parameters:
  repo_owner: hitoshura25
  repo_name: health-sync-app
  github_token: <user-provides-or-from-env>
  required_secrets: [default list]
```

Result shows which secrets are configured.

```
Tool: validate_play_store_setup
Parameters:
  service_account_json_path: /path/to/downloaded/service-account.json
  package_name: io.github.hitoshura25.healthsyncapp
```

Validates:
- Service account is valid
- API is enabled
- App exists in Play Console
- Permissions are sufficient

**Step 8: Test Locally**

```
Tool: test_deployment_workflow
Parameters:
  project_path: /Users/vinayakmenon/health-sync-app
  keystore_path: /Users/vinayakmenon/health-sync-app/release.jks
  store_password: <from earlier>
  key_alias: healthsync-key
  key_password: <from earlier>
  dry_run: true
```

Result:
- Builds AAB successfully
- Verifies signing
- Reports AAB size
- Confirms ready for deployment

**Step 9: First Deployment**

Claude Code instructs user:
> "Everything is configured! To deploy:
> 1. Commit and push your changes (build.gradle.kts, workflow file)
> 2. Go to GitHub Actions in your repository
> 3. Run the 'Deploy to Play Store internal' workflow manually
> 4. Monitor the workflow progress"

### 3.3 Expected Outcomes

After completing the workflow:

**Files Modified**:
- `app/build.gradle.kts`: Added signing config, enabled minification

**Files Created**:
- `.github/workflows/deploy-internal.yml`: GitHub Actions workflow
- `release.jks`: Keystore file (user backs up, not committed)

**GitHub Configuration**:
- 5 Secrets configured

**Google Play Console**:
- Service account created with permissions
- API enabled

**Ready for**:
- Manual workflow dispatch
- Automated internal track deployment

### 3.4 Troubleshooting with MCP Server

If issues arise, the MCP server helps debug:

**Build Failures**:
```
Tool: analyze_android_project
```
Re-analyzes to identify configuration issues.

**Signing Issues**:
```
Tool: test_deployment_workflow
```
Tests locally to isolate problem.

**API Access Issues**:
```
Tool: validate_play_store_setup
```
Verifies service account and permissions.

**GitHub Secrets Issues**:
```
Tool: validate_github_secrets
```
Checks which secrets are missing.

---

## Phase 4: Documentation and Maintenance

### 4.1 MCP Server Documentation

**README.md** should include:
1. Overview and purpose
2. Installation instructions
3. Claude Code configuration
4. Quick start guide
5. Tool reference
6. Examples
7. Troubleshooting
8. Contributing guidelines

**MCP-USAGE.md** (generated by mcp-server-generator):
- How to configure with Claude Code
- How to configure with other MCP clients
- Tool discovery
- Example conversations

### 4.2 Health Sync App Documentation

Create: `docs/play-store-deployment.md`

Contents:
- Overview of automated deployment
- Workflow trigger instructions
- How to add internal testers
- How to promote to other tracks
- Troubleshooting common issues
- Keystore backup procedures
- Rotating credentials

### 4.3 Maintenance Tasks

**MCP Server**:
- Monitor for Google Play API changes
- Update GitHub Actions versions
- Add new tools based on user feedback
- Maintain compatibility with MCP SDK updates

**Health Sync App**:
- Monitor workflow runs
- Update version codes before releases
- Rotate service account keys annually
- Test deployment process after major Android SDK updates

---

## Implementation Timeline

### Phase 1: MCP Server Development
**Estimated Time**: 2-3 weeks

- Week 1:
  - Generate project with mcp-server-generator (includes pypi-workflow-generator)
  - Create test Android project in `tests/fixtures/test-android-app/`
  - Implement tools 1-4 (analyze, keystore, signing, guide)
  - Write unit tests

- Week 2:
  - Implement tools 5-7 (workflow, secrets validation, secrets guide)
  - Write integration tests (using test Android project)
  - Verify test Android project builds

- Week 3:
  - Implement tools 8-9 (Play Store validation, test workflow)
  - End-to-end testing (complete workflow with test project)
  - Documentation
  - Verify all tests pass with test Android project

### Phase 2: PyPI Publishing
**Estimated Time**: 1 day (simplified by pypi-workflow-generator)

**Note**: Publishing workflow is auto-generated by mcp-server-generator via pypi-workflow-generator

- Initial manual publish (to create PyPI project):
  - Run final tests
  - Build package: `python -m build`
  - Upload to PyPI: `python -m twine upload dist/*`
  - Verify installation: `pip install mcp-android-playstore-deploy`

- Future releases (automated):
  - Update version in `pyproject.toml`
  - Create git tag: `git tag v0.x.x`
  - Create GitHub Release
  - GitHub Actions automatically publishes to PyPI

### Phase 3: Health Sync App Setup
**Estimated Time**: 1-2 days

- Day 1:
  - Install MCP server: `pip install mcp-android-playstore-deploy`
  - Configure in Claude Code
  - Run through guided setup
  - Generate keystore, signing config, workflow
  - Fix any issues

- Day 2:
  - Set up Google Play service account
  - Configure GitHub Secrets
  - Test first deployment
  - Verify on Play Console internal track
  - Document process

**Total Estimated Time**: 3-4 weeks (simplified Phase 2)

---

## Success Criteria

### Phase 1: MCP Server
- [ ] All 9 tools implemented and functional
- [ ] Unit tests passing (>80% coverage)
- [ ] Integration tests passing
- [ ] Documentation complete
- [ ] Works with Claude Code locally

### Phase 2: PyPI Publishing
- [ ] Package published to PyPI
- [ ] Installation works: `pip install mcp-android-playstore-deploy`
- [ ] Package metadata correct
- [ ] Documentation visible on PyPI

### Phase 3: Health Sync App
- [ ] Signing configuration added
- [ ] Code minification enabled
- [ ] GitHub Actions workflow created
- [ ] GitHub Secrets configured
- [ ] Service account set up
- [ ] First internal release deployed successfully
- [ ] App appears in Play Console internal track

---

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Google Play API changes | Low | High | Version pin, monitor API announcements |
| MCP SDK compatibility issues | Medium | Medium | Test with multiple MCP SDK versions |
| Keystore generation platform issues | Medium | Low | Test on Linux, macOS, Windows |
| GitHub API rate limiting | Low | Low | Implement retry logic, cache results |

### Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Tool implementations more complex than estimated | Medium | Medium | Start with core tools, iterate |
| Testing challenges with external APIs | High | Low | Use mocking, create test fixtures |
| Documentation takes longer than expected | Medium | Low | Write docs alongside implementation |

### Adoption Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Users find setup too complex | Low | Medium | Provide clear examples, troubleshooting |
| Tool outputs not useful to AI agents | Low | High | Test with Claude Code throughout |
| Missing features users need | Medium | Low | Gather feedback, iterate |

---

## Open Questions

### Before Implementation

1. **Author Email**: What email should be used for PyPI package?
   - Recommendation: Use GitHub noreply email or create project-specific email

2. **License**: Which license to use?
   - Recommendation: MIT (most permissive) or Apache 2.0 (includes patent protection)

3. **GitHub Repository**: Where to host the MCP server?
   - Recommendation: Create new repository: `mcp-android-playstore-deploy`

4. **Service Account Security**: How to handle service account JSON in test_deployment_workflow?
   - Recommendation: Accept file path, never log contents, clear from memory

5. **Cross-Platform Support**: Should we support Windows for keystore generation?
   - Recommendation: Yes, provide alternative commands in guides

### For Health Sync App

1. **Keystore Storage**: Where to back up the keystore?
   - Recommendation: Multiple secure locations (password manager, encrypted backup)

2. **Version Management**: Automated or manual version bumping?
   - Recommendation: Manual for now, can automate later

3. **Internal Testers**: Who should be added to internal testing?
   - User decision: Add email addresses in Play Console

---

## Specification Validation Results

This specification has been validated using the Gemini MCP Server validation tool.

### Validation Summary

**Initial Completeness Score**: 60%

**Critical Issues Identified and Addressed**:

1. **Security - Credential Handling** ✅ ADDRESSED
   - **Issue**: Specification lacked detail on secure credential management
   - **Severity**: Critical
   - **Resolution**: Added comprehensive Section 1.2 covering:
     - Credential sources (environment variables, secure stores)
     - Tool-specific security requirements
     - File permission validation
     - Logging security (credential sanitization)
     - Security testing requirements

2. **Error Handling for API Interactions** ✅ ADDRESSED
   - **Issue**: No specifications for handling external API failures
   - **Severity**: Medium
   - **Resolution**: Added comprehensive Section 1.3 covering:
     - GitHub API error handling patterns
     - Google Play API error handling patterns
     - File system error handling
     - System command error handling
     - Custom exception hierarchy
     - Consistent error response format

3. **Testing Strategy** ✅ ADDRESSED
   - **Issue**: Lacked detailed testing strategy for individual tools
   - **Severity**: Medium
   - **Resolution**: Added comprehensive Section 1.4 covering:
     - Unit tests for all 9 tools
     - Integration tests
     - End-to-end tests
     - Test coverage requirements (80-90%)
     - CI/CD testing with GitHub Actions
     - Cross-platform testing (Linux, macOS, Windows)

### Implementation Readiness

**Status**: ✅ **READY FOR IMPLEMENTATION**

All critical gaps have been addressed:
- [x] Security requirements fully specified
- [x] Error handling patterns defined
- [x] Testing strategy comprehensive
- [x] Tool specifications complete
- [x] Dependencies identified
- [x] PyPI publishing workflow defined
- [x] Usage workflow documented

### Quality Assurance Checklist

**Security**:
- [x] Credential handling specified for all tools
- [x] File permission validation required
- [x] Logging security requirements defined
- [x] Environment variable documentation included

**Error Handling**:
- [x] API error patterns defined
- [x] Network error handling specified
- [x] User-friendly error messages required
- [x] Recovery suggestions included

**Testing**:
- [x] Unit test requirements for all tools
- [x] Integration test scenarios defined
- [x] Coverage targets set (80-90%)
- [x] CI/CD pipeline specified

**Documentation**:
- [x] Tool specifications complete
- [x] Usage examples provided
- [x] Troubleshooting scenarios covered
- [x] Security best practices documented

### Patterns Alignment

**Matches Existing Patterns**: ✅ Yes
- Python project for Android tooling is sound architecture
- Does not conflict with Health Sync App structure (separate project)
- Follows MCP best practices

**No Conflicts Detected**

---

## Next Steps

### Immediate Actions

1. **Decide on project details**:
   - Confirm author email for PyPI
   - Choose license (MIT recommended)
   - Create GitHub repository

2. **Generate MCP server project**:
   - Use mcp-server-generator with tool specifications above
   - Note: PyPI publishing workflow will be auto-generated via pypi-workflow-generator
   - Review generated structure

3. **Create test Android project**:
   - Set up `tests/fixtures/test-android-app/`
   - Minimal native Android project with Kotlin
   - Ensure it builds successfully
   - Document in README

4. **Set up development environment**:
   - Install dependencies
   - Configure IDE/editor
   - Set up virtual environment
   - Verify test Android project builds

### Development Phases

**Phase 1 Start**: Implement MCP server
- Begin with core tools (analyze, keystore, signing)
- Test each tool independently
- Iterate based on testing

**Phase 2 Start**: Publish to PyPI
- Complete all tools and tests
- Test on TestPyPI
- Publish to PyPI

**Phase 3 Start**: Use for Health Sync App
- Install MCP server
- Configure with Claude Code
- Complete guided setup

---

## Conclusion

This implementation plan provides a comprehensive roadmap for:

1. **Creating** a reusable MCP server using mcp-server-generator (with pypi-workflow-generator integration)
2. **Publishing** the server to PyPI for community use (automated via generated workflows)
3. **Testing** with an included test Android project
4. **Using** the MCP server to set up Play Store deployment for Health Sync App

The approach is methodical, well-tested, and designed to create a high-quality tool that benefits the broader Android development community while solving your immediate need for automated Play Store deployment.

**Key Advantages**:
- Reusable for any Android project
- Reduces manual setup complexity
- Integrates seamlessly with Claude Code
- Follows MCP best practices
- Thoroughly documented
- **PyPI publishing automated** via pypi-workflow-generator
- **Self-contained testing** with included test Android project

**Key Updates from Original Spec**:
1. ✅ **PyPI Publishing Simplified**: mcp-server-generator uses pypi-workflow-generator, eliminating manual workflow setup
2. ✅ **Test Android Project Added**: Barebones project in `tests/fixtures/test-android-app/` for validating generated workflows and configs
3. ✅ **Phase 2 Shortened**: From 2-3 days to 1 day due to automated publishing workflow

**Ready to Proceed**: This specification is ready for implementation once project details (author email, repository location) are finalized.

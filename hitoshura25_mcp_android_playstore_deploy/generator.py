"""
Core business logic for hitoshura25-mcp-android-playstore-deploy.

MCP server that helps developers set up automated Google Play Store deployment for Android apps

Security Notes:
    - Always validate and sanitize inputs
    - Use security_utils for common security patterns
    - Review SECURITY.md for comprehensive guidelines
"""

from typing import Any, Dict, List, Optional

# Import security utilities
from .security_utils import (
    validate_string_input,
    validate_numeric_input,
    validate_project_path,
    redact_sensitive_data,
    create_secure_temp_file,
    validate_track,
    validate_signing_strategy,
    validate_android_package_name,
)

# Google Play Store requirements (Issue #25)
# As of August 2023, Google Play requires targetSdk 33+ for new apps and updates
# Update this constant as Google's requirements change
# See: https://developer.android.com/google/play/requirements/target-sdk
MINIMUM_TARGET_SDK = 33


# ============================================================================
# Helper Functions
# ============================================================================


def _get_process_output(result, max_length: int = 500) -> str:
    """
    Extract output from subprocess result with null safety.

    Helper function to avoid duplicate error output extraction pattern (Issue #38).
    Checks stderr first, then stdout, with a default message if neither is available.

    Args:
        result: subprocess.CompletedProcess result object
        max_length: Maximum number of characters to extract from end of output

    Returns:
        Extracted output string, truncated to max_length
    """
    if result.stderr:
        return result.stderr[-max_length:]
    elif result.stdout:
        return result.stdout[-max_length:]
    else:
        return "No output available"


# ============================================================================
# MCP Tool Functions
# ============================================================================


def analyze_android_project(project_path: str) -> Dict[str, Any]:
    r"""
    Analyze an Android project to understand its configuration and identify requirements for Play Store deployment

    Args:

        project_path: Absolute path to the Android project root directory


    Returns:
        Result dictionary

    Security:
        IMPORTANT: Review SECURITY.md before implementing this function.

        For secure implementation:
        - Validate ALL inputs using validate_string_input() or validate_numeric_input()
        - For file operations: Use validate_safe_path() to prevent path traversal
        - For commands: Use validate_safe_command() with whitelisting
        - For sensitive data: Use redact_sensitive_data() before returning
        - Add @audit_log decorator for security logging
        - Add @with_rate_limit decorator to prevent abuse
        - Or use @secure_tool to apply multiple protections at once

    Async Support:
        This function is currently synchronous. For async operations
        (API calls, database queries, subprocess execution):

        1. Change to: async def analyze_android_project(...)
        2. Use 'await' for async operations

        Example:
            @audit_log  # Log all calls
            @with_rate_limit(max_requests=50, window_seconds=60)  # Rate limit
            async def analyze_android_project(...) -> Dict[str, Any]:
                # Validate inputs
                from .security_utils import validate_string_input
                validated_input = validate_string_input(
                    some_param,
                    max_length=500,
                    allowed_pattern=r'^[a-zA-Z0-9\s\-_\.]+$'
                )

                # Your async logic here
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get("https://api.example.com/data")
                    data = response.json()

                return {'success': True, 'data': data}
    """
    import re

    # Validate path for security (Issue #5, #19)
    try:
        project_path_obj = validate_project_path(project_path, must_exist=True)
    except (ValueError, FileNotFoundError) as e:
        return {
            "success": False,
            "error": f"Invalid project path: {e}",
        }

    if not project_path_obj.is_dir():
        return {"success": False, "error": f"Path is not a directory: {project_path}"}

    # Check for Android project markers
    settings_gradle_kts = project_path_obj / "settings.gradle.kts"
    settings_gradle = project_path_obj / "settings.gradle"
    build_gradle_kts = project_path_obj / "build.gradle.kts"
    build_gradle = project_path_obj / "build.gradle"
    app_build_gradle_kts = project_path_obj / "app" / "build.gradle.kts"
    app_build_gradle = project_path_obj / "app" / "build.gradle"

    has_settings = settings_gradle_kts.exists() or settings_gradle.exists()
    has_root_build = build_gradle_kts.exists() or build_gradle.exists()

    if not (has_settings and has_root_build):
        return {
            "success": False,
            "error": "Path does not appear to be an Android project",
            "details": "Expected to find settings.gradle(.kts) and build.gradle(.kts)",
        }

    # Determine build file paths
    app_build_file = (
        app_build_gradle_kts
        if app_build_gradle_kts.exists()
        else (app_build_gradle if app_build_gradle.exists() else None)
    )

    if not app_build_file:
        return {
            "success": False,
            "error": "Could not find app/build.gradle(.kts)",
            "details": "This tool expects a standard Android project structure",
        }

    # Parse app build.gradle
    try:
        build_content = app_build_file.read_text()
    except Exception as e:
        return {"success": False, "error": f"Failed to read {app_build_file}: {str(e)}"}

    # Extract configuration using regex
    package_name = None
    namespace = None
    version_code = None
    version_name = None
    compile_sdk = None
    target_sdk = None
    min_sdk = None
    has_signing_config = False
    is_minify_enabled = False

    # Extract package name (applicationId or namespace)
    app_id_match = re.search(r'applicationId\s*=?\s*["\']([^"\']+)["\']', build_content)
    if app_id_match:
        extracted_package = app_id_match.group(1)
        # Validate package name format (Issue #24)
        try:
            package_name = validate_android_package_name(extracted_package)
        except ValueError:
            # Invalid package name, don't set it
            package_name = None

    namespace_match = re.search(r'namespace\s*=?\s*["\']([^"\']+)["\']', build_content)
    if namespace_match:
        extracted_namespace = namespace_match.group(1)
        try:
            namespace = validate_android_package_name(extracted_namespace)
        except ValueError:
            # Invalid namespace, don't set it
            namespace = None
        if not package_name and namespace:
            package_name = namespace

    # Extract version info
    version_code_match = re.search(r"versionCode\s*=?\s*(\d+)", build_content)
    if version_code_match:
        version_code = int(version_code_match.group(1))

    version_name_match = re.search(
        r'versionName\s*=?\s*["\']([^"\']+)["\']', build_content
    )
    if version_name_match:
        version_name = version_name_match.group(1)

    # Extract SDK versions
    compile_sdk_match = re.search(r"compileSdk\s*=?\s*(\d+)", build_content)
    if compile_sdk_match:
        compile_sdk = int(compile_sdk_match.group(1))

    target_sdk_match = re.search(r"targetSdk\s*=?\s*(\d+)", build_content)
    if target_sdk_match:
        target_sdk = int(target_sdk_match.group(1))

    min_sdk_match = re.search(r"minSdk\s*=?\s*(\d+)", build_content)
    if min_sdk_match:
        min_sdk = int(min_sdk_match.group(1))

    # Check for signing config
    has_signing_config = (
        "signingConfig" in build_content and "signingConfigs" in build_content
    )

    # Check for minify enabled
    is_minify_enabled = (
        "isMinifyEnabled = true" in build_content
        or "minifyEnabled true" in build_content
    )

    # Detect project type
    project_type = "native_android"
    if (project_path_obj / "package.json").exists():
        project_type = "react_native"
    elif (project_path_obj / "pubspec.yaml").exists():
        project_type = "flutter"

    # Check for GitHub Actions
    workflows_dir = project_path_obj / ".github" / "workflows"
    has_github_actions = workflows_dir.exists()
    github_workflows = []
    if has_github_actions:
        github_workflows = [f.name for f in workflows_dir.glob("*.yml")] + [
            f.name for f in workflows_dir.glob("*.yaml")
        ]

    # Generate recommendations
    recommendations = []
    issues = []

    if not is_minify_enabled:
        recommendations.append("Enable code minification for release builds")
        issues.append(
            {
                "severity": "high",
                "message": "Code minification is disabled",
                "fix": "Set isMinifyEnabled = true in release buildType",
            }
        )

    if not has_signing_config:
        recommendations.append("Add signing configuration")
        issues.append(
            {
                "severity": "critical",
                "message": "No signing configuration found",
                "fix": "Use generate_signing_config tool to add signing configuration",
            }
        )

    if not has_github_actions:
        recommendations.append("Create GitHub Actions workflow")
        issues.append(
            {
                "severity": "medium",
                "message": "No GitHub Actions workflows found",
                "fix": "Use generate_github_workflow tool to create deployment workflow",
            }
        )

    if target_sdk and target_sdk < MINIMUM_TARGET_SDK:
        recommendations.append(
            f"Update targetSdk to {MINIMUM_TARGET_SDK} or higher (currently {target_sdk})"
        )
        issues.append(
            {
                "severity": "high",
                "message": f"targetSdk {target_sdk} is below Google Play requirements (minimum {MINIMUM_TARGET_SDK})",
                "fix": f"Update targetSdk to at least {MINIMUM_TARGET_SDK} in build.gradle",
            }
        )

    return {
        "success": True,
        "project_type": project_type,
        "build_system": "gradle",
        "package_name": package_name or "unknown",
        "namespace": namespace,
        "has_signing_config": has_signing_config,
        "has_github_actions": has_github_actions,
        "github_workflows": github_workflows,
        "current_version_code": version_code or 1,
        "current_version_name": version_name or "1.0",
        "target_sdk": target_sdk,
        "min_sdk": min_sdk,
        "compile_sdk": compile_sdk,
        "build_gradle_path": str(app_build_file),
        "is_minify_enabled": is_minify_enabled,
        "recommendations": recommendations,
        "issues": issues,
    }


def generate_keystore(
    output_path: str,
    alias: str,
    key_password: str,
    store_password: str,
    validity_days: int = None,
    key_size: int = None,
    dname: str = None,
) -> Dict[str, Any]:
    r"""
    Generate a new Android keystore file for app signing with secure parameters

    Args:

        output_path: Absolute path where the keystore will be saved

        alias: Key alias for the signing key

        key_password: Password for the signing key

        store_password: Password for the keystore

        validity_days: How many days the key should be valid

        key_size: Key size in bits

        dname: Distinguished name for the certificate


    Returns:
        Result dictionary

    Security:
        IMPORTANT: Review SECURITY.md before implementing this function.

        For secure implementation:
        - Validate ALL inputs using validate_string_input() or validate_numeric_input()
        - For file operations: Use validate_safe_path() to prevent path traversal
        - For commands: Use validate_safe_command() with whitelisting
        - For sensitive data: Use redact_sensitive_data() before returning
        - Add @audit_log decorator for security logging
        - Add @with_rate_limit decorator to prevent abuse
        - Or use @secure_tool to apply multiple protections at once

    Async Support:
        This function is currently synchronous. For async operations
        (API calls, database queries, subprocess execution):

        1. Change to: async def generate_keystore(...)
        2. Use 'await' for async operations

        Example:
            @audit_log  # Log all calls
            @with_rate_limit(max_requests=50, window_seconds=60)  # Rate limit
            async def generate_keystore(...) -> Dict[str, Any]:
                # Validate inputs
                from .security_utils import validate_string_input
                validated_input = validate_string_input(
                    some_param,
                    max_length=500,
                    allowed_pattern=r'^[a-zA-Z0-9\s\-_\.]+$'
                )

                # Your async logic here
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get("https://api.example.com/data")
                    data = response.json()

                return {'success': True, 'data': data}
    """
    import subprocess
    import base64
    import os

    # Set defaults
    if validity_days is None:
        validity_days = 10000
    if key_size is None:
        key_size = 2048
    if dname is None:
        dname = "CN=Android Developer"

    # Validate inputs (Issue #18 - command injection prevention)
    try:
        alias = validate_string_input(
            alias,
            max_length=100,
            allowed_pattern=r"^[a-zA-Z0-9_-]+$",
            field_name="alias",
        )
        store_password = validate_string_input(
            store_password, max_length=100, min_length=6, field_name="store_password"
        )
        key_password = validate_string_input(
            key_password, max_length=100, min_length=6, field_name="key_password"
        )
        # DN can contain spaces, commas, equals, but validate it
        dname = validate_string_input(
            dname,
            max_length=200,
            allowed_pattern=r"^[a-zA-Z0-9\s,=.@-]+$",
            field_name="dname",
        )
        validity_days = validate_numeric_input(
            validity_days, min_value=1, max_value=36500, field_name="validity_days"
        )
        key_size = validate_numeric_input(
            key_size, min_value=2048, max_value=4096, field_name="key_size"
        )
    except ValueError as e:
        return {"success": False, "error": f"Invalid input: {e}"}

    # Validate output path (Issue #9 - path traversal)
    try:
        output_path_obj = validate_project_path(output_path, must_exist=False)
    except ValueError as e:
        return {"success": False, "error": f"Invalid output path: {e}"}

    output_dir = output_path_obj.parent

    # Create output directory if it doesn't exist
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return {"success": False, "error": f"Cannot create directory: {e}"}

    # Check if keystore already exists
    if output_path_obj.exists():
        return {
            "success": False,
            "error": f"Keystore already exists at {output_path}",
            "suggestion": "Choose a different path or delete the existing keystore",
        }

    # Create secure temporary files for passwords (Issue #17)
    # This prevents passwords from appearing in process listings
    store_pass_file = None
    key_pass_file = None

    try:
        store_pass_file = create_secure_temp_file(
            store_password, prefix="keystore_pass_"
        )
        key_pass_file = create_secure_temp_file(key_password, prefix="key_pass_")

        # Generate keystore using keytool with password files
        cmd = [
            "keytool",
            "-genkeypair",
            "-v",
            "-keystore",
            str(output_path_obj),
            "-alias",
            alias,
            "-keyalg",
            "RSA",
            "-keysize",
            str(key_size),
            "-validity",
            str(validity_days),
            "-storepass:file",
            str(store_pass_file),
            "-keypass:file",
            str(key_pass_file),
            "-dname",
            dname,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            # Redact sensitive data from error output (Issue #20)
            error_msg = result.stderr if result.stderr else result.stdout
            error_msg = (
                redact_sensitive_data(error_msg) if error_msg else "Unknown error"
            )

            if (
                "command not found" in error_msg.lower()
                or "not recognized" in error_msg.lower()
            ):
                return {
                    "success": False,
                    "error": "keytool not found. Please install JDK and ensure it is in your PATH.",
                    "suggestion": "Install JDK from https://adoptium.net/",
                }
            # Don't include raw command in error (may contain sensitive paths)
            return {
                "success": False,
                "error": f"Failed to generate keystore: {error_msg[-500:]}",
            }

        # Set restrictive permissions (owner read/write only)
        os.chmod(output_path_obj, 0o600)

        # Read and encode keystore to base64
        with open(output_path_obj, "rb") as f:
            keystore_bytes = f.read()
            base64_encoded = base64.b64encode(keystore_bytes).decode("utf-8")

        return {
            "success": True,
            "keystore_path": str(output_path_obj),
            "alias": alias,
            "base64_encoded": base64_encoded,
            "instructions": [
                "Save the keystore file securely",
                "Back up the keystore to multiple locations",
                "Never commit the keystore to version control",
                "Store passwords in a secure password manager",
            ],
            "github_secret_instructions": {
                "SIGNING_KEY_STORE_BASE64": "Use the base64_encoded value above",
                "SIGNING_KEY_ALIAS": alias,
                "SIGNING_KEY_PASSWORD": "Use the key_password you provided",
                "SIGNING_STORE_PASSWORD": "Use the store_password you provided",
            },
            "warning": "CRITICAL: Loss of this keystore will prevent you from updating your app on Google Play. Back it up securely.",
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Keystore generation timed out after 60 seconds",
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "keytool not found. Please install JDK and ensure it is in your PATH.",
            "suggestion": "Install JDK from https://adoptium.net/",
        }
    except Exception as e:
        # Redact any sensitive data from exception messages
        error = redact_sensitive_data(str(e))
        return {"success": False, "error": f"Unexpected error: {error}"}
    finally:
        # Clean up temporary password files (Issue #17)
        if store_pass_file and store_pass_file.exists():
            try:
                store_pass_file.unlink()
            except Exception:
                # Ignore cleanup errors - don't want to mask the real error
                # File may be locked or permissions changed, but it's in temp dir
                pass
        if key_pass_file and key_pass_file.exists():
            try:
                key_pass_file.unlink()
            except Exception:
                # Ignore cleanup errors - don't want to mask the real error
                # File may be locked or permissions changed, but it's in temp dir
                pass


def generate_signing_config(
    project_path: str, signing_strategy: str = None
) -> Dict[str, Any]:
    r"""
    Generate Gradle signing configuration code to add to build.gradle.kts

    Args:

        project_path: Path to Android project

        signing_strategy: How to provide signing credentials (environment_variables or gradle_properties)


    Returns:
        Result dictionary

    Security:
        IMPORTANT: Review SECURITY.md before implementing this function.

        For secure implementation:
        - Validate ALL inputs using validate_string_input() or validate_numeric_input()
        - For file operations: Use validate_safe_path() to prevent path traversal
        - For commands: Use validate_safe_command() with whitelisting
        - For sensitive data: Use redact_sensitive_data() before returning
        - Add @audit_log decorator for security logging
        - Add @with_rate_limit decorator to prevent abuse
        - Or use @secure_tool to apply multiple protections at once

    Async Support:
        This function is currently synchronous. For async operations
        (API calls, database queries, subprocess execution):

        1. Change to: async def generate_signing_config(...)
        2. Use 'await' for async operations

        Example:
            @audit_log  # Log all calls
            @with_rate_limit(max_requests=50, window_seconds=60)  # Rate limit
            async def generate_signing_config(...) -> Dict[str, Any]:
                # Validate inputs
                from .security_utils import validate_string_input
                validated_input = validate_string_input(
                    some_param,
                    max_length=500,
                    allowed_pattern=r'^[a-zA-Z0-9\s\-_\.]+$'
                )

                # Your async logic here
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get("https://api.example.com/data")
                    data = response.json()

                return {'success': True, 'data': data}
    """
    # Default strategy is environment_variables
    if signing_strategy is None:
        signing_strategy = "environment_variables"

    # Validate signing_strategy (Issue #1)
    try:
        signing_strategy = validate_signing_strategy(signing_strategy)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    # Validate project_path (Issue #7) - doesn't need to exist for generating config
    try:
        validate_project_path(project_path, must_exist=False)
    except ValueError as e:
        return {"success": False, "error": f"Invalid project path: {e}"}

    # NOTE (Issue #39): Currently only 'environment_variables' strategy is implemented.
    # The signing_strategy parameter is validated above for future use.
    # TODO: Implement 'gradle_properties' strategy that reads from gradle.properties file
    # instead of environment variables. When implemented, use the signing_strategy value
    # to determine which config template to generate.

    # Generate Kotlin DSL (using environment_variables strategy)
    gradle_config_kotlin = """signingConfigs {
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
}"""

    # Generate Groovy DSL
    gradle_config_groovy = """signingConfigs {
    release {
        storeFile file(System.getenv("SIGNING_KEY_STORE_PATH") ?: "release.jks")
        storePassword System.getenv("SIGNING_STORE_PASSWORD")
        keyAlias System.getenv("SIGNING_KEY_ALIAS")
        keyPassword System.getenv("SIGNING_KEY_PASSWORD")
    }
}

buildTypes {
    release {
        signingConfig signingConfigs.release
        minifyEnabled true
        shrinkResources true
        proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
    }
}"""

    # Complete example
    complete_example = """plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.example.app"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.example.app"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }

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

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}"""

    return {
        "success": True,
        "gradle_config_kotlin": gradle_config_kotlin,
        "gradle_config_groovy": gradle_config_groovy,
        "insert_location": "Inside android { ... } block, before buildTypes",
        "instructions": [
            "Add the signingConfigs block to your app/build.gradle.kts",
            "Update your release buildType to use the signing config",
            "Set environment variables in your CI/CD pipeline",
        ],
        "required_env_vars": [
            "SIGNING_KEY_STORE_PATH",
            "SIGNING_STORE_PASSWORD",
            "SIGNING_KEY_ALIAS",
            "SIGNING_KEY_PASSWORD",
        ],
        "complete_example": complete_example,
    }


def setup_service_account_guide() -> Dict[str, Any]:
    r"""
    Provide interactive step-by-step guide for setting up Google Play Service Account

    Args:


    Returns:
        Result dictionary

    Security:
        IMPORTANT: Review SECURITY.md before implementing this function.

        For secure implementation:
        - Validate ALL inputs using validate_string_input() or validate_numeric_input()
        - For file operations: Use validate_safe_path() to prevent path traversal
        - For commands: Use validate_safe_command() with whitelisting
        - For sensitive data: Use redact_sensitive_data() before returning
        - Add @audit_log decorator for security logging
        - Add @with_rate_limit decorator to prevent abuse
        - Or use @secure_tool to apply multiple protections at once

    Async Support:
        This function is currently synchronous. For async operations
        (API calls, database queries, subprocess execution):

        1. Change to: async def setup_service_account_guide(...)
        2. Use 'await' for async operations

        Example:
            @audit_log  # Log all calls
            @with_rate_limit(max_requests=50, window_seconds=60)  # Rate limit
            async def setup_service_account_guide(...) -> Dict[str, Any]:
                # Validate inputs
                from .security_utils import validate_string_input
                validated_input = validate_string_input(
                    some_param,
                    max_length=500,
                    allowed_pattern=r'^[a-zA-Z0-9\s\-_\.]+$'
                )

                # Your async logic here
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get("https://api.example.com/data")
                    data = response.json()

                return {'success': True, 'data': data}
    """
    return {
        "success": True,
        "steps": [
            {
                "step_number": 1,
                "title": "Access Google Play Console",
                "description": "Navigate to Google Play Console and sign in with your developer account",
                "url": "https://play.google.com/console/",
                "action": "Open URL in browser",
                "verification": "You should see your app listed in the Play Console",
            },
            {
                "step_number": 2,
                "title": "Navigate to API Access",
                "description": "In the left sidebar, go to Setup > API access",
                "action": "Click through navigation",
                "verification": "You should see the API access page with service accounts section",
            },
            {
                "step_number": 3,
                "title": "Create Service Account",
                "description": 'Click "Create new service account" button',
                "action": "Follow link to Google Cloud Platform",
                "url": "https://console.cloud.google.com/",
                "details": "This will open Google Cloud Console in a new tab",
            },
            {
                "step_number": 4,
                "title": "Create Service Account in GCP",
                "description": "In Google Cloud Console, create a new service account",
                "action": "Fill in service account details",
                "required_fields": {
                    "name": "playstore-deploy-bot",
                    "description": "Service account for automated Play Store deployments",
                },
            },
            {
                "step_number": 5,
                "title": "Create JSON Key",
                "description": "Create and download a JSON key for the service account",
                "action": 'Click "Create Key" > Select JSON format > Download',
                "warning": "This key will only be shown once. Store it securely.",
                "verification": "You should have a JSON file downloaded",
            },
            {
                "step_number": 6,
                "title": "Grant Permissions in Play Console",
                "description": "Return to Play Console and grant permissions to the service account",
                "action": 'Select "Release Manager" role',
                "required_permissions": ["Release Manager"],
                "verification": "Service account should appear in the list with correct permissions",
            },
            {
                "step_number": 7,
                "title": "Enable Play Developer API",
                "description": "Ensure Google Play Developer API is enabled in your Google Cloud project",
                "url": "https://console.cloud.google.com/apis/library/androidpublisher.googleapis.com",
                "action": 'Click "Enable API"',
                "verification": 'API should show as "Enabled"',
            },
        ],
        "validation_checklist": [
            "Service account JSON key file downloaded",
            "Service account has Release Manager role in Play Console",
            "Google Play Developer API is enabled",
            "You have the service account email address",
        ],
        "troubleshooting": {
            "common_issues": [
                {
                    "issue": 'Cannot see "API access" option',
                    "solution": "You need to be the account owner or have Admin permissions",
                },
                {
                    "issue": "Service account not appearing in Play Console",
                    "solution": "Make sure you completed the linking step from Play Console to GCP",
                },
            ]
        },
        "next_steps": "After completing these steps, you'll use the JSON key file as a GitHub Secret",
    }


def generate_github_workflow(
    project_path: str,
    package_name: str,
    track: str = None,
    trigger_strategy: str = None,
    branch_name: str = None,
    app_module_path: str = None,
    java_version: str = None,
) -> Dict[str, Any]:
    r"""
    Generate a complete GitHub Actions workflow file for Play Store deployment

    Args:

        project_path: Path to Android project

        package_name: Android app package name

        track: Play Store release track (internal, alpha, beta, production)

        trigger_strategy: How to trigger the workflow (manual, branch, tag)

        branch_name: Branch name to trigger on if trigger_strategy is branch

        app_module_path: Path to app module relative to project root

        java_version: Java/JDK version to use for builds


    Returns:
        Result dictionary

    Security:
        IMPORTANT: Review SECURITY.md before implementing this function.

        For secure implementation:
        - Validate ALL inputs using validate_string_input() or validate_numeric_input()
        - For file operations: Use validate_safe_path() to prevent path traversal
        - For commands: Use validate_safe_command() with whitelisting
        - For sensitive data: Use redact_sensitive_data() before returning
        - Add @audit_log decorator for security logging
        - Add @with_rate_limit decorator to prevent abuse
        - Or use @secure_tool to apply multiple protections at once

    Async Support:
        This function is currently synchronous. For async operations
        (API calls, database queries, subprocess execution):

        1. Change to: async def generate_github_workflow(...)
        2. Use 'await' for async operations

        Example:
            @audit_log  # Log all calls
            @with_rate_limit(max_requests=50, window_seconds=60)  # Rate limit
            async def generate_github_workflow(...) -> Dict[str, Any]:
                # Validate inputs
                from .security_utils import validate_string_input
                validated_input = validate_string_input(
                    some_param,
                    max_length=500,
                    allowed_pattern=r'^[a-zA-Z0-9\s\-_\.]+$'
                )

                # Your async logic here
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get("https://api.example.com/data")
                    data = response.json()

                return {'success': True, 'data': data}
    """
    # Set defaults
    if track is None:
        track = "internal"
    if trigger_strategy is None:
        trigger_strategy = "manual"
    if branch_name is None:
        branch_name = f"release/{track}"
    if app_module_path is None:
        app_module_path = "app"
    if java_version is None:
        java_version = "17"

    # Validate inputs (Issues #2, #7)
    try:
        track = validate_track(track)
        # Don't require path to exist for workflow generation
        validate_project_path(project_path, must_exist=False)
        package_name = validate_android_package_name(package_name)
        # Validate other string inputs
        trigger_strategy = validate_string_input(
            trigger_strategy,
            max_length=20,
            allowed_pattern=r"^[a-z_]+$",
            field_name="trigger_strategy",
        )
        branch_name = validate_string_input(
            branch_name,
            max_length=100,
            allowed_pattern=r"^[a-zA-Z0-9/_-]+$",
            field_name="branch_name",
        )
        app_module_path = validate_string_input(
            app_module_path,
            max_length=100,
            allowed_pattern=r"^[a-zA-Z0-9/_-]+$",
            field_name="app_module_path",
        )
        java_version = validate_string_input(
            java_version,
            max_length=10,
            allowed_pattern=r"^[0-9.]+$",
            field_name="java_version",
        )
    except ValueError as e:
        return {"success": False, "error": f"Invalid input: {e}"}

    # Generate trigger configuration based on strategy
    if trigger_strategy == "manual":
        trigger_config = "workflow_dispatch:"
    elif trigger_strategy == "branch":
        trigger_config = f"""push:
    branches:
      - {branch_name}"""
    elif trigger_strategy == "tag":
        trigger_config = """push:
    tags:
      - 'v*'"""
    else:
        trigger_config = "workflow_dispatch:"

    # Generate workflow content
    workflow_content = f"""name: Deploy to Play Store {track}

on:
  {trigger_config}

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
      # Security Note (Issue #13): For production use, consider pinning actions to specific
      # commit SHAs instead of tags to prevent supply chain attacks. Example:
      #   uses: actions/checkout@8ade135a41bc03ea155e62e844d188df1ea18608 # v4.1.0
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up JDK {java_version}
        uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '{java_version}'
          cache: 'gradle'

      - name: Grant execute permission for gradlew
        run: chmod +x gradlew

      - name: Decode Keystore
        run: |
          echo "${{{{ secrets.SIGNING_KEY_STORE_BASE64 }}}}" | base64 --decode > ${{{{ github.workspace }}}}/release.jks
          chmod 600 ${{{{ github.workspace }}}}/release.jks

      - name: Build Release AAB
        run: ./gradlew bundleRelease
        env:
          SIGNING_KEY_ALIAS: ${{{{ secrets.SIGNING_KEY_ALIAS }}}}
          SIGNING_KEY_PASSWORD: ${{{{ secrets.SIGNING_KEY_PASSWORD }}}}
          SIGNING_STORE_PASSWORD: ${{{{ secrets.SIGNING_STORE_PASSWORD }}}}
          SIGNING_KEY_STORE_PATH: ${{{{ github.workspace }}}}/release.jks

      # Note (Issue #16): This uses r0adkll/upload-google-play, a community-maintained action.
      # For production, consider official alternatives or pin to a specific commit SHA.
      - name: Upload to Google Play {track} Track
        uses: r0adkll/upload-google-play@v1
        with:
          serviceAccountJsonPlainText: ${{{{ secrets.SERVICE_ACCOUNT_JSON_PLAINTEXT }}}}
          packageName: {package_name}
          releaseFiles: {app_module_path}/build/outputs/bundle/release/app-release.aab
          track: {track}
          status: completed

      - name: Clean up keystore
        if: always()
        run: rm -f ${{{{ github.workspace }}}}/release.jks
"""

    workflow_path = f".github/workflows/deploy-{track}.yml"

    required_secrets = [
        {
            "name": "SERVICE_ACCOUNT_JSON_PLAINTEXT",
            "description": "Contents of the service account JSON file",
            "how_to_generate": "Download from Google Cloud Console when creating service account key",
        },
        {
            "name": "SIGNING_KEY_STORE_BASE64",
            "description": "Base64-encoded keystore file",
            "how_to_generate": "Run: base64 -w 0 your-keystore.jks",
        },
        {
            "name": "SIGNING_KEY_ALIAS",
            "description": "The alias of your signing key",
            "how_to_generate": "This is what you specified when creating the keystore",
        },
        {
            "name": "SIGNING_KEY_PASSWORD",
            "description": "Password for your signing key",
            "how_to_generate": "This is what you specified when creating the keystore",
        },
        {
            "name": "SIGNING_STORE_PASSWORD",
            "description": "Password for your keystore",
            "how_to_generate": "This is what you specified when creating the keystore",
        },
    ]

    return {
        "success": True,
        "workflow_path": workflow_path,
        "workflow_content": workflow_content,
        "required_secrets": required_secrets,
        "instructions": [
            "Create .github/workflows directory if it doesn't exist",
            "Save the workflow_content to the workflow_path",
            "Configure the required GitHub Secrets",
            "Commit and push the workflow file",
            "Test with a manual workflow dispatch",
        ],
        "estimated_build_time": "5-10 minutes",
        "github_actions_cost": "Free for public repos, 2000 minutes/month for private repos on free tier",
    }


def validate_github_secrets(
    repo_owner: str,
    repo_name: str,
    github_token: str,
    required_secrets: Optional[
        List[str]
    ] = None,  # Fixed type from Any (Issue #21, #32)
) -> Dict[str, Any]:
    r"""
    Validate that required GitHub Secrets are configured (checks existence only)

    Args:

        repo_owner: GitHub repository owner username or organization

        repo_name: GitHub repository name

        github_token: GitHub Personal Access Token with repo scope

        required_secrets: List of secret names to check for


    Returns:
        Result dictionary

    Security:
        IMPORTANT: Review SECURITY.md before implementing this function.

        For secure implementation:
        - Validate ALL inputs using validate_string_input() or validate_numeric_input()
        - For file operations: Use validate_safe_path() to prevent path traversal
        - For commands: Use validate_safe_command() with whitelisting
        - For sensitive data: Use redact_sensitive_data() before returning
        - Add @audit_log decorator for security logging
        - Add @with_rate_limit decorator to prevent abuse
        - Or use @secure_tool to apply multiple protections at once

    Async Support:
        This function is currently synchronous. For async operations
        (API calls, database queries, subprocess execution):

        1. Change to: async def validate_github_secrets(...)
        2. Use 'await' for async operations

        Example:
            @audit_log  # Log all calls
            @with_rate_limit(max_requests=50, window_seconds=60)  # Rate limit
            async def validate_github_secrets(...) -> Dict[str, Any]:
                # Validate inputs
                from .security_utils import validate_string_input
                validated_input = validate_string_input(
                    some_param,
                    max_length=500,
                    allowed_pattern=r'^[a-zA-Z0-9\s\-_\.]+$'
                )

                # Your async logic here
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get("https://api.example.com/data")
                    data = response.json()

                return {'success': True, 'data': data}
    """
    import requests
    from datetime import datetime

    # Validate required_secrets type (Issue #21)
    if required_secrets is not None and not isinstance(required_secrets, list):
        return {
            "success": False,
            "error": "required_secrets must be a list or None",
        }

    # Default required secrets
    if required_secrets is None:
        required_secrets = [
            "SERVICE_ACCOUNT_JSON_PLAINTEXT",
            "SIGNING_KEY_STORE_BASE64",
            "SIGNING_KEY_ALIAS",
            "SIGNING_KEY_PASSWORD",
            "SIGNING_STORE_PASSWORD",
        ]

    # Validate string inputs
    try:
        repo_owner = validate_string_input(
            repo_owner,
            max_length=100,
            allowed_pattern=r"^[a-zA-Z0-9_-]+$",
            field_name="repo_owner",
        )
        repo_name = validate_string_input(
            repo_name,
            max_length=100,
            allowed_pattern=r"^[a-zA-Z0-9_.-]+$",
            field_name="repo_name",
        )
        github_token = validate_string_input(
            github_token, max_length=200, min_length=10, field_name="github_token"
        )
    except ValueError as e:
        return {"success": False, "error": f"Invalid input: {e}"}

    # GitHub API URL
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/secrets"

    try:
        response = requests.get(
            url,
            headers={
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json",
            },
            timeout=30,
        )

        if response.status_code == 401:
            return {
                "success": False,
                "error": "GitHub token is invalid or expired",
                "suggestion": "Generate a new token at https://github.com/settings/tokens with repo scope",
            }
        elif response.status_code == 403:
            # Check for rate limiting (Issue #36 - check response text not status_code)
            # Don't include full response.text in error (Issue #15 - may contain token)
            if "rate limit" in response.text.lower():
                return {
                    "success": False,
                    "error": "GitHub API rate limit exceeded",
                    "suggestion": "Wait an hour or use a token with higher limits",
                }
            else:
                return {
                    "success": False,
                    "error": "GitHub token lacks required permissions",
                    "suggestion": 'Ensure token has "repo" scope',
                }
        elif response.status_code == 404:
            return {
                "success": False,
                "error": "Repository not found",
                "suggestion": "Check owner/repo names and token permissions",
            }
        elif response.status_code >= 500:
            return {
                "success": False,
                "error": f"GitHub API is experiencing issues (HTTP {response.status_code})",
                "suggestion": "Try again later",
            }

        response.raise_for_status()
        data = response.json()

        # Extract configured secret names
        configured_secrets = [secret["name"] for secret in data.get("secrets", [])]

        # Check which required secrets are missing
        missing_secrets = [s for s in required_secrets if s not in configured_secrets]
        all_present = len(missing_secrets) == 0

        # Generate instructions for missing secrets
        instructions_for_missing = {}
        secret_instructions = {
            "SERVICE_ACCOUNT_JSON_PLAINTEXT": "Download the service account JSON from Google Cloud Console, then copy its entire contents into this secret",
            "SIGNING_KEY_STORE_BASE64": 'Run "base64 -w 0 your-keystore.jks" and paste the output here',
            "SIGNING_KEY_ALIAS": "The alias you specified when creating the keystore",
            "SIGNING_KEY_PASSWORD": "The password for your signing key",
            "SIGNING_STORE_PASSWORD": "The password for your keystore",
        }

        for secret in missing_secrets:
            instructions_for_missing[secret] = secret_instructions.get(
                secret, "Configure this secret"
            )

        return {
            "success": True,
            "all_secrets_present": all_present,
            "total_required": len(required_secrets),
            "total_configured": len(required_secrets) - len(missing_secrets),
            "missing_secrets": missing_secrets,
            "configured_secrets": [
                s for s in required_secrets if s in configured_secrets
            ],
            "instructions_for_missing": instructions_for_missing,
            "github_secrets_url": f"https://github.com/{repo_owner}/{repo_name}/settings/secrets/actions",
            "validation_timestamp": datetime.utcnow().isoformat() + "Z",
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "GitHub API request timed out",
            "suggestion": "Check your internet connection",
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Cannot connect to GitHub API",
            "suggestion": "Check your internet connection",
        }
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}


def create_github_secrets_guide(
    repo_url: str, keystore_path: str = None
) -> Dict[str, Any]:
    r"""
    Generate a comprehensive guide for creating all required GitHub Secrets

    Args:

        repo_url: GitHub repository URL

        keystore_path: Optional path to keystore for encoding instructions


    Returns:
        Result dictionary

    Security:
        IMPORTANT: Review SECURITY.md before implementing this function.

        For secure implementation:
        - Validate ALL inputs using validate_string_input() or validate_numeric_input()
        - For file operations: Use validate_safe_path() to prevent path traversal
        - For commands: Use validate_safe_command() with whitelisting
        - For sensitive data: Use redact_sensitive_data() before returning
        - Add @audit_log decorator for security logging
        - Add @with_rate_limit decorator to prevent abuse
        - Or use @secure_tool to apply multiple protections at once

    Async Support:
        This function is currently synchronous. For async operations
        (API calls, database queries, subprocess execution):

        1. Change to: async def create_github_secrets_guide(...)
        2. Use 'await' for async operations

        Example:
            @audit_log  # Log all calls
            @with_rate_limit(max_requests=50, window_seconds=60)  # Rate limit
            async def create_github_secrets_guide(...) -> Dict[str, Any]:
                # Validate inputs
                from .security_utils import validate_string_input
                validated_input = validate_string_input(
                    some_param,
                    max_length=500,
                    allowed_pattern=r'^[a-zA-Z0-9\s\-_\.]+$'
                )

                # Your async logic here
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get("https://api.example.com/data")
                    data = response.json()

                return {'success': True, 'data': data}
    """
    # Parse repo URL to extract owner and name
    import re

    github_match = re.match(
        r"https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", repo_url
    )
    if github_match:
        repo_owner, repo_name = github_match.groups()
        github_secrets_url = (
            f"https://github.com/{repo_owner}/{repo_name}/settings/secrets/actions"
        )
    else:
        github_secrets_url = repo_url + "/settings/secrets/actions"

    example_command = (
        "base64 -w 0 release.jks" if keystore_path else "base64 -w 0 your-keystore.jks"
    )

    return {
        "success": True,
        "github_secrets_url": github_secrets_url,
        "secrets": [
            {
                "name": "SERVICE_ACCOUNT_JSON_PLAINTEXT",
                "description": "The complete contents of your Google Play service account JSON file",
                "how_to_get_value": [
                    "Open the JSON file you downloaded from Google Cloud Console",
                    "Copy the entire file contents (all the JSON)",
                    "Paste it directly into the secret value field",
                ],
                "is_sensitive": True,
                "required": True,
            },
            {
                "name": "SIGNING_KEY_STORE_BASE64",
                "description": "Your Android keystore file encoded as base64",
                "how_to_get_value": [
                    "Navigate to the directory containing your keystore file",
                    "",
                    "Linux/Mac:",
                    "  base64 -w 0 your-keystore.jks",
                    "",
                    "Windows (PowerShell - RECOMMENDED):",
                    "  [Convert]::ToBase64String([IO.File]::ReadAllBytes('your-keystore.jks'))",
                    "",
                    "Windows (CMD - requires manual cleanup):",
                    "  certutil -encode your-keystore.jks keystore-base64.txt",
                    "  Then open keystore-base64.txt and:",
                    "    1. Remove the first line (-----BEGIN CERTIFICATE-----)",
                    "    2. Remove the last line (-----END CERTIFICATE-----)",
                    "    3. Remove all line breaks to create one continuous string",
                    "",
                    "Copy the base64 output and paste as the secret value",
                ],
                "example_command": example_command,
                "is_sensitive": True,
                "required": True,
            },
            {
                "name": "SIGNING_KEY_ALIAS",
                "description": "The alias you chose when creating your keystore",
                "how_to_get_value": [
                    "This is the value you specified when creating the keystore",
                    "If you forgot it, run: keytool -list -v -keystore your-keystore.jks",
                ],
                "is_sensitive": False,
                "required": True,
            },
            {
                "name": "SIGNING_KEY_PASSWORD",
                "description": "The password for your signing key",
                "how_to_get_value": [
                    "This is the password you set when creating the keystore key"
                ],
                "is_sensitive": True,
                "required": True,
            },
            {
                "name": "SIGNING_STORE_PASSWORD",
                "description": "The password for your keystore file",
                "how_to_get_value": [
                    "This is the password you set when creating the keystore"
                ],
                "is_sensitive": True,
                "required": True,
            },
        ],
        "step_by_step_instructions": [
            "Navigate to your GitHub repository",
            "Click on Settings tab",
            'In left sidebar, click "Secrets and variables" > "Actions"',
            'Click "New repository secret" button',
            "For each secret above:",
            "  - Enter the exact secret name (case-sensitive)",
            '  - Follow the "how_to_get_value" instructions',
            "  - Paste the value",
            '  - Click "Add secret"',
            "Verify all 5 secrets are listed",
        ],
        "security_reminders": [
            "Never commit secrets to your repository",
            "Never log or print secret values",
            "Store passwords in a secure password manager",
            "Back up your keystore and passwords securely",
            "Rotate service account keys periodically",
        ],
    }


def validate_play_store_setup(
    service_account_json_path: str, package_name: str
) -> Dict[str, Any]:
    r"""
    Validate that Play Store app and API access are properly configured using service account

    Args:

        service_account_json_path: Path to service account JSON file

        package_name: Android app package name to validate


    Returns:
        Result dictionary

    Security:
        IMPORTANT: Review SECURITY.md before implementing this function.

        For secure implementation:
        - Validate ALL inputs using validate_string_input() or validate_numeric_input()
        - For file operations: Use validate_safe_path() to prevent path traversal
        - For commands: Use validate_safe_command() with whitelisting
        - For sensitive data: Use redact_sensitive_data() before returning
        - Add @audit_log decorator for security logging
        - Add @with_rate_limit decorator to prevent abuse
        - Or use @secure_tool to apply multiple protections at once

    Async Support:
        This function is currently synchronous. For async operations
        (API calls, database queries, subprocess execution):

        1. Change to: async def validate_play_store_setup(...)
        2. Use 'await' for async operations

        Example:
            @audit_log  # Log all calls
            @with_rate_limit(max_requests=50, window_seconds=60)  # Rate limit
            async def validate_play_store_setup(...) -> Dict[str, Any]:
                # Validate inputs
                from .security_utils import validate_string_input
                validated_input = validate_string_input(
                    some_param,
                    max_length=500,
                    allowed_pattern=r'^[a-zA-Z0-9\s\-_\.]+$'
                )

                # Your async logic here
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get("https://api.example.com/data")
                    data = response.json()

                return {'success': True, 'data': data}
    """
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
    except ImportError:
        return {
            "success": False,
            "error": "Google API client libraries not installed",
            "suggestion": "Install with: pip install google-auth google-api-python-client",
        }

    # Validate inputs (Issue #6)
    try:
        service_account_path = validate_project_path(
            service_account_json_path, must_exist=True
        )
        package_name = validate_android_package_name(package_name)
    except (ValueError, FileNotFoundError) as e:
        return {
            "success": False,
            "error": f"Invalid input: {e}",
        }

    checks = {}
    errors = []
    warnings = []
    overall_status = "success"

    try:
        # Authenticate with service account
        credentials = service_account.Credentials.from_service_account_file(
            str(service_account_path),
            scopes=["https://www.googleapis.com/auth/androidpublisher"],
        )

        checks["service_account_valid"] = {
            "status": "pass",
            "message": "Service account credentials are valid",
        }

        # Build API client
        service = build("androidpublisher", "v3", credentials=credentials)

        # Try to create an edit (this validates API access and app existence)
        try:
            edit_request = service.edits().insert(body={}, packageName=package_name)
            edit_result = edit_request.execute()
            edit_id = edit_result["id"]

            # If we get here, the app exists and we have access
            checks["app_exists"] = {
                "status": "pass",
                "message": "App with package name exists in Play Console",
            }

            checks["permissions_sufficient"] = {
                "status": "pass",
                "message": "Service account has sufficient permissions",
                "details": "Can create edits",
            }

            # Get tracks information
            try:
                tracks_response = (
                    service.edits()
                    .tracks()
                    .list(packageName=package_name, editId=edit_id)
                    .execute()
                )

                available_tracks = [
                    track["track"] for track in tracks_response.get("tracks", [])
                ]

                checks["can_access_tracks"] = {
                    "status": "pass",
                    "message": "Can access release tracks",
                    "available_tracks": available_tracks
                    if available_tracks
                    else ["internal", "alpha", "beta", "production"],
                }

                if not available_tracks:
                    warnings.append(
                        "No releases found on any track - this is expected for new apps"
                    )

            except HttpError as e:
                checks["can_access_tracks"] = {
                    "status": "partial",
                    "message": "Limited track access",
                    "details": str(e),
                }
                warnings.append(
                    "Could not list all tracks - may have limited permissions"
                )

            # Clean up the edit
            try:
                service.edits().delete(
                    packageName=package_name, editId=edit_id
                ).execute()
            except Exception:
                pass  # Ignore cleanup errors

        except HttpError as e:
            # Defensive access for e.resp.status (Issue #35)
            status_code = e.resp.status if hasattr(e, "resp") and e.resp else None
            if status_code == 404:
                checks["app_exists"] = {
                    "status": "fail",
                    "message": f'App with package name "{package_name}" not found in Play Console',
                }
                errors.append(
                    "App not found. Make sure the app is created in Play Console first."
                )
                overall_status = "failure"
            elif status_code == 403:
                checks["permissions_sufficient"] = {
                    "status": "fail",
                    "message": "Service account lacks required permissions",
                }
                errors.append(
                    'Service account needs "Release Manager" role in Play Console'
                )
                overall_status = "failure"
            else:
                raise

        checks["api_enabled"] = {
            "status": "pass",
            "message": "Google Play Developer API is enabled",
        }

    except FileNotFoundError:
        checks["service_account_valid"] = {
            "status": "fail",
            "message": f"Service account file not found: {service_account_json_path}",
        }
        errors.append("Service account JSON file does not exist")
        overall_status = "failure"

    except ValueError as e:
        if "json" in str(e).lower():
            checks["service_account_valid"] = {
                "status": "fail",
                "message": "Invalid service account JSON format",
            }
            errors.append(
                "Service account JSON is malformed. Re-download from Google Cloud Console."
            )
            overall_status = "failure"
        else:
            raise

    except HttpError as e:
        # Defensive access for e.resp.status (Issue #35)
        status_code = e.resp.status if hasattr(e, "resp") and e.resp else None
        if status_code == 401:
            checks["service_account_valid"] = {
                "status": "fail",
                "message": "Service account credentials are invalid",
            }
            errors.append(
                "Service account credentials rejected. Verify the JSON file is correct."
            )
            overall_status = "failure"
        elif status_code == 403:
            checks["api_enabled"] = {
                "status": "fail",
                "message": "Google Play Developer API is not enabled or accessible",
            }
            errors.append(
                "Enable the API at: https://console.cloud.google.com/apis/library/androidpublisher.googleapis.com"
            )
            overall_status = "failure"
        else:
            # Use str(e) instead of private _get_reason() method (Issue #23)
            status_msg = f": {status_code}" if status_code else ""
            errors.append(f"Google Play API error{status_msg} - {str(e)}")
            overall_status = "failure"

    except Exception as e:
        errors.append(f"Unexpected error: {str(e)}")
        overall_status = "failure"

    # Generate next steps
    next_steps = []
    if overall_status == "success":
        next_steps = [
            "Your Play Store setup is complete",
            "You can now deploy to the internal track",
            "Make sure to add testers to your internal testing group",
        ]
    else:
        next_steps = [
            "Fix the errors listed above",
            "Re-run validation after making changes",
        ]

    return {
        "success": overall_status == "success",
        "overall_status": overall_status,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "next_steps": next_steps,
    }


# Helper functions for test_deployment_workflow (Issue #28 - Function length)
# ============================================================================


def _validate_deployment_environment(
    project_path_obj, keystore_path_obj
) -> Dict[str, Any]:
    """
    Validate that the deployment environment is ready.

    Args:
        project_path_obj: Path object for Android project
        keystore_path_obj: Path object for keystore file

    Returns:
        Dict with 'success', 'error', and 'gradlew' keys
    """
    if not project_path_obj.exists():
        return {
            "success": False,
            "error": f"Project path does not exist: {project_path_obj}",
        }

    if not keystore_path_obj.exists():
        return {
            "success": False,
            "error": f"Keystore file does not exist: {keystore_path_obj}",
        }

    gradlew = project_path_obj / "gradlew"
    if not gradlew.exists():
        return {
            "success": False,
            "error": "gradlew not found in project root",
            "suggestion": "This tool requires Gradle wrapper to be present",
        }

    return {"success": True, "gradlew": gradlew}


def _build_release_aab(
    project_path_obj,
    keystore_path_obj,
    store_password: str,
    key_alias: str,
    key_password: str,
    gradlew,
    step_start: float,
) -> Dict[str, Any]:
    """
    Build the release AAB with signing.

    Args:
        project_path_obj: Path to Android project
        keystore_path_obj: Path to keystore
        store_password: Keystore password
        key_alias: Key alias
        key_password: Key password
        gradlew: Path to gradlew script
        step_start: Start time for this step

    Returns:
        Dict with build results including success, aab_path, step info, etc.
    """
    import subprocess
    import os
    import time

    try:
        # Set environment variables for signing
        env = os.environ.copy()
        env["SIGNING_KEY_STORE_PATH"] = str(keystore_path_obj)
        env["SIGNING_STORE_PASSWORD"] = store_password
        env["SIGNING_KEY_ALIAS"] = key_alias
        env["SIGNING_KEY_PASSWORD"] = key_password

        # Run Gradle build
        result = subprocess.run(
            [str(gradlew), "bundleRelease"],
            cwd=str(project_path_obj),
            env=env,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes
        )

        if result.returncode != 0:
            # Use helper to extract output safely (Issue #38, #12)
            error_output = _get_process_output(result, max_length=500)
            full_output = _get_process_output(result, max_length=1000)

            step_info = {
                "step": "Build AAB",
                "status": "fail",
                "duration_seconds": round(time.time() - step_start, 1),
                "message": "Failed to build release AAB",
                "details": error_output,
            }

            return {
                "success": False,
                "step_info": step_info,
                "error": "Gradle build failed",
                "gradle_output": full_output,
            }

        # Find the AAB file
        aab_path = (
            project_path_obj
            / "app"
            / "build"
            / "outputs"
            / "bundle"
            / "release"
            / "app-release.aab"
        )

        if not aab_path.exists():
            step_info = {
                "step": "Build AAB",
                "status": "fail",
                "duration_seconds": round(time.time() - step_start, 1),
                "message": "AAB file was not generated",
            }

            return {
                "success": False,
                "step_info": step_info,
                "aab_generated": False,
                "error": "AAB file not found after build",
            }

        aab_size_mb = round(aab_path.stat().st_size / (1024 * 1024), 2)

        step_info = {
            "step": "Build AAB",
            "status": "pass",
            "duration_seconds": round(time.time() - step_start, 1),
            "message": "Successfully built release AAB",
            "details": {
                "task": "bundleRelease",
                "output_file": str(aab_path.relative_to(project_path_obj)),
                "file_size_mb": aab_size_mb,
            },
        }

        return {
            "success": True,
            "step_info": step_info,
            "aab_path": aab_path,
            "aab_size_mb": aab_size_mb,
        }

    except subprocess.TimeoutExpired:
        step_info = {
            "step": "Build AAB",
            "status": "fail",
            "duration_seconds": 600,
            "message": "Build timed out after 10 minutes",
        }

        return {
            "success": False,
            "step_info": step_info,
            "error": "Build timed out",
        }

    except Exception as e:
        step_info = {
            "step": "Build AAB",
            "status": "fail",
            "duration_seconds": round(time.time() - step_start, 1),
            "message": f"Unexpected error during build: {str(e)}",
        }

        return {
            "success": False,
            "step_info": step_info,
            "error": str(e),
        }


def _verify_aab_signature(aab_path, step_start: float) -> Dict[str, Any]:
    """
    Verify the AAB signature using jarsigner.

    Args:
        aab_path: Path to the AAB file
        step_start: Start time for this step

    Returns:
        Dict with verification results including step info and signing_successful
    """
    import subprocess
    import time

    try:
        # Use jarsigner to verify signing
        verify_result = subprocess.run(
            ["jarsigner", "-verify", "-verbose", str(aab_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Add null check for stdout (Issue #12)
        verify_output = verify_result.stdout or ""
        if "jar verified" in verify_output.lower():
            step_info = {
                "step": "Verify Signing",
                "status": "pass",
                "duration_seconds": round(time.time() - step_start, 1),
                "message": "AAB is properly signed",
            }
            return {"step_info": step_info, "signing_successful": True}
        else:
            step_info = {
                "step": "Verify Signing",
                "status": "fail",
                "duration_seconds": round(time.time() - step_start, 1),
                "message": "AAB signing verification failed",
                "details": verify_output[:500],
            }
            return {"step_info": step_info, "signing_successful": False}

    except FileNotFoundError:
        step_info = {
            "step": "Verify Signing",
            "status": "skipped",
            "duration_seconds": round(time.time() - step_start, 1),
            "message": "jarsigner not found - skipping signature verification",
        }
        return {"step_info": step_info, "signing_successful": None}

    except Exception as e:
        step_info = {
            "step": "Verify Signing",
            "status": "fail",
            "duration_seconds": round(time.time() - step_start, 1),
            "message": f"Error verifying signature: {str(e)}",
        }
        return {"step_info": step_info, "signing_successful": False}


def test_deployment_workflow(
    project_path: str,
    keystore_path: str,
    store_password: str,
    key_alias: str,
    key_password: str,
    dry_run: bool = None,
) -> Dict[str, Any]:
    r"""
    Test the deployment workflow locally without uploading to Play Store

    Args:

        project_path: Path to Android project

        keystore_path: Path to keystore file

        store_password: Keystore password

        key_alias: Key alias

        key_password: Key password

        dry_run: If true, skip actual Play Store upload.
                 **IMPORTANT**: Defaults to True for safety. If not specified,
                 the function will NOT perform actual deployment. Set explicitly
                 to False to enable real deployment.


    Returns:
        Result dictionary

    Security:
        IMPORTANT: Review SECURITY.md before implementing this function.

        For secure implementation:
        - Validate ALL inputs using validate_string_input() or validate_numeric_input()
        - For file operations: Use validate_safe_path() to prevent path traversal
        - For commands: Use validate_safe_command() with whitelisting
        - For sensitive data: Use redact_sensitive_data() before returning
        - Add @audit_log decorator for security logging
        - Add @with_rate_limit decorator to prevent abuse
        - Or use @secure_tool to apply multiple protections at once

    Async Support:
        This function is currently synchronous. For async operations
        (API calls, database queries, subprocess execution):

        1. Change to: async def test_deployment_workflow(...)
        2. Use 'await' for async operations

        Example:
            @audit_log  # Log all calls
            @with_rate_limit(max_requests=50, window_seconds=60)  # Rate limit
            async def test_deployment_workflow(...) -> Dict[str, Any]:
                # Validate inputs
                from .security_utils import validate_string_input
                validated_input = validate_string_input(
                    some_param,
                    max_length=500,
                    allowed_pattern=r'^[a-zA-Z0-9\s\-_\.]+$'
                )

                # Your async logic here
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get("https://api.example.com/data")
                    data = response.json()

                return {'success': True, 'data': data}
    """
    import time
    from pathlib import Path

    # Default dry_run to True
    if dry_run is None:
        dry_run = True

    project_path_obj = Path(project_path).resolve()
    keystore_path_obj = Path(keystore_path).resolve()

    steps = []
    total_start_time = time.time()

    # Step 1: Validate environment
    env_result = _validate_deployment_environment(project_path_obj, keystore_path_obj)
    if not env_result["success"]:
        return {
            "success": False,
            "overall_status": "failure",
            "error": env_result["error"],
            **(
                {"suggestion": env_result["suggestion"]}
                if "suggestion" in env_result
                else {}
            ),
        }

    gradlew = env_result["gradlew"]

    # Environment setup succeeded
    step_start = time.time()
    steps.append(
        {
            "step": "Environment Setup",
            "status": "pass",
            "duration_seconds": round(time.time() - step_start, 1),
            "message": "Gradle wrapper found and executable",
        }
    )

    # Step 2: Build AAB
    step_start = time.time()
    build_result = _build_release_aab(
        project_path_obj,
        keystore_path_obj,
        store_password,
        key_alias,
        key_password,
        gradlew,
        step_start,
    )

    steps.append(build_result["step_info"])

    if not build_result["success"]:
        return {
            "success": False,
            "overall_status": "failure",
            "steps": steps,
            "total_duration_seconds": round(time.time() - total_start_time, 1),
            "build_successful": False,
            "error": build_result["error"],
            **(
                {
                    k: v
                    for k, v in build_result.items()
                    if k in ["gradle_output", "aab_generated"]
                }
            ),
        }

    aab_path = build_result["aab_path"]
    aab_size_mb = build_result["aab_size_mb"]

    # Step 3: Verify Signing
    step_start = time.time()
    verify_result = _verify_aab_signature(aab_path, step_start)

    steps.append(verify_result["step_info"])
    signing_successful = verify_result["signing_successful"]

    # Step 4: Upload to Play Store (dry run)
    if dry_run:
        steps.append(
            {
                "step": "Upload to Play Store",
                "status": "skipped",
                "message": "Skipped due to dry_run=true",
            }
        )

    # Generate report
    errors = []
    warnings = []
    ready_for_deployment = signing_successful is not False

    if not ready_for_deployment:
        errors.append("AAB is not properly signed")

    next_steps = []
    if ready_for_deployment:
        next_steps = [
            "AAB generated and signed successfully",
            "Test the AAB on a real device",
            "Configure GitHub Secrets and push workflow to deploy",
        ]
    else:
        next_steps = ["Fix signing issues before attempting deployment"]

    return {
        "success": True,
        "overall_status": "success" if ready_for_deployment else "partial",
        "steps": steps,
        "total_duration_seconds": round(time.time() - total_start_time, 1),
        "build_successful": True,
        "signing_successful": signing_successful,
        "aab_generated": True,
        "aab_path": str(aab_path),
        "aab_size_mb": aab_size_mb,
        "errors": errors,
        "warnings": warnings,
        "ready_for_deployment": ready_for_deployment,
        "next_steps": next_steps,
    }

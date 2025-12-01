# Implementation Plan: Simplified Signing Configuration with Dual-Source Support

## Overview

Simplify the signing configuration by removing all optional parameters and making dual-source support (environment variables + gradle.properties fallback) the default and only behavior.

## Key Changes

1. **Remove `signing_strategy` parameter** - Simplify API to just `generate_signing_config(project_path: str)`
2. **Always generate dual-source config** - Environment variables (CI/CD priority) → gradle.properties (local dev fallback)
3. **Always use task-based validation** - Debug builds work without setup, release builds validate only on execution
4. **Generate gradle.properties.template** - Template file for local development setup

## API Design

### New Function Signature

```python
def generate_signing_config(project_path: str) -> Dict[str, Any]:
    """
    Generate signing configuration with dual-source support.

    Generates configuration that:
    - Checks environment variables first (CI/CD)
    - Falls back to gradle.properties (local development)
    - Validates only when building release (task-based)
    - Includes gradle.properties.template for easy setup

    Args:
        project_path: Path to Android project

    Returns:
        {
            "success": True,
            "gradle_config_kotlin": "Kotlin DSL configuration",
            "gradle_config_groovy": "Groovy DSL configuration",
            "gradle_properties_template": "Template for local development",
            "gitignore_entries": ["gradle.properties"],
            "instructions": ["Setup steps"],
            "required_env_vars": ["List of env vars"],
            "complete_example": "Full build.gradle.kts example"
        }
    """
```

## Implementation Steps

### Step 1: Update generator.py (lines 602-784)

**File:** `hitoshura25_mcp_android_playstore_deploy/generator.py`

#### 1.1 Update function signature (line 602)
- Remove `signing_strategy: str = None` parameter
- Update to: `def generate_signing_config(project_path: str) -> Dict[str, Any]:`

#### 1.2 Remove TODO comment (lines 671-675)
- Delete the TODO about gradle_properties strategy (no longer needed)

#### 1.3 Replace Kotlin DSL config (lines 677-697)
Replace with dual-source configuration:

```kotlin
signingConfigs {
    create("release") {
        // Priority: environment variables (CI/CD) > gradle.properties (local dev)
        val keystorePath = System.getenv("SIGNING_KEY_STORE_PATH")
            ?: project.findProperty("SIGNING_KEY_STORE_PATH")?.toString()
        val storePass = System.getenv("SIGNING_STORE_PASSWORD")
            ?: project.findProperty("SIGNING_STORE_PASSWORD")?.toString()
        val alias = System.getenv("SIGNING_KEY_ALIAS")
            ?: project.findProperty("SIGNING_KEY_ALIAS")?.toString()
        val keyPass = System.getenv("SIGNING_KEY_PASSWORD")
            ?: project.findProperty("SIGNING_KEY_PASSWORD")?.toString()

        if (keystorePath != null && storePass != null && alias != null && keyPass != null) {
            storeFile = file(keystorePath)
            storePassword = storePass
            keyAlias = alias
            keyPassword = keyPass
        }
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

// Validate signing config only when building release variants
tasks.matching { it.name.contains("Release") }.configureEach {
    doFirst {
        val releaseConfig = android.signingConfigs.getByName("release")
        if (releaseConfig.storeFile == null) {
            throw GradleException(
                ""${'"'}
                Release signing not configured!

                For CI/CD: Set environment variables:
                  - SIGNING_KEY_STORE_PATH
                  - SIGNING_STORE_PASSWORD
                  - SIGNING_KEY_ALIAS
                  - SIGNING_KEY_PASSWORD

                For local development: Create gradle.properties with:
                  SIGNING_KEY_STORE_PATH=/path/to/release-keystore.jks
                  SIGNING_STORE_PASSWORD=your-password
                  SIGNING_KEY_ALIAS=upload
                  SIGNING_KEY_PASSWORD=your-password

                See gradle.properties.template for template.
                ""${'"'}.trimIndent()
            )
        }
    }
}
```

#### 1.4 Update Groovy DSL config (lines 699-716)
Apply similar dual-source pattern for Groovy:

```groovy
android {
    signingConfigs {
        release {
            def keystorePath = System.getenv('SIGNING_KEY_STORE_PATH') ?: project.findProperty('SIGNING_KEY_STORE_PATH')
            def storePass = System.getenv('SIGNING_STORE_PASSWORD') ?: project.findProperty('SIGNING_STORE_PASSWORD')
            def alias = System.getenv('SIGNING_KEY_ALIAS') ?: project.findProperty('SIGNING_KEY_ALIAS')
            def keyPass = System.getenv('SIGNING_KEY_PASSWORD') ?: project.findProperty('SIGNING_KEY_PASSWORD')

            if (keystorePath && storePass && alias && keyPass) {
                storeFile file(keystorePath)
                storePassword storePass
                keyAlias alias
                keyPassword keyPass
            }
        }
    }

    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            shrinkResources true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}

tasks.matching { it.name.contains('Release') }.configureEach {
    doFirst {
        if (android.signingConfigs.release.storeFile == null) {
            throw new GradleException('''
                Release signing not configured!

                For CI/CD: Set environment variables:
                  - SIGNING_KEY_STORE_PATH
                  - SIGNING_STORE_PASSWORD
                  - SIGNING_KEY_ALIAS
                  - SIGNING_KEY_PASSWORD

                For local development: Create gradle.properties with:
                  SIGNING_KEY_STORE_PATH=/path/to/release-keystore.jks
                  SIGNING_STORE_PASSWORD=your-password
                  SIGNING_KEY_ALIAS=upload
                  SIGNING_KEY_PASSWORD=your-password

                See gradle.properties.template for template.
            '''.stripIndent())
        }
    }
}
```

#### 1.5 Add gradle.properties.template generation
After line 716, add:

```python
gradle_properties_template = """# Local Development Signing Configuration
#
# Copy this file to gradle.properties (gitignored) to enable local release builds
#
# IMPORTANT: Never commit gradle.properties with real credentials!
# CI/CD will use environment variables instead.

# Path to your local keystore file (use absolute path)
SIGNING_KEY_STORE_PATH=/absolute/path/to/release-keystore.jks

# Keystore password
SIGNING_STORE_PASSWORD=your-store-password

# Key alias (usually "upload" for Play Store)
SIGNING_KEY_ALIAS=upload

# Key password
SIGNING_KEY_PASSWORD=your-key-password
"""
```

#### 1.6 Update complete_example (lines 718-765)
Ensure complete_example includes the task-based validation block.

#### 1.7 Update return dictionary (lines 767-784)
```python
return {
    "success": True,
    "gradle_config_kotlin": gradle_config_kotlin,
    "gradle_config_groovy": gradle_config_groovy,
    "gradle_properties_template": gradle_properties_template,  # NEW
    "gitignore_entries": ["gradle.properties"],  # NEW
    "insert_location": "Inside android { ... } block, before buildTypes",
    "instructions": [
        "Add the signingConfigs block to your app/build.gradle.kts",
        "Update your release buildType to use the signing config",
        "Create gradle.properties.template at project root",
        "For local development: Copy gradle.properties.template to gradle.properties and fill in values",
        "For CI/CD: Set environment variables in your pipeline",
        "Verify gradle.properties is in .gitignore"
    ],
    "required_env_vars": [
        "SIGNING_KEY_STORE_PATH",
        "SIGNING_STORE_PASSWORD",
        "SIGNING_KEY_ALIAS",
        "SIGNING_KEY_PASSWORD",
    ],
    "complete_example": complete_example,
}
```

#### 1.8 Update docstring (lines 603-654)
Update to reflect new simplified API and dual-source behavior.

### Step 2: Update server.py (lines 88-107)

**File:** `hitoshura25_mcp_android_playstore_deploy/server.py`

#### 2.1 Update tool definition (line 89)
Remove `signing_strategy` parameter from function signature:

```python
@mcp.tool()
async def generate_signing_config(project_path: str) -> str:
```

#### 2.2 Update docstring (lines 90-107)
```python
"""Generate Gradle signing configuration with dual-source support

Generates signing configuration that works seamlessly for both local development and CI/CD:
- Environment variables (prioritized for CI/CD)
- gradle.properties fallback (for local development)
- Task-based validation (debug builds always work)

Automatically generates gradle.properties.template for easy local setup.

Args:
    project_path: Path to Android project

Returns:
    Result including gradle_config_kotlin, gradle_properties_template, and setup instructions
"""
```

#### 2.3 Update function call (line 109)
Remove signing_strategy parameter:

```python
result = generator.generate_signing_config(project_path)
```

### Step 3: Update tests (lines 27-36)

**File:** `hitoshura25_mcp_android_playstore_deploy/tests/test_generator.py`

#### 3.1 Update existing test
```python
def test_generate_signing_config():
    """Test that generate_signing_config generates proper Gradle config with dual-source support"""
    result = generate_signing_config(project_path="/fake/path")

    assert result["success"] is True
    assert "gradle_config_kotlin" in result
    assert "gradle_config_groovy" in result
    assert "gradle_properties_template" in result  # NEW
    assert "gitignore_entries" in result  # NEW

    # Check for dual-source pattern
    assert "project.findProperty" in result["gradle_config_kotlin"]
    assert "System.getenv" in result["gradle_config_kotlin"]

    # Check for task-based validation
    assert "tasks.matching" in result["gradle_config_kotlin"]
    assert 'it.name.contains("Release")' in result["gradle_config_kotlin"]

    # Check template content
    assert "SIGNING_KEY_STORE_PATH" in result["gradle_properties_template"]
    assert "gradle.properties" in result["gitignore_entries"]
```

#### 3.2 Add new test cases

```python
def test_generate_signing_config_includes_validation():
    """Test that task-based validation is included"""
    result = generate_signing_config(project_path="/fake/path")

    assert "GradleException" in result["gradle_config_kotlin"]
    assert "Release signing not configured!" in result["gradle_config_kotlin"]

def test_generate_signing_config_gradle_properties_template():
    """Test gradle.properties.template generation"""
    result = generate_signing_config(project_path="/fake/path")

    template = result["gradle_properties_template"]
    assert "SIGNING_KEY_STORE_PATH=" in template
    assert "SIGNING_STORE_PASSWORD=" in template
    assert "SIGNING_KEY_ALIAS=" in template
    assert "SIGNING_KEY_PASSWORD=" in template
    assert "Never commit gradle.properties" in template

def test_generate_signing_config_priority_order():
    """Test that environment variables have priority over gradle.properties"""
    result = generate_signing_config(project_path="/fake/path")

    # Check that env vars are checked first in the elvis operator
    kotlin_config = result["gradle_config_kotlin"]
    assert kotlin_config.index("System.getenv") < kotlin_config.index("project.findProperty")
```

### Step 4: Remove security_utils validation (if needed)

**File:** `hitoshura25_mcp_android_playstore_deploy/security_utils.py` (lines 564-584)

Check if `validate_signing_strategy()` function exists and remove it, or update it if it's used elsewhere. Since we're removing the parameter, this validation is no longer needed.

## Critical Files to Modify

1. **generator.py** (lines 602-784) - Core implementation
2. **server.py** (lines 88-109) - MCP tool interface
3. **test_generator.py** (lines 27-36+) - Tests
4. **security_utils.py** (lines 564-584) - Remove signing_strategy validation if exists

## Testing Checklist

After implementation, verify:

1. ✅ Debug build works without any config
2. ✅ Release build fails with helpful error when no config exists
3. ✅ Release build succeeds with gradle.properties
4. ✅ Release build succeeds with environment variables
5. ✅ Environment variables take priority over gradle.properties
6. ✅ Gradle sync succeeds in IDE without config
7. ✅ All unit tests pass
8. ✅ gradle.properties.template is properly formatted

## Benefits

- **Simpler API**: Single parameter instead of three
- **Zero-setup debug builds**: Works immediately after clone
- **Easy release testing**: One-time gradle.properties setup
- **CI/CD friendly**: Environment variables prioritized
- **Best practices**: Follows standard Android development patterns

## Rationale

This simplified approach removes all optional parameters because:
1. Dual-source config is the right default for 99% of users
2. Task-based validation has no drawbacks (always best)
3. Users can manually edit generated code for edge cases
4. Simpler API = better developer experience
5. No backward compatibility concerns per user request

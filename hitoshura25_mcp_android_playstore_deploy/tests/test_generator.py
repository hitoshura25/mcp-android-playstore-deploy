"""Tests for MCP tools in generator.py"""

import pytest
import yaml
from pathlib import Path
from hitoshura25_mcp_android_playstore_deploy.generator import (
    analyze_android_project,
    generate_keystore,
    generate_signing_config,
    setup_local_development,
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
    """Test that generate_signing_config generates proper Gradle config with dual-source support"""
    result = generate_signing_config(project_path="/fake/path")

    assert result["success"] is True
    assert "gradle_config_kotlin" in result
    assert "gradle_config_groovy" in result
    assert "gradle_properties_template" in result
    assert "gitignore_entries" in result

    # Check for dual-source pattern in Kotlin config
    assert "project.findProperty" in result["gradle_config_kotlin"]
    assert "System.getenv" in result["gradle_config_kotlin"]

    # Check for task-based validation
    assert "tasks.matching" in result["gradle_config_kotlin"]
    assert 'it.name.contains("Release")' in result["gradle_config_kotlin"]

    # Check template content (now with APP_ prefix)
    assert "APP_SIGNING_KEY_STORE_PATH" in result["gradle_properties_template"]
    assert "gradle.properties" in result["gitignore_entries"]


def test_generate_signing_config_includes_validation():
    """Test that task-based validation is included"""
    result = generate_signing_config(project_path="/fake/path")

    assert "GradleException" in result["gradle_config_kotlin"]
    assert "Release signing not configured!" in result["gradle_config_kotlin"]


def test_generate_signing_config_gradle_properties_template():
    """Test gradle.properties.template generation"""
    result = generate_signing_config(project_path="/fake/path")

    template = result["gradle_properties_template"]
    assert "APP_SIGNING_KEY_STORE_PATH=" in template
    assert "APP_SIGNING_STORE_PASSWORD=" in template
    assert "APP_SIGNING_KEY_ALIAS=" in template
    assert "APP_SIGNING_KEY_PASSWORD=" in template
    assert "Never commit gradle.properties" in template


def test_generate_signing_config_priority_order():
    """Test that environment variables have priority over gradle.properties"""
    result = generate_signing_config(project_path="/fake/path")
    kotlin_config = result["gradle_config_kotlin"]

    # Define the 4 signing config variables we expect (now with APP_ prefix)
    config_vars = [
        "APP_SIGNING_KEY_STORE_PATH",
        "APP_SIGNING_STORE_PASSWORD",
        "APP_SIGNING_KEY_ALIAS",
        "APP_SIGNING_KEY_PASSWORD",
    ]

    # Verify each variable has correct priority order in its elvis operator line
    for var in config_vars:
        # Find the line containing both patterns for this variable
        # (should be the variable declaration line - only one per variable)
        for line in kotlin_config.split("\n"):
            if f'System.getenv("{var}")' in line and f'project.findProperty("{var}")' in line:
                # Verify env var comes before property in this specific line
                env_pos = line.find("System.getenv")
                prop_pos = line.find("project.findProperty")
                assert env_pos < prop_pos, f"Priority order incorrect for {var} in line: {line.strip()}"
                break  # Only one declaration line per variable


def test_generate_signing_config_custom_prefix():
    """Test that custom prefix works correctly"""
    result = generate_signing_config(project_path="/fake/path", env_var_prefix="MYAPP_")

    assert result["success"] is True
    # Check Kotlin config has custom prefix
    assert "MYAPP_SIGNING_KEY_STORE_PATH" in result["gradle_config_kotlin"]
    assert "MYAPP_SIGNING_STORE_PASSWORD" in result["gradle_config_kotlin"]
    assert "MYAPP_SIGNING_KEY_ALIAS" in result["gradle_config_kotlin"]
    assert "MYAPP_SIGNING_KEY_PASSWORD" in result["gradle_config_kotlin"]

    # Verify in template too
    assert "MYAPP_SIGNING_KEY_STORE_PATH=" in result["gradle_properties_template"]
    assert "MYAPP_SIGNING_STORE_PASSWORD=" in result["gradle_properties_template"]
    assert "MYAPP_SIGNING_KEY_ALIAS=" in result["gradle_properties_template"]
    assert "MYAPP_SIGNING_KEY_PASSWORD=" in result["gradle_properties_template"]

    # Verify in required_env_vars
    assert "MYAPP_SIGNING_KEY_STORE_PATH" in result["required_env_vars"]


def test_generate_signing_config_no_prefix():
    """Test that empty prefix works (original behavior)"""
    result = generate_signing_config(project_path="/fake/path", env_var_prefix="")

    assert result["success"] is True
    # Original variable names without prefix
    assert "SIGNING_KEY_STORE_PATH" in result["gradle_config_kotlin"]
    assert "SIGNING_STORE_PASSWORD" in result["gradle_config_kotlin"]
    assert "SIGNING_KEY_ALIAS" in result["gradle_config_kotlin"]
    assert "SIGNING_KEY_PASSWORD" in result["gradle_config_kotlin"]

    # Should not have APP_ prefix
    assert "APP_SIGNING" not in result["gradle_config_kotlin"]
    assert "APP_SIGNING" not in result["gradle_properties_template"]


def test_generate_signing_config_groovy_dual_source():
    """Test that Groovy config has dual-source pattern"""
    result = generate_signing_config(project_path="/fake/path")
    groovy_config = result["gradle_config_groovy"]

    # Check for dual-source pattern in Groovy
    assert "System.getenv" in groovy_config
    assert "project.findProperty" in groovy_config
    assert "?:" in groovy_config  # Elvis operator in Groovy


def test_generate_signing_config_groovy_prefix():
    """Test that Groovy config uses prefixed variables with default APP_ prefix"""
    result = generate_signing_config(project_path="/fake/path")
    groovy_config = result["gradle_config_groovy"]

    # Check for APP_ prefixed variables
    assert "APP_SIGNING_KEY_STORE_PATH" in groovy_config
    assert "APP_SIGNING_STORE_PASSWORD" in groovy_config
    assert "APP_SIGNING_KEY_ALIAS" in groovy_config
    assert "APP_SIGNING_KEY_PASSWORD" in groovy_config


def test_generate_signing_config_groovy_custom_prefix():
    """Test that Groovy config respects custom prefix"""
    result = generate_signing_config(project_path="/fake/path", env_var_prefix="MYAPP_")
    groovy_config = result["gradle_config_groovy"]

    # Check for custom prefixed variables
    assert "MYAPP_SIGNING_KEY_STORE_PATH" in groovy_config
    assert "MYAPP_SIGNING_STORE_PASSWORD" in groovy_config
    assert "MYAPP_SIGNING_KEY_ALIAS" in groovy_config
    assert "MYAPP_SIGNING_KEY_PASSWORD" in groovy_config


def test_create_github_secrets_guide():
    """Test that create_github_secrets_guide generates proper guide"""
    result = create_github_secrets_guide(repo_url="https://github.com/owner/repo")

    assert result["success"] is True
    assert "secrets" in result
    assert len(result["secrets"]) == 5
    assert result["github_secrets_url"] == "https://github.com/owner/repo/settings/secrets/actions"


def test_generate_github_workflow_defaults():
    """Test that generate_github_workflow uses proper defaults"""
    result = generate_github_workflow(project_path="/fake/path", package_name="com.example.app")

    assert result["success"] is True
    assert "workflow_content" in result
    assert "internal" in result["workflow_path"]
    assert "workflow_dispatch" in result["workflow_content"]
    assert "com.example.app" in result["workflow_content"]


def test_generate_github_workflow_with_track():
    """Test that generate_github_workflow respects track parameter"""
    result = generate_github_workflow(project_path="/fake/path", package_name="com.example.app", track="beta")

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


# NEW: Tests for ProGuard mapping and release notes support


def test_generate_workflow_with_proguard_defaults():
    """Test that ProGuard mapping is enabled by default"""
    result = generate_github_workflow(project_path="/fake/path", package_name="com.example.app")

    assert result["success"] is True
    assert "proguard_config" in result
    assert result["proguard_config"]["enforced"] is True
    assert "mapping/release/mapping.txt" in result["proguard_config"]["mapping_file_path"]
    assert "mappingFile:" in result["workflow_content"]


def test_generate_workflow_with_proguard_disabled():
    """Test that ProGuard can be explicitly disabled"""
    result = generate_github_workflow(project_path="/fake/path", package_name="com.example.app", enforce_proguard=False)

    assert result["success"] is True
    assert "proguard_config" in result
    assert result["proguard_config"]["enforced"] is False
    assert result["proguard_config"]["mapping_file_path"] is None
    # Should not contain mappingFile parameter in workflow
    assert "mappingFile:" not in result["workflow_content"]


def test_generate_workflow_with_custom_mapping_path():
    """Test custom ProGuard mapping file path"""
    result = generate_github_workflow(
        project_path="/fake/path",
        package_name="com.example.app",
        enforce_proguard=True,
        mapping_file_path="custom/path/mapping.txt",
    )

    assert result["success"] is True
    assert result["proguard_config"]["mapping_file_path"] == "custom/path/mapping.txt"
    assert "mappingFile: custom/path/mapping.txt" in result["workflow_content"]


def test_generate_workflow_with_release_notes_defaults():
    """Test that release notes are enabled by default"""
    result = generate_github_workflow(project_path="/fake/path", package_name="com.example.app")

    assert result["success"] is True
    assert "release_notes_config" in result
    assert result["release_notes_config"]["enabled"] is True
    assert result["release_notes_config"]["directory"] == "distribution/whatsnew"
    assert "whatsNewDirectory:" in result["workflow_content"]


def test_generate_workflow_with_release_notes_disabled():
    """Test that release notes can be explicitly disabled"""
    result = generate_github_workflow(
        project_path="/fake/path", package_name="com.example.app", include_release_notes=False
    )

    assert result["success"] is True
    assert "release_notes_config" in result
    assert result["release_notes_config"]["enabled"] is False
    assert result["release_notes_config"]["directory"] is None
    # Should not contain whatsNewDirectory parameter in workflow
    assert "whatsNewDirectory:" not in result["workflow_content"]


def test_generate_workflow_with_custom_release_notes_directory():
    """Test custom release notes directory"""
    result = generate_github_workflow(
        project_path="/fake/path",
        package_name="com.example.app",
        include_release_notes=True,
        release_notes_directory="custom/release-notes",
    )

    assert result["success"] is True
    assert result["release_notes_config"]["directory"] == "custom/release-notes"
    assert "whatsNewDirectory: custom/release-notes" in result["workflow_content"]


def test_generate_workflow_with_both_features_disabled():
    """Test workflow generation with both ProGuard and release notes disabled"""
    result = generate_github_workflow(
        project_path="/fake/path", package_name="com.example.app", enforce_proguard=False, include_release_notes=False
    )

    assert result["success"] is True
    assert result["proguard_config"]["enforced"] is False
    assert result["release_notes_config"]["enabled"] is False
    assert "mappingFile:" not in result["workflow_content"]
    assert "whatsNewDirectory:" not in result["workflow_content"]


def test_proguard_config_structure():
    """Test that proguard_config has proper structure"""
    result = generate_github_workflow(project_path="/fake/path", package_name="com.example.app", enforce_proguard=True)

    assert result["success"] is True
    config = result["proguard_config"]
    assert "enforced" in config
    assert "was_enabled_by_mcp" in config
    assert "modified_files" in config
    assert "mapping_file_path" in config
    assert "why_important" in config
    assert isinstance(config["modified_files"], list)


def test_release_notes_config_structure():
    """Test that release_notes_config has proper structure"""
    result = generate_github_workflow(
        project_path="/fake/path", package_name="com.example.app", include_release_notes=True
    )

    assert result["success"] is True
    config = result["release_notes_config"]
    assert "enabled" in config
    assert "directory" in config
    assert "created_by_mcp" in config
    assert "locales_created" in config
    assert "setup_instructions" in config
    assert "supported_locales" in config
    assert isinstance(config["locales_created"], list)
    assert isinstance(config["supported_locales"], list)


def test_release_notes_setup_instructions():
    """Test that release notes setup instructions are included"""
    result = generate_github_workflow(
        project_path="/fake/path", package_name="com.example.app", include_release_notes=True
    )

    assert result["success"] is True
    instructions = result["release_notes_config"]["setup_instructions"]
    assert "Release Notes Setup" in instructions
    assert "whatsnew" in instructions
    assert "500 characters" in instructions


def test_dynamic_instructions_with_proguard():
    """Test that instructions include ProGuard information when enabled"""
    result = generate_github_workflow(project_path="/fake/path", package_name="com.example.app", enforce_proguard=True)

    assert result["success"] is True
    instructions_text = "\n".join(result["instructions"])
    assert "ProGuard" in instructions_text or "Mapping" in instructions_text


def test_dynamic_instructions_with_release_notes():
    """Test that instructions include release notes information when enabled"""
    result = generate_github_workflow(
        project_path="/fake/path", package_name="com.example.app", include_release_notes=True
    )

    assert result["success"] is True
    instructions_text = "\n".join(result["instructions"])
    assert "Release Notes" in instructions_text


def test_yaml_validity_with_optional_params():
    """Test that generated YAML is valid with optional parameters"""
    result = generate_github_workflow(
        project_path="/fake/path", package_name="com.example.app", enforce_proguard=True, include_release_notes=True
    )

    assert result["success"] is True

    # Try to parse the YAML to ensure it's valid
    try:
        parsed = yaml.safe_load(result["workflow_content"])
        assert parsed is not None
        assert "name" in parsed
        assert "jobs" in parsed
    except yaml.YAMLError as e:
        pytest.fail(f"Generated YAML is invalid: {e}")


# NEW: Tests for setup_local_development()


def test_setup_local_development_basic():
    """Test basic setup_local_development functionality"""
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        result = setup_local_development(project_path=tmpdir)

        assert result["success"] is True
        assert "keystore" in result
        assert "actions" in result
        assert "validation_commands" in result
        assert "fallback_instructions" in result
        assert "security_notes" in result
        assert "next_steps" in result

        # Check keystore details
        assert result["keystore"]["alias"] == "local-dev"
        assert len(result["keystore"]["store_password"]) == 16
        assert len(result["keystore"]["key_password"]) == 16
        assert result["keystore"]["validity_days"] == 10950

        # Check actions structure
        assert len(result["actions"]) >= 2
        action_types = [a["action_type"] for a in result["actions"]]
        assert "write_keystore" in action_types
        assert "ask_permission" in action_types
        assert "append_to_gitignore" in action_types

        # Check validation commands (now structured data, not shell commands)
        assert len(result["validation_commands"]) == 2
        assert result["validation_commands"][0]["command"] == "./gradlew"
        assert "assembleDebug" in result["validation_commands"][0]["args"]
        assert result["validation_commands"][1]["command"] == "./gradlew"
        assert "bundleRelease" in result["validation_commands"][1]["args"]

        # Check keystore file was created
        keystore_path = result["keystore"]["path"]
        assert os.path.exists(keystore_path)


def test_setup_local_development_custom_prefix():
    """Test setup_local_development with custom prefix"""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        result = setup_local_development(project_path=tmpdir, env_var_prefix="MYAPP_")

        assert result["success"] is True

        # Find the ask_permission action and check its content
        ask_permission_action = next((a for a in result["actions"] if a["action_type"] == "ask_permission"), None)
        assert ask_permission_action is not None

        gradle_content = ask_permission_action["content_to_append"]
        assert "MYAPP_SIGNING_KEY_STORE_PATH" in gradle_content
        assert "MYAPP_SIGNING_STORE_PASSWORD" in gradle_content
        assert "MYAPP_SIGNING_KEY_ALIAS" in gradle_content
        assert "MYAPP_SIGNING_KEY_PASSWORD" in gradle_content

        # Should not have APP_ prefix (check for variables starting with APP_ at line start)
        assert "\nAPP_SIGNING" not in gradle_content
        # Also check it doesn't start with APP_ (edge case for first line)
        assert not gradle_content.strip().startswith("APP_SIGNING")


def test_setup_local_development_gradle_home_detection():
    """Test Gradle home directory detection"""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        result = setup_local_development(project_path=tmpdir)

        assert result["success"] is True
        assert "gradle_user_home" in result
        assert "gradle_properties_path" in result

        # Should end with .gradle
        assert result["gradle_user_home"].endswith(".gradle")
        assert result["gradle_properties_path"].endswith("gradle.properties")

        # gradle_properties_path should be inside gradle_user_home
        assert result["gradle_user_home"] in result["gradle_properties_path"]


def test_setup_local_development_actions_structure():
    """Test that actions array has proper structure"""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        result = setup_local_development(project_path=tmpdir)

        assert result["success"] is True
        actions = result["actions"]

        # Check each action has required fields
        for action in actions:
            assert "action_type" in action
            assert "description" in action

            # write_keystore action is already completed
            if action["action_type"] == "write_keystore":
                assert "completed" in action
                assert action["completed"] is True
                assert "file_path" in action

            # ask_permission action has specific fields
            elif action["action_type"] == "ask_permission":
                assert "question" in action
                assert "file_path" in action
                assert "content_to_append" in action
                assert "backup_existing" in action
                assert action["backup_existing"] is True

            # append_to_gitignore action has specific fields
            elif action["action_type"] == "append_to_gitignore":
                assert "file_path" in action
                assert "content" in action
                assert "skip_if_pattern_exists" in action


# Error scenario tests for setup_local_development()


def test_setup_local_development_invalid_project_path():
    """Test setup_local_development with invalid project path"""
    # Path traversal attempt - may be caught at validation or keystore generation
    result = setup_local_development(project_path="../../etc/passwd")

    assert result["success"] is False
    assert "error" in result
    # Error can be from path validation or keystore generation
    assert "Invalid project path" in result["error"] or "Failed to generate keystore" in result["error"]


def test_setup_local_development_empty_project_path():
    """Test setup_local_development with empty project path"""
    result = setup_local_development(project_path="")

    assert result["success"] is False
    assert "error" in result
    assert "project_path is required" in result["error"]


def test_setup_local_development_invalid_keystore_alias():
    """Test setup_local_development with invalid keystore alias"""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        # Alias with special shell characters
        result = setup_local_development(project_path=tmpdir, keystore_alias="test; rm -rf /")

        assert result["success"] is False
        assert "error" in result
        assert "Invalid keystore_alias" in result["error"]


def test_setup_local_development_invalid_env_var_prefix():
    """Test setup_local_development with invalid env var prefix"""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        # Lowercase letters not allowed in env var prefix
        result = setup_local_development(project_path=tmpdir, env_var_prefix="myapp_")

        assert result["success"] is False
        assert "error" in result
        assert "Invalid env_var_prefix" in result["error"]
        assert "uppercase" in result["error"]


def test_setup_local_development_invalid_password_length():
    """Test setup_local_development with invalid password length"""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        # Test negative length
        result = setup_local_development(project_path=tmpdir, keystore_password_length=-1)

        assert result["success"] is False
        assert "error" in result
        assert "Invalid keystore_password_length" in result["error"]

        # Test zero length
        result = setup_local_development(project_path=tmpdir, keystore_password_length=0)

        assert result["success"] is False
        assert "error" in result

        # Test extremely large length
        result = setup_local_development(project_path=tmpdir, keystore_password_length=10000)

        assert result["success"] is False
        assert "error" in result

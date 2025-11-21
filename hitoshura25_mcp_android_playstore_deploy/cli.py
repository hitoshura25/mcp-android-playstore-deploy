#!/usr/bin/env python3
"""
CLI for hitoshura25-mcp-android-playstore-deploy.

MCP server that helps developers set up automated Google Play Store deployment for Android apps

Security Notes:
    CLI arguments are user-controlled and should be validated.
    The generator functions should handle validation, but you can
    add additional CLI-level validation here if needed.
"""

import sys
import argparse
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

# Uncomment to add CLI-level input validation
# from .security_utils import validate_string_input, validate_numeric_input


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MCP server that helps developers set up automated Google Play Store deployment for Android apps"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # analyze_android_project command
    analyze_android_project_parser = subparsers.add_parser(
        "analyze_android_project",
        help="Analyze an Android project to understand its configuration and identify requirements for Play Store deployment",
    )

    analyze_android_project_parser.add_argument(
        "--project_path",
        type=str,
        required=True,
        help="Absolute path to the Android project root directory",
    )

    # generate_keystore command
    generate_keystore_parser = subparsers.add_parser(
        "generate_keystore",
        help="Generate a new Android keystore file for app signing with secure parameters",
    )

    generate_keystore_parser.add_argument(
        "--output_path",
        type=str,
        required=True,
        help="Absolute path where the keystore will be saved",
    )

    generate_keystore_parser.add_argument(
        "--alias", type=str, required=True, help="Key alias for the signing key"
    )

    generate_keystore_parser.add_argument(
        "--key_password", type=str, required=True, help="Password for the signing key"
    )

    generate_keystore_parser.add_argument(
        "--store_password", type=str, required=True, help="Password for the keystore"
    )

    generate_keystore_parser.add_argument(
        "--validity_days", type=int, help="How many days the key should be valid"
    )

    generate_keystore_parser.add_argument(
        "--key_size", type=int, help="Key size in bits"
    )

    generate_keystore_parser.add_argument(
        "--dname", type=str, help="Distinguished name for the certificate"
    )

    # generate_signing_config command
    generate_signing_config_parser = subparsers.add_parser(
        "generate_signing_config",
        help="Generate Gradle signing configuration code to add to build.gradle.kts",
    )

    generate_signing_config_parser.add_argument(
        "--project_path", type=str, required=True, help="Path to Android project"
    )

    generate_signing_config_parser.add_argument(
        "--signing_strategy",
        type=str,
        help="How to provide signing credentials (environment_variables or gradle_properties)",
    )

    # setup_service_account_guide command
    _ = subparsers.add_parser(
        "setup_service_account_guide",
        help="Provide interactive step-by-step guide for setting up Google Play Service Account",
    )

    # generate_github_workflow command
    generate_github_workflow_parser = subparsers.add_parser(
        "generate_github_workflow",
        help="Generate a complete GitHub Actions workflow file for Play Store deployment",
    )

    generate_github_workflow_parser.add_argument(
        "--project_path", type=str, required=True, help="Path to Android project"
    )

    generate_github_workflow_parser.add_argument(
        "--package_name", type=str, required=True, help="Android app package name"
    )

    generate_github_workflow_parser.add_argument(
        "--track",
        type=str,
        help="Play Store release track (internal, alpha, beta, production)",
    )

    generate_github_workflow_parser.add_argument(
        "--trigger_strategy",
        type=str,
        help="How to trigger the workflow (manual, branch, tag)",
    )

    generate_github_workflow_parser.add_argument(
        "--branch_name",
        type=str,
        help="Branch name to trigger on if trigger_strategy is branch",
    )

    generate_github_workflow_parser.add_argument(
        "--app_module_path",
        type=str,
        help="Path to app module relative to project root",
    )

    generate_github_workflow_parser.add_argument(
        "--java_version", type=str, help="Java/JDK version to use for builds"
    )

    # validate_github_secrets command
    validate_github_secrets_parser = subparsers.add_parser(
        "validate_github_secrets",
        help="Validate that required GitHub Secrets are configured (checks existence only)",
    )

    validate_github_secrets_parser.add_argument(
        "--repo_owner",
        type=str,
        required=True,
        help="GitHub repository owner username or organization",
    )

    validate_github_secrets_parser.add_argument(
        "--repo_name", type=str, required=True, help="GitHub repository name"
    )

    validate_github_secrets_parser.add_argument(
        "--github_token",
        type=str,
        required=True,
        help="GitHub Personal Access Token with repo scope",
    )

    validate_github_secrets_parser.add_argument(
        "--required_secrets", type=str, help="List of secret names to check for"
    )

    # create_github_secrets_guide command
    create_github_secrets_guide_parser = subparsers.add_parser(
        "create_github_secrets_guide",
        help="Generate a comprehensive guide for creating all required GitHub Secrets",
    )

    create_github_secrets_guide_parser.add_argument(
        "--repo_url", type=str, required=True, help="GitHub repository URL"
    )

    create_github_secrets_guide_parser.add_argument(
        "--keystore_path",
        type=str,
        help="Optional path to keystore for encoding instructions",
    )

    # validate_play_store_setup command
    validate_play_store_setup_parser = subparsers.add_parser(
        "validate_play_store_setup",
        help="Validate that Play Store app and API access are properly configured using service account",
    )

    validate_play_store_setup_parser.add_argument(
        "--service_account_json_path",
        type=str,
        required=True,
        help="Path to service account JSON file",
    )

    validate_play_store_setup_parser.add_argument(
        "--package_name",
        type=str,
        required=True,
        help="Android app package name to validate",
    )

    # test_deployment_workflow command
    test_deployment_workflow_parser = subparsers.add_parser(
        "test_deployment_workflow",
        help="Test the deployment workflow locally without uploading to Play Store",
    )

    test_deployment_workflow_parser.add_argument(
        "--project_path", type=str, required=True, help="Path to Android project"
    )

    test_deployment_workflow_parser.add_argument(
        "--keystore_path", type=str, required=True, help="Path to keystore file"
    )

    test_deployment_workflow_parser.add_argument(
        "--store_password", type=str, required=True, help="Keystore password"
    )

    test_deployment_workflow_parser.add_argument(
        "--key_alias", type=str, required=True, help="Key alias"
    )

    test_deployment_workflow_parser.add_argument(
        "--key_password", type=str, required=True, help="Key password"
    )

    test_deployment_workflow_parser.add_argument(
        "--dry_run", action="store_true", help="If true, skip actual Play Store upload"
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    try:
        if args.command == "analyze_android_project":
            result = analyze_android_project(project_path=args.project_path)

            print(result)

        if args.command == "generate_keystore":
            result = generate_keystore(
                output_path=args.output_path,
                alias=args.alias,
                key_password=args.key_password,
                store_password=args.store_password,
                validity_days=args.validity_days,
                key_size=args.key_size,
                dname=args.dname,
            )

            print(result)

        if args.command == "generate_signing_config":
            result = generate_signing_config(
                project_path=args.project_path, signing_strategy=args.signing_strategy
            )

            print(result)

        if args.command == "setup_service_account_guide":
            result = setup_service_account_guide()

            print(result)

        if args.command == "generate_github_workflow":
            result = generate_github_workflow(
                project_path=args.project_path,
                package_name=args.package_name,
                track=args.track,
                trigger_strategy=args.trigger_strategy,
                branch_name=args.branch_name,
                app_module_path=args.app_module_path,
                java_version=args.java_version,
            )

            print(result)

        if args.command == "validate_github_secrets":
            result = validate_github_secrets(
                repo_owner=args.repo_owner,
                repo_name=args.repo_name,
                github_token=args.github_token,
                required_secrets=args.required_secrets,
            )

            print(result)

        if args.command == "create_github_secrets_guide":
            result = create_github_secrets_guide(
                repo_url=args.repo_url, keystore_path=args.keystore_path
            )

            print(result)

        if args.command == "validate_play_store_setup":
            result = validate_play_store_setup(
                service_account_json_path=args.service_account_json_path,
                package_name=args.package_name,
            )

            print(result)

        if args.command == "test_deployment_workflow":
            result = test_deployment_workflow(
                project_path=args.project_path,
                keystore_path=args.keystore_path,
                store_password=args.store_password,
                key_alias=args.key_alias,
                key_password=args.key_password,
                dry_run=args.dry_run,
            )

            print(result)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

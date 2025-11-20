"""Tool to generate GitHub Actions workflow for Play Store deployment."""

from pathlib import Path
from jinja2 import Template


def generate_github_workflow(
    project_path: str,
    package_name: str,
    track: str = "internal",
    trigger_strategy: str = "manual",
    branch_name: str = "release/internal",
    app_module_path: str = "app",
    java_version: str = "17"
) -> dict:
    """Generate a complete GitHub Actions workflow file for Play Store deployment."""

    # Load template
    template_path = Path(__file__).parent.parent / "templates" / "github_workflow.yml.j2"
    template_content = template_path.read_text()
    template = Template(template_content)

    # Render workflow
    workflow_content = template.render(
        track=track,
        trigger_strategy=trigger_strategy,
        branch_name=branch_name,
        package_name=package_name,
        app_module_path=app_module_path,
        java_version=java_version
    )

    # Determine workflow file name
    workflow_filename = f"deploy-{track}.yml"
    workflow_path = f".github/workflows/{workflow_filename}"

    required_secrets = [
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
    ]

    instructions = [
        "Create .github/workflows directory if it doesn't exist",
        f"Save the workflow_content to {workflow_path}",
        "Configure the required GitHub Secrets in your repository settings",
        "Commit and push the workflow file",
    ]

    if trigger_strategy == "manual":
        instructions.append("Test with a manual workflow dispatch from GitHub Actions tab")
    elif trigger_strategy == "branch":
        instructions.append(f"Push to {branch_name} branch to trigger deployment")
    elif trigger_strategy == "tag":
        instructions.append("Create and push a version tag (e.g., v1.0.0) to trigger deployment")

    return {
        "success": True,
        "workflow_path": workflow_path,
        "workflow_content": workflow_content,
        "required_secrets": required_secrets,
        "instructions": instructions,
        "estimated_build_time": "5-10 minutes",
        "github_actions_cost": "Free for public repos, 2000 minutes/month for private repos on free tier"
    }

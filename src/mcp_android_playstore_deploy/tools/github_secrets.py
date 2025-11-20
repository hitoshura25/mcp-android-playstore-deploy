"""Tools for GitHub Secrets validation and guide creation."""

import requests
from datetime import datetime
from ..exceptions import AuthenticationError, PermissionError, NetworkError, APIError, RateLimitError


def validate_github_secrets(
    repo_owner: str,
    repo_name: str,
    github_token: str,
    required_secrets: list = None
) -> dict:
    """Validate that required GitHub Secrets are configured."""

    if required_secrets is None:
        required_secrets = [
            "SERVICE_ACCOUNT_JSON_PLAINTEXT",
            "SIGNING_KEY_STORE_BASE64",
            "SIGNING_KEY_ALIAS",
            "SIGNING_KEY_PASSWORD",
            "SIGNING_STORE_PASSWORD"
        ]

    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/secrets"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)

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
            from ..exceptions import NotFoundError
            raise NotFoundError(
                "Repository not found. Check owner/repo names and token permissions."
            )
        elif response.status_code >= 500:
            from ..exceptions import ServiceError
            raise ServiceError(
                f"GitHub API is experiencing issues (HTTP {response.status_code}). "
                "Try again later."
            )

        response.raise_for_status()
        data = response.json()

        # Extract secret names
        configured_secret_names = [secret["name"] for secret in data.get("secrets", [])]

        # Determine which secrets are missing
        missing_secrets = [s for s in required_secrets if s not in configured_secret_names]
        configured_secrets = [s for s in required_secrets if s in configured_secret_names]

        # Generate instructions for missing secrets
        instructions_for_missing = {}
        for secret in missing_secrets:
            if secret == "SERVICE_ACCOUNT_JSON_PLAINTEXT":
                instructions_for_missing[secret] = (
                    "Download the service account JSON from Google Cloud Console, "
                    "then copy its entire contents into this secret"
                )
            elif secret == "SIGNING_KEY_STORE_BASE64":
                instructions_for_missing[secret] = "Run 'base64 -w 0 your-keystore.jks' and paste the output here"
            else:
                instructions_for_missing[secret] = "Enter the value you specified when creating the keystore"

        return {
            "success": True,
            "all_secrets_present": len(missing_secrets) == 0,
            "total_required": len(required_secrets),
            "total_configured": len(configured_secrets),
            "missing_secrets": missing_secrets,
            "configured_secrets": configured_secrets,
            "instructions_for_missing": instructions_for_missing,
            "github_secrets_url": f"https://github.com/{repo_owner}/{repo_name}/settings/secrets/actions",
            "validation_timestamp": datetime.utcnow().isoformat() + "Z"
        }

    except requests.exceptions.Timeout:
        from ..exceptions import TimeoutError
        raise TimeoutError("GitHub API request timed out. Check your internet connection.")
    except requests.exceptions.ConnectionError:
        raise NetworkError("Cannot connect to GitHub API. Check your internet connection.")
    except (AuthenticationError, PermissionError, RateLimitError, NetworkError) as e:
        raise
    except Exception as e:
        raise APIError(f"GitHub API error: {str(e)}")


def create_github_secrets_guide(repo_url: str, keystore_path: str = None) -> dict:
    """Generate a comprehensive guide for creating all required GitHub Secrets."""

    # Parse repo URL to extract owner and repo name
    import re
    match = re.match(r'https://github\.com/([^/]+)/([^/]+)', repo_url)
    if match:
        repo_owner, repo_name = match.groups()
        github_secrets_url = f"https://github.com/{repo_owner}/{repo_name}/settings/secrets/actions"
    else:
        github_secrets_url = f"{repo_url}/settings/secrets/actions"

    secrets = [
        {
            "name": "SERVICE_ACCOUNT_JSON_PLAINTEXT",
            "description": "The complete contents of your Google Play service account JSON file",
            "how_to_get_value": [
                "Open the JSON file you downloaded from Google Cloud Console",
                "Copy the entire file contents (all the JSON)",
                "Paste it directly into the secret value field"
            ],
            "is_sensitive": True,
            "required": True
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
            "example_command": "base64 -w 0 release.jks" if not keystore_path else f"base64 -w 0 {keystore_path}",
            "is_sensitive": True,
            "required": True
        },
        {
            "name": "SIGNING_KEY_ALIAS",
            "description": "The alias you chose when creating your keystore",
            "how_to_get_value": [
                "This is the value you specified when creating the keystore",
                "If you forgot it, run: keytool -list -v -keystore your-keystore.jks"
            ],
            "is_sensitive": False,
            "required": True
        },
        {
            "name": "SIGNING_KEY_PASSWORD",
            "description": "The password for your signing key",
            "how_to_get_value": [
                "This is the password you set when creating the keystore key"
            ],
            "is_sensitive": True,
            "required": True
        },
        {
            "name": "SIGNING_STORE_PASSWORD",
            "description": "The password for your keystore file",
            "how_to_get_value": [
                "This is the password you set when creating the keystore"
            ],
            "is_sensitive": True,
            "required": True
        }
    ]

    step_by_step_instructions = [
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
    ]

    security_reminders = [
        "Never commit secrets to your repository",
        "Never log or print secret values",
        "Store passwords in a secure password manager",
        "Back up your keystore and passwords securely",
        "Rotate service account keys periodically"
    ]

    return {
        "success": True,
        "github_secrets_url": github_secrets_url,
        "secrets": secrets,
        "step_by_step_instructions": step_by_step_instructions,
        "security_reminders": security_reminders
    }

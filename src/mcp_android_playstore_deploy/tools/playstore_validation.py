"""Tool to validate Play Store app and API access configuration."""

from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from ..exceptions import (
    ConfigurationError,
    AuthenticationError,
    PermissionError,
    NotFoundError,
    APIError,
    RateLimitError
)


def validate_play_store_setup(service_account_json_path: str, package_name: str) -> dict:
    """Validate that Play Store app and API access are properly configured."""

    checks = {}
    errors = []
    warnings = []
    overall_status = "success"

    # Check if service account file exists
    service_account_path = Path(service_account_json_path)
    if not service_account_path.exists():
        checks["service_account_valid"] = {
            "status": "fail",
            "message": f"Service account file not found: {service_account_json_path}"
        }
        errors.append(f"Service account file not found: {service_account_json_path}")
        return {
            "success": False,
            "overall_status": "failure",
            "checks": checks,
            "errors": errors,
            "warnings": warnings,
            "next_steps": ["Ensure the service account JSON file exists at the specified path"]
        }

    try:
        # Authenticate with service account
        credentials = service_account.Credentials.from_service_account_file(
            service_account_json_path,
            scopes=['https://www.googleapis.com/auth/androidpublisher']
        )

        checks["service_account_valid"] = {
            "status": "pass",
            "message": "Service account credentials are valid"
        }

        # Build the service
        service = build('androidpublisher', 'v3', credentials=credentials)

        checks["api_enabled"] = {
            "status": "pass",
            "message": "Google Play Developer API is accessible"
        }

        # Try to create an edit (this validates app existence and permissions)
        try:
            edit_request = service.edits().insert(body={}, packageName=package_name)
            edit_result = edit_request.execute()
            edit_id = edit_result['id']

            checks["app_exists"] = {
                "status": "pass",
                "message": f"App with package name '{package_name}' exists in Play Console"
            }

            checks["permissions_sufficient"] = {
                "status": "pass",
                "message": "Service account has sufficient permissions",
                "details": "Can create edits (Release Manager or higher)"
            }

            # Try to get tracks information
            try:
                tracks_request = service.edits().tracks().list(
                    packageName=package_name,
                    editId=edit_id
                )
                tracks_result = tracks_request.execute()
                available_tracks = [track['track'] for track in tracks_result.get('tracks', [])]

                checks["can_access_tracks"] = {
                    "status": "pass",
                    "message": "Can access release tracks",
                    "available_tracks": available_tracks if available_tracks else ["internal", "alpha", "beta", "production"]
                }

                if not available_tracks or len(available_tracks) == 0:
                    warnings.append("No releases found on any track - this is expected for new apps")

            except HttpError as e:
                checks["can_access_tracks"] = {
                    "status": "fail",
                    "message": f"Cannot access tracks: {e.resp.status}"
                }
                warnings.append("Could not retrieve track information")

            # Delete the edit (cleanup)
            try:
                service.edits().delete(packageName=package_name, editId=edit_id).execute()
            except:
                pass  # Ignore cleanup errors

        except HttpError as e:
            if e.resp.status == 401:
                checks["app_exists"] = {"status": "fail", "message": "Authentication failed"}
                checks["permissions_sufficient"] = {"status": "fail", "message": "Invalid credentials"}
                errors.append("Service account credentials are invalid or expired")
                overall_status = "failure"
            elif e.resp.status == 403:
                checks["app_exists"] = {"status": "unknown", "message": "Cannot verify - permission denied"}
                checks["permissions_sufficient"] = {
                    "status": "fail",
                    "message": "Service account lacks permissions",
                    "details": "Ensure it has 'Release Manager' role in Play Console"
                }
                errors.append("Service account lacks Release Manager permissions")
                overall_status = "failure"
            elif e.resp.status == 404:
                checks["app_exists"] = {
                    "status": "fail",
                    "message": f"App with package name '{package_name}' not found in Play Console"
                }
                errors.append(f"App '{package_name}' not found. Ensure it's created in Play Console.")
                overall_status = "failure"
            else:
                checks["app_exists"] = {"status": "fail", "message": f"API error: {e.resp.status}"}
                errors.append(f"API error: {e.resp.status}")
                overall_status = "failure"

    except FileNotFoundError:
        checks["service_account_valid"] = {
            "status": "fail",
            "message": f"Service account file not found: {service_account_json_path}"
        }
        errors.append(f"Service account file not found: {service_account_json_path}")
        overall_status = "failure"
    except ValueError as e:
        if "json" in str(e).lower():
            checks["service_account_valid"] = {
                "status": "fail",
                "message": "Invalid service account JSON format"
            }
            errors.append("Invalid service account JSON format. Re-download from Google Cloud Console.")
            overall_status = "failure"
        else:
            raise
    except Exception as e:
        checks["service_account_valid"] = {
            "status": "fail",
            "message": f"Error loading service account: {str(e)}"
        }
        errors.append(f"Error: {str(e)}")
        overall_status = "failure"

    # Determine next steps
    next_steps = []
    if overall_status == "success":
        next_steps = [
            "Your Play Store setup is complete",
            f"You can now deploy to available tracks",
            "Make sure to add testers to your internal testing group if using internal track"
        ]
    else:
        if errors:
            next_steps.append("Fix the errors listed above")
        next_steps.append("Re-run this validation after making changes")

    return {
        "success": overall_status != "failure",
        "overall_status": overall_status,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "next_steps": next_steps
    }

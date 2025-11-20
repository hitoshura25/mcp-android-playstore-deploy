"""Tool to provide Google Play Service Account setup guide."""


def setup_service_account_guide() -> dict:
    """Provide interactive step-by-step guide for setting up Google Play Service Account."""

    return {
        "success": True,
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

"""Tool to generate Android keystore files for app signing."""

import base64
import os
from pathlib import Path
from .utils import run_command


def generate_keystore(
    output_path: str,
    alias: str,
    key_password: str,
    store_password: str,
    validity_days: int = 10000,
    key_size: int = 2048,
    dname: str = "CN=Android Developer"
) -> dict:
    """Generate a new Android keystore file for app signing."""

    # Validate parameters
    if not alias or not key_password or not store_password:
        return {
            "success": False,
            "error": "alias, key_password, and store_password are required"
        }

    # Ensure output directory exists
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    # Check if keystore already exists
    if output_path_obj.exists():
        return {
            "success": False,
            "error": f"Keystore file already exists at {output_path}. Delete it first or choose a different path."
        }

    try:
        # Generate keystore using keytool
        cmd = [
            "keytool",
            "-genkeypair",
            "-v",
            "-keystore", output_path,
            "-alias", alias,
            "-keyalg", "RSA",
            "-keysize", str(key_size),
            "-validity", str(validity_days),
            "-storepass", store_password,
            "-keypass", key_password,
            "-dname", dname
        ]

        run_command(cmd)

        # Set restrictive permissions
        os.chmod(output_path, 0o600)

        # Read and encode keystore to base64
        with open(output_path, "rb") as f:
            keystore_bytes = f.read()
            base64_encoded = base64.b64encode(keystore_bytes).decode('utf-8')

        return {
            "success": True,
            "keystore_path": output_path,
            "alias": alias,
            "base64_encoded": base64_encoded,
            "instructions": [
                "Save the keystore file securely",
                "Back up the keystore to multiple locations",
                "Never commit the keystore to version control",
                "Store passwords in a secure password manager"
            ],
            "github_secret_instructions": {
                "SIGNING_KEY_STORE_BASE64": "Use the base64_encoded value above",
                "SIGNING_KEY_ALIAS": alias,
                "SIGNING_KEY_PASSWORD": "[REDACTED - Use the key_password you provided]",
                "SIGNING_STORE_PASSWORD": "[REDACTED - Use the store_password you provided]"
            },
            "warning": "CRITICAL: Loss of this keystore will prevent you from updating your app on Google Play. Back it up securely."
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to generate keystore: {str(e)}"
        }

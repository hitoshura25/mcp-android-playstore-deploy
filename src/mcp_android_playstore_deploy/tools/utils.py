"""Utility functions for MCP Android Play Store Deploy tools."""

import os
import re
import subprocess
from pathlib import Path
from typing import Tuple

from ..exceptions import (
    ValidationError,
    CommandError,
    DependencyError,
    TimeoutError as MCPTimeoutError
)


def validate_project_path(project_path: str) -> Path:
    """Validate Android project path with helpful errors."""
    path = Path(project_path).resolve()

    if not path.exists():
        raise FileNotFoundError(
            f"Project path does not exist: {project_path}\n"
            "Provide an absolute path to your Android project root."
        )

    if not path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {project_path}")

    # Check for Android project markers
    has_gradle = (path / "build.gradle").exists() or (path / "build.gradle.kts").exists()
    has_settings = (path / "settings.gradle").exists() or (path / "settings.gradle.kts").exists()

    if not (has_gradle and has_settings):
        raise ValidationError(
            f"Path does not appear to be an Android project: {project_path}\n"
            "Expected to find build.gradle(.kts) and settings.gradle(.kts)"
        )

    return path


def run_command(cmd: list, cwd: str = None) -> Tuple[str, str]:
    """Run system command with comprehensive error handling."""
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
                    from ..exceptions import AuthenticationError
                    raise AuthenticationError("Incorrect keystore password.")

            raise CommandError(
                f"Command failed: {' '.join(cmd)}\n"
                f"Exit code: {result.returncode}\n"
                f"Error: {result.stderr}"
            )

        return result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        raise MCPTimeoutError(f"Command timed out after 5 minutes: {' '.join(cmd)}")
    except FileNotFoundError:
        raise DependencyError(
            f"Command not found: {cmd[0]}\nEnsure required tools are installed."
        )


def parse_gradle_file(file_path: Path) -> dict:
    """Parse Gradle build file for key configurations."""
    if not file_path.exists():
        return {}

    content = file_path.read_text()

    result = {}

    # Extract package name/namespace
    namespace_match = re.search(r'namespace\s*=\s*"([^"]+)"', content)
    if namespace_match:
        result["namespace"] = namespace_match.group(1)

    app_id_match = re.search(r'applicationId\s*=\s*"([^"]+)"', content)
    if app_id_match:
        result["package_name"] = app_id_match.group(1)

    # Extract version code
    version_code_match = re.search(r'versionCode\s*=\s*(\d+)', content)
    if version_code_match:
        result["version_code"] = int(version_code_match.group(1))

    # Extract version name
    version_name_match = re.search(r'versionName\s*=\s*"([^"]+)"', content)
    if version_name_match:
        result["version_name"] = version_name_match.group(1)

    # Extract SDK versions
    compile_sdk_match = re.search(r'compileSdk\s*=\s*(\d+)', content)
    if compile_sdk_match:
        result["compile_sdk"] = int(compile_sdk_match.group(1))

    min_sdk_match = re.search(r'minSdk\s*=\s*(\d+)', content)
    if min_sdk_match:
        result["min_sdk"] = int(min_sdk_match.group(1))

    target_sdk_match = re.search(r'targetSdk\s*=\s*(\d+)', content)
    if target_sdk_match:
        result["target_sdk"] = int(target_sdk_match.group(1))

    # Check for signing config
    result["has_signing_config"] = "signingConfigs" in content

    # Check for minify
    result["is_minify_enabled"] = re.search(r'isMinifyEnabled\s*=\s*true', content) is not None

    return result


def validate_secure_file(file_path: str) -> bool:
    """Ensure file has secure permissions (600 or 400)."""
    import stat

    st = os.stat(file_path)
    mode = st.st_mode & 0o777

    if mode not in [0o600, 0o400]:
        from ..exceptions import SecurityError
        raise SecurityError(
            f"Insecure file permissions: {oct(mode)}. "
            f"Expected 600 or 400. Run: chmod 600 {file_path}"
        )
    return True

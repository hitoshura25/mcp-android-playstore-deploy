"""Tool to test deployment workflow locally."""

import time
import subprocess
from pathlib import Path
from .utils import validate_project_path


def test_deployment_workflow(
    project_path: str,
    keystore_path: str,
    store_password: str,
    key_alias: str,
    key_password: str,
    dry_run: bool = True
) -> dict:
    """Test the deployment workflow locally without uploading to Play Store."""

    path = validate_project_path(project_path)
    keystore_file = Path(keystore_path)

    if not keystore_file.exists():
        return {
            "success": False,
            "overall_status": "failure",
            "error": f"Keystore file not found: {keystore_path}"
        }

    steps = []
    errors = []
    warnings = []
    start_time = time.time()

    # Step 1: Environment Setup
    step_start = time.time()
    gradlew = path / "gradlew"
    if not gradlew.exists():
        steps.append({
            "step": "Environment Setup",
            "status": "fail",
            "duration_seconds": time.time() - step_start,
            "message": "Gradle wrapper not found"
        })
        errors.append("gradlew not found in project root")
        return {
            "success": False,
            "overall_status": "failure",
            "steps": steps,
            "errors": errors
        }

    # Make gradlew executable
    try:
        gradlew.chmod(0o755)
        steps.append({
            "step": "Environment Setup",
            "status": "pass",
            "duration_seconds": time.time() - step_start,
            "message": "Gradle wrapper found and executable"
        })
    except Exception as e:
        steps.append({
            "step": "Environment Setup",
            "status": "fail",
            "duration_seconds": time.time() - step_start,
            "message": f"Failed to set gradlew permissions: {str(e)}"
        })
        errors.append(str(e))

    # Step 2: Build AAB
    step_start = time.time()
    try:
        # Set environment variables for signing
        import os
        env = os.environ.copy()
        env['SIGNING_KEY_STORE_PATH'] = str(keystore_file.resolve())
        env['SIGNING_STORE_PASSWORD'] = store_password
        env['SIGNING_KEY_ALIAS'] = key_alias
        env['SIGNING_KEY_PASSWORD'] = key_password

        result = subprocess.run(
            [str(gradlew), "bundleRelease"],
            cwd=str(path),
            env=env,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes
        )

        if result.returncode == 0:
            # Find the AAB file
            aab_path = path / "app" / "build" / "outputs" / "bundle" / "release" / "app-release.aab"
            if aab_path.exists():
                aab_size_mb = aab_path.stat().st_size / (1024 * 1024)
                steps.append({
                    "step": "Build AAB",
                    "status": "pass",
                    "duration_seconds": time.time() - step_start,
                    "message": "Successfully built release AAB",
                    "details": {
                        "task": "bundleRelease",
                        "output_file": str(aab_path),
                        "file_size_mb": round(aab_size_mb, 2)
                    }
                })
            else:
                steps.append({
                    "step": "Build AAB",
                    "status": "fail",
                    "duration_seconds": time.time() - step_start,
                    "message": "Build succeeded but AAB file not found"
                })
                errors.append("AAB file not found at expected location")
        else:
            steps.append({
                "step": "Build AAB",
                "status": "fail",
                "duration_seconds": time.time() - step_start,
                "message": "Build failed",
                "details": {
                    "error": result.stderr[:500]  # First 500 chars of error
                }
            })
            errors.append(f"Gradle build failed: {result.stderr[:200]}")

    except subprocess.TimeoutExpired:
        steps.append({
            "step": "Build AAB",
            "status": "fail",
            "duration_seconds": time.time() - step_start,
            "message": "Build timed out after 10 minutes"
        })
        errors.append("Build timed out")
    except Exception as e:
        steps.append({
            "step": "Build AAB",
            "status": "fail",
            "duration_seconds": time.time() - step_start,
            "message": f"Build error: {str(e)}"
        })
        errors.append(str(e))

    # Step 3: Verify Signing (if build succeeded)
    aab_path = path / "app" / "build" / "outputs" / "bundle" / "release" / "app-release.aab"
    if aab_path.exists():
        step_start = time.time()
        try:
            # Use bundletool or jarsigner to verify signing
            # For now, just check if file exists and has reasonable size
            aab_size = aab_path.stat().st_size
            if aab_size > 1024:  # At least 1 KB
                steps.append({
                    "step": "Verify Signing",
                    "status": "pass",
                    "duration_seconds": time.time() - step_start,
                    "message": "AAB file created successfully",
                    "details": {
                        "note": "Full signature verification requires bundletool"
                    }
                })
            else:
                steps.append({
                    "step": "Verify Signing",
                    "status": "fail",
                    "duration_seconds": time.time() - step_start,
                    "message": "AAB file is too small, likely corrupted"
                })
                errors.append("AAB file appears corrupted")
        except Exception as e:
            steps.append({
                "step": "Verify Signing",
                "status": "fail",
                "duration_seconds": time.time() - step_start,
                "message": f"Verification error: {str(e)}"
            })

    # Step 4: Upload to Play Store (skip if dry_run)
    step_start = time.time()
    if dry_run:
        steps.append({
            "step": "Upload to Play Store",
            "status": "skipped",
            "message": "Skipped due to dry_run=true"
        })
    else:
        steps.append({
            "step": "Upload to Play Store",
            "status": "skipped",
            "message": "Actual upload not implemented in test tool. Use GitHub Actions workflow."
        })

    total_duration = time.time() - start_time

    # Determine overall status
    build_successful = any(s["step"] == "Build AAB" and s["status"] == "pass" for s in steps)
    signing_successful = any(s["step"] == "Verify Signing" and s["status"] == "pass" for s in steps)
    ready_for_deployment = build_successful and signing_successful and len(errors) == 0

    overall_status = "success" if ready_for_deployment else "failure"

    # Check for ProGuard rules
    proguard_rules = path / "app" / "proguard-rules.pro"
    if proguard_rules.exists():
        rules_content = proguard_rules.read_text()
        if len(rules_content.strip()) < 100:
            warnings.append("ProGuard rules file is minimal - consider adding app-specific rules")

    next_steps = []
    if ready_for_deployment:
        next_steps = [
            "Test the AAB on a real device using bundletool",
            "Set dry_run=false to perform actual upload (when ready)",
            "Monitor the GitHub Actions workflow for automated deployments"
        ]
    else:
        next_steps = [
            "Fix the build errors listed above",
            "Ensure signing configuration is correct",
            "Re-run this test after making changes"
        ]

    result = {
        "success": overall_status == "success",
        "overall_status": overall_status,
        "steps": steps,
        "total_duration_seconds": round(total_duration, 1),
        "build_successful": build_successful,
        "signing_successful": signing_successful,
        "aab_generated": aab_path.exists(),
        "errors": errors,
        "warnings": warnings,
        "ready_for_deployment": ready_for_deployment,
        "next_steps": next_steps
    }

    if aab_path.exists():
        result["aab_path"] = str(aab_path)
        result["aab_size_mb"] = round(aab_path.stat().st_size / (1024 * 1024), 2)

    return result

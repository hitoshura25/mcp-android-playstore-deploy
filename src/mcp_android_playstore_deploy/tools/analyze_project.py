"""Tool to analyze Android projects for Play Store deployment readiness."""

from pathlib import Path
from .utils import validate_project_path, parse_gradle_file


def analyze_android_project(project_path: str) -> dict:
    """Analyze an Android project to understand its configuration."""

    path = validate_project_path(project_path)

    # Determine build system
    has_gradle = (path / "build.gradle").exists() or (path / "build.gradle.kts").exists()
    build_system = "gradle" if has_gradle else "unknown"

    # Find app module
    app_dir = path / "app"
    if not app_dir.exists():
        return {
            "success": False,
            "error": "Could not find app module directory",
            "recommendations": ["Ensure your project has an 'app' module"]
        }

    # Parse app build.gradle
    app_build_gradle_kts = app_dir / "build.gradle.kts"
    app_build_gradle = app_dir / "build.gradle"

    if app_build_gradle_kts.exists():
        build_gradle_path = str(app_build_gradle_kts)
        gradle_config = parse_gradle_file(app_build_gradle_kts)
    elif app_build_gradle.exists():
        build_gradle_path = str(app_build_gradle)
        gradle_config = parse_gradle_file(app_build_gradle)
    else:
        return {
            "success": False,
            "error": "Could not find app/build.gradle or app/build.gradle.kts"
        }

    # Detect project type
    project_type = detect_project_type(path)

    # Check for GitHub Actions
    github_workflows_dir = path / ".github" / "workflows"
    has_github_actions = github_workflows_dir.exists()
    github_workflows = []
    if has_github_actions:
        github_workflows = [f.name for f in github_workflows_dir.glob("*.yml")]

    # Generate recommendations
    recommendations = []
    issues = []

    if not gradle_config.get("has_signing_config", False):
        issues.append({
            "severity": "critical",
            "message": "No signing configuration found",
            "fix": "Use generate_signing_config tool to add signing configuration"
        })
        recommendations.append("Add signing configuration")

    if not gradle_config.get("is_minify_enabled", False):
        issues.append({
            "severity": "high",
            "message": "Code minification is not enabled for release builds",
            "fix": "Enable minification in release buildType"
        })
        recommendations.append("Enable code minification for release builds")

    if not has_github_actions:
        recommendations.append("Create GitHub Actions workflow")

    # Detect dependencies
    dependencies = detect_dependencies(path)

    return {
        "success": True,
        "project_type": project_type,
        "build_system": build_system,
        "package_name": gradle_config.get("package_name", gradle_config.get("namespace", "unknown")),
        "namespace": gradle_config.get("namespace", "unknown"),
        "has_signing_config": gradle_config.get("has_signing_config", False),
        "has_github_actions": has_github_actions,
        "github_workflows": github_workflows,
        "current_version_code": gradle_config.get("version_code", 1),
        "current_version_name": gradle_config.get("version_name", "1.0"),
        "gradle_jdk_version": "17",  # Default assumption
        "target_sdk": gradle_config.get("target_sdk", 34),
        "min_sdk": gradle_config.get("min_sdk", 21),
        "build_gradle_path": build_gradle_path,
        "is_minify_enabled": gradle_config.get("is_minify_enabled", False),
        "dependencies": dependencies,
        "recommendations": recommendations,
        "issues": issues
    }


def detect_project_type(path: Path) -> str:
    """Detect if project is native Android, React Native, or Flutter."""

    # Check for React Native
    if (path / "package.json").exists():
        return "react_native"

    # Check for Flutter
    if (path / "pubspec.yaml").exists():
        return "flutter"

    # Check for native Android markers
    if (path / "app" / "src" / "main" / "java").exists() or \
       (path / "app" / "src" / "main" / "kotlin").exists():
        return "native_android"

    return "unknown"


def detect_dependencies(path: Path) -> dict:
    """Detect common Android dependencies."""
    dependencies = {
        "compose": False,
        "hilt": False,
        "room": False
    }

    # Read build.gradle files
    for build_file in path.rglob("build.gradle*"):
        content = build_file.read_text()

        if "androidx.compose" in content:
            dependencies["compose"] = True
        if "com.google.dagger:hilt" in content or "dagger.hilt" in content:
            dependencies["hilt"] = True
        if "androidx.room" in content:
            dependencies["room"] = True

    return dependencies

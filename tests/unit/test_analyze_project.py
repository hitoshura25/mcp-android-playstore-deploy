"""Unit tests for analyze_android_project tool."""

import pytest
from pathlib import Path
from mcp_android_playstore_deploy.tools.analyze_project import (
    analyze_android_project,
    detect_project_type,
    detect_dependencies
)


class TestAnalyzeProject:
    """Test suite for analyze_android_project tool."""

    def test_analyze_test_android_project(self):
        """Test analyzing the test Android project fixture."""
        # Get path to test Android project
        test_project_path = Path(__file__).parent.parent / "fixtures" / "test-android-app"

        if not test_project_path.exists():
            pytest.skip("Test Android project not found")

        result = analyze_android_project(str(test_project_path))

        assert result["success"] == True
        assert result["project_type"] == "native_android"
        assert result["package_name"] == "com.test.playstore"
        assert result["build_system"] == "gradle"
        assert result["has_signing_config"] == False

    def test_invalid_path(self):
        """Test with non-existent path."""
        with pytest.raises(FileNotFoundError):
            analyze_android_project("/nonexistent/path")

    def test_detect_native_android(self, tmp_path):
        """Test detecting native Android project type."""
        # Create mock native Android structure
        (tmp_path / "app" / "src" / "main" / "java").mkdir(parents=True)

        project_type = detect_project_type(tmp_path)
        assert project_type == "native_android"

    def test_detect_react_native(self, tmp_path):
        """Test detecting React Native project type."""
        # Create package.json marker
        (tmp_path / "package.json").write_text('{"name": "test"}')

        project_type = detect_project_type(tmp_path)
        assert project_type == "react_native"

    def test_detect_flutter(self, tmp_path):
        """Test detecting Flutter project type."""
        # Create pubspec.yaml marker
        (tmp_path / "pubspec.yaml").write_text("name: test")

        project_type = detect_project_type(tmp_path)
        assert project_type == "flutter"

    def test_detect_dependencies(self, tmp_path):
        """Test detecting common Android dependencies."""
        # Create build.gradle with dependencies
        build_file = tmp_path / "build.gradle.kts"
        build_file.write_text("""
            dependencies {
                implementation("androidx.compose.ui:ui:1.0.0")
                implementation("com.google.dagger:hilt-android:2.44")
                implementation("androidx.room:room-runtime:2.5.0")
            }
        """)

        deps = detect_dependencies(tmp_path)
        assert deps["compose"] == True
        assert deps["hilt"] == True
        assert deps["room"] == True

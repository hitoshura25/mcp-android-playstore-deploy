# Test Android Project

This is a minimal Android project used for testing the mcp-android-playstore-deploy tools.

## Purpose

- Integration testing
- E2E testing
- Example for documentation

## Structure

This is a barebones native Android application with:
- Minimal dependencies (only AndroidX core and appcompat)
- Empty MainActivity
- No signing configuration (tests will add it)
- Minification disabled by default (tests will enable it)

## Building

**Note**: This project requires Android SDK and JDK 17+ to build.

```bash
cd tests/fixtures/test-android-app
./gradlew assembleDebug
```

## Using in Tests

This project is used as a fixture for:
- Testing `analyze_android_project` tool
- Testing `generate_signing_config` tool
- Testing `generate_github_workflow` tool
- Testing `test_deployment_workflow` tool
- Integration and E2E tests

## Updating

When updating Android SDK versions or dependencies:
1. Update `compileSdk` and `targetSdk` in `app/build.gradle.kts`
2. Update dependencies to latest stable versions
3. Update plugin versions in root `build.gradle.kts`
4. Test that all MCP server tools still work correctly
5. Run full test suite

## Notes

- This project is intentionally minimal to keep build times fast
- It has no UI beyond an empty activity
- Gradle wrapper files are not included to keep the repository clean
- Tests should initialize Gradle wrapper when needed

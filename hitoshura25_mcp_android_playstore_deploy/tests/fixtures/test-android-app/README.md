# Test Android Project

This is a minimal Android project used for testing the mcp-android-playstore-deploy tools.

## Purpose
- Integration testing
- E2E testing
- Example for documentation

## Building
```bash
cd tests/fixtures/test-android-app
./gradlew assembleDebug
```

## Updating
When updating Android SDK versions or dependencies:
1. Update `compileSdk` and `targetSdk` in `app/build.gradle.kts`
2. Update dependencies to latest stable versions
3. Test that all MCP server tools still work correctly
4. Run full test suite

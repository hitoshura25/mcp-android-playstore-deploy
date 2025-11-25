# Implementation Summary: ProGuard Mapping & Release Notes

## Quick Overview

Add support for two critical Play Store features to `generate_github_workflow`:

### 1. ProGuard Mapping Files
- **Why**: Deobfuscate crash reports in Play Console
- **How**: Auto-detect from `isMinifyEnabled` setting
- **Path**: `app/build/outputs/mapping/release/mapping.txt`

### 2. Release Notes
- **Why**: Show "What's New" to users
- **How**: Point to localized directory
- **Path**: `distribution/whatsnew/` (default)

## Changes Required

### Function Signature (generator.py:868)

```python
def generate_github_workflow(
    # ... existing parameters ...
    include_mapping_file: bool = None,        # NEW: Auto-detect if None
    mapping_file_path: str = None,            # NEW: Override default path
    include_release_notes: bool = True,       # NEW: Enabled by default
    release_notes_directory: str = None,      # NEW: Default "distribution/whatsnew"
) -> Dict[str, Any]:
```

### Workflow Template Update (generator.py:1039-1048)

**Current:**
```yaml
- name: Upload to Google Play {track} Track
  uses: r0adkll/upload-google-play@v1
  with:
    serviceAccountJsonPlainText: ${{ secrets.SERVICE_ACCOUNT_JSON_PLAINTEXT }}
    packageName: {package_name}
    releaseFiles: {app_module_path}/build/outputs/bundle/release/app-release.aab
    track: {track}
    status: completed
```

**Updated:**
```yaml
- name: Upload to Google Play {track} Track
  uses: r0adkll/upload-google-play@v1
  with:
    serviceAccountJsonPlainText: ${{ secrets.SERVICE_ACCOUNT_JSON_PLAINTEXT }}
    packageName: {package_name}
    releaseFiles: {app_module_path}/build/outputs/bundle/release/app-release.aab
    track: {track}
    status: completed
    mappingFile: app/build/outputs/mapping/release/mapping.txt  # NEW (if enabled)
    whatsNewDirectory: distribution/whatsnew                    # NEW (if enabled)
```

## Auto-Detection Logic

```python
# If include_mapping_file is None, auto-detect
if include_mapping_file is None:
    analysis = analyze_android_project(project_path)
    include_mapping_file = analysis.get("is_minify_enabled", False)
```

## Return Value Additions

```python
return {
    # ... existing fields ...
    "mapping_file_config": {
        "enabled": True/False,
        "path": "app/build/outputs/mapping/release/mapping.txt",
        "auto_detected": True/False,
        "why_important": "..."
    },
    "release_notes_config": {
        "enabled": True/False,
        "directory": "distribution/whatsnew",
        "setup_instructions": "...",
        "supported_locales": [...]
    }
}
```

## Usage Examples

### Auto-detection (Recommended)
```python
result = generate_github_workflow(
    project_path="/path/to/project",
    package_name="com.example.app"
)
# ProGuard: Auto-detected from isMinifyEnabled
# Release Notes: Enabled by default
```

### Explicit Control
```python
result = generate_github_workflow(
    project_path="/path/to/project",
    package_name="com.example.app",
    include_mapping_file=True,
    include_release_notes=True,
    release_notes_directory="custom/path"
)
```

### Disable Both
```python
result = generate_github_workflow(
    project_path="/path/to/project",
    package_name="com.example.app",
    include_mapping_file=False,
    include_release_notes=False
)
```

## Implementation Checklist

### Code Changes
- [ ] Update function signature (generator.py:868)
- [ ] Add parameter validation
- [ ] Implement auto-detection logic
- [ ] Update workflow template generation
- [ ] Add conditional instructions
- [ ] Update return dictionary
- [ ] Add constants (RELEASE_NOTES_SETUP_GUIDE, COMMON_PLAY_STORE_LOCALES)

### MCP Tool Updates
- [ ] Update tool registration (server.py:131-148)
- [ ] Add new parameters to tool definition
- [ ] Update docstring

### Documentation
- [ ] Update main spec (specs/mcp-playstore-deploy-implementation.md)
- [ ] Update README.md with advanced features section
- [ ] Update CLAUDE-USAGE-GUIDE.md

### Testing
- [ ] Unit tests for default parameters
- [ ] Unit tests for explicit enable/disable
- [ ] Unit tests for auto-detection
- [ ] Unit tests for custom paths
- [ ] Integration tests with real Android project
- [ ] YAML validity tests

## Files to Modify

1. `hitoshura25_mcp_android_playstore_deploy/generator.py`
2. `hitoshura25_mcp_android_playstore_deploy/server.py`
3. `specs/mcp-playstore-deploy-implementation.md`
4. `README.md`
5. `CLAUDE-USAGE-GUIDE.md`
6. `hitoshura25_mcp_android_playstore_deploy/tests/test_generator.py` (new)

## Breaking Changes

**None** - All new parameters are optional with sensible defaults.

## Migration Path

Existing users: No action required. Workflows continue working.
To get new features: Regenerate workflow with `generate_github_workflow`.

## Success Metrics

- ✅ No breaking changes
- ✅ Auto-detection works correctly
- ✅ Generated workflows are valid YAML
- ✅ Instructions are clear and helpful
- ✅ Test coverage >80%

## Estimated Effort

- **Development**: 4-6 hours
- **Testing**: 2-3 hours
- **Documentation**: 1-2 hours
- **Total**: ~8 hours

---

**See full specification**: `specs/proguard-mapping-and-release-notes-support.md`

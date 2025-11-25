# ProGuard Mapping and Release Notes Support - Specification

## Executive Summary

This specification details the enhancement of the `generate_github_workflow` tool to support:
1. **ProGuard mapping files** - For crash deobfuscation in Play Console
2. **Release notes** - Localized "What's New" content for each release

These features leverage existing capabilities of the r0adkll/upload-google-play GitHub Action.

---

## Current State Analysis

### Current Implementation (generator.py:868-1100)

**Function Signature:**
```python
def generate_github_workflow(
    project_path: str,
    package_name: str,
    track: str = None,              # Default: "internal"
    trigger_strategy: str = None,   # Default: "manual"
    branch_name: str = None,        # Default: f"release/{track}"
    app_module_path: str = None,    # Default: "app"
    java_version: str = None,       # Default: "17"
) -> Dict[str, Any]:
```

**Current Workflow Template (lines 1000-1053):**
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

**Missing Parameters:**
- `mappingFile` - ProGuard mapping for deobfuscation
- `whatsNewDirectory` - Release notes directory

### Android Build Configuration Analysis

From `analyze_android_project` (generator.py:73-315):
- Detects if ProGuard/R8 is enabled via `is_minify_enabled` check (line 227)
- Checks for `isMinifyEnabled = true` or `minifyEnabled true` in build files
- Standard ProGuard files location: `proguard-rules.pro` (lines 641-643, 699-701)

**ProGuard Mapping Output Location:**
- When `minifyEnabled = true`, Gradle outputs mapping file to:
  ```
  {app_module_path}/build/outputs/mapping/{buildType}/mapping.txt
  ```
- For release builds: `app/build/outputs/mapping/release/mapping.txt`

---

## Requirements

### 1. ProGuard Mapping File Support

**User Story:**
> As an Android developer, when I enable code minification (ProGuard/R8) for my release builds, I want the mapping file automatically uploaded to Play Console so I can deobfuscate crash reports.

**Acceptance Criteria:**
- ✅ If project has `minifyEnabled = true`, include `mappingFile` parameter in workflow
- ✅ Use standard Gradle output path: `{app_module_path}/build/outputs/mapping/release/mapping.txt`
- ✅ Make this configurable via optional parameter (default: auto-detect from project analysis)
- ✅ Provide clear documentation about why this is important
- ✅ Handle case where mapping file doesn't exist (build will fail with clear error)

**Technical Details:**
- r0adkll action parameter: `mappingFile: path/to/mapping.txt`
- Only include if minification is enabled
- Path is relative to repository root

### 2. Release Notes Support

**User Story:**
> As an Android developer, I want to provide localized "What's New" release notes for each deployment so users see relevant update information in their language.

**Acceptance Criteria:**
- ✅ Support `whatsNewDirectory` parameter pointing to release notes
- ✅ Use standard directory structure: `distribution/whatsnew/`
- ✅ Make this configurable via optional parameter
- ✅ Provide clear setup instructions for directory structure
- ✅ Include example release notes files in documentation
- ✅ Handle case where directory doesn't exist (graceful skip or clear error)

**Technical Details:**
- r0adkll action parameter: `whatsNewDirectory: distribution/whatsnew/`
- Directory structure (Google Play standard):
  ```
  distribution/
    whatsnew/
      en-US/           # English (US)
        whatsnew
      de-DE/           # German
        whatsnew
      es-ES/           # Spanish
        whatsnew
  ```
- Each `whatsnew` file contains plain text (max 500 characters)
- Locales follow BCP 47 format (e.g., en-US, fr-FR, ja-JP)

---

## Proposed Changes

### 1. Update `generate_github_workflow` Function Signature

**Add New Optional Parameters:**

```python
def generate_github_workflow(
    project_path: str,
    package_name: str,
    track: str = None,
    trigger_strategy: str = None,
    branch_name: str = None,
    app_module_path: str = None,
    java_version: str = None,
    # NEW PARAMETERS:
    include_mapping_file: bool = None,        # Auto-detect if None
    mapping_file_path: str = None,            # Override default path
    include_release_notes: bool = True,       # Enable by default
    release_notes_directory: str = None,      # Default: "distribution/whatsnew"
) -> Dict[str, Any]:
```

**Parameter Details:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_mapping_file` | bool | None (auto-detect) | Whether to include ProGuard mapping. If None, auto-detect from `analyze_android_project` |
| `mapping_file_path` | str | `{app_module_path}/build/outputs/mapping/release/mapping.txt` | Override default mapping file path |
| `include_release_notes` | bool | True | Whether to include release notes directory |
| `release_notes_directory` | str | `distribution/whatsnew` | Path to release notes directory |

### 2. Auto-Detection Logic

**ProGuard Mapping Auto-Detection:**

```python
# If include_mapping_file is None, auto-detect
if include_mapping_file is None:
    # Call analyze_android_project to check minification
    analysis = analyze_android_project(project_path)
    include_mapping_file = analysis.get("is_minify_enabled", False)

# Set default mapping file path
if mapping_file_path is None:
    mapping_file_path = f"{app_module_path}/build/outputs/mapping/release/mapping.txt"
```

**Release Notes Default:**

```python
# Set default release notes directory
if release_notes_directory is None:
    release_notes_directory = "distribution/whatsnew"
```

### 3. Updated Workflow Template

**New Upload Step with Conditional Parameters:**

```yaml
      - name: Upload to Google Play {track} Track
        uses: r0adkll/upload-google-play@v1
        with:
          serviceAccountJsonPlainText: ${{{{ secrets.SERVICE_ACCOUNT_JSON_PLAINTEXT }}}}
          packageName: {package_name}
          releaseFiles: {app_module_path}/build/outputs/bundle/release/app-release.aab
          track: {track}
          status: completed
          {mapping_file_line}
          {release_notes_line}
```

**Template Generation Logic:**

```python
# Conditionally add mappingFile parameter
if include_mapping_file:
    mapping_file_line = f"mappingFile: {mapping_file_path}"
else:
    mapping_file_line = ""

# Conditionally add whatsNewDirectory parameter
if include_release_notes:
    release_notes_line = f"whatsNewDirectory: {release_notes_directory}"
else:
    release_notes_line = ""

# Remove empty lines from final template
workflow_content = "\n".join(
    line for line in workflow_content.split("\n")
    if line.strip()
)
```

### 4. Updated Return Value

**Add New Fields to Response:**

```python
return {
    "success": True,
    "workflow_path": workflow_path,
    "workflow_content": workflow_content,
    "required_secrets": required_secrets,
    "instructions": [
        "Create .github/workflows directory if it doesn't exist",
        "Save the workflow_content to the workflow_path",
        "Configure the required GitHub Secrets",
        # NEW INSTRUCTIONS:
        *mapping_instructions,
        *release_notes_instructions,
        "Commit and push the workflow file",
        "Test with a manual workflow dispatch",
    ],
    # NEW FIELDS:
    "mapping_file_config": {
        "enabled": include_mapping_file,
        "path": mapping_file_path if include_mapping_file else None,
        "auto_detected": include_mapping_file is None,
    },
    "release_notes_config": {
        "enabled": include_release_notes,
        "directory": release_notes_directory if include_release_notes else None,
        "setup_instructions": release_notes_setup_guide,
    },
    "estimated_build_time": "5-10 minutes",
    "github_actions_cost": "Free for public repos, 2000 minutes/month for private repos on free tier",
}
```

**Conditional Instructions:**

```python
# ProGuard mapping instructions (if enabled)
mapping_instructions = []
if include_mapping_file:
    mapping_instructions = [
        f"Ensure ProGuard/R8 is enabled (isMinifyEnabled = true) in your release buildType",
        f"The mapping file will be generated at: {mapping_file_path}",
        "This mapping file is essential for deobfuscating crash reports in Play Console",
    ]

# Release notes instructions (if enabled)
release_notes_instructions = []
if include_release_notes:
    release_notes_instructions = [
        f"Create release notes directory: {release_notes_directory}",
        "Add locale-specific subdirectories (e.g., en-US, de-DE)",
        "Create 'whatsnew' file in each locale directory with release notes (max 500 chars)",
        "See release_notes_config.setup_instructions for detailed guide",
    ]

# Release notes setup guide (detailed)
release_notes_setup_guide = """
# Setting Up Release Notes

1. Create the directory structure:
   ```bash
   mkdir -p distribution/whatsnew/en-US
   ```

2. Create a whatsnew file for each locale:
   ```bash
   cat > distribution/whatsnew/en-US/whatsnew << 'EOF'
   - New feature: Dark mode support
   - Fixed: Crash when opening settings
   - Improved: Performance optimizations
   EOF
   ```

3. Supported locales (examples):
   - en-US (English - United States)
   - en-GB (English - United Kingdom)
   - de-DE (German - Germany)
   - es-ES (Spanish - Spain)
   - fr-FR (French - France)
   - it-IT (Italian - Italy)
   - ja-JP (Japanese - Japan)
   - ko-KR (Korean - Korea)
   - pt-BR (Portuguese - Brazil)
   - ru-RU (Russian - Russia)
   - zh-CN (Chinese - China)
   - zh-TW (Chinese - Taiwan)

4. File format:
   - Plain text file named 'whatsnew' (no extension)
   - Maximum 500 characters
   - Use bullet points or short paragraphs
   - Focus on user-visible changes

5. Example structure:
   ```
   distribution/
     whatsnew/
       en-US/
         whatsnew
       de-DE/
         whatsnew
       es-ES/
         whatsnew
   ```

6. Testing:
   - Commit the directory to your repository
   - The workflow will automatically include these notes
   - Notes appear in Play Console for each release
   - Users see notes in the appropriate language
"""
```

---

## Implementation Details

### Code Changes

**File:** `hitoshura25_mcp_android_playstore_deploy/generator.py`

**Location:** Function `generate_github_workflow` (lines 868-1100)

**Changes Required:**

1. **Update function signature** (line 868-876)
   - Add 4 new optional parameters

2. **Add parameter validation** (after line 949)
   ```python
   # Validate new parameters
   if mapping_file_path is not None:
       mapping_file_path = validate_string_input(
           mapping_file_path,
           max_length=200,
           allowed_pattern=r"^[a-zA-Z0-9/_.-]+$",
           field_name="mapping_file_path",
       )

   if release_notes_directory is not None:
       release_notes_directory = validate_string_input(
           release_notes_directory,
           max_length=200,
           allowed_pattern=r"^[a-zA-Z0-9/_.-]+$",
           field_name="release_notes_directory",
       )
   ```

3. **Add auto-detection logic** (after line 983)
   ```python
   # Auto-detect ProGuard mapping if not explicitly set
   if include_mapping_file is None:
       # Analyze project to check if minification is enabled
       analysis = analyze_android_project(project_path)
       include_mapping_file = analysis.get("is_minify_enabled", False)

   # Set default paths
   if mapping_file_path is None:
       mapping_file_path = f"{app_module_path}/build/outputs/mapping/release/mapping.txt"

   if include_release_notes and release_notes_directory is None:
       release_notes_directory = "distribution/whatsnew"
   ```

4. **Update workflow template** (lines 1039-1048)
   ```python
   # Build upload step parameters
   upload_params = [
       f"serviceAccountJsonPlainText: ${{{{ secrets.SERVICE_ACCOUNT_JSON_PLAINTEXT }}}}",
       f"packageName: {package_name}",
       f"releaseFiles: {app_module_path}/build/outputs/bundle/release/app-release.aab",
       f"track: {track}",
       "status: completed",
   ]

   if include_mapping_file:
       upload_params.append(f"mappingFile: {mapping_file_path}")

   if include_release_notes:
       upload_params.append(f"whatsNewDirectory: {release_notes_directory}")

   upload_params_yaml = "\n          ".join(upload_params)

   upload_step = f"""      - name: Upload to Google Play {track} Track
        uses: r0adkll/upload-google-play@v1
        with:
          {upload_params_yaml}"""
   ```

5. **Build conditional instructions** (before line 1085)
   ```python
   # Build instructions list
   instructions = [
       "Create .github/workflows directory if it doesn't exist",
       "Save the workflow_content to the workflow_path",
       "Configure the required GitHub Secrets",
   ]

   # Add mapping file instructions
   if include_mapping_file:
       instructions.extend([
           "",  # Blank line for readability
           "ProGuard Mapping Configuration:",
           f"  - Ensure isMinifyEnabled = true in {app_module_path}/build.gradle.kts",
           f"  - Mapping file will be at: {mapping_file_path}",
           "  - This is crucial for crash deobfuscation in Play Console",
       ])

   # Add release notes instructions
   if include_release_notes:
       instructions.extend([
           "",  # Blank line
           "Release Notes Setup:",
           f"  - Create directory: {release_notes_directory}",
           "  - Add locale subdirectories (e.g., en-US, de-DE, es-ES)",
           "  - Create 'whatsnew' file in each with release notes (max 500 chars)",
           "  - See 'release_notes_config.setup_instructions' for detailed guide",
       ])

   instructions.extend([
       "",  # Blank line
       "Final Steps:",
       "  - Commit and push the workflow file",
       "  - Test with a manual workflow dispatch",
   ])
   ```

6. **Update return dictionary** (lines 1085-1100)
   ```python
   return {
       "success": True,
       "workflow_path": workflow_path,
       "workflow_content": workflow_content,
       "required_secrets": required_secrets,
       "instructions": instructions,
       "mapping_file_config": {
           "enabled": include_mapping_file,
           "path": mapping_file_path if include_mapping_file else None,
           "auto_detected": include_mapping_file is None,
           "why_important": (
               "ProGuard mapping files allow Google Play Console to deobfuscate "
               "crash stack traces, making it possible to debug production crashes. "
               "Without this file, crash reports will show obfuscated class and method names."
           ) if include_mapping_file else None,
       },
       "release_notes_config": {
           "enabled": include_release_notes,
           "directory": release_notes_directory if include_release_notes else None,
           "setup_instructions": RELEASE_NOTES_SETUP_GUIDE if include_release_notes else None,
           "supported_locales": COMMON_PLAY_STORE_LOCALES if include_release_notes else None,
       },
       "estimated_build_time": "5-10 minutes",
       "github_actions_cost": "Free for public repos, 2000 minutes/month for private repos on free tier",
   }
   ```

7. **Add constants** (top of generator.py, after line 30)
   ```python
   # Release notes setup guide
   RELEASE_NOTES_SETUP_GUIDE = """
   [Include the full guide from earlier in this spec]
   """

   # Common Play Store locales
   COMMON_PLAY_STORE_LOCALES = [
       "en-US", "en-GB", "de-DE", "es-ES", "fr-FR",
       "it-IT", "ja-JP", "ko-KR", "pt-BR", "ru-RU",
       "zh-CN", "zh-TW", "ar", "hi-IN", "id",
   ]
   ```

---

## MCP Server Tool Updates

### Update Tool Registration

**File:** `hitoshura25_mcp_android_playstore_deploy/server.py`

**Current Tool Definition** (lines 131-148):

```python
@mcp.tool()
async def generate_github_workflow(
    project_path: str,
    package_name: str,
    track: str = "internal",
    trigger_strategy: str = "manual",
    branch_name: str = None,
    app_module_path: str = "app",
    java_version: str = "17",
) -> dict:
```

**Updated Tool Definition:**

```python
@mcp.tool()
async def generate_github_workflow(
    project_path: str,
    package_name: str,
    track: str = "internal",
    trigger_strategy: str = "manual",
    branch_name: str = None,
    app_module_path: str = "app",
    java_version: str = "17",
    include_mapping_file: bool = None,
    mapping_file_path: str = None,
    include_release_notes: bool = True,
    release_notes_directory: str = None,
) -> dict:
    """Generate a complete GitHub Actions workflow file for Play Store deployment

    Args:
        project_path: Path to Android project
        package_name: Android app package name
        track: Play Store release track (internal, alpha, beta, production)
        trigger_strategy: How to trigger the workflow (manual, branch, tag)
        branch_name: Branch name to trigger on if trigger_strategy is branch
        app_module_path: Path to app module relative to project root
        java_version: Java/JDK version to use for builds
        include_mapping_file: Include ProGuard mapping file (auto-detects if None)
        mapping_file_path: Override default ProGuard mapping file path
        include_release_notes: Include release notes directory
        release_notes_directory: Path to release notes directory

    Returns:
        Workflow configuration with setup instructions
    """
    result = generator.generate_github_workflow(
        project_path=project_path,
        package_name=package_name,
        track=track,
        trigger_strategy=trigger_strategy,
        branch_name=branch_name,
        app_module_path=app_module_path,
        java_version=java_version,
        include_mapping_file=include_mapping_file,
        mapping_file_path=mapping_file_path,
        include_release_notes=include_release_notes,
        release_notes_directory=release_notes_directory,
    )

    if inspect.isawaitable(result):
        return await result
    return result
```

---

## Documentation Updates

### 1. Update Main Specification

**File:** `specs/mcp-playstore-deploy-implementation.md`

**Section to Update:** Tool 5: `generate_github_workflow` (lines 332-478)

**Add New Parameters:**

```markdown
#### Tool 5: `generate_github_workflow`

**Purpose**: Generate a complete GitHub Actions workflow file for Play Store deployment.

**Parameters**:
```json
{
  "project_path": {
    "type": "string",
    "description": "Path to Android project",
    "required": true
  },
  "package_name": {
    "type": "string",
    "description": "Android app package name",
    "required": true
  },
  "track": {
    "type": "string",
    "description": "Play Store release track",
    "required": false,
    "default": "internal",
    "enum": ["internal", "alpha", "beta", "production"]
  },
  "trigger_strategy": {
    "type": "string",
    "description": "How to trigger the workflow",
    "required": false,
    "default": "manual",
    "enum": ["manual", "branch", "tag"]
  },
  "branch_name": {
    "type": "string",
    "description": "Branch name to trigger on (if trigger_strategy=branch)",
    "required": false,
    "default": "release/internal"
  },
  "app_module_path": {
    "type": "string",
    "description": "Path to app module",
    "required": false,
    "default": "app"
  },
  "java_version": {
    "type": "string",
    "description": "Java/JDK version to use",
    "required": false,
    "default": "17"
  },
  "include_mapping_file": {
    "type": "boolean",
    "description": "Include ProGuard/R8 mapping file for crash deobfuscation. If null, auto-detects from project configuration.",
    "required": false,
    "default": null
  },
  "mapping_file_path": {
    "type": "string",
    "description": "Override default ProGuard mapping file path",
    "required": false,
    "default": "app/build/outputs/mapping/release/mapping.txt"
  },
  "include_release_notes": {
    "type": "boolean",
    "description": "Include release notes directory for 'What's New' content",
    "required": false,
    "default": true
  },
  "release_notes_directory": {
    "type": "string",
    "description": "Path to release notes directory",
    "required": false,
    "default": "distribution/whatsnew"
  }
}
```
```

### 2. Update README.md

**File:** `README.md`

**Add Section:** "Advanced Features"

```markdown
## Advanced Features

### ProGuard Mapping Files

When code minification is enabled (`isMinifyEnabled = true`), ProGuard/R8 obfuscates your code for security and size reduction. However, this makes crash reports unreadable.

The MCP server automatically includes ProGuard mapping files in your deployments:

```python
# Auto-detection (recommended)
generate_github_workflow(
    project_path="/path/to/project",
    package_name="com.example.app",
    # include_mapping_file defaults to None, which auto-detects from project
)

# Explicit control
generate_github_workflow(
    project_path="/path/to/project",
    package_name="com.example.app",
    include_mapping_file=True,  # Force include
    mapping_file_path="app/build/outputs/mapping/release/mapping.txt"
)
```

**Why This Matters:**
- Play Console uses mapping files to deobfuscate crash stack traces
- Without mapping files, crashes show obfuscated names like `a.b.c.d()`
- With mapping files, crashes show real class/method names for debugging

### Release Notes

Provide localized "What's New" content for each release:

1. **Create directory structure:**
   ```bash
   mkdir -p distribution/whatsnew/en-US
   ```

2. **Add release notes:**
   ```bash
   cat > distribution/whatsnew/en-US/whatsnew << 'EOF'
   - New: Dark mode support
   - Fixed: Settings crash
   - Improved: Performance
   EOF
   ```

3. **Supported locales:** en-US, de-DE, es-ES, fr-FR, ja-JP, and more

4. **Generate workflow:**
   ```python
   generate_github_workflow(
       project_path="/path/to/project",
       package_name="com.example.app",
       include_release_notes=True,  # Default
       release_notes_directory="distribution/whatsnew"
   )
   ```

The workflow will automatically include release notes for each deployment.
```

### 3. Update CLAUDE-USAGE-GUIDE.md

**File:** `CLAUDE-USAGE-GUIDE.md`

**Update Section:** "Next Steps After Setup" (lines 374-383)

Change from:
```markdown
1. **Configure release notes** - Add a `whatsnew` directory for release descriptions
2. **Set up staged rollouts** - Roll out to small percentage first
```

To:
```markdown
1. **Release notes are already configured!** - The workflow includes `distribution/whatsnew/` by default
   - Add locale directories: `mkdir -p distribution/whatsnew/en-US`
   - Create `whatsnew` file with your release notes (max 500 chars)

2. **ProGuard mapping is auto-configured** - If you have `isMinifyEnabled = true`, mappings are included
   - No manual setup needed
   - Enables crash deobfuscation in Play Console
```

---

## Testing Strategy

### Unit Tests

**File:** `hitoshura25_mcp_android_playstore_deploy/tests/test_generator.py`

**New Test Cases:**

```python
class TestGenerateGithubWorkflow:
    """Tests for generate_github_workflow function"""

    def test_default_parameters(self):
        """Test workflow generation with default parameters"""
        result = generate_github_workflow(
            project_path="/fake/path",
            package_name="com.example.app"
        )

        assert result["success"] is True
        assert "mappingFile" not in result["workflow_content"]  # Auto-detect, no minify
        assert "whatsNewDirectory: distribution/whatsnew" in result["workflow_content"]  # Default enabled

    def test_proguard_mapping_explicit_enable(self):
        """Test explicit ProGuard mapping inclusion"""
        result = generate_github_workflow(
            project_path="/fake/path",
            package_name="com.example.app",
            include_mapping_file=True
        )

        assert result["success"] is True
        assert "mappingFile: app/build/outputs/mapping/release/mapping.txt" in result["workflow_content"]
        assert result["mapping_file_config"]["enabled"] is True

    def test_proguard_mapping_auto_detect(self, tmp_path):
        """Test ProGuard mapping auto-detection"""
        # Create test project with minification enabled
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()

        app_dir = project_dir / "app"
        app_dir.mkdir()

        build_file = app_dir / "build.gradle.kts"
        build_file.write_text("""
        android {
            buildTypes {
                release {
                    isMinifyEnabled = true
                }
            }
        }
        """)

        (project_dir / "settings.gradle.kts").write_text("")

        result = generate_github_workflow(
            project_path=str(project_dir),
            package_name="com.example.app",
            include_mapping_file=None  # Auto-detect
        )

        assert result["success"] is True
        assert "mappingFile" in result["workflow_content"]
        assert result["mapping_file_config"]["enabled"] is True
        assert result["mapping_file_config"]["auto_detected"] is True

    def test_custom_mapping_path(self):
        """Test custom ProGuard mapping path"""
        result = generate_github_workflow(
            project_path="/fake/path",
            package_name="com.example.app",
            include_mapping_file=True,
            mapping_file_path="custom/path/to/mapping.txt"
        )

        assert "mappingFile: custom/path/to/mapping.txt" in result["workflow_content"]

    def test_release_notes_enabled_by_default(self):
        """Test release notes are enabled by default"""
        result = generate_github_workflow(
            project_path="/fake/path",
            package_name="com.example.app"
        )

        assert "whatsNewDirectory: distribution/whatsnew" in result["workflow_content"]
        assert result["release_notes_config"]["enabled"] is True

    def test_release_notes_disabled(self):
        """Test disabling release notes"""
        result = generate_github_workflow(
            project_path="/fake/path",
            package_name="com.example.app",
            include_release_notes=False
        )

        assert "whatsNewDirectory" not in result["workflow_content"]
        assert result["release_notes_config"]["enabled"] is False

    def test_custom_release_notes_directory(self):
        """Test custom release notes directory"""
        result = generate_github_workflow(
            project_path="/fake/path",
            package_name="com.example.app",
            release_notes_directory="custom/whatsnew"
        )

        assert "whatsNewDirectory: custom/whatsnew" in result["workflow_content"]

    def test_both_features_enabled(self):
        """Test workflow with both ProGuard and release notes"""
        result = generate_github_workflow(
            project_path="/fake/path",
            package_name="com.example.app",
            include_mapping_file=True,
            include_release_notes=True
        )

        content = result["workflow_content"]
        assert "mappingFile" in content
        assert "whatsNewDirectory" in content

    def test_instructions_include_mapping_setup(self):
        """Test instructions include ProGuard setup when enabled"""
        result = generate_github_workflow(
            project_path="/fake/path",
            package_name="com.example.app",
            include_mapping_file=True
        )

        instructions = "\n".join(result["instructions"])
        assert "ProGuard" in instructions or "mapping" in instructions.lower()
        assert "deobfuscat" in instructions.lower()

    def test_instructions_include_release_notes_setup(self):
        """Test instructions include release notes setup"""
        result = generate_github_workflow(
            project_path="/fake/path",
            package_name="com.example.app",
            include_release_notes=True
        )

        instructions = "\n".join(result["instructions"])
        assert "whatsnew" in instructions.lower() or "release notes" in instructions.lower()
        assert result["release_notes_config"]["setup_instructions"] is not None
```

### Integration Tests

**File:** `hitoshura25_mcp_android_playstore_deploy/tests/integration/test_full_workflow.py`

```python
class TestFullWorkflowWithProGuard:
    """Integration tests for complete workflow with ProGuard and release notes"""

    def test_workflow_with_minification(self, test_android_project):
        """Test workflow generation for project with minification"""
        # Assume test_android_project fixture provides a real Android project

        # Enable minification in test project
        build_file = test_android_project / "app" / "build.gradle.kts"
        content = build_file.read_text()
        content = content.replace("isMinifyEnabled = false", "isMinifyEnabled = true")
        build_file.write_text(content)

        # Generate workflow
        result = generate_github_workflow(
            project_path=str(test_android_project),
            package_name="com.test.playstore",
            include_mapping_file=None  # Auto-detect
        )

        assert result["success"] is True
        assert result["mapping_file_config"]["enabled"] is True

        # Verify workflow YAML is valid
        import yaml
        workflow = yaml.safe_load(result["workflow_content"])

        upload_step = next(
            step for job in workflow["jobs"].values()
            for step in job["steps"]
            if "upload-google-play" in step.get("uses", "")
        )

        assert "mappingFile" in upload_step["with"]

    def test_workflow_yaml_validity(self):
        """Test generated workflow is valid YAML"""
        result = generate_github_workflow(
            project_path="/fake/path",
            package_name="com.example.app",
            include_mapping_file=True,
            include_release_notes=True
        )

        import yaml
        try:
            workflow = yaml.safe_load(result["workflow_content"])
            assert workflow is not None
            assert "jobs" in workflow
        except yaml.YAMLError as e:
            pytest.fail(f"Generated workflow is not valid YAML: {e}")
```

---

## Example Usage

### Scenario 1: Auto-Detection (Recommended)

```python
# Claude Code conversation:
# User: "Generate a GitHub workflow for my app"

result = generate_github_workflow(
    project_path="/Users/vinayak/health-sync-app",
    package_name="io.github.hitoshura25.healthsyncapp"
)

# If project has isMinifyEnabled = true:
#   - Automatically includes mappingFile
#   - result["mapping_file_config"]["enabled"] = True
#   - result["mapping_file_config"]["auto_detected"] = True

# Always includes release notes by default:
#   - result["release_notes_config"]["enabled"] = True
#   - Instructions include setup guide
```

### Scenario 2: Explicit Control

```python
# User wants full control
result = generate_github_workflow(
    project_path="/Users/vinayak/health-sync-app",
    package_name="io.github.hitoshura25.healthsyncapp",
    include_mapping_file=True,          # Force include
    include_release_notes=True,         # Explicit enable
    release_notes_directory="release/notes"  # Custom path
)
```

### Scenario 3: Minimal Setup (No Extras)

```python
# User doesn't want release notes or mapping
result = generate_github_workflow(
    project_path="/Users/vinayak/health-sync-app",
    package_name="io.github.hitoshura25.healthsyncapp",
    include_mapping_file=False,
    include_release_notes=False
)
```

---

## Generated Workflow Example

**With ProGuard and Release Notes Enabled:**

```yaml
name: Deploy to Play Store internal

on:
  workflow_dispatch:

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'
          cache: 'gradle'

      - name: Grant execute permission for gradlew
        run: chmod +x gradlew

      - name: Decode Keystore
        run: |
          echo "${{ secrets.SIGNING_KEY_STORE_BASE64 }}" | base64 --decode > ${{ github.workspace }}/release.jks
          chmod 600 ${{ github.workspace }}/release.jks

      - name: Build Release AAB
        run: ./gradlew bundleRelease
        env:
          SIGNING_KEY_ALIAS: ${{ secrets.SIGNING_KEY_ALIAS }}
          SIGNING_KEY_PASSWORD: ${{ secrets.SIGNING_KEY_PASSWORD }}
          SIGNING_STORE_PASSWORD: ${{ secrets.SIGNING_STORE_PASSWORD }}
          SIGNING_KEY_STORE_PATH: ${{ github.workspace }}/release.jks

      - name: Upload to Google Play internal Track
        uses: r0adkll/upload-google-play@v1
        with:
          serviceAccountJsonPlainText: ${{ secrets.SERVICE_ACCOUNT_JSON_PLAINTEXT }}
          packageName: io.github.hitoshura25.healthsyncapp
          releaseFiles: app/build/outputs/bundle/release/app-release.aab
          track: internal
          status: completed
          mappingFile: app/build/outputs/mapping/release/mapping.txt
          whatsNewDirectory: distribution/whatsnew

      - name: Clean up keystore
        if: always()
        run: rm -f ${{ github.workspace }}/release.jks
```

---

## Migration Guide

### For Existing Users

Users who already have workflows generated by the MCP server will need to regenerate:

1. **No Breaking Changes** - Old workflows continue to work
2. **Regenerate for New Features**:
   ```
   # In Claude Code:
   "Regenerate my GitHub workflow to include ProGuard mapping and release notes"
   ```

3. **Setup Release Notes Directory**:
   ```bash
   mkdir -p distribution/whatsnew/en-US
   echo "Initial release" > distribution/whatsnew/en-US/whatsnew
   git add distribution/
   git commit -m "Add release notes structure"
   ```

---

## Success Criteria

### Functional Requirements

- ✅ `include_mapping_file=None` auto-detects from `analyze_android_project`
- ✅ `include_mapping_file=True` includes mapping file in workflow
- ✅ `include_mapping_file=False` excludes mapping file
- ✅ Custom mapping paths work via `mapping_file_path` parameter
- ✅ Release notes enabled by default (`include_release_notes=True`)
- ✅ Release notes can be disabled
- ✅ Custom release notes directories work
- ✅ Generated workflows are valid YAML
- ✅ Instructions include setup guides for enabled features
- ✅ Return value includes configuration details for both features

### Non-Functional Requirements

- ✅ No breaking changes to existing API
- ✅ Backward compatible with existing workflows
- ✅ Clear error messages if validation fails
- ✅ Comprehensive documentation
- ✅ Unit test coverage >80%
- ✅ Integration tests with real Android project

---

## Open Questions

1. **Should we validate that release notes directory exists?**
   - **Recommendation**: No, allow workflow to create it or fail gracefully
   - **Reasoning**: User might create directory after workflow generation

2. **Should we provide a helper tool to create release notes templates?**
   - **Recommendation**: Yes, add as future enhancement (Tool 11)
   - **Reasoning**: Would improve user experience

3. **Should mapping file auto-detection fail if project has minify but no mapping file?**
   - **Recommendation**: No, let Gradle build handle this
   - **Reasoning**: Mapping file is generated during build, not before

4. **Should we support debug symbols (native libraries)?**
   - **Recommendation**: Add in future release if requested
   - **Reasoning**: Less common use case, adds complexity

---

## Future Enhancements

### Tool 11: `create_release_notes_template`

Generate release notes directory structure with templates:

```python
def create_release_notes_template(
    project_path: str,
    locales: List[str] = None,  # Default: ["en-US"]
    directory: str = None,       # Default: "distribution/whatsnew"
) -> Dict[str, Any]:
    """Create release notes directory structure with templates"""

    # Creates:
    # distribution/
    #   whatsnew/
    #     en-US/
    #       whatsnew (template)
    #     de-DE/
    #       whatsnew (template)

    # Returns:
    # - List of created files
    # - Template content for each locale
    # - Instructions for editing
```

### Tool 12: `validate_release_notes`

Validate release notes before deployment:

```python
def validate_release_notes(
    directory: str,
) -> Dict[str, Any]:
    """Validate release notes structure and content"""

    # Checks:
    # - Directory exists
    # - Contains valid locale subdirectories
    # - Each locale has 'whatsnew' file
    # - Content is <500 characters
    # - Encoding is UTF-8

    # Returns:
    # - Validation results
    # - List of issues
    # - Suggestions for fixes
```

---

## Summary

This specification adds essential production features to the MCP server:

1. **ProGuard Mapping Support**
   - Auto-detects from project configuration
   - Enables crash deobfuscation in Play Console
   - Configurable for advanced users

2. **Release Notes Support**
   - Enabled by default
   - Localized content support
   - Simple directory structure

**Implementation Complexity**: Medium
- 4 new parameters
- Auto-detection logic
- Template updates
- Comprehensive testing

**User Value**: High
- ProGuard mapping is essential for production apps
- Release notes improve user communication
- Both are Play Store best practices

**Backward Compatibility**: ✅ Full
- All new parameters are optional
- Existing workflows continue working
- No breaking changes to API

---

## Approval Checklist

- [ ] Specification reviewed by stakeholders
- [ ] Technical approach validated
- [ ] Test strategy approved
- [ ] Documentation plan confirmed
- [ ] Migration guide reviewed
- [ ] Success criteria agreed upon

**Ready for Implementation**: ✅ Yes (pending approval)

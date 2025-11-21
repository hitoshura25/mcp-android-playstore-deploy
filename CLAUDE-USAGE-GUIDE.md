# Claude Desktop User Guide: Android Play Store Deployment

This guide shows you how to use this MCP server with Claude Desktop to set up automated Google Play Store deployments for your Android app.

## Prerequisites

Before starting, make sure you have:

- **Claude Desktop** installed and running
- **An Android app project** on your computer
- **A Google Play Console account** (free to create, $25 one-time registration fee)
- **A GitHub repository** for your Android app
- **Basic familiarity** with Android development

You'll also need these tools installed locally (Claude will guide you if they're missing):
- Java/JDK 17 or higher
- Android SDK (usually comes with Android Studio)

## Installation

### Step 1: Install uv

First, install `uv` (a fast Python package manager):

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Step 2: Configure Claude Desktop

Add this MCP server to your Claude Desktop configuration:

**macOS:** Edit `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** Edit `%APPDATA%\Claude\claude_desktop_config.json`

Add this configuration:
```json
{
  "mcpServers": {
    "android-playstore-deploy": {
      "command": "uvx",
      "args": ["hitoshura25-mcp-android-playstore-deploy"]
    }
  }
}
```

**Note:** If the file doesn't exist, create it with the above content.

### Step 3: Restart Claude Desktop

Close and reopen Claude Desktop completely for the changes to take effect.

### Step 4: Verify Installation

In Claude Desktop, ask:
```
What MCP servers are available?
```

You should see `android-playstore-deploy` in the list. If not, check the [Troubleshooting](#troubleshooting) section.

## How to Use This MCP Server with Claude

This MCP server helps you set up **automated GitHub Actions workflows** that deploy your Android app to Google Play Store whenever you push code. The setup happens in phases.

### Phase 1: Initial Setup (First Time Only)

Start a new conversation with Claude and provide this prompt:

```
I want to set up automated Google Play Store deployment for my Android app using GitHub Actions.

My Android project is located at: /path/to/your/android/app

Please walk me through the complete setup process step by step. Start by analyzing my project.
```

**What Claude will do:**

1. **Analyze your project** - Claude will examine your Android project structure, find your package name, check build configurations, etc.

2. **Generate a keystore** - Claude will help you create a secure Android keystore file for signing your app releases. You'll need to provide:
   - Where to save the keystore
   - Passwords (store these securely!)
   - Certificate details (your name, organization, etc.)

3. **Configure Gradle signing** - Claude will generate the Gradle configuration code you need to add to your `build.gradle.kts` file.

4. **Set up Google Play Service Account** - Claude will provide detailed instructions for creating a service account in Google Cloud Console and linking it to Play Console.

5. **Generate GitHub workflow** - Claude will create a complete GitHub Actions workflow file for your repository.

6. **Create GitHub secrets guide** - Claude will give you specific instructions for adding all required secrets to your GitHub repository.

**Important:** Keep the conversation going - Claude will guide you through each step and wait for your confirmation before moving to the next.

### Phase 2: Google Play Console Setup

At this stage, you'll need to manually complete some steps in your browser:

**Prompt Claude:**
```
I'm ready to set up the Google Play Service Account. Show me the detailed steps.
```

Claude will guide you through:
- Creating a Google Cloud project
- Enabling the Google Play Developer API
- Creating a service account
- Downloading the JSON key file
- Granting permissions in Play Console

**Follow each step carefully** and let Claude know when you're done.

### Phase 3: GitHub Repository Setup

**Prompt Claude:**
```
I have my keystore at /path/to/release.jks and my service account JSON at /path/to/service-account.json.

My GitHub repository is: https://github.com/username/repo-name

Please help me set up GitHub secrets and the workflow file.
```

Claude will:
1. Provide exact commands to encode your keystore to base64
2. Give you a checklist of all GitHub secrets to create
3. Generate the workflow YAML file
4. Tell you where to save it (`.github/workflows/deploy-playstore.yml`)

### Phase 4: Testing Before Going Live

**Important:** Test locally before pushing to GitHub!

**Prompt Claude:**
```
I want to test the deployment process locally without actually uploading to Play Store.

Project path: /path/to/your/android/app
Keystore path: /path/to/release.jks

Please run a dry-run test.
```

You'll need to provide your keystore passwords. Claude will:
- Build your release AAB (Android App Bundle)
- Verify the signing
- Show you detailed results
- Identify any issues

### Phase 5: Going Live

Once testing passes, commit and push the workflow file:

**Prompt Claude:**
```
The test passed! Please help me commit the workflow file and push it to GitHub.
```

Claude can help you with the git commands if needed.

Then, manually trigger your first deployment from GitHub:
1. Go to your repository on GitHub
2. Click **Actions** tab
3. Click your workflow name (e.g., "Deploy to Play Store internal")
4. Click **Run workflow**
5. Watch it run!

## Common Prompts and Workflows

### First-Time Setup (All at Once)
```
I want to set up Google Play Store deployment for my Android app at /Users/me/MyApp.
My GitHub repo is https://github.com/myusername/my-app.
Please guide me through the complete setup from start to finish.
```

### Just Generate a Keystore
```
I need to create a new Android keystore for app signing.
Output path: /Users/me/keystores/my-app-release.jks
Alias: my-app-key
Please generate it with secure defaults.
```

### Validate Existing Setup
```
I've already set up my Play Store deployment, but I want to verify everything is configured correctly.

Service account JSON: /path/to/service-account.json
Package name: com.mycompany.myapp

Please validate my setup.
```

### Check GitHub Secrets
```
Can you verify that my GitHub repository has all the required secrets configured?

Repository: owner/repo-name
GitHub token: ghp_xxxxxxxxxxxx

Please check for all required secrets.
```

### Migrate to a Different Track
```
I want to create a separate workflow for beta releases.

Project: /path/to/project
Package name: com.mycompany.myapp
Track: beta

Please generate a workflow file for this track.
```

### Generate Signing Configuration Only
```
I need the Gradle signing configuration code for my build.gradle.kts file.

Project path: /path/to/project

Please generate the signing config using environment variables.
```

## What to Expect

### Tool Execution Times

- **Analyze project**: 1-2 seconds
- **Generate keystore**: 5-10 seconds
- **Generate workflow**: Instant
- **Test deployment**: 2-5 minutes (builds your app)
- **Validate Play Store setup**: 3-5 seconds (API calls)

### Files Created

During setup, these files will be created:
- `release.jks` (or your chosen name) - Your keystore file (KEEP THIS SECURE!)
- `.github/workflows/deploy-playstore-*.yml` - GitHub Actions workflow
- `service-account.json` - Google Play API credentials (KEEP THIS SECURE!)

**Security Note:** Never commit `release.jks` or `service-account.json` to git!

### Required GitHub Secrets

You'll need to create these secrets in your GitHub repository:

1. **SIGNING_KEY_STORE_BASE64** - Your keystore encoded as base64
2. **SIGNING_KEY_ALIAS** - Key alias (e.g., "my-app-key")
3. **SIGNING_KEY_PASSWORD** - Password for the signing key
4. **SIGNING_STORE_PASSWORD** - Password for the keystore
5. **PLAY_STORE_CONFIG_JSON** - Service account JSON content
6. **ANDROID_PACKAGE_NAME** - Your app's package name (e.g., "com.mycompany.myapp")

Claude will provide the exact values for each of these.

## Understanding the Workflow

The generated GitHub Actions workflow does this:

1. **Checkout code** - Gets your latest code
2. **Set up Java** - Installs the correct JDK version
3. **Decode keystore** - Converts base64 secret back to keystore file
4. **Build release AAB** - Runs Gradle to build signed app bundle
5. **Upload to Play Store** - Sends AAB to Google Play (specific track)

### Deployment Tracks

- **internal** - Internal testing (fastest review, limited users)
- **alpha** - Closed testing
- **beta** - Open/closed testing (more users)
- **production** - Public release (requires review)

**Recommendation:** Start with `internal` track for testing.

## Troubleshooting

### MCP Server Not Showing Up

**Check installation:**
```bash
uvx hitoshura25-mcp-android-playstore-deploy --version
```

If this fails, reinstall `uv`:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Check Claude Desktop logs:**
- macOS: `~/Library/Logs/Claude/mcp*.log`
- Windows: `%APPDATA%\Claude\logs\mcp*.log`

### Tool Execution Fails

**Common issues:**

1. **"keytool not found"** - Install Java JDK
2. **"gradlew not found"** - Provide the full path to your Android project
3. **"Invalid project path"** - Make sure the path exists and contains `build.gradle.kts`
4. **"App not found in Play Console"** - Create your app in Play Console first (even if empty)

### Build Fails in GitHub Actions

**Check these:**

1. **Gradle version** - Your project might need a specific Gradle/Java version
2. **Dependencies** - Make sure all dependencies are available in public repositories
3. **Secrets** - Verify all GitHub secrets are set correctly (no extra spaces, correct encoding)
4. **Build configuration** - Test the build works locally first

### API Authentication Errors

**"401 Unauthorized":**
- Service account JSON is incorrect or corrupted
- Re-download from Google Cloud Console

**"403 Forbidden":**
- Service account doesn't have proper permissions
- Add it to Play Console with "Release Manager" role
- Google Play Developer API might not be enabled

**"404 Not Found":**
- App doesn't exist in Play Console yet
- Package name mismatch between your app and Play Console

### Play Store Upload Fails

**Common reasons:**

1. **Version code not incremented** - Each upload needs a higher version code
2. **Minimum SDK issues** - Play Store requires targetSdk 33+
3. **App not created in console** - Create app shell in Play Console first
4. **Missing required assets** - Need app icon, feature graphic, screenshots
5. **Policy violations** - Review Play Store policies

## Tips for Success

### 1. Test Locally First
Always run `test_deployment_workflow` with `dry_run=true` before pushing to GitHub.

### 2. Start with Internal Track
Use the `internal` track for initial testing - it's fastest and allows rapid iteration.

### 3. Keep Credentials Secure
- Store keystore and service account files in a secure password manager
- Never commit these files to git
- Use different keystores for debug/release if needed

### 4. Version Management
Update `versionCode` in your `build.gradle.kts` before each deployment:
```kotlin
versionCode = 2  // Increment this each time
versionName = "1.0.1"
```

### 5. Use Meaningful Branch Names
Configure workflows to trigger on specific branches like `release/*` or `main`.

### 6. Monitor Your Deployments
- Check GitHub Actions logs for detailed build output
- Monitor Play Console for review status
- Set up email notifications for workflow failures

## Next Steps After Setup

Once your deployment is working:

1. **Configure release notes** - Add a `whatsnew` directory for release descriptions
2. **Set up staged rollouts** - Roll out to small percentage first
3. **Add Slack/Discord notifications** - Get notified on deployments
4. **Create multiple workflows** - Different workflows for different tracks
5. **Add automated testing** - Run tests before deployment

## Getting Help

If you encounter issues:

1. **Check tool output** - Claude shows detailed error messages
2. **Review GitHub Actions logs** - See complete build output
3. **Validate each step** - Use validation tools to check configuration
4. **Test locally** - Isolate whether issue is with build or deployment

**Prompt for debugging:**
```
I'm getting this error during deployment: [paste error message]

Can you help me diagnose and fix it?
```

## Example Complete Conversation

Here's what a full setup conversation might look like:

**You:**
```
I want to set up automated Google Play Store deployment for my Android app.
Project path: /Users/me/Projects/MyAwesomeApp
GitHub repo: https://github.com/me/awesome-app
I'm starting from scratch - I don't have a keystore or service account yet.
```

**Claude:** [Analyzes project, shows package name, build configuration]

**You:**
```
Looks good! Let's continue.
```

**Claude:** [Generates keystore, provides secure parameters]

**You:**
```
Keystore created successfully. What's next?
```

**Claude:** [Provides Gradle configuration to add to build.gradle.kts]

**You:**
```
I've added the configuration. Continue.
```

**Claude:** [Shows detailed Google Play Service Account setup steps]

**You:**
```
I've created the service account and downloaded the JSON to /Users/me/service-account.json
```

**Claude:** [Validates the service account, generates GitHub workflow and secrets guide]

**You:**
```
Can you test the build locally before I push to GitHub?
Keystore password: [your password]
```

**Claude:** [Runs test build, shows results]

**You:**
```
Perfect! Help me commit the workflow file.
```

**Claude:** [Provides git commands to commit and push]

## Summary

This MCP server automates the complex process of setting up Google Play Store deployments. Claude will:

- ✅ Generate all necessary configuration files
- ✅ Provide step-by-step guidance for external services
- ✅ Test your setup before going live
- ✅ Validate configurations
- ✅ Help troubleshoot issues

The entire setup typically takes 30-45 minutes on your first time, but subsequent apps will be much faster since you'll know the process.

**Ready to get started?** Open Claude Desktop and paste the [Phase 1 prompt](#phase-1-initial-setup-first-time-only) above!

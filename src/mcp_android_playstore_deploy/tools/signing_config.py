"""Tool to generate Gradle signing configuration."""

from .utils import validate_project_path


def generate_signing_config(project_path: str, signing_strategy: str = "environment_variables") -> dict:
    """Generate Gradle signing configuration code to add to build.gradle.kts."""

    validate_project_path(project_path)

    if signing_strategy == "environment_variables":
        kotlin_dsl = """signingConfigs {
    create("release") {
        storeFile = file(System.getenv("SIGNING_KEY_STORE_PATH") ?: "release.jks")
        storePassword = System.getenv("SIGNING_STORE_PASSWORD")
        keyAlias = System.getenv("SIGNING_KEY_ALIAS")
        keyPassword = System.getenv("SIGNING_KEY_PASSWORD")
    }
}"""

        groovy_dsl = """signingConfigs {
    release {
        storeFile file(System.getenv("SIGNING_KEY_STORE_PATH") ?: "release.jks")
        storePassword System.getenv("SIGNING_STORE_PASSWORD")
        keyAlias System.getenv("SIGNING_KEY_ALIAS")
        keyPassword System.getenv("SIGNING_KEY_PASSWORD")
    }
}"""

        required_env_vars = [
            "SIGNING_KEY_STORE_PATH",
            "SIGNING_STORE_PASSWORD",
            "SIGNING_KEY_ALIAS",
            "SIGNING_KEY_PASSWORD"
        ]

    else:  # gradle_properties
        kotlin_dsl = """signingConfigs {
    create("release") {
        storeFile = file(project.properties["SIGNING_KEY_STORE_PATH"] ?: "release.jks")
        storePassword = project.properties["SIGNING_STORE_PASSWORD"] as String
        keyAlias = project.properties["SIGNING_KEY_ALIAS"] as String
        keyPassword = project.properties["SIGNING_KEY_PASSWORD"] as String
    }
}"""

        groovy_dsl = """signingConfigs {
    release {
        storeFile file(project.properties["SIGNING_KEY_STORE_PATH"] ?: "release.jks")
        storePassword project.properties["SIGNING_STORE_PASSWORD"]
        keyAlias project.properties["SIGNING_KEY_ALIAS"]
        keyPassword project.properties["SIGNING_KEY_PASSWORD"]
    }
}"""

        required_env_vars = []

    build_types = """buildTypes {
    release {
        signingConfig = signingConfigs.getByName("release")
        isMinifyEnabled = true
        isShrinkResources = true
        proguardFiles(
            getDefaultProguardFile("proguard-android-optimize.txt"),
            "proguard-rules.pro"
        )
    }
}"""

    complete_example = f"""android {{
    namespace = "com.example.app"
    compileSdk = 34

    defaultConfig {{
        applicationId = "com.example.app"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }}

    {kotlin_dsl}

    {build_types}

    compileOptions {{
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }}

    kotlinOptions {{
        jvmTarget = "17"
    }}
}}"""

    instructions = [
        "Add the signingConfigs block to your app/build.gradle.kts",
        "Place it inside the android { ... } block, before buildTypes",
        "Update your release buildType to use the signing config",
    ]

    if signing_strategy == "environment_variables":
        instructions.append("Set environment variables in your CI/CD pipeline")
    else:
        instructions.append("Add signing credentials to gradle.properties (DO NOT commit this file)")

    return {
        "success": True,
        "gradle_config_kotlin": kotlin_dsl,
        "gradle_config_groovy": groovy_dsl,
        "build_types_config": build_types,
        "insert_location": "Inside android { ... } block, before buildTypes",
        "instructions": instructions,
        "required_env_vars": required_env_vars,
        "complete_example": complete_example
    }

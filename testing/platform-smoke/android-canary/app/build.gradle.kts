// SPDX-License-Identifier: Apache-2.0
plugins {
    id("com.android.application")
}

val canaryAar = providers.environmentVariable("LINGUUM_ANDROID_AAR")
val canaryAssets = providers.environmentVariable("LINGUUM_ANDROID_ASSETS")
val canaryBuild = providers.environmentVariable("LINGUUM_ANDROID_APK_OUTPUT")

layout.buildDirectory.set(file(canaryBuild.get()))

android {
    namespace = "io.linguum.translation.canary"
    compileSdk = 36
    buildToolsVersion = "36.0.0"
    ndkVersion = "28.2.13676358"

    defaultConfig {
        applicationId = "io.linguum.translation.canary"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0-M1"
    }

    sourceSets.named("main") {
        assets.directories.add(canaryAssets.get())
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    packaging {
        jniLibs.useLegacyPackaging = false
    }
}

dependencies {
    implementation(files(canaryAar.get()))
}

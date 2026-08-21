// SPDX-License-Identifier: Apache-2.0
import org.jetbrains.kotlin.gradle.plugin.mpp.KotlinNativeTarget
import org.jetbrains.kotlin.gradle.plugin.mpp.NativeBuildType

plugins {
    kotlin("multiplatform") version "2.4.10"
}

val profileId = providers.gradleProperty("linguumIosProfile").get()
val staticArchive = file(providers.gradleProperty("linguumIosArchive").get())
val headerDirectory = file(providers.gradleProperty("linguumIosHeaders").get())
layout.buildDirectory.set(file(providers.gradleProperty("linguumIosBuildDirectory").get()))

check(staticArchive.isFile) { "The locked iOS static archive does not exist: $staticArchive" }
check(headerDirectory.resolve("linguum_translation.h").isFile) {
    "The stable Linguum C ABI header is missing from $headerDirectory"
}

kotlin {
    val target: KotlinNativeTarget =
        when (profileId) {
            "ios-arm64" -> iosArm64("iosArm64")
            "ios-simulator-arm64" -> iosSimulatorArm64("iosSimulatorArm64")
            "ios-simulator-x64" -> iosX64("iosX64")
            else -> error("Unsupported locked iOS profile: $profileId")
        }

    target.compilations.getByName("main").apply {
        cinterops.create("linguum") {
            definitionFile.set(file("src/nativeInterop/cinterop/linguum.def"))
            includeDirs.headerFilterOnly(headerDirectory)
            extraOpts("-libraryPath", staticArchive.parentFile.absolutePath)
        }
    }
    target.binaries.executable(listOf(NativeBuildType.RELEASE)) {
        entryPoint = "main"
    }
}

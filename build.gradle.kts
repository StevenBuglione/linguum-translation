import org.gradle.api.attributes.Bundling
import org.gradle.api.attributes.Category
import org.gradle.api.attributes.LibraryElements
import org.gradle.api.attributes.Usage
import org.gradle.api.attributes.java.TargetJvmEnvironment
import org.gradle.api.tasks.bundling.AbstractArchiveTask

plugins {
    base
    id("io.linguum.translation.architecture")
    alias(libs.plugins.kotlin.multiplatform) apply false
    alias(libs.plugins.android.kmp.library) apply false
    alias(libs.plugins.detekt)
    alias(libs.plugins.dokka) apply false
    alias(libs.plugins.kover) apply false
    alias(libs.plugins.maven.publish) apply false
}

group = "io.linguum"
version = "0.0.0-SNAPSHOT"

val expectedGradleVersion = libs.versions.gradle.get()
val expectedJdkVersion = libs.versions.jdk.get()

check(gradle.gradleVersion == expectedGradleVersion) {
    "Gradle $expectedGradleVersion is required; found ${gradle.gradleVersion}."
}
check(JavaVersion.current().majorVersion == expectedJdkVersion) {
    "JDK $expectedJdkVersion is required to run the build; found ${JavaVersion.current()}."
}

val toolchainProof by configurations.creating {
    isCanBeConsumed = false
    isCanBeResolved = true
    description = "Pinned artifacts resolved during the M0 toolchain compatibility proof."
    resolutionStrategy.activateDependencyLocking()
    attributes {
        attribute(Category.CATEGORY_ATTRIBUTE, objects.named(Category.LIBRARY))
        attribute(Usage.USAGE_ATTRIBUTE, objects.named(Usage.JAVA_RUNTIME))
        attribute(Bundling.BUNDLING_ATTRIBUTE, objects.named(Bundling.EXTERNAL))
        attribute(LibraryElements.LIBRARY_ELEMENTS_ATTRIBUTE, objects.named(LibraryElements.JAR))
        attribute(
            TargetJvmEnvironment.TARGET_JVM_ENVIRONMENT_ATTRIBUTE,
            objects.named(TargetJvmEnvironment.STANDARD_JVM),
        )
    }
}

dependencies {
    toolchainProof(libs.kotlin.gradle.plugin)
    toolchainProof(libs.android.gradle.plugin)
    toolchainProof(libs.coroutines.core)
}

allprojects {
    dependencyLocking {
        lockAllConfigurations()
        lockMode.set(LockMode.STRICT)
    }

    tasks.withType<AbstractArchiveTask>().configureEach {
        isPreserveFileTimestamps = false
        isReproducibleFileOrder = true
    }
}

detekt {
    toolVersion = libs.versions.detekt.get()
    source.setFrom(
        files(
            "build-logic/src/main/kotlin",
            "build-logic/src/test/kotlin",
            "testing/architecture/src/test/kotlin",
        ),
    )
    config.setFrom(files("config/detekt/detekt.yml"))
    buildUponDefaultConfig = true
    allRules = false
    parallel = true
    ignoreFailures = false
    basePath.set(rootDir)
}

tasks.withType<dev.detekt.gradle.Detekt>().configureEach {
    jvmTarget.set("17")
    reports {
        checkstyle.required.set(true)
        html.required.set(true)
        markdown.required.set(true)
        sarif.required.set(true)
    }
}

val verifyToolchain by tasks.registering {
    group = LifecycleBasePlugin.VERIFICATION_GROUP
    description = "Verifies the M0 Gradle, JDK, Kotlin, AGP, and dependency version lock."
    inputs.files(toolchainProof).withPropertyName("pinnedToolchainArtifacts")
}

tasks.register("verificationGate") {
    group = LifecycleBasePlugin.VERIFICATION_GROUP
    description = "Runs every verification available in the active repository milestone."
    dependsOn(
        verifyToolchain,
        tasks.named("architectureCheck"),
        tasks.named("qualityCheck"),
        ":testing:architecture:check",
        ":testing:architecture:koverXmlReport",
        gradle.includedBuild("build-logic").task(":test"),
    )
}

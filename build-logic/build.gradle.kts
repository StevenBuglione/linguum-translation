plugins {
    `java-gradle-plugin`
    id("org.jetbrains.kotlin.jvm") version "2.4.10"
}

group = "io.linguum.translation.buildlogic"

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(21)
    }
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

kotlin {
    jvmToolchain(21)
    compilerOptions {
        allWarningsAsErrors = true
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

dependencyLocking {
    lockAllConfigurations()
    lockMode.set(LockMode.STRICT)
}

gradlePlugin {
    plugins {
        create("architecture") {
            id = "io.linguum.translation.architecture"
            implementationClass = "io.linguum.translation.buildlogic.ArchitecturePlugin"
        }
    }
}

dependencies {
    testImplementation(kotlin("test"))
}

tasks.test {
    useJUnitPlatform()
}

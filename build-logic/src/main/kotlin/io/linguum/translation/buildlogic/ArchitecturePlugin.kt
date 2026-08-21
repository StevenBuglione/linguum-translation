// SPDX-License-Identifier: Apache-2.0
package io.linguum.translation.buildlogic

import org.gradle.api.Action
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.tasks.TaskProvider

internal class ArchitecturePlugin : Plugin<Project> {
    override fun apply(target: Project) {
        require(target == target.rootProject) { "The architecture plugin may be applied only to the root project." }
        registerArchitectureCheck(target)
        val policyCheck = registerPolicyCheck(target)
        registerPolicyLifecycle(target, policyCheck)
    }

    private fun registerArchitectureCheck(target: Project) {
        target.tasks.register(
            "architectureCheck",
            ArchitectureCheckTask::class.java,
            Action { task ->
                task.group = "verification"
                task.description = "Validates modules, dependency direction, packages, and protected files."
                task.architectureDirectory.set(target.layout.projectDirectory.dir("architecture"))
                task.settingsFile.set(target.layout.projectDirectory.file("settings.gradle.kts"))
                val scripts = target.fileTree(target.layout.projectDirectory)
                scripts.include("**/build.gradle.kts")
                scripts.exclude(
                    "build-logic/**",
                    "**/build/**",
                    "testing/architecture/src/test/resources/**",
                    // M1 feasibility consumers are deliberately isolated Gradle
                    // builds, not repository modules. Their own settings file and
                    // pinned plugin declarations are verified by their platform gates.
                    "testing/platform-smoke/android-canary/**",
                    "testing/platform-smoke/apple-export-canary/**",
                    "testing/platform-smoke/ios-canary/**",
                )
                task.buildScripts.from(scripts)
            },
        )
    }

    private fun registerPolicyCheck(target: Project): TaskProvider<RepositoryPolicyCheckTask> =
        target.tasks.register(
            "repositoryPolicyCheck",
            RepositoryPolicyCheckTask::class.java,
            Action { task ->
                task.group = "verification"
                task.description = "Checks formatting, suppressions, baselines, and coverage policy."
                val sources = target.fileTree(target.layout.projectDirectory)
                sources.include(
                    "**/*.gradle.kts",
                    "build-logic/src/**/*.kt",
                    "testing/**/*.kt",
                    ".github/**/*.yml",
                    ".github/**/*.yaml",
                    ".github/**/*.json",
                    "config/**/*.yml",
                    "scripts/admin/*.sh",
                    "scripts/ci/*.sh",
                    "toolchains/**/*.yaml",
                )
                sources.exclude("**/build/**", "**/.gradle/**")
                task.sourceFiles.from(sources)

                val baselines = target.fileTree(target.layout.projectDirectory)
                baselines.include("**/*detekt*baseline*.xml", "**/detekt-baseline.xml")
                baselines.exclude("**/build/**", "**/.gradle/**")
                task.prohibitedBaselines.from(baselines)
                task.coveragePolicy.set(target.layout.projectDirectory.file("config/quality/coverage-policy.yaml"))
                task.currentMilestone.set(target.layout.projectDirectory.file("architecture/current-milestone.txt"))
            },
        )

    private fun registerPolicyLifecycle(
        target: Project,
        policyCheck: TaskProvider<RepositoryPolicyCheckTask>,
    ) {
        listOf("formatCheck", "apiValidationCheck", "coveragePolicyCheck").forEach { name ->
            target.tasks.register(
                name,
                Action { task ->
                    task.group = "verification"
                    task.dependsOn(policyCheck)
                },
            )
        }
        target.tasks.register(
            "qualityCheck",
            Action { task ->
                task.group = "verification"
                task.dependsOn("formatCheck", "apiValidationCheck", "coveragePolicyCheck", "detekt")
            },
        )
    }
}

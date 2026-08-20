// SPDX-License-Identifier: Apache-2.0
package io.linguum.translation.buildlogic

import org.gradle.api.Action
import org.gradle.api.Plugin
import org.gradle.api.Project

internal class ArchitecturePlugin : Plugin<Project> {
    override fun apply(target: Project) {
        require(target == target.rootProject) { "The architecture plugin may be applied only to the root project." }
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
                )
                task.buildScripts.from(scripts)
            },
        )
    }
}

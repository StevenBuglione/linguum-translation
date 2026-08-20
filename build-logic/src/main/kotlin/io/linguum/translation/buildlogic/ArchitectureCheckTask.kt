// SPDX-License-Identifier: Apache-2.0
package io.linguum.translation.buildlogic

import java.security.MessageDigest
import org.gradle.api.DefaultTask
import org.gradle.api.file.ConfigurableFileCollection
import org.gradle.api.file.DirectoryProperty
import org.gradle.api.file.RegularFileProperty
import org.gradle.api.tasks.CacheableTask
import org.gradle.api.tasks.InputDirectory
import org.gradle.api.tasks.InputFile
import org.gradle.api.tasks.InputFiles
import org.gradle.api.tasks.PathSensitive
import org.gradle.api.tasks.PathSensitivity
import org.gradle.api.tasks.TaskAction

@CacheableTask
internal abstract class ArchitectureCheckTask : DefaultTask() {
    @get:InputDirectory
    @get:PathSensitive(PathSensitivity.RELATIVE)
    abstract val architectureDirectory: DirectoryProperty

    @get:InputFile
    @get:PathSensitive(PathSensitivity.RELATIVE)
    abstract val settingsFile: RegularFileProperty

    @get:InputFiles
    @get:PathSensitive(PathSensitivity.RELATIVE)
    abstract val buildScripts: ConfigurableFileCollection

    @TaskAction
    fun checkArchitecture() {
        val root = architectureDirectory.get().asFile.parentFile
        val architecture = architectureDirectory.get().asFile
        val modules = ModuleCatalog.parse(architecture.resolve("MODULE_CATALOG.yaml").readText())
        val milestone = architecture.resolve("current-milestone.txt").readText().trim()
        val declared = declaredProjects(settingsFile.get().asFile.readText())
        val edges = dependencyEdges(root, modules)
        val failures = ArchitectureRules.validate(modules, milestone, declared, edges).toMutableList()

        failures += validateBuildScripts(root, modules, declared)
        failures += validatePublicPackages(architecture.resolve("public-packages.txt"))
        failures += validateProtectedFiles(root, architecture.resolve("protected-files.sha256"))

        check(failures.isEmpty()) {
            failures.sorted().joinToString(prefix = "Architecture violations:\n- ", separator = "\n- ")
        }
        logger.lifecycle(
            "Architecture check passed: {} catalog modules, {} active projects, {} dependency edges.",
            modules.size,
            declared.size,
            edges.size,
        )
    }

    private fun declaredProjects(settings: String): Set<String> =
        QUOTED_PROJECT.findAll(settings).map { it.groupValues[1] }.toSet()

    private fun dependencyEdges(root: java.io.File, modules: List<ModuleSpec>): Set<Pair<String, String>> =
        buildScripts.files.flatMapTo(mutableSetOf()) { script ->
            if (script.parentFile == root) return@flatMapTo emptyList()
            val source = modules.firstOrNull { root.resolve(it.directory) == script.parentFile }?.path
                ?: return@flatMapTo emptyList()
            PROJECT_DEPENDENCY.findAll(script.readText()).map { source to it.groupValues[1] }.toList()
        }

    private fun validateBuildScripts(
        root: java.io.File,
        modules: List<ModuleSpec>,
        declared: Set<String>,
    ): List<String> {
        val moduleByDirectory = modules.associateBy { root.resolve(it.directory).normalize() }
        return buildScripts.files.mapNotNull { script ->
            if (script.parentFile == root) return@mapNotNull null
            val module = moduleByDirectory[script.parentFile.normalize()]
            when {
                module == null -> "Build script is not classified: ${script.relativeTo(root)}"
                module.path !in declared -> "Build script module is not included in settings: ${module.path}"
                else -> null
            }
        }
    }

    private fun validatePublicPackages(file: java.io.File): List<String> {
        val packages = file.readLines().map(String::trim).filter { it.isNotEmpty() && !it.startsWith('#') }
        return buildList {
            if (packages.isEmpty()) add("Public package allowlist is empty.")
            packages.filterNot { it == "io.linguum.translation" || it.startsWith("io.linguum.translation.") }
                .forEach { add("Public package is outside io.linguum.translation: $it") }
            if (packages.size != packages.distinct().size) add("Public package allowlist contains duplicates.")
        }
    }

    private fun validateProtectedFiles(root: java.io.File, manifest: java.io.File): List<String> =
        manifest.readLines().filter(String::isNotBlank).mapNotNull { line ->
            val match = PROTECTED_ENTRY.matchEntire(line)
                ?: return@mapNotNull "Malformed protected-file entry: $line"
            val expected = match.groupValues[1]
            val path = match.groupValues[2]
            val target = root.resolve(path)
            when {
                !target.isFile -> "Protected file is missing: $path"
                target.sha256() != expected -> "Protected file digest changed without authorization: $path"
                else -> null
            }
        }

    private fun java.io.File.sha256(): String = MessageDigest.getInstance("SHA-256")
        .digest(readBytes())
        .joinToString(separator = "") { byte -> "%02x".format(byte) }

    private companion object {
        val QUOTED_PROJECT = Regex("""[\"'](:[^\"']+)[\"']""")
        val PROJECT_DEPENDENCY = Regex("""project\s*\([^)]*[\"'](:[^\"']+)[\"'][^)]*\)""")
        val PROTECTED_ENTRY = Regex("""([a-f0-9]{64})  (.+)""")
    }
}

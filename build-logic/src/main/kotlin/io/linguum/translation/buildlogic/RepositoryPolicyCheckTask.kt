// SPDX-License-Identifier: Apache-2.0
package io.linguum.translation.buildlogic

import org.gradle.api.DefaultTask
import org.gradle.api.file.ConfigurableFileCollection
import org.gradle.api.file.RegularFileProperty
import org.gradle.api.tasks.CacheableTask
import org.gradle.api.tasks.InputFile
import org.gradle.api.tasks.InputFiles
import org.gradle.api.tasks.PathSensitive
import org.gradle.api.tasks.PathSensitivity
import org.gradle.api.tasks.TaskAction

@CacheableTask
internal abstract class RepositoryPolicyCheckTask : DefaultTask() {
    @get:InputFiles
    @get:PathSensitive(PathSensitivity.RELATIVE)
    abstract val sourceFiles: ConfigurableFileCollection

    @get:InputFiles
    @get:PathSensitive(PathSensitivity.RELATIVE)
    abstract val prohibitedBaselines: ConfigurableFileCollection

    @get:InputFile
    @get:PathSensitive(PathSensitivity.RELATIVE)
    abstract val coveragePolicy: RegularFileProperty

    @get:InputFile
    @get:PathSensitive(PathSensitivity.RELATIVE)
    abstract val currentMilestone: RegularFileProperty

    @TaskAction
    fun checkRepositoryPolicy() {
        val failures = sourceFiles.files.sorted().flatMap(::validateSource).toMutableList()
        prohibitedBaselines.files.sorted().forEach { failures += "Prohibited baseline exists: $it" }
        failures += validateCoveragePolicy(coveragePolicy.get().asFile.readText())
        failures += validateGithubContract(sourceFiles.files)

        check(failures.isEmpty()) {
            failures.joinToString(prefix = "Repository policy violations:\n- ", separator = "\n- ")
        }
        logger.lifecycle(
            "Repository policy check passed for {} source/configuration files at {}.",
            sourceFiles.files.size,
            currentMilestone.get().asFile.readText().trim(),
        )
    }

    private fun validateSource(file: java.io.File): List<String> {
        val text = file.readText()
        val failures = text.lineSequence().flatMapIndexed { index, line ->
            validateLine(file, index + 1, line).asSequence()
        }.toMutableList()
        if (text.isNotEmpty() && !text.endsWith('\n')) failures += "Missing final newline: $file"
        if (file.extension in KOTLIN_EXTENSIONS) {
            failures += validateKotlinSource(file, text)
        }
        if (inGithubDirectory(file) && file.extension in YAML_EXTENSIONS) {
            failures += validateActionPins(file, text)
        }
        return failures
    }

    private fun validateLine(file: java.io.File, lineNumber: Int, line: String): List<String> = buildList {
        if (line.endsWith(' ') || line.endsWith('\t')) add("Trailing whitespace: $file:$lineNumber")
        if (file.extension in INDENTED_EXTENSIONS && '\t' in line) add("Tab indentation: $file:$lineNumber")
        if (file.extension in KOTLIN_EXTENSIONS && line.length > MAX_KOTLIN_LINE_LENGTH) {
            add("Kotlin line exceeds $MAX_KOTLIN_LINE_LENGTH characters: $file:$lineNumber")
        }
    }

    private fun validateKotlinSource(file: java.io.File, text: String): List<String> = buildList {
        FORBIDDEN_KOTLIN_TOKENS.filter(text::contains)
            .forEach { add("Forbidden Kotlin token '$it': $file") }
        if (text.lineSequence().count() > MAX_KOTLIN_FILE_LINES) {
            add("Kotlin file exceeds $MAX_KOTLIN_FILE_LINES lines: $file")
        }
    }

    private fun validateCoveragePolicy(content: String): List<String> = REQUIRED_COVERAGE_POLICY
        .filterNot(content::contains)
        .map { "Coverage policy is missing protected setting: $it" }

    private fun validateActionPins(file: java.io.File, content: String): List<String> = content
        .lineSequence()
        .mapIndexedNotNull { index, line ->
            val action = ACTION_USAGE.find(line)?.groupValues?.get(1) ?: return@mapIndexedNotNull null
            if (action.startsWith("./") || action.matches(FULLY_PINNED_ACTION)) {
                null
            } else {
                "GitHub Action is not pinned to a full commit SHA: $file:${index + 1} ($action)"
            }
        }
        .toList()

    private fun validateGithubContract(files: Set<java.io.File>): List<String> {
        val workflow = files.singleOrNull { it.invariantSeparatorsPath.endsWith(PR_WORKFLOW_PATH) }
        val ruleset = files.singleOrNull { it.invariantSeparatorsPath.endsWith(MAIN_RULESET_PATH) }
        return buildList {
            if (workflow == null) add("Missing protected PR workflow: $PR_WORKFLOW_PATH")
            if (ruleset == null) add("Missing main-branch ruleset: $MAIN_RULESET_PATH")
            if (workflow != null && ruleset != null) {
                addAll(validateProtectedChecks(workflow, ruleset))
            }
        }
    }

    private fun validateProtectedChecks(workflow: java.io.File, ruleset: java.io.File): List<String> {
        val workflowChecks = PR_JOB_NAME.findAll(workflow.readText()).map { it.groupValues[1] }.toSet()
        val protectedChecks = RULESET_CONTEXT.findAll(ruleset.readText()).map { it.groupValues[1] }.toSet()
        return buildList {
            if (workflowChecks.size != REQUIRED_PR_CHECK_COUNT) {
                add("PR workflow must define exactly $REQUIRED_PR_CHECK_COUNT protected checks")
            }
            addAll((workflowChecks - protectedChecks).map { "PR check is not protected by the ruleset: $it" })
            addAll((protectedChecks - workflowChecks).map { "Ruleset check has no matching PR job: $it" })
        }
    }

    private fun inGithubDirectory(file: java.io.File): Boolean =
        file.invariantSeparatorsPath.contains("/.github/")

    private companion object {
        const val MAX_KOTLIN_LINE_LENGTH = 120
        const val MAX_KOTLIN_FILE_LINES = 400
        const val REQUIRED_PR_CHECK_COUNT = 15
        const val PR_WORKFLOW_PATH = "/.github/workflows/pr.yml"
        const val MAIN_RULESET_PATH = "/.github/rulesets/main.json"
        val INDENTED_EXTENSIONS = setOf("kt", "kts", "yaml", "yml")
        val KOTLIN_EXTENSIONS = setOf("kt", "kts")
        val YAML_EXTENSIONS = setOf("yaml", "yml")
        val ACTION_USAGE = Regex("""^\s*-\s*uses:\s*([^\s#]+)""")
        val FULLY_PINNED_ACTION = Regex("""[^/@\s]+/[^@\s]+@[0-9a-fA-F]{40}""")
        val PR_JOB_NAME = Regex("""(?m)^\s{4}name:\s*(PR / .+)\s*$""")
        val RULESET_CONTEXT = Regex(""""context"\s*:\s*"(PR / [^"]+)"""")
        val FORBIDDEN_KOTLIN_TOKENS = setOf(
            "@" + "Disabled",
            "@" + "Ignore",
            "@Suppress(\"ALL\")",
            "FIX" + "ME:",
            "System" + ".out",
            "TO" + "DO:",
            "print" + "ln(",
        )
        val REQUIRED_COVERAGE_POLICY = setOf(
            "line_percent: 95",
            "branch_percent: 90",
            "line_percent: 90",
            "branch_percent: 85",
            "normal_pull_request: forbidden",
        )
    }
}

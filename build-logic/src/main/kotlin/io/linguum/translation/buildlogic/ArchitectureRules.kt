// SPDX-License-Identifier: Apache-2.0
package io.linguum.translation.buildlogic

internal object ArchitectureRules {
    fun validate(
        modules: List<ModuleSpec>,
        currentMilestone: String,
        declaredProjects: Set<String>,
        dependencyEdges: Set<Pair<String, String>>,
    ): List<String> = buildList {
        val activeMilestoneNumber = milestoneNumber(currentMilestone)
        val modulesByPath = modules.associateBy(ModuleSpec::path)
        val requiredProjects = modules
            .filter { module ->
                val introducedNumber = milestoneNumber(module.introduced)
                introducedNumber < activeMilestoneNumber ||
                    activeMilestoneNumber == 0 && introducedNumber == 0
            }
            .map(ModuleSpec::path)
            .toSet()

        addAll((requiredProjects - declaredProjects).map { "Required module is not included: $it" })
        addAll((declaredProjects - modulesByPath.keys).map { "Included module is not classified: $it" })

        modules.filter { spec ->
            FORBIDDEN_NAMES.any { forbidden ->
                spec.directory.split('/', '-', '_').any { it.equals(forbidden, ignoreCase = true) }
            }
        }.forEach { add("Module has a prohibited vague name: ${it.directory}") }

        dependencyEdges.forEach { (sourcePath, targetPath) ->
            val source = modulesByPath[sourcePath]
            val target = modulesByPath[targetPath]
            if (source == null) add("Dependency source is not classified: $sourcePath")
            if (target == null) add("Dependency target is not classified: $targetPath")
            if (source != null && target != null && !isAllowed(source.type, target.type)) {
                add("Forbidden dependency edge: $sourcePath (${source.type}) -> $targetPath (${target.type})")
            }
        }
    }

    fun milestoneNumber(value: String): Int {
        require(value.matches(Regex("M(?:10|[0-9])"))) { "Invalid milestone: $value" }
        return value.removePrefix("M").toInt()
    }

    private fun isAllowed(sourceType: String, targetType: String): Boolean = when {
        sourceType == "test-harness" -> true
        sourceType == "publication" -> targetType != "immutable-upstream"
        else -> targetType in ALLOWED_TARGETS[sourceType].orEmpty()
    }

    private val FORBIDDEN_NAMES = setOf(
        "common",
        "core",
        "helper",
        "helpers",
        "misc",
        "stuff",
        "util",
        "utils",
    )
    private val ALLOWED_TARGETS = mapOf(
        "public-api" to setOf("public-api"),
        "orchestration" to setOf("public-api", "orchestration", "internal-contract"),
        "internal-contract" to setOf("public-api", "internal-contract"),
        "platform-adapter" to setOf("public-api", "orchestration", "internal-contract", "native-bridge"),
        "native-bridge" to setOf("native-abi", "native-adapter"),
        "native-adapter" to setOf("native-abi", "immutable-upstream"),
    )
}

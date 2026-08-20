// SPDX-License-Identifier: Apache-2.0
package io.linguum.translation.buildlogic

internal data class ModuleSpec(
    val path: String,
    val directory: String,
    val type: String,
    val introduced: String,
)

internal object ModuleCatalog {
    fun parse(content: String): List<ModuleSpec> {
        val modules = mutableListOf<ModuleSpec>()
        var fields = mutableMapOf<String, String>()

        fun finishModule() {
            if (fields.isEmpty()) return
            val required = listOf("path", "directory", "type", "introduced")
            val missing = required.filterNot(fields::containsKey)
            require(missing.isEmpty()) { "Module entry is missing: ${missing.joinToString()}" }
            modules += ModuleSpec(
                path = fields.getValue("path"),
                directory = fields.getValue("directory"),
                type = fields.getValue("type"),
                introduced = fields.getValue("introduced"),
            )
            fields = mutableMapOf()
        }

        content.lineSequence().forEach { line ->
            val match = FIELD.matchEntire(line) ?: return@forEach
            val key = match.groupValues[1]
            if (key == "path") finishModule()
            fields[key] = match.groupValues[2].trim()
        }
        finishModule()

        require(modules.isNotEmpty()) { "The module catalog contains no modules." }
        require(modules.map(ModuleSpec::path).distinct().size == modules.size) {
            "The module catalog contains duplicate project paths."
        }
        require(modules.map(ModuleSpec::directory).distinct().size == modules.size) {
            "The module catalog contains duplicate directories."
        }
        return modules
    }

    private val FIELD = Regex(
        pattern = """\s*(?:-\s*)?(path|directory|type|introduced):\s*(\S.*?)\s*""",
    )
}

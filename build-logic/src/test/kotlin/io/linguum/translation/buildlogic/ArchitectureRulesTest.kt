// SPDX-License-Identifier: Apache-2.0
package io.linguum.translation.buildlogic

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class ArchitectureRulesTest {
    @Test
    fun `accepts the clean public API graph`() {
        val failures = ArchitectureRules.validate(
            modules = modules,
            currentMilestone = "M0",
            declaredProjects = modules.map(ModuleSpec::path).toSet(),
            dependencyEdges = emptySet(),
        )

        assertEquals(emptyList(), failures)
    }

    @Test
    fun `rejects public API dependency on a platform adapter`() {
        val failures = ArchitectureRules.validate(
            modules = modules,
            currentMilestone = "M0",
            declaredProjects = modules.map(ModuleSpec::path).toSet(),
            dependencyEdges = setOf(":translation-api" to ":platform:jvm"),
        )

        assertTrue(
            failures.single().contains("Forbidden dependency edge: :translation-api"),
            failures.toString(),
        )
    }

    private companion object {
        val modules = listOf(
            ModuleSpec(":translation-api", "translation-api", "public-api", "M0"),
            ModuleSpec(":platform:jvm", "platform/jvm", "platform-adapter", "M0"),
        )
    }
}

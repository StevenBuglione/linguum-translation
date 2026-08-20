// SPDX-License-Identifier: Apache-2.0
package io.linguum.translation.architecture

import java.nio.file.Files
import java.nio.file.Path
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

public class RepositoryArchitectureTest {
    @Test
    public fun `M0 architecture test module is declared in the canonical catalog`() {
        val root = repositoryRoot()
        val catalog = Files.readString(root.resolve("architecture/MODULE_CATALOG.yaml"))
        val milestone = Files.readString(root.resolve("architecture/current-milestone.txt")).trim()

        assertEquals("M0", milestone)
        assertTrue(catalog.contains("path: :testing:architecture"))
        assertTrue(catalog.contains("introduced: M0"))
    }

    private fun repositoryRoot(): Path {
        var candidate = Path.of("").toAbsolutePath()
        while (!Files.isRegularFile(candidate.resolve("architecture/MODULE_CATALOG.yaml"))) {
            candidate = candidate.parent ?: error("Repository root was not found.")
        }
        return candidate
    }
}

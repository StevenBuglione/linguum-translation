// SPDX-License-Identifier: Apache-2.0
package io.linguum.translation.buildlogic

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

class ModuleCatalogTest {
    @Test
    fun `parses required module fields`() {
        val modules = ModuleCatalog.parse(CATALOG)

        assertEquals(2, modules.size)
        assertEquals(":translation-api", modules.first().path)
        assertEquals("platform-adapter", modules.last().type)
    }

    @Test
    fun `rejects incomplete module entries`() {
        assertFailsWith<IllegalArgumentException> {
            ModuleCatalog.parse("  - path: :translation-api\n    type: public-api")
        }
    }

    private companion object {
        val CATALOG = """
            modules:
              - path: :translation-api
                directory: translation-api
                type: public-api
                introduced: M0
              - path: :platform:jvm
                directory: platform/jvm
                type: platform-adapter
                introduced: M0
        """.trimIndent()
    }
}

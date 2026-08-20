/* SPDX-License-Identifier: Apache-2.0 */
#include <stddef.h>
#include <stdint.h>

#include "linguum_translation.h"

_Static_assert(LINGUUM_TRANSLATION_ABI_MAJOR == 1u, "unexpected ABI major");
_Static_assert(LINGUUM_TRANSLATION_ABI_MINOR == 0u, "unexpected ABI minor");
_Static_assert(offsetof(linguum_translation_runtime_config, struct_size) == 0u,
               "runtime config must begin with struct_size");
_Static_assert(offsetof(linguum_translation_model_descriptor, struct_size) == 0u,
               "model descriptor must begin with struct_size");
_Static_assert(offsetof(linguum_translation_request, struct_size) == 0u,
               "request must begin with struct_size");

int main(void) {
    if (linguum_translation_abi_major() != LINGUUM_TRANSLATION_ABI_MAJOR) {
        return 1;
    }
    if (linguum_translation_abi_minor() != LINGUUM_TRANSLATION_ABI_MINOR) {
        return 2;
    }
    linguum_translation_runtime_destroy(NULL);
    linguum_translation_model_destroy(NULL);
    linguum_translation_translator_destroy(NULL);
    linguum_translation_result_destroy(NULL);
    linguum_translation_error_destroy(NULL);
    linguum_translation_runtime_info_destroy(NULL);
    return 0;
}

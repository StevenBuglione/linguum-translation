// SPDX-License-Identifier: Apache-2.0
#include <type_traits>

#include "linguum_translation.h"

static_assert(std::is_standard_layout<linguum_translation_string_view>::value,
              "string view must remain a standard-layout C type");
static_assert(std::is_standard_layout<linguum_translation_runtime_config>::value,
              "runtime config must remain a standard-layout C type");

int main() {
  return linguum_translation_abi_major() == 1u && linguum_translation_abi_minor() == 0u ? 0 : 1;
}

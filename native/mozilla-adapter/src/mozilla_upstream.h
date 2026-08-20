// SPDX-License-Identifier: Apache-2.0
#pragma once

// The pinned Mozilla/Bergamot dependency predates several diagnostics enabled
// for Linguum's adapter. Treat only this wrapper and its transitive includes as
// system headers so third-party warnings do not weaken warnings-as-errors for
// Linguum's own implementation.
#if defined(__clang__) || defined(__GNUC__)
#pragma GCC system_header
#endif

#include "common/logging.h"
#include "translator/parser.h"
#include "translator/response.h"
#include "translator/response_options.h"
#include "translator/service.h"
#include "translator/translation_model.h"

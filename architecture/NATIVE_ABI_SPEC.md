# Stable Native C ABI Specification

## 1. Purpose

The Linguum C ABI is the only contract between platform bindings and Mozilla/Bergamot C++ internals.

It must remain stable even when Firefox changes its pinned source or Mozilla changes C++ classes.

Header path:

```text
native/abi/include/linguum_translation.h
```

Symbol prefix:

```text
linguum_translation_
```

## 2. ABI version

Initial ABI:

```text
major = 1
minor = 0
```

Rules:

- major change: incompatible struct, ownership, symbol, or semantic change;
- minor change: backward-compatible additive function/field capability;
- patch behavior is represented by library SemVer, not ABI version;
- Kotlin/JNI/cinterop checks ABI before creating a runtime;
- incompatible runtime is rejected before any non-version ABI call.

Required functions:

```c
uint32_t linguum_translation_abi_major(void);
uint32_t linguum_translation_abi_minor(void);
```

## 3. Header shape

Normative starting header:

```c
#ifndef LINGUUM_TRANSLATION_H
#define LINGUUM_TRANSLATION_H

#include <stddef.h>
#include <stdint.h>

#if defined(_WIN32)
  #if defined(LINGUUM_TRANSLATION_BUILD)
    #define LINGUUM_TRANSLATION_API __declspec(dllexport)
  #else
    #define LINGUUM_TRANSLATION_API __declspec(dllimport)
  #endif
#else
  #define LINGUUM_TRANSLATION_API __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
extern "C" {
#endif

#define LINGUUM_TRANSLATION_ABI_MAJOR 1u
#define LINGUUM_TRANSLATION_ABI_MINOR 0u

typedef struct linguum_translation_runtime linguum_translation_runtime;
typedef struct linguum_translation_model linguum_translation_model;
typedef struct linguum_translation_translator linguum_translation_translator;
typedef struct linguum_translation_result linguum_translation_result;
typedef struct linguum_translation_error linguum_translation_error;
typedef struct linguum_translation_runtime_info linguum_translation_runtime_info;

typedef struct linguum_translation_string_view {
    const uint8_t* data;
    size_t length;
} linguum_translation_string_view;

typedef enum linguum_translation_status {
    LINGUUM_TRANSLATION_STATUS_OK = 0,

    LINGUUM_TRANSLATION_STATUS_INVALID_ARGUMENT = 100,
    LINGUUM_TRANSLATION_STATUS_INVALID_UTF8 = 101,
    LINGUUM_TRANSLATION_STATUS_INVALID_HANDLE = 102,
    LINGUUM_TRANSLATION_STATUS_ABI_INCOMPATIBLE = 103,
    LINGUUM_TRANSLATION_STATUS_RUNTIME_CLOSED = 104,
    LINGUUM_TRANSLATION_STATUS_REQUEST_TOO_LARGE = 105,

    LINGUUM_TRANSLATION_STATUS_MODEL_DESCRIPTOR_INVALID = 200,
    LINGUUM_TRANSLATION_STATUS_MODEL_LOAD_FAILED = 201,
    LINGUUM_TRANSLATION_STATUS_MODEL_INCOMPATIBLE = 202,
    LINGUUM_TRANSLATION_STATUS_MODEL_CORRUPT = 203,

    LINGUUM_TRANSLATION_STATUS_TRANSLATION_FAILED = 300,

    LINGUUM_TRANSLATION_STATUS_UNSUPPORTED_CPU = 400,
    LINGUUM_TRANSLATION_STATUS_PLATFORM_UNSUPPORTED = 401,

    LINGUUM_TRANSLATION_STATUS_OUT_OF_MEMORY = 500,
    LINGUUM_TRANSLATION_STATUS_INTERNAL_ERROR = 900
} linguum_translation_status;

typedef enum linguum_translation_input_format {
    LINGUUM_TRANSLATION_INPUT_PLAIN_TEXT = 0,
    LINGUUM_TRANSLATION_INPUT_INTERNAL_STRUCTURED = 1
} linguum_translation_input_format;

typedef struct linguum_translation_runtime_config {
    uint32_t struct_size;
    uint32_t expected_abi_major;
    uint32_t expected_abi_minor;
    uint32_t worker_count;
    uint64_t maximum_input_bytes;
    uint64_t reserved_u64[8];
    const void* reserved_ptr[8];
} linguum_translation_runtime_config;

typedef struct linguum_translation_model_descriptor {
    uint32_t struct_size;
    linguum_translation_string_view language_pair;
    linguum_translation_string_view model_path;
    linguum_translation_string_view shortlist_path;
    const linguum_translation_string_view* vocabulary_paths;
    size_t vocabulary_path_count;
    linguum_translation_string_view configuration_yaml;
    uint64_t reserved_u64[8];
    const void* reserved_ptr[8];
} linguum_translation_model_descriptor;

typedef struct linguum_translation_request {
    uint32_t struct_size;
    linguum_translation_string_view input;
    linguum_translation_input_format input_format;
    uint32_t reserved_u32[8];
    uint64_t reserved_u64[8];
    const void* reserved_ptr[8];
} linguum_translation_request;

LINGUUM_TRANSLATION_API uint32_t linguum_translation_abi_major(void);
LINGUUM_TRANSLATION_API uint32_t linguum_translation_abi_minor(void);

LINGUUM_TRANSLATION_API linguum_translation_status
linguum_translation_runtime_create(
    const linguum_translation_runtime_config* config,
    linguum_translation_runtime** runtime_out,
    linguum_translation_error** error_out
);

LINGUUM_TRANSLATION_API linguum_translation_status
linguum_translation_runtime_info_create(
    const linguum_translation_runtime* runtime,
    linguum_translation_runtime_info** info_out,
    linguum_translation_error** error_out
);

LINGUUM_TRANSLATION_API void
linguum_translation_runtime_destroy(linguum_translation_runtime* runtime);

LINGUUM_TRANSLATION_API linguum_translation_status
linguum_translation_model_load(
    linguum_translation_runtime* runtime,
    const linguum_translation_model_descriptor* descriptor,
    linguum_translation_model** model_out,
    linguum_translation_error** error_out
);

LINGUUM_TRANSLATION_API void
linguum_translation_model_destroy(linguum_translation_model* model);

LINGUUM_TRANSLATION_API linguum_translation_status
linguum_translation_translator_create(
    linguum_translation_runtime* runtime,
    linguum_translation_model* model,
    linguum_translation_translator** translator_out,
    linguum_translation_error** error_out
);

LINGUUM_TRANSLATION_API void
linguum_translation_translator_destroy(
    linguum_translation_translator* translator
);

LINGUUM_TRANSLATION_API linguum_translation_status
linguum_translation_translator_translate(
    linguum_translation_translator* translator,
    const linguum_translation_request* request,
    linguum_translation_result** result_out,
    linguum_translation_error** error_out
);

LINGUUM_TRANSLATION_API linguum_translation_string_view
linguum_translation_result_text(
    const linguum_translation_result* result
);

LINGUUM_TRANSLATION_API void
linguum_translation_result_destroy(linguum_translation_result* result);

LINGUUM_TRANSLATION_API int32_t
linguum_translation_error_code(const linguum_translation_error* error);

LINGUUM_TRANSLATION_API linguum_translation_string_view
linguum_translation_error_message(const linguum_translation_error* error);

LINGUUM_TRANSLATION_API void
linguum_translation_error_destroy(linguum_translation_error* error);

LINGUUM_TRANSLATION_API linguum_translation_string_view
linguum_translation_runtime_info_library_version(
    const linguum_translation_runtime_info* info
);

LINGUUM_TRANSLATION_API linguum_translation_string_view
linguum_translation_runtime_info_firefox_revision(
    const linguum_translation_runtime_info* info
);

LINGUUM_TRANSLATION_API linguum_translation_string_view
linguum_translation_runtime_info_bergamot_version(
    const linguum_translation_runtime_info* info
);

LINGUUM_TRANSLATION_API linguum_translation_string_view
linguum_translation_runtime_info_acceleration_profile(
    const linguum_translation_runtime_info* info
);

LINGUUM_TRANSLATION_API void
linguum_translation_runtime_info_destroy(
    linguum_translation_runtime_info* info
);

#ifdef __cplusplus
}
#endif

#endif
```

The implementation may add backward-compatible minor-version functions, but may not remove or reinterpret these contracts within ABI major 1.

## 4. Ownership

- The caller owns input buffers for the duration of the call only.
- The ABI copies or consumes input synchronously before returning.
- Native-owned runtime/model/translator/result/error/info handles are destroyed only by their matching Linguum destroy functions.
- Bindings must never call `free`, `delete`, `LocalFree`, `CoTaskMemFree`, or platform allocators on ABI-owned memory.
- Returned string views are borrowed from their owning result/error/info object and remain valid only until that object is destroyed.
- Destroy functions are idempotent only for null pointers; destroying the same non-null handle twice is invalid and must be caught in debug/abuse tests.

## 5. Error contract

- no C++ exception crosses the ABI;
- every exported implementation function is exception-guarded;
- status code is the programmatic contract;
- error message is diagnostic, privacy-safe, and not used for branching;
- error messages contain no source or translated text;
- `error_out` may be null;
- when provided, successful calls set `*error_out = NULL`;
- failed calls either create an error object or return a status whose allocation failure makes that impossible;
- there is no global or thread-local `last_error`.

## 6. Thread safety

- ABI version functions are thread-safe.
- runtime creation/destruction is externally serialized.
- model load/destroy is externally serialized against destruction but may occur while other model generations translate when the runtime supports it.
- translator calls may originate from multiple platform threads, but the Kotlin scheduler normally serializes a pair-bound translator; the native adapter must still reject invalid lifecycle races safely.
- result/error/info objects are immutable after creation.
- no callback from C++ into Kotlin/Java/Swift is part of ABI v1.

## 7. Synchronous boundary rationale

ABI v1 uses a synchronous `translate` call even though Mozilla internally uses `AsyncService`.

The adapter:

1. submits to `AsyncService`;
2. waits on its private promise/future;
3. returns the completed result through C ABI.

Platform bindings invoke this from library-owned background execution contexts. This avoids cross-language callback lifetime complexity and preserves cooperative cancellation semantics: queued work can be removed before the call, while an already-running ~30 ms call safely completes and may have its result discarded.

## 8. Model descriptor

The C ABI accepts only already-installed, fully verified model paths/configuration.

It never:

- downloads models;
- trusts the live Mozilla registry;
- chooses model versions;
- verifies network policy;
- manages disk eviction.

Those are Kotlin model-management responsibilities.

The native adapter validates that files exist/read, config is bounded, vocab count is valid, and model creation succeeds. Cryptographic integrity must already have been established by the model installer; a native compatibility probe remains required before activation.

## 9. Structured input

`LINGUUM_TRANSLATION_INPUT_INTERNAL_STRUCTURED` is a private internal serialization between the Kotlin structured-text module and the native adapter. It is not arbitrary HTML and is not exposed as public user input.

Its exact grammar must be versioned and tested before M7. ABI major 1 reserves the enum but production support remains capability-gated until M7 passes.

## 10. CPU dispatch

The loader selects a compatible native artifact before calling the ABI.

- no unsupported instruction may be executed to detect support;
- no SIGILL/illegal-instruction recovery strategy;
- selected acceleration profile is exposed through runtime info;
- incompatible CPU returns `UNSUPPORTED_CPU` before model load;
- optimized and fallback artifacts share ABI major/minor and behavior.

## 11. ABI testing

Required:

- C compiler consumer test;
- C++ consumer test using only the C header;
- JNI and cinterop tests;
- struct-size forward/backward compatibility tests;
- symbol export allowlist;
- binary ABI snapshot/diff;
- null/invalid/destroyed handle abuse tests;
- invalid UTF-8 and embedded NUL tests;
- oversized input tests;
- allocation-failure tests where feasible;
- ASan/UBSan/TSan matrix;
- coverage-guided fuzzing of ABI argument validation;
- repeated create/load/translate/destroy soak tests.

A breaking ABI change requires a major ABI bump, migration documentation, compatibility fixture updates, and a library major release if it affects stable consumers.

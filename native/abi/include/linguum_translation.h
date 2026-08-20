/* SPDX-License-Identifier: Apache-2.0 */
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

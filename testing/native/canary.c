/* SPDX-License-Identifier: Apache-2.0 */
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "linguum_translation.h"

#if defined(_WIN32)
#define LINGUUM_PATH_SEPARATOR '\\'
#else
#define LINGUUM_PATH_SEPARATOR '/'
#endif

static const char* const CANARY_INPUT = "¿Qué estás haciendo?";
static const char* const CANARY_EXPECTED = "What are you doing?";
static const char* const FIREFOX_REVISION = "48d55cf7ec80093903e2ef7f58b61a84a22ef716";

static linguum_translation_string_view string_view(const char* value) {
    linguum_translation_string_view view;
    view.data = (const uint8_t*)value;
    view.length = strlen(value);
    return view;
}

static int view_equals(linguum_translation_string_view view, const char* expected) {
    const size_t expected_length = strlen(expected);
    return view.length == expected_length &&
           (expected_length == 0U || memcmp(view.data, expected, expected_length) == 0);
}

static void print_error(const char* operation, linguum_translation_status status,
                        linguum_translation_error* error) {
    const linguum_translation_string_view message = linguum_translation_error_message(error);
    fprintf(stderr, "%s failed with status %d", operation, (int)status);
    if (message.data != NULL && message.length != 0U) {
        fprintf(stderr, ": %.*s", (int)message.length, (const char*)message.data);
    }
    fputc('\n', stderr);
}

static char* join_path(const char* directory, const char* name) {
    const size_t directory_length = strlen(directory);
    const size_t name_length = strlen(name);
    const int needs_separator = directory_length != 0U &&
                                directory[directory_length - 1U] != '/' &&
                                directory[directory_length - 1U] != '\\';
    char* path = (char*)malloc(directory_length + (size_t)needs_separator + name_length + 1U);
    if (path == NULL) {
        return NULL;
    }
    memcpy(path, directory, directory_length);
    if (needs_separator) {
        path[directory_length] = LINGUUM_PATH_SEPARATOR;
    }
    memcpy(path + directory_length + (size_t)needs_separator, name, name_length + 1U);
    return path;
}

static char* read_file(const char* path, size_t* length_out) {
    FILE* stream = fopen(path, "rb");
    long length;
    char* bytes;
    if (stream == NULL) {
        return NULL;
    }
    if (fseek(stream, 0L, SEEK_END) != 0) {
        fclose(stream);
        return NULL;
    }
    length = ftell(stream);
    if (length <= 0L || fseek(stream, 0L, SEEK_SET) != 0) {
        fclose(stream);
        return NULL;
    }
    bytes = (char*)malloc((size_t)length + 1U);
    if (bytes == NULL) {
        fclose(stream);
        return NULL;
    }
    if (fread(bytes, 1U, (size_t)length, stream) != (size_t)length) {
        free(bytes);
        fclose(stream);
        return NULL;
    }
    bytes[length] = '\0';
    *length_out = (size_t)length;
    fclose(stream);
    return bytes;
}

static int verify_abi_mismatch(void) {
    linguum_translation_runtime_config config = {0};
    linguum_translation_runtime* runtime = NULL;
    linguum_translation_error* error = NULL;
    linguum_translation_status status;
    config.struct_size = (uint32_t)sizeof(config);
    config.expected_abi_major = LINGUUM_TRANSLATION_ABI_MAJOR + 1U;
    config.expected_abi_minor = 0U;
    config.worker_count = 1U;
    status = linguum_translation_runtime_create(&config, &runtime, &error);
    if (status != LINGUUM_TRANSLATION_STATUS_ABI_INCOMPATIBLE || runtime != NULL || error == NULL ||
        linguum_translation_error_code(error) != (int32_t)LINGUUM_TRANSLATION_STATUS_ABI_INCOMPATIBLE) {
        print_error("ABI mismatch probe", status, error);
        linguum_translation_error_destroy(error);
        linguum_translation_runtime_destroy(runtime);
        return 1;
    }
    linguum_translation_error_destroy(error);
    return 0;
}

static int expect_translation_failure(linguum_translation_translator* translator,
                                      const linguum_translation_request* request,
                                      linguum_translation_status expected,
                                      const char* probe) {
    linguum_translation_result* result = NULL;
    linguum_translation_error* error = NULL;
    const linguum_translation_status status = linguum_translation_translator_translate(
        translator, request, &result, &error
    );
    if (status != expected || result != NULL || error == NULL ||
        linguum_translation_error_code(error) != (int32_t)expected ||
        linguum_translation_error_message(error).length == 0U) {
        print_error(probe, status, error);
        linguum_translation_result_destroy(result);
        linguum_translation_error_destroy(error);
        return 1;
    }
    linguum_translation_error_destroy(error);
    return 0;
}

static int verify_translation_rejections(linguum_translation_translator* translator) {
    static const uint8_t invalid_utf8[] = {0xc3U, 0x28U};
    static const uint8_t embedded_nul[] = {'o', 'k', 0U, 'x'};
    linguum_translation_request request = {0};

    request.struct_size = (uint32_t)sizeof(request);
    request.input_format = LINGUUM_TRANSLATION_INPUT_PLAIN_TEXT;
    request.input.data = invalid_utf8;
    request.input.length = sizeof(invalid_utf8);
    if (expect_translation_failure(translator, &request, LINGUUM_TRANSLATION_STATUS_INVALID_UTF8,
                                   "invalid UTF-8 probe") != 0) {
        return 1;
    }

    request.input.data = embedded_nul;
    request.input.length = sizeof(embedded_nul);
    if (expect_translation_failure(translator, &request, LINGUUM_TRANSLATION_STATUS_INVALID_ARGUMENT,
                                   "embedded NUL probe") != 0) {
        return 1;
    }

    request.input = string_view(CANARY_INPUT);
    request.input_format = LINGUUM_TRANSLATION_INPUT_INTERNAL_STRUCTURED;
    if (expect_translation_failure(translator, &request, LINGUUM_TRANSLATION_STATUS_INVALID_ARGUMENT,
                                   "structured input probe") != 0) {
        return 1;
    }

    request.input_format = LINGUUM_TRANSLATION_INPUT_PLAIN_TEXT;
    request.input.length = (1024U * 1024U) + 1U;
    if (expect_translation_failure(translator, &request, LINGUUM_TRANSLATION_STATUS_REQUEST_TOO_LARGE,
                                   "oversized input probe") != 0) {
        return 1;
    }

    request.struct_size = (uint32_t)sizeof(request) - 1U;
    request.input = string_view(CANARY_INPUT);
    if (expect_translation_failure(translator, &request, LINGUUM_TRANSLATION_STATUS_INVALID_ARGUMENT,
                                   "short request probe") != 0) {
        return 1;
    }
    return 0;
}

static int verify_model_descriptor_bounds(
    linguum_translation_runtime* runtime,
    const linguum_translation_model_descriptor* valid_descriptor
) {
    linguum_translation_model_descriptor descriptor = *valid_descriptor;
    linguum_translation_model* model = NULL;
    linguum_translation_error* error = NULL;
    linguum_translation_status status;

    descriptor.model_path.length = SIZE_MAX;
    status = linguum_translation_model_load(runtime, &descriptor, &model, &error);
    if (status != LINGUUM_TRANSLATION_STATUS_MODEL_DESCRIPTOR_INVALID || model != NULL || error == NULL ||
        linguum_translation_error_code(error) !=
            (int32_t)LINGUUM_TRANSLATION_STATUS_MODEL_DESCRIPTOR_INVALID) {
        print_error("oversized model path probe", status, error);
        linguum_translation_model_destroy(model);
        linguum_translation_error_destroy(error);
        return 1;
    }
    linguum_translation_error_destroy(error);
    return 0;
}

static int run_iteration(const char* model_path, const char* shortlist_path, const char* vocabulary_path,
                         const char* configuration, size_t configuration_length) {
    linguum_translation_runtime_config runtime_config = {0};
    linguum_translation_runtime* runtime = NULL;
    linguum_translation_runtime_info* info = NULL;
    linguum_translation_model_descriptor descriptor = {0};
    linguum_translation_string_view vocabularies[1];
    linguum_translation_model* model = NULL;
    linguum_translation_translator* translator = NULL;
    linguum_translation_request request = {0};
    linguum_translation_result* result = NULL;
    linguum_translation_error* error = NULL;
    linguum_translation_status status;
    int result_code = 1;

    runtime_config.struct_size = (uint32_t)sizeof(runtime_config);
    runtime_config.expected_abi_major = LINGUUM_TRANSLATION_ABI_MAJOR;
    runtime_config.expected_abi_minor = LINGUUM_TRANSLATION_ABI_MINOR;
    runtime_config.worker_count = 1U;
    runtime_config.maximum_input_bytes = 1024U * 1024U;
    status = linguum_translation_runtime_create(&runtime_config, &runtime, &error);
    if (status != LINGUUM_TRANSLATION_STATUS_OK) {
        print_error("runtime create", status, error);
        goto cleanup;
    }

    status = linguum_translation_runtime_info_create(runtime, &info, &error);
    if (status != LINGUUM_TRANSLATION_STATUS_OK) {
        print_error("runtime info create", status, error);
        goto cleanup;
    }
    if (!view_equals(linguum_translation_runtime_info_firefox_revision(info), FIREFOX_REVISION) ||
        !view_equals(linguum_translation_runtime_info_bergamot_version(info), "v0.6.0") ||
        linguum_translation_runtime_info_library_version(info).length == 0U ||
        linguum_translation_runtime_info_acceleration_profile(info).length == 0U) {
        fprintf(stderr, "runtime info identity mismatch\n");
        goto cleanup;
    }

    vocabularies[0] = string_view(vocabulary_path);
    descriptor.struct_size = (uint32_t)sizeof(descriptor);
    descriptor.language_pair = string_view("es-en");
    descriptor.model_path = string_view(model_path);
    descriptor.shortlist_path = string_view(shortlist_path);
    descriptor.vocabulary_paths = vocabularies;
    descriptor.vocabulary_path_count = 1U;
    descriptor.configuration_yaml.data = (const uint8_t*)configuration;
    descriptor.configuration_yaml.length = configuration_length;
    if (verify_model_descriptor_bounds(runtime, &descriptor) != 0) {
        goto cleanup;
    }
    status = linguum_translation_model_load(runtime, &descriptor, &model, &error);
    if (status != LINGUUM_TRANSLATION_STATUS_OK) {
        print_error("model load", status, error);
        goto cleanup;
    }

    status = linguum_translation_translator_create(runtime, model, &translator, &error);
    if (status != LINGUUM_TRANSLATION_STATUS_OK) {
        print_error("translator create", status, error);
        goto cleanup;
    }

    if (verify_translation_rejections(translator) != 0) {
        goto cleanup;
    }

    request.struct_size = (uint32_t)sizeof(request);
    request.input = string_view(CANARY_INPUT);
    request.input_format = LINGUUM_TRANSLATION_INPUT_PLAIN_TEXT;
    status = linguum_translation_translator_translate(translator, &request, &result, &error);
    if (status != LINGUUM_TRANSLATION_STATUS_OK) {
        print_error("translation", status, error);
        goto cleanup;
    }
    if (!view_equals(linguum_translation_result_text(result), CANARY_EXPECTED)) {
        fprintf(stderr, "canary output mismatch\n");
        goto cleanup;
    }
    result_code = 0;

cleanup:
    linguum_translation_error_destroy(error);
    linguum_translation_result_destroy(result);
    linguum_translation_translator_destroy(translator);
    linguum_translation_model_destroy(model);
    linguum_translation_runtime_info_destroy(info);
    linguum_translation_runtime_destroy(runtime);
    return result_code;
}

int main(int argc, char** argv) {
    char* model_path;
    char* shortlist_path;
    char* vocabulary_path;
    char* configuration;
    size_t configuration_length = 0U;
    char* parse_end = NULL;
    long iterations;
    long iteration;

    if (argc != 4) {
        fprintf(stderr, "usage: linguum_translation_canary <model-directory> <configuration> <iterations>\n");
        return 2;
    }
    errno = 0;
    iterations = strtol(argv[3], &parse_end, 10);
    if (errno != 0 || parse_end == argv[3] || *parse_end != '\0' || iterations < 1L || iterations > 1000L) {
        fprintf(stderr, "iterations must be between 1 and 1000\n");
        return 2;
    }
    if (linguum_translation_abi_major() != LINGUUM_TRANSLATION_ABI_MAJOR ||
        linguum_translation_abi_minor() != LINGUUM_TRANSLATION_ABI_MINOR || verify_abi_mismatch() != 0) {
        fprintf(stderr, "ABI version probe failed\n");
        return 1;
    }

    model_path = join_path(argv[1], "model.esen.intgemm.alphas.bin");
    shortlist_path = join_path(argv[1], "lex.50.50.esen.s2t.bin");
    vocabulary_path = join_path(argv[1], "vocab.esen.spm");
    configuration = read_file(argv[2], &configuration_length);
    if (model_path == NULL || shortlist_path == NULL || vocabulary_path == NULL || configuration == NULL) {
        fprintf(stderr, "canary fixture preparation failed\n");
        free(model_path);
        free(shortlist_path);
        free(vocabulary_path);
        free(configuration);
        return 1;
    }

    for (iteration = 0; iteration < iterations; ++iteration) {
        if (run_iteration(model_path, shortlist_path, vocabulary_path, configuration, configuration_length) != 0) {
            fprintf(stderr, "canary lifecycle failed at iteration %ld\n", iteration + 1L);
            free(model_path);
            free(shortlist_path);
            free(vocabulary_path);
            free(configuration);
            return 1;
        }
    }

    free(model_path);
    free(shortlist_path);
    free(vocabulary_path);
    free(configuration);
    printf("canary lifecycle PASS: %ld iterations, ABI %u.%u\n",
           iterations, linguum_translation_abi_major(), linguum_translation_abi_minor());
    return 0;
}

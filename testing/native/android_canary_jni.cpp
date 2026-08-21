// SPDX-License-Identifier: Apache-2.0
#include <jni.h>

#include <cstdint>
#include <cstring>
#include <limits>
#include <string>

#include "linguum_translation.h"

namespace {

constexpr char kBridgeClass[] = "io/linguum/translation/internal/android/CanaryBridge";
constexpr char kFirefoxRevision[] = "48d55cf7ec80093903e2ef7f58b61a84a22ef716";
constexpr char kCanaryInput[] = "\xC2\xBFQu\xC3\xA9 est\xC3\xA1s haciendo?";
constexpr char kCanaryExpected[] = "What are you doing?";

linguum_translation_string_view string_view(const std::string& value) {
  return {reinterpret_cast<const std::uint8_t*>(value.data()), value.size()};
}

bool view_equals(linguum_translation_string_view view, const char* expected) {
  const std::size_t length = std::strlen(expected);
  return view.length == length &&
         (length == 0U || std::memcmp(view.data, expected, length) == 0);
}

std::string error_message(const char* operation,
                          linguum_translation_status status,
                          linguum_translation_error* error) {
  const linguum_translation_string_view message = linguum_translation_error_message(error);
  std::string result(operation);
  result.append(" failed with status ");
  result.append(std::to_string(static_cast<int>(status)));
  if (message.data != nullptr && message.length != 0U) {
    result.append(": ");
    result.append(reinterpret_cast<const char*>(message.data), message.length);
  }
  return result;
}

bool expect_translation_failure(linguum_translation_translator* translator,
                                const linguum_translation_request& request,
                                linguum_translation_status expected,
                                std::string* failure) {
  linguum_translation_result* result = nullptr;
  linguum_translation_error* error = nullptr;
  const linguum_translation_status status = linguum_translation_translator_translate(
      translator, &request, &result, &error);
  const bool passed = status == expected && result == nullptr && error != nullptr &&
                      linguum_translation_error_code(error) == static_cast<std::int32_t>(expected) &&
                      linguum_translation_error_message(error).length != 0U;
  if (!passed) {
    *failure = error_message("translation rejection probe", status, error);
  }
  linguum_translation_result_destroy(result);
  linguum_translation_error_destroy(error);
  return passed;
}

bool verify_abi_mismatch(std::string* failure) {
  linguum_translation_runtime_config config{};
  linguum_translation_runtime* runtime = nullptr;
  linguum_translation_error* error = nullptr;
  config.struct_size = static_cast<std::uint32_t>(sizeof(config));
  config.expected_abi_major = LINGUUM_TRANSLATION_ABI_MAJOR + 1U;
  config.worker_count = 1U;
  const linguum_translation_status status =
      linguum_translation_runtime_create(&config, &runtime, &error);
  const bool passed = status == LINGUUM_TRANSLATION_STATUS_ABI_INCOMPATIBLE &&
                      runtime == nullptr && error != nullptr &&
                      linguum_translation_error_code(error) ==
                          static_cast<std::int32_t>(LINGUUM_TRANSLATION_STATUS_ABI_INCOMPATIBLE);
  if (!passed) {
    *failure = error_message("ABI mismatch probe", status, error);
  }
  linguum_translation_error_destroy(error);
  linguum_translation_runtime_destroy(runtime);
  return passed;
}

bool verify_rejections(linguum_translation_translator* translator, std::string* failure) {
  static const std::uint8_t invalid_utf8[] = {0xc3U, 0x28U};
  static const std::uint8_t embedded_nul[] = {'o', 'k', 0U, 'x'};
  linguum_translation_request request{};
  request.struct_size = static_cast<std::uint32_t>(sizeof(request));
  request.input_format = LINGUUM_TRANSLATION_INPUT_PLAIN_TEXT;

  request.input = {invalid_utf8, sizeof(invalid_utf8)};
  if (!expect_translation_failure(
          translator, request, LINGUUM_TRANSLATION_STATUS_INVALID_UTF8, failure)) {
    return false;
  }
  request.input = {embedded_nul, sizeof(embedded_nul)};
  if (!expect_translation_failure(
          translator, request, LINGUUM_TRANSLATION_STATUS_INVALID_ARGUMENT, failure)) {
    return false;
  }
  const std::string input(kCanaryInput);
  request.input = string_view(input);
  request.input_format = LINGUUM_TRANSLATION_INPUT_INTERNAL_STRUCTURED;
  if (!expect_translation_failure(
          translator, request, LINGUUM_TRANSLATION_STATUS_INVALID_ARGUMENT, failure)) {
    return false;
  }
  request.input_format = LINGUUM_TRANSLATION_INPUT_PLAIN_TEXT;
  request.input.length = (1024U * 1024U) + 1U;
  if (!expect_translation_failure(
          translator, request, LINGUUM_TRANSLATION_STATUS_REQUEST_TOO_LARGE, failure)) {
    return false;
  }
  request.input = string_view(input);
  request.struct_size = static_cast<std::uint32_t>(sizeof(request) - 1U);
  return expect_translation_failure(
      translator, request, LINGUUM_TRANSLATION_STATUS_INVALID_ARGUMENT, failure);
}

bool run_iteration(const std::string& model_directory,
                   const std::string& configuration,
                   std::string* failure) {
  linguum_translation_runtime* runtime = nullptr;
  linguum_translation_runtime_info* info = nullptr;
  linguum_translation_model* model = nullptr;
  linguum_translation_translator* translator = nullptr;
  linguum_translation_result* result = nullptr;
  linguum_translation_error* error = nullptr;
  bool passed = false;

  linguum_translation_runtime_config runtime_config{};
  runtime_config.struct_size = static_cast<std::uint32_t>(sizeof(runtime_config));
  runtime_config.expected_abi_major = LINGUUM_TRANSLATION_ABI_MAJOR;
  runtime_config.expected_abi_minor = LINGUUM_TRANSLATION_ABI_MINOR;
  runtime_config.worker_count = 1U;
  runtime_config.maximum_input_bytes = 1024U * 1024U;
  linguum_translation_status status =
      linguum_translation_runtime_create(&runtime_config, &runtime, &error);
  if (status != LINGUUM_TRANSLATION_STATUS_OK) {
    *failure = error_message("runtime create", status, error);
    goto cleanup;
  }

  status = linguum_translation_runtime_info_create(runtime, &info, &error);
  if (status != LINGUUM_TRANSLATION_STATUS_OK ||
      !view_equals(linguum_translation_runtime_info_firefox_revision(info), kFirefoxRevision) ||
      !view_equals(linguum_translation_runtime_info_bergamot_version(info), "v0.6.0") ||
      linguum_translation_runtime_info_library_version(info).length == 0U ||
      linguum_translation_runtime_info_acceleration_profile(info).length == 0U) {
    *failure = status == LINGUUM_TRANSLATION_STATUS_OK
                   ? "runtime identity probe failed"
                   : error_message("runtime info create", status, error);
    goto cleanup;
  }

  {
    const std::string model_path = model_directory + "/model.esen.intgemm.alphas.bin";
    const std::string shortlist_path = model_directory + "/lex.50.50.esen.s2t.bin";
    const std::string vocabulary_path = model_directory + "/vocab.esen.spm";
    const std::string language_pair = "es-en";
    const linguum_translation_string_view vocabularies[] = {string_view(vocabulary_path)};
    linguum_translation_model_descriptor descriptor{};
    descriptor.struct_size = static_cast<std::uint32_t>(sizeof(descriptor));
    descriptor.language_pair = string_view(language_pair);
    descriptor.model_path = string_view(model_path);
    descriptor.shortlist_path = string_view(shortlist_path);
    descriptor.vocabulary_paths = vocabularies;
    descriptor.vocabulary_path_count = 1U;
    descriptor.configuration_yaml = string_view(configuration);

    linguum_translation_model_descriptor invalid_descriptor = descriptor;
    invalid_descriptor.model_path.length = std::numeric_limits<std::size_t>::max();
    linguum_translation_model* invalid_model = nullptr;
    linguum_translation_error* invalid_error = nullptr;
    status = linguum_translation_model_load(
        runtime, &invalid_descriptor, &invalid_model, &invalid_error);
    const bool invalid_passed =
        status == LINGUUM_TRANSLATION_STATUS_MODEL_DESCRIPTOR_INVALID &&
        invalid_model == nullptr && invalid_error != nullptr &&
        linguum_translation_error_code(invalid_error) ==
            static_cast<std::int32_t>(LINGUUM_TRANSLATION_STATUS_MODEL_DESCRIPTOR_INVALID);
    if (!invalid_passed) {
      *failure = error_message("model descriptor bounds probe", status, invalid_error);
      linguum_translation_model_destroy(invalid_model);
      linguum_translation_error_destroy(invalid_error);
      goto cleanup;
    }
    linguum_translation_error_destroy(invalid_error);

    status = linguum_translation_model_load(runtime, &descriptor, &model, &error);
    if (status != LINGUUM_TRANSLATION_STATUS_OK) {
      *failure = error_message("model load", status, error);
      goto cleanup;
    }
  }

  status = linguum_translation_translator_create(runtime, model, &translator, &error);
  if (status != LINGUUM_TRANSLATION_STATUS_OK) {
    *failure = error_message("translator create", status, error);
    goto cleanup;
  }
  if (!verify_rejections(translator, failure)) {
    goto cleanup;
  }

  {
    const std::string input(kCanaryInput);
    linguum_translation_request request{};
    request.struct_size = static_cast<std::uint32_t>(sizeof(request));
    request.input = string_view(input);
    request.input_format = LINGUUM_TRANSLATION_INPUT_PLAIN_TEXT;
    status = linguum_translation_translator_translate(translator, &request, &result, &error);
    if (status != LINGUUM_TRANSLATION_STATUS_OK) {
      *failure = error_message("translation", status, error);
      goto cleanup;
    }
    if (!view_equals(linguum_translation_result_text(result), kCanaryExpected)) {
      *failure = "canary output mismatch";
      goto cleanup;
    }
  }
  passed = true;

cleanup:
  linguum_translation_error_destroy(error);
  linguum_translation_result_destroy(result);
  linguum_translation_translator_destroy(translator);
  linguum_translation_model_destroy(model);
  linguum_translation_runtime_info_destroy(info);
  linguum_translation_runtime_destroy(runtime);
  return passed;
}

void throw_illegal_state(JNIEnv* environment, const std::string& message) {
  jclass exception_class = environment->FindClass("java/lang/IllegalStateException");
  if (exception_class != nullptr) {
    environment->ThrowNew(exception_class, message.c_str());
    environment->DeleteLocalRef(exception_class);
  }
}

jstring native_run_canary(JNIEnv* environment,
                          jclass,
                          jstring model_directory_value,
                          jstring configuration_value,
                          jint iterations) {
  if (model_directory_value == nullptr || configuration_value == nullptr ||
      iterations < 1 || iterations > 100) {
    throw_illegal_state(environment, "invalid native canary arguments");
    return nullptr;
  }
  const char* model_directory_bytes =
      environment->GetStringUTFChars(model_directory_value, nullptr);
  if (model_directory_bytes == nullptr) {
    return nullptr;
  }
  const char* configuration_bytes =
      environment->GetStringUTFChars(configuration_value, nullptr);
  if (configuration_bytes == nullptr) {
    environment->ReleaseStringUTFChars(model_directory_value, model_directory_bytes);
    return nullptr;
  }
  const std::string model_directory(model_directory_bytes);
  const std::string configuration(configuration_bytes);
  environment->ReleaseStringUTFChars(configuration_value, configuration_bytes);
  environment->ReleaseStringUTFChars(model_directory_value, model_directory_bytes);

  std::string failure;
  if (linguum_translation_abi_major() != LINGUUM_TRANSLATION_ABI_MAJOR ||
      linguum_translation_abi_minor() != LINGUUM_TRANSLATION_ABI_MINOR ||
      !verify_abi_mismatch(&failure)) {
    throw_illegal_state(environment, failure.empty() ? "ABI version probe failed" : failure);
    return nullptr;
  }
  for (jint iteration = 0; iteration < iterations; ++iteration) {
    if (!run_iteration(model_directory, configuration, &failure)) {
      throw_illegal_state(
          environment,
          failure + " at lifecycle iteration " + std::to_string(iteration + 1));
      return nullptr;
    }
  }
  const std::string result = "canary lifecycle PASS: " + std::to_string(iterations) +
                             " iterations, ABI " +
                             std::to_string(LINGUUM_TRANSLATION_ABI_MAJOR) + "." +
                             std::to_string(LINGUUM_TRANSLATION_ABI_MINOR);
  return environment->NewStringUTF(result.c_str());
}

const JNINativeMethod kMethods[] = {
    {const_cast<char*>("nativeRunCanary"),
     const_cast<char*>("(Ljava/lang/String;Ljava/lang/String;I)Ljava/lang/String;"),
     reinterpret_cast<void*>(native_run_canary)},
};

}  // namespace

extern "C" JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* virtual_machine, void*) {
  JNIEnv* environment = nullptr;
  if (virtual_machine->GetEnv(
          reinterpret_cast<void**>(&environment), JNI_VERSION_1_6) != JNI_OK) {
    return JNI_ERR;
  }
  jclass bridge_class = environment->FindClass(kBridgeClass);
  if (bridge_class == nullptr) {
    return JNI_ERR;
  }
  const jint result = environment->RegisterNatives(
      bridge_class,
      kMethods,
      static_cast<jint>(sizeof(kMethods) / sizeof(kMethods[0])));
  environment->DeleteLocalRef(bridge_class);
  return result == JNI_OK ? JNI_VERSION_1_6 : JNI_ERR;
}

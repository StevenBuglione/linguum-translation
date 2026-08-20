// SPDX-License-Identifier: Apache-2.0
#include "linguum_translation.h"

#include <algorithm>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <exception>
#include <fstream>
#include <future>
#include <limits>
#include <memory>
#include <mutex>
#include <new>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "mozilla_upstream.h"

#ifndef LINGUUM_LIBRARY_VERSION
#define LINGUUM_LIBRARY_VERSION "0.0.0-SNAPSHOT"
#endif
#ifndef LINGUUM_FIREFOX_REVISION
#define LINGUUM_FIREFOX_REVISION "unknown"
#endif
#ifndef LINGUUM_BERGAMOT_VERSION
#define LINGUUM_BERGAMOT_VERSION "unknown"
#endif
#ifndef LINGUUM_ACCELERATION_PROFILE
#define LINGUUM_ACCELERATION_PROFILE "unknown"
#endif

namespace {

using marian::bergamot::AsyncService;
using marian::bergamot::Response;
using marian::bergamot::ResponseOptions;
using marian::bergamot::TranslationModel;

constexpr std::uint64_t kDefaultMaximumInputBytes = 1024U * 1024U;
constexpr std::size_t kMaximumConfigurationBytes = 64U * 1024U;
constexpr std::size_t kMaximumLanguagePairBytes = 63U;
constexpr std::size_t kMaximumPathBytes = 32U * 1024U;
constexpr std::chrono::seconds kTranslationTimeout{120};

std::mutex& marian_abort_mutex() {
  static std::mutex mutex;
  return mutex;
}

class AbiFailure final : public std::runtime_error {
 public:
  AbiFailure(linguum_translation_status status, const char* message)
      : std::runtime_error(message), status_(status) {}

  linguum_translation_status status() const noexcept { return status_; }

 private:
  linguum_translation_status status_;
};

class MarianAbortMode final {
 public:
  MarianAbortMode()
      : lock_(marian_abort_mutex()), previous_(marian::getThrowExceptionOnAbort()) {
    marian::setThrowExceptionOnAbort(true);
  }

  ~MarianAbortMode() { marian::setThrowExceptionOnAbort(previous_); }

  MarianAbortMode(const MarianAbortMode&) = delete;
  MarianAbortMode& operator=(const MarianAbortMode&) = delete;

 private:
  std::unique_lock<std::mutex> lock_;
  bool previous_;
};

bool valid_utf8(const std::uint8_t* data, std::size_t length) noexcept {
  std::size_t index = 0;
  while (index < length) {
    const std::uint8_t first = data[index];
    if (first <= 0x7FU) {
      ++index;
      continue;
    }
    std::size_t continuation_count = 0;
    std::uint32_t code_point = 0;
    if (first >= 0xC2U && first <= 0xDFU) {
      continuation_count = 1;
      code_point = first & 0x1FU;
    } else if (first >= 0xE0U && first <= 0xEFU) {
      continuation_count = 2;
      code_point = first & 0x0FU;
    } else if (first >= 0xF0U && first <= 0xF4U) {
      continuation_count = 3;
      code_point = first & 0x07U;
    } else {
      return false;
    }
    if (index + continuation_count >= length) {
      return false;
    }
    for (std::size_t offset = 1; offset <= continuation_count; ++offset) {
      const std::uint8_t next = data[index + offset];
      if ((next & 0xC0U) != 0x80U) {
        return false;
      }
      code_point = (code_point << 6U) | (next & 0x3FU);
    }
    if ((continuation_count == 2 && code_point < 0x800U) ||
        (continuation_count == 3 && code_point < 0x10000U) ||
        code_point > 0x10FFFFU ||
        (code_point >= 0xD800U && code_point <= 0xDFFFU)) {
      return false;
    }
    index += continuation_count + 1;
  }
  return true;
}

std::string copy_view(
    linguum_translation_string_view view,
    linguum_translation_status invalid_status,
    const char* invalid_message,
    bool allow_empty = false,
    std::size_t maximum_length = std::numeric_limits<std::size_t>::max()) {
  if ((view.data == nullptr && view.length != 0U) || (!allow_empty && view.length == 0U)) {
    throw AbiFailure(invalid_status, invalid_message);
  }
  if (view.length > maximum_length) {
    throw AbiFailure(invalid_status, invalid_message);
  }
  if (view.length == 0U) {
    return {};
  }
  if (!valid_utf8(view.data, view.length)) {
    throw AbiFailure(LINGUUM_TRANSLATION_STATUS_INVALID_UTF8, "input is not valid UTF-8");
  }
  if (std::find(view.data, view.data + view.length, static_cast<std::uint8_t>(0)) != view.data + view.length) {
    throw AbiFailure(invalid_status, invalid_message);
  }
  return std::string(reinterpret_cast<const char*>(view.data), view.length);
}

bool reserved_configuration_key(const std::string& configuration) {
  std::size_t cursor = 0;
  while (cursor <= configuration.size()) {
    const std::size_t end = configuration.find('\n', cursor);
    const std::string line = configuration.substr(cursor, end == std::string::npos ? end : end - cursor);
    const std::size_t first = line.find_first_not_of(" \t");
    if (first != std::string::npos) {
      const std::string key = line.substr(first);
      if (key.rfind("models:", 0) == 0 || key.rfind("model:", 0) == 0 ||
          key.rfind("vocabs:", 0) == 0 || key.rfind("shortlist:", 0) == 0) {
        return true;
      }
    }
    if (end == std::string::npos) {
      break;
    }
    cursor = end + 1;
  }
  return false;
}

std::string yaml_quote(const std::string& value) {
  std::string quoted{"'"};
  quoted.reserve(value.size() + 2);
  for (const char character : value) {
    quoted.push_back(character);
    if (character == '\'') {
      quoted.push_back('\'');
    }
  }
  quoted.push_back('\'');
  return quoted;
}

void require_readable_file(const std::string& path) {
  std::ifstream stream(path, std::ios::binary);
  if (!stream.good()) {
    throw AbiFailure(LINGUUM_TRANSLATION_STATUS_MODEL_DESCRIPTOR_INVALID,
                     "model descriptor contains an unreadable file");
  }
  stream.seekg(0, std::ios::end);
  if (stream.tellg() <= 0) {
    throw AbiFailure(LINGUUM_TRANSLATION_STATUS_MODEL_DESCRIPTOR_INVALID,
                     "model descriptor contains an empty file");
  }
}

std::string build_model_configuration(const linguum_translation_model_descriptor& descriptor) {
  const std::string language_pair = copy_view(
      descriptor.language_pair,
      LINGUUM_TRANSLATION_STATUS_MODEL_DESCRIPTOR_INVALID,
      "model language pair is missing",
      false,
      kMaximumLanguagePairBytes);
  if (language_pair.find('-') == std::string::npos) {
    throw AbiFailure(LINGUUM_TRANSLATION_STATUS_MODEL_DESCRIPTOR_INVALID,
                     "model language pair is invalid");
  }
  const std::string model_path = copy_view(
      descriptor.model_path,
      LINGUUM_TRANSLATION_STATUS_MODEL_DESCRIPTOR_INVALID,
      "model path is missing",
      false,
      kMaximumPathBytes);
  const std::string shortlist_path = copy_view(
      descriptor.shortlist_path,
      LINGUUM_TRANSLATION_STATUS_MODEL_DESCRIPTOR_INVALID,
      "shortlist path is missing",
      false,
      kMaximumPathBytes);
  if (descriptor.vocabulary_paths == nullptr ||
      descriptor.vocabulary_path_count == 0U ||
      descriptor.vocabulary_path_count > 2U) {
    throw AbiFailure(LINGUUM_TRANSLATION_STATUS_MODEL_DESCRIPTOR_INVALID,
                     "model descriptor must contain one or two vocabularies");
  }
  std::vector<std::string> vocabularies;
  vocabularies.reserve(2);
  for (std::size_t index = 0; index < descriptor.vocabulary_path_count; ++index) {
    vocabularies.push_back(copy_view(
        descriptor.vocabulary_paths[index],
        LINGUUM_TRANSLATION_STATUS_MODEL_DESCRIPTOR_INVALID,
        "vocabulary path is missing",
        false,
        kMaximumPathBytes));
  }
  if (vocabularies.size() == 1U) {
    vocabularies.push_back(vocabularies.front());
  }
  std::string configuration = copy_view(
      descriptor.configuration_yaml,
      LINGUUM_TRANSLATION_STATUS_MODEL_DESCRIPTOR_INVALID,
      "model configuration is missing",
      false,
      kMaximumConfigurationBytes);
  if (reserved_configuration_key(configuration)) {
    throw AbiFailure(LINGUUM_TRANSLATION_STATUS_MODEL_DESCRIPTOR_INVALID,
                     "model configuration is invalid");
  }
  require_readable_file(model_path);
  require_readable_file(shortlist_path);
  for (const std::string& vocabulary : vocabularies) {
    require_readable_file(vocabulary);
  }
  configuration.append("\nmodels:\n  - ");
  configuration.append(yaml_quote(model_path));
  configuration.append("\nvocabs:\n  - ");
  configuration.append(yaml_quote(vocabularies[0]));
  configuration.append("\n  - ");
  configuration.append(yaml_quote(vocabularies[1]));
  configuration.append("\nshortlist:\n  - ");
  configuration.append(yaml_quote(shortlist_path));
  configuration.append("\n  - false\n");
  return configuration;
}

linguum_translation_string_view borrowed_view(const std::string& value) noexcept {
  return {reinterpret_cast<const std::uint8_t*>(value.data()), value.size()};
}

linguum_translation_string_view empty_view() noexcept { return {nullptr, 0U}; }

}  // namespace

struct linguum_translation_error {
  std::int32_t code;
  std::string message;
};

struct linguum_translation_runtime {
  explicit linguum_translation_runtime(std::uint32_t workers, std::uint64_t maximum_input)
      : maximum_input_bytes(maximum_input) {
    AsyncService::Config configuration;
    configuration.numWorkers = workers;
    configuration.cacheSize = 0U;
    configuration.workerExceptionHandler =
        [this](std::exception_ptr error) noexcept { fail_active_translation(error); };
    service = std::make_unique<AsyncService>(configuration);
  }

  void activate_translation(const std::shared_ptr<std::promise<Response>>& promise) {
    std::lock_guard<std::mutex> lock(active_translation_mutex);
    active_translation = promise;
  }

  void deactivate_translation(const std::shared_ptr<std::promise<Response>>& promise) {
    std::lock_guard<std::mutex> lock(active_translation_mutex);
    if (active_translation.lock() == promise) {
      active_translation.reset();
    }
  }

  void fail_active_translation(std::exception_ptr error) noexcept {
    std::shared_ptr<std::promise<Response>> promise;
    {
      std::lock_guard<std::mutex> lock(active_translation_mutex);
      promise = active_translation.lock();
    }
    if (promise != nullptr) {
      try {
        promise->set_exception(error);
      } catch (const std::future_error&) {
      }
    }
  }

  std::mutex active_translation_mutex;
  std::weak_ptr<std::promise<Response>> active_translation;
  std::unique_ptr<AsyncService> service;
  std::uint64_t maximum_input_bytes;
};

struct linguum_translation_model {
  linguum_translation_runtime* runtime;
  std::shared_ptr<TranslationModel> model;
};

struct linguum_translation_translator {
  linguum_translation_runtime* runtime;
  std::shared_ptr<TranslationModel> model;
};

struct linguum_translation_result {
  std::string text;
};

struct linguum_translation_runtime_info {
  std::string library_version{LINGUUM_LIBRARY_VERSION};
  std::string firefox_revision{LINGUUM_FIREFOX_REVISION};
  std::string bergamot_version{LINGUUM_BERGAMOT_VERSION};
  std::string acceleration_profile{LINGUUM_ACCELERATION_PROFILE};
};

namespace {

class TranslationPromiseLease final {
 public:
  TranslationPromiseLease(
      linguum_translation_runtime* runtime,
      std::shared_ptr<std::promise<Response>> promise)
      : runtime_(runtime), promise_(std::move(promise)) {
    runtime_->activate_translation(promise_);
  }

  ~TranslationPromiseLease() { runtime_->deactivate_translation(promise_); }

  TranslationPromiseLease(const TranslationPromiseLease&) = delete;
  TranslationPromiseLease& operator=(const TranslationPromiseLease&) = delete;

 private:
  linguum_translation_runtime* runtime_;
  std::shared_ptr<std::promise<Response>> promise_;
};

void clear_error(linguum_translation_error** error_out) noexcept {
  if (error_out != nullptr) {
    *error_out = nullptr;
  }
}

linguum_translation_status fail(
    linguum_translation_status status,
    const char* message,
    linguum_translation_error** error_out) noexcept {
  if (error_out != nullptr) {
    try {
      *error_out = new linguum_translation_error{static_cast<std::int32_t>(status), message};
    } catch (...) {
      *error_out = nullptr;
      return LINGUUM_TRANSLATION_STATUS_OUT_OF_MEMORY;
    }
  }
  return status;
}

linguum_translation_status exception_status(
    const AbiFailure& error,
    linguum_translation_error** error_out) noexcept {
  return fail(error.status(), error.what(), error_out);
}

linguum_translation_status unknown_failure(
    linguum_translation_status status,
    const char* message,
    linguum_translation_error** error_out) noexcept {
  return fail(status, message, error_out);
}

}  // namespace

extern "C" {

std::uint32_t linguum_translation_abi_major(void) { return LINGUUM_TRANSLATION_ABI_MAJOR; }

std::uint32_t linguum_translation_abi_minor(void) { return LINGUUM_TRANSLATION_ABI_MINOR; }

linguum_translation_status linguum_translation_runtime_create(
    const linguum_translation_runtime_config* config,
    linguum_translation_runtime** runtime_out,
    linguum_translation_error** error_out) {
  clear_error(error_out);
  if (runtime_out == nullptr) {
    return fail(LINGUUM_TRANSLATION_STATUS_INVALID_ARGUMENT, "runtime output is required", error_out);
  }
  *runtime_out = nullptr;
  if (config == nullptr || config->struct_size < sizeof(linguum_translation_runtime_config)) {
    return fail(LINGUUM_TRANSLATION_STATUS_INVALID_ARGUMENT, "runtime configuration is invalid", error_out);
  }
  if (config->expected_abi_major != LINGUUM_TRANSLATION_ABI_MAJOR ||
      config->expected_abi_minor > LINGUUM_TRANSLATION_ABI_MINOR) {
    return fail(LINGUUM_TRANSLATION_STATUS_ABI_INCOMPATIBLE, "native ABI is incompatible", error_out);
  }
  if (config->worker_count != 1U) {
    return fail(LINGUUM_TRANSLATION_STATUS_INVALID_ARGUMENT, "M1 runtime requires exactly one worker", error_out);
  }
  try {
    const std::uint64_t maximum_input =
        config->maximum_input_bytes == 0U ? kDefaultMaximumInputBytes : config->maximum_input_bytes;
    *runtime_out = new linguum_translation_runtime(config->worker_count, maximum_input);
    return LINGUUM_TRANSLATION_STATUS_OK;
  } catch (const std::bad_alloc&) {
    return unknown_failure(LINGUUM_TRANSLATION_STATUS_OUT_OF_MEMORY, "runtime allocation failed", error_out);
  } catch (...) {
    return unknown_failure(LINGUUM_TRANSLATION_STATUS_INTERNAL_ERROR, "runtime creation failed", error_out);
  }
}

linguum_translation_status linguum_translation_runtime_info_create(
    const linguum_translation_runtime* runtime,
    linguum_translation_runtime_info** info_out,
    linguum_translation_error** error_out) {
  clear_error(error_out);
  if (info_out == nullptr) {
    return fail(LINGUUM_TRANSLATION_STATUS_INVALID_ARGUMENT, "runtime info output is required", error_out);
  }
  *info_out = nullptr;
  if (runtime == nullptr || runtime->service == nullptr) {
    return fail(LINGUUM_TRANSLATION_STATUS_INVALID_HANDLE, "runtime handle is invalid", error_out);
  }
  try {
    *info_out = new linguum_translation_runtime_info();
    return LINGUUM_TRANSLATION_STATUS_OK;
  } catch (const std::bad_alloc&) {
    return unknown_failure(LINGUUM_TRANSLATION_STATUS_OUT_OF_MEMORY, "runtime info allocation failed", error_out);
  } catch (...) {
    return unknown_failure(LINGUUM_TRANSLATION_STATUS_INTERNAL_ERROR, "runtime info creation failed", error_out);
  }
}

void linguum_translation_runtime_destroy(linguum_translation_runtime* runtime) { delete runtime; }

linguum_translation_status linguum_translation_model_load(
    linguum_translation_runtime* runtime,
    const linguum_translation_model_descriptor* descriptor,
    linguum_translation_model** model_out,
    linguum_translation_error** error_out) {
  clear_error(error_out);
  if (model_out == nullptr) {
    return fail(LINGUUM_TRANSLATION_STATUS_INVALID_ARGUMENT, "model output is required", error_out);
  }
  *model_out = nullptr;
  if (runtime == nullptr || runtime->service == nullptr) {
    return fail(LINGUUM_TRANSLATION_STATUS_INVALID_HANDLE, "runtime handle is invalid", error_out);
  }
  if (descriptor == nullptr || descriptor->struct_size < sizeof(linguum_translation_model_descriptor)) {
    return fail(LINGUUM_TRANSLATION_STATUS_MODEL_DESCRIPTOR_INVALID, "model descriptor is invalid", error_out);
  }
  try {
    const std::string configuration = build_model_configuration(*descriptor);
    MarianAbortMode abort_mode;
    auto options = marian::bergamot::parseOptionsFromString(configuration, true);
    auto model = runtime->service->createCompatibleModel(options);
    *model_out = new linguum_translation_model{runtime, std::move(model)};
    return LINGUUM_TRANSLATION_STATUS_OK;
  } catch (const AbiFailure& error) {
    return exception_status(error, error_out);
  } catch (const std::bad_alloc&) {
    return unknown_failure(LINGUUM_TRANSLATION_STATUS_OUT_OF_MEMORY, "model allocation failed", error_out);
  } catch (...) {
    return unknown_failure(LINGUUM_TRANSLATION_STATUS_MODEL_LOAD_FAILED, "native model load failed", error_out);
  }
}

void linguum_translation_model_destroy(linguum_translation_model* model) { delete model; }

linguum_translation_status linguum_translation_translator_create(
    linguum_translation_runtime* runtime,
    linguum_translation_model* model,
    linguum_translation_translator** translator_out,
    linguum_translation_error** error_out) {
  clear_error(error_out);
  if (translator_out == nullptr) {
    return fail(LINGUUM_TRANSLATION_STATUS_INVALID_ARGUMENT, "translator output is required", error_out);
  }
  *translator_out = nullptr;
  if (runtime == nullptr || runtime->service == nullptr || model == nullptr || model->model == nullptr ||
      model->runtime != runtime) {
    return fail(LINGUUM_TRANSLATION_STATUS_INVALID_HANDLE, "runtime or model handle is invalid", error_out);
  }
  try {
    *translator_out = new linguum_translation_translator{runtime, model->model};
    return LINGUUM_TRANSLATION_STATUS_OK;
  } catch (const std::bad_alloc&) {
    return unknown_failure(LINGUUM_TRANSLATION_STATUS_OUT_OF_MEMORY, "translator allocation failed", error_out);
  } catch (...) {
    return unknown_failure(LINGUUM_TRANSLATION_STATUS_INTERNAL_ERROR, "translator creation failed", error_out);
  }
}

void linguum_translation_translator_destroy(linguum_translation_translator* translator) { delete translator; }

linguum_translation_status linguum_translation_translator_translate(
    linguum_translation_translator* translator,
    const linguum_translation_request* request,
    linguum_translation_result** result_out,
    linguum_translation_error** error_out) {
  clear_error(error_out);
  if (result_out == nullptr) {
    return fail(LINGUUM_TRANSLATION_STATUS_INVALID_ARGUMENT, "result output is required", error_out);
  }
  *result_out = nullptr;
  if (translator == nullptr || translator->runtime == nullptr || translator->runtime->service == nullptr ||
      translator->model == nullptr) {
    return fail(LINGUUM_TRANSLATION_STATUS_INVALID_HANDLE, "translator handle is invalid", error_out);
  }
  if (request == nullptr || request->struct_size < sizeof(linguum_translation_request)) {
    return fail(LINGUUM_TRANSLATION_STATUS_INVALID_ARGUMENT, "translation request is invalid", error_out);
  }
  if (request->input_format != LINGUUM_TRANSLATION_INPUT_PLAIN_TEXT) {
    return fail(LINGUUM_TRANSLATION_STATUS_INVALID_ARGUMENT, "translation input format is unsupported", error_out);
  }
  if (request->input.length > translator->runtime->maximum_input_bytes) {
    return fail(LINGUUM_TRANSLATION_STATUS_REQUEST_TOO_LARGE, "translation request exceeds the configured limit", error_out);
  }
  try {
    std::string input = copy_view(
        request->input,
        LINGUUM_TRANSLATION_STATUS_INVALID_ARGUMENT,
        "translation input is missing");
    MarianAbortMode abort_mode;
    auto promise = std::make_shared<std::promise<Response>>();
    std::future<Response> future = promise->get_future();
    TranslationPromiseLease promise_lease(translator->runtime, promise);
    ResponseOptions options;
    options.qualityScores = false;
    options.alignment = false;
    options.HTML = false;
    translator->runtime->service->translate(
        translator->model,
        std::move(input),
        [promise](Response&& response) {
          try {
            promise->set_value(std::move(response));
          } catch (const std::future_error&) {
          }
        },
        options);
    if (future.wait_for(kTranslationTimeout) != std::future_status::ready) {
      return fail(LINGUUM_TRANSLATION_STATUS_TRANSLATION_FAILED, "native translation timed out", error_out);
    }
    Response response = future.get();
    *result_out = new linguum_translation_result{response.target.text};
    return LINGUUM_TRANSLATION_STATUS_OK;
  } catch (const AbiFailure& error) {
    return exception_status(error, error_out);
  } catch (const std::bad_alloc&) {
    return unknown_failure(LINGUUM_TRANSLATION_STATUS_OUT_OF_MEMORY, "translation allocation failed", error_out);
  } catch (const std::exception& error) {
    return unknown_failure(LINGUUM_TRANSLATION_STATUS_TRANSLATION_FAILED, error.what(), error_out);
  } catch (...) {
    return unknown_failure(LINGUUM_TRANSLATION_STATUS_TRANSLATION_FAILED, "native translation failed", error_out);
  }
}

linguum_translation_string_view linguum_translation_result_text(const linguum_translation_result* result) {
  return result == nullptr ? empty_view() : borrowed_view(result->text);
}

void linguum_translation_result_destroy(linguum_translation_result* result) { delete result; }

std::int32_t linguum_translation_error_code(const linguum_translation_error* error) {
  return error == nullptr ? 0 : error->code;
}

linguum_translation_string_view linguum_translation_error_message(const linguum_translation_error* error) {
  return error == nullptr ? empty_view() : borrowed_view(error->message);
}

void linguum_translation_error_destroy(linguum_translation_error* error) { delete error; }

linguum_translation_string_view linguum_translation_runtime_info_library_version(
    const linguum_translation_runtime_info* info) {
  return info == nullptr ? empty_view() : borrowed_view(info->library_version);
}

linguum_translation_string_view linguum_translation_runtime_info_firefox_revision(
    const linguum_translation_runtime_info* info) {
  return info == nullptr ? empty_view() : borrowed_view(info->firefox_revision);
}

linguum_translation_string_view linguum_translation_runtime_info_bergamot_version(
    const linguum_translation_runtime_info* info) {
  return info == nullptr ? empty_view() : borrowed_view(info->bergamot_version);
}

linguum_translation_string_view linguum_translation_runtime_info_acceleration_profile(
    const linguum_translation_runtime_info* info) {
  return info == nullptr ? empty_view() : borrowed_view(info->acceleration_profile);
}

void linguum_translation_runtime_info_destroy(linguum_translation_runtime_info* info) { delete info; }

}  // extern "C"

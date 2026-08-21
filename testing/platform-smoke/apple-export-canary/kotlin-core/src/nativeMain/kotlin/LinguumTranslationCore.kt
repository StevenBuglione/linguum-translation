// SPDX-License-Identifier: Apache-2.0
@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

import cnames.structs.linguum_translation_error
import cnames.structs.linguum_translation_model
import cnames.structs.linguum_translation_result
import cnames.structs.linguum_translation_runtime
import cnames.structs.linguum_translation_translator
import io.linguum.translation.internal.cinterop.LINGUUM_TRANSLATION_ABI_MAJOR
import io.linguum.translation.internal.cinterop.LINGUUM_TRANSLATION_ABI_MINOR
import io.linguum.translation.internal.cinterop.LINGUUM_TRANSLATION_INPUT_PLAIN_TEXT
import io.linguum.translation.internal.cinterop.LINGUUM_TRANSLATION_STATUS_OK
import io.linguum.translation.internal.cinterop.linguum_translation_abi_major
import io.linguum.translation.internal.cinterop.linguum_translation_abi_minor
import io.linguum.translation.internal.cinterop.linguum_translation_error_destroy
import io.linguum.translation.internal.cinterop.linguum_translation_error_message
import io.linguum.translation.internal.cinterop.linguum_translation_model_descriptor
import io.linguum.translation.internal.cinterop.linguum_translation_model_destroy
import io.linguum.translation.internal.cinterop.linguum_translation_model_load
import io.linguum.translation.internal.cinterop.linguum_translation_request
import io.linguum.translation.internal.cinterop.linguum_translation_result_destroy
import io.linguum.translation.internal.cinterop.linguum_translation_result_text
import io.linguum.translation.internal.cinterop.linguum_translation_runtime_config
import io.linguum.translation.internal.cinterop.linguum_translation_runtime_create
import io.linguum.translation.internal.cinterop.linguum_translation_runtime_destroy
import io.linguum.translation.internal.cinterop.linguum_translation_string_view
import io.linguum.translation.internal.cinterop.linguum_translation_translator_create
import io.linguum.translation.internal.cinterop.linguum_translation_translator_destroy
import io.linguum.translation.internal.cinterop.linguum_translation_translator_translate
import kotlinx.cinterop.*
import platform.posix.SEEK_END
import platform.posix.SEEK_SET
import platform.posix.fclose
import platform.posix.fopen
import platform.posix.fread
import platform.posix.fseek
import platform.posix.ftell
import platform.posix.memset

private const val ERROR_NONE = 0
private const val ERROR_CLOSED = 1
private const val ERROR_TRANSLATION = 2

class LinguumTranslationCoreOutcome(
    val text: String?,
    val errorCode: Int,
    val errorMessage: String?,
)

class LinguumTranslationCoreService(
    private val modelDirectory: String,
    private val configurationPath: String,
) {
    private var closed = false

    val abiVersion: String
        get() = "${linguum_translation_abi_major()}.${linguum_translation_abi_minor()}"

    fun supportsLanguagePair(source: String, target: String): Boolean =
        source == "es" && target == "en"

    fun translateText(text: String): LinguumTranslationCoreOutcome {
        if (closed) {
            return LinguumTranslationCoreOutcome(null, ERROR_CLOSED, "service is closed")
        }
        return try {
            check(linguum_translation_abi_major() == LINGUUM_TRANSLATION_ABI_MAJOR)
            check(linguum_translation_abi_minor() == LINGUUM_TRANSLATION_ABI_MINOR)
            LinguumTranslationCoreOutcome(
                runTranslation(modelDirectory, configurationPath, text),
                ERROR_NONE,
                null,
            )
        } catch (failure: Throwable) {
            LinguumTranslationCoreOutcome(
                null,
                ERROR_TRANSLATION,
                failure.message ?: "translation failed",
            )
        }
    }

    fun close() {
        closed = true
    }
}

private fun MemScope.assignStringView(
    target: linguum_translation_string_view,
    value: String,
) {
    val bytes = value.encodeToByteArray()
    val storage = allocArray<UByteVar>(bytes.size + 1)
    bytes.forEachIndexed { index, byte -> storage[index] = byte.toUByte() }
    storage[bytes.size] = 0u
    target.data = storage
    target.length = bytes.size.convert()
}

private fun viewText(view: CValue<linguum_translation_string_view>): String =
    view.useContents {
        val pointer = data ?: return@useContents ""
        pointer.readBytes(length.toInt()).decodeToString()
    }

private fun errorText(error: CPointer<linguum_translation_error>?): String =
    if (error == null) "no native error" else viewText(linguum_translation_error_message(error))

private fun requireStatus(
    operation: String,
    status: UInt,
    error: CPointer<linguum_translation_error>?,
) {
    check(status == LINGUUM_TRANSLATION_STATUS_OK) {
        "$operation failed with status $status: ${errorText(error)}"
    }
}

private fun readUtf8File(path: String): String {
    val stream = fopen(path, "rb") ?: error("cannot open canary configuration")
    try {
        check(fseek(stream, 0, SEEK_END) == 0) { "cannot seek canary configuration" }
        val length = ftell(stream)
        check(length > 0) { "canary configuration is empty" }
        check(fseek(stream, 0, SEEK_SET) == 0) { "cannot rewind canary configuration" }
        val bytes = ByteArray(length.toInt())
        val read = bytes.usePinned { pinned ->
            fread(pinned.addressOf(0), 1u, bytes.size.convert(), stream)
        }
        check(read.toLong() == length) { "cannot read canary configuration" }
        return bytes.decodeToString()
    } finally {
        fclose(stream)
    }
}

private fun runTranslation(
    modelDirectory: String,
    configurationPath: String,
    input: String,
): String = memScoped {
    val runtimeConfig = alloc<linguum_translation_runtime_config>()
    memset(runtimeConfig.ptr, 0, sizeOf<linguum_translation_runtime_config>().convert())
    runtimeConfig.struct_size = sizeOf<linguum_translation_runtime_config>().convert()
    runtimeConfig.expected_abi_major = LINGUUM_TRANSLATION_ABI_MAJOR
    runtimeConfig.expected_abi_minor = LINGUUM_TRANSLATION_ABI_MINOR
    runtimeConfig.worker_count = 1u
    runtimeConfig.maximum_input_bytes = 1024uL * 1024uL

    val runtime = alloc<CPointerVar<linguum_translation_runtime>>()
    val model = alloc<CPointerVar<linguum_translation_model>>()
    val translator = alloc<CPointerVar<linguum_translation_translator>>()
    val result = alloc<CPointerVar<linguum_translation_result>>()
    val nativeError = alloc<CPointerVar<linguum_translation_error>>()
    runtime.value = null
    model.value = null
    translator.value = null
    result.value = null
    nativeError.value = null

    try {
        requireStatus(
            "runtime create",
            linguum_translation_runtime_create(runtimeConfig.ptr, runtime.ptr, nativeError.ptr),
            nativeError.value,
        )
        val vocabulary = alloc<linguum_translation_string_view>()
        assignStringView(vocabulary, "$modelDirectory/vocab.esen.spm")
        val descriptor = alloc<linguum_translation_model_descriptor>()
        memset(descriptor.ptr, 0, sizeOf<linguum_translation_model_descriptor>().convert())
        descriptor.struct_size = sizeOf<linguum_translation_model_descriptor>().convert()
        assignStringView(descriptor.language_pair, "es-en")
        assignStringView(descriptor.model_path, "$modelDirectory/model.esen.intgemm.alphas.bin")
        assignStringView(descriptor.shortlist_path, "$modelDirectory/lex.50.50.esen.s2t.bin")
        descriptor.vocabulary_paths = vocabulary.ptr
        descriptor.vocabulary_path_count = 1u
        assignStringView(descriptor.configuration_yaml, readUtf8File(configurationPath))
        requireStatus(
            "model load",
            linguum_translation_model_load(runtime.value, descriptor.ptr, model.ptr, nativeError.ptr),
            nativeError.value,
        )
        requireStatus(
            "translator create",
            linguum_translation_translator_create(
                runtime.value,
                model.value,
                translator.ptr,
                nativeError.ptr,
            ),
            nativeError.value,
        )
        val request = alloc<linguum_translation_request>()
        memset(request.ptr, 0, sizeOf<linguum_translation_request>().convert())
        request.struct_size = sizeOf<linguum_translation_request>().convert()
        assignStringView(request.input, input)
        request.input_format = LINGUUM_TRANSLATION_INPUT_PLAIN_TEXT
        requireStatus(
            "translation",
            linguum_translation_translator_translate(
                translator.value,
                request.ptr,
                result.ptr,
                nativeError.ptr,
            ),
            nativeError.value,
        )
        viewText(linguum_translation_result_text(result.value))
    } finally {
        linguum_translation_error_destroy(nativeError.value)
        linguum_translation_result_destroy(result.value)
        linguum_translation_translator_destroy(translator.value)
        linguum_translation_model_destroy(model.value)
        linguum_translation_runtime_destroy(runtime.value)
    }
}

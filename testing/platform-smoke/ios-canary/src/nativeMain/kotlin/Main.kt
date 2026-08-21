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
import platform.Foundation.NSBundle
import platform.posix.SEEK_END
import platform.posix.SEEK_SET
import platform.posix.fclose
import platform.posix.fflush
import platform.posix.fopen
import platform.posix.fputs
import platform.posix.fread
import platform.posix.fseek
import platform.posix.ftell
import platform.posix.memset
import platform.posix.stdout
import kotlin.system.exitProcess

private const val CANARY_INPUT = "¿Qué estás haciendo?"
private const val CANARY_EXPECTED = "What are you doing?"

private fun emitMarker(message: String) {
    check(fputs("$message\n", stdout) >= 0) { "cannot write iOS canary marker" }
    check(fflush(stdout) == 0) { "cannot flush iOS canary marker" }
}

private fun resolveResourcePath(value: String): String {
    val prefix = "@bundle/"
    if (!value.startsWith(prefix)) {
        return value
    }
    val resourcePath = NSBundle.mainBundle.resourcePath
        ?: error("installed canary bundle has no resource path")
    return "$resourcePath/${value.removePrefix(prefix)}"
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
    val stream = fopen(path, "rb") ?: error("cannot open fixed canary configuration")
    try {
        check(fseek(stream, 0, SEEK_END) == 0) { "cannot seek fixed canary configuration" }
        val length = ftell(stream)
        check(length > 0) { "fixed canary configuration is empty" }
        check(fseek(stream, 0, SEEK_SET) == 0) { "cannot rewind fixed canary configuration" }
        val bytes = ByteArray(length.toInt())
        val read = bytes.usePinned { pinned ->
            fread(pinned.addressOf(0), 1u, bytes.size.convert(), stream)
        }
        check(read.toLong() == length) { "cannot read fixed canary configuration" }
        return bytes.decodeToString()
    } finally {
        fclose(stream)
    }
}

private fun runIteration(modelDirectory: String, configuration: String) = memScoped {
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
        assignStringView(descriptor.configuration_yaml, configuration)
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
        assignStringView(request.input, CANARY_INPUT)
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
        check(viewText(linguum_translation_result_text(result.value)) == CANARY_EXPECTED) {
            "fixed canary output mismatch"
        }
    } finally {
        linguum_translation_error_destroy(nativeError.value)
        linguum_translation_result_destroy(result.value)
        linguum_translation_translator_destroy(translator.value)
        linguum_translation_model_destroy(model.value)
        linguum_translation_runtime_destroy(runtime.value)
    }
}

fun main(args: Array<String>) {
    if (args.size != 4) {
        emitMarker("LINGUUM_IOS_CANARY_FAIL reason=invalid-arguments")
        exitProcess(2)
    }
    val target = args[0]
    val modelDirectory = resolveResourcePath(args[1])
    val configuration = readUtf8File(resolveResourcePath(args[2]))
    val iterations = args[3].toIntOrNull()
    if (iterations == null || iterations !in 1..1000) {
        emitMarker("LINGUUM_IOS_CANARY_FAIL target=$target reason=invalid-iterations")
        exitProcess(2)
    }
    emitMarker("LINGUUM_IOS_CANARY_START target=$target iterations=$iterations")
    try {
        check(linguum_translation_abi_major() == LINGUUM_TRANSLATION_ABI_MAJOR)
        check(linguum_translation_abi_minor() == LINGUUM_TRANSLATION_ABI_MINOR)
        repeat(iterations) {
            runIteration(modelDirectory, configuration)
        }
    } catch (failure: Throwable) {
        emitMarker("LINGUUM_IOS_CANARY_FAIL target=$target reason=${failure.message ?: "unknown"}")
        exitProcess(1)
    }
    emitMarker("LINGUUM_IOS_CANARY_PASS target=$target iterations=$iterations abi=1.0")
}

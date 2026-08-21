# SPDX-License-Identifier: Apache-2.0
cmake_minimum_required(VERSION 4.0.2)
project(linguum_translation_native VERSION 0.0.0 LANGUAGES C CXX)

include(CTest)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

set(LINGUUM_TRANSLATIONS_SOURCE "" CACHE PATH "Staged Firefox-pinned translations source")
set(LINGUUM_TRANSLATIONS_REVISION "eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d" CACHE STRING "Pinned translations revision")
set(LINGUUM_FIREFOX_REVISION "48d55cf7ec80093903e2ef7f58b61a84a22ef716" CACHE STRING "Firefox source pin revision")
set(LINGUUM_LIBRARY_VERSION "0.0.0-SNAPSHOT" CACHE STRING "Linguum library version")
set(LINGUUM_ACCELERATION_PROFILE "host-unknown" CACHE STRING "Resolved native acceleration profile")
set(LINGUUM_CANARY_MODEL_DIR "" CACHE PATH "Directory containing the pinned es-en canary model")
set(LINGUUM_CANARY_ITERATIONS "100" CACHE STRING "Full canary lifecycle repetitions")
set(LINGUUM_INTGEMM_BASELINE_ONLY OFF CACHE BOOL "Exclude AVX-family intgemm kernels")
set(LINGUUM_INTGEMM_AVX2_ONLY OFF CACHE BOOL "Exclude intgemm kernels above AVX2")
set(LINGUUM_SANITIZERS "" CACHE STRING "Linux sanitizer set: address,undefined or thread")

if(UNIX AND NOT APPLE AND
   CMAKE_SYSTEM_PROCESSOR MATCHES "^(x86_64|amd64|AMD64)$")
  set(LINGUUM_LINUX_X64 ON)
else()
  set(LINGUUM_LINUX_X64 OFF)
endif()
if(LINGUUM_INTGEMM_BASELINE_ONLY AND NOT (MSVC OR LINGUUM_LINUX_X64))
  message(FATAL_ERROR "LINGUUM_INTGEMM_BASELINE_ONLY requires MSVC x64 or Linux x86_64")
endif()
if(LINGUUM_INTGEMM_AVX2_ONLY AND NOT (MSVC OR LINGUUM_LINUX_X64))
  message(FATAL_ERROR "LINGUUM_INTGEMM_AVX2_ONLY requires MSVC x64 or Linux x86_64")
endif()
if(LINGUUM_INTGEMM_BASELINE_ONLY AND LINGUUM_INTGEMM_AVX2_ONLY)
  message(FATAL_ERROR "intgemm baseline-only and AVX2-only modes are mutually exclusive")
endif()
if(LINGUUM_SANITIZERS)
  if(NOT UNIX OR APPLE)
    message(FATAL_ERROR "LINGUUM_SANITIZERS is proven only for Linux")
  endif()
  if(LINGUUM_SANITIZERS STREQUAL "address,undefined")
    set(LINGUUM_SANITIZER_FLAGS -fsanitize=address,undefined)
  elseif(LINGUUM_SANITIZERS STREQUAL "thread")
    set(LINGUUM_SANITIZER_FLAGS -fsanitize=thread)
  else()
    message(FATAL_ERROR "LINGUUM_SANITIZERS must be empty, address,undefined, or thread")
  endif()
  add_compile_options(${LINGUUM_SANITIZER_FLAGS} -fno-omit-frame-pointer -fno-sanitize-recover=all)
  add_link_options(${LINGUUM_SANITIZER_FLAGS} -fno-sanitize-recover=all)
endif()
if(MSVC AND LINGUUM_INTGEMM_BASELINE_ONLY)
  # The static MSVC STL contains runtime-dispatched AVX2 vector algorithms.
  # Keep that object out of the non-AVX candidate by disabling vectorized STL
  # call sites across every C++ target in this build tree. /O2 also enables
  # intrinsic substitution, so explicitly disable it before any upstream
  # targets are created; otherwise MSVC can synthesize AVX2 wmemchr code even
  # when /arch:SSE2 is selected.
  add_compile_definitions(
    _USE_STD_VECTOR_ALGORITHMS=0
    LINGUUM_MSVC_BASELINE=1
  )
  add_compile_options(/Oi-)
endif()

if(NOT IS_DIRECTORY "${LINGUUM_TRANSLATIONS_SOURCE}/inference")
  message(FATAL_ERROR "LINGUUM_TRANSLATIONS_SOURCE must name a staged translations checkout")
endif()
string(LENGTH "${LINGUUM_TRANSLATIONS_REVISION}" LINGUUM_TRANSLATIONS_REVISION_LENGTH)
if(NOT LINGUUM_TRANSLATIONS_REVISION_LENGTH EQUAL 40 OR
   NOT LINGUUM_TRANSLATIONS_REVISION MATCHES "^[0-9a-f]+$")
  message(FATAL_ERROR "LINGUUM_TRANSLATIONS_REVISION must be an exact 40-character Git revision")
endif()
string(LENGTH "${LINGUUM_FIREFOX_REVISION}" LINGUUM_FIREFOX_REVISION_LENGTH)
if(NOT LINGUUM_FIREFOX_REVISION_LENGTH EQUAL 40 OR
   NOT LINGUUM_FIREFOX_REVISION MATCHES "^[0-9a-f]+$")
  message(FATAL_ERROR "LINGUUM_FIREFOX_REVISION must be an exact 40-character Git revision")
endif()

set(PROJECT_VERSION_GIT_SHA "${LINGUUM_TRANSLATIONS_REVISION}" CACHE STRING "Pinned source identity" FORCE)
set(CMAKE_POLICY_VERSION_MINIMUM 3.5 CACHE STRING "Compatibility floor for pinned upstream CMake" FORCE)
set(USE_WASM_COMPATIBLE_SOURCE OFF CACHE BOOL "Use native Mozilla inference source" FORCE)
set(SSPLIT_USE_INTERNAL_PCRE2 ON CACHE BOOL "Build pinned PCRE2 source" FORCE)
set(USE_MKL OFF CACHE BOOL "Disable MKL" FORCE)
set(COMPILE_CUDA OFF CACHE BOOL "Disable CUDA" FORCE)
set(COMPILE_TESTS OFF CACHE BOOL "Disable upstream integration tests" FORCE)
set(COMPILE_UNIT_TESTS OFF CACHE BOOL "Disable upstream unit tests" FORCE)
set(COMPILE_PYTHON OFF CACHE BOOL "Disable upstream Python binding" FORCE)
set(USE_DOXYGEN OFF CACHE BOOL "Disable host-dependent upstream documentation" FORCE)
set(GIT_SUBMODULE OFF CACHE BOOL "Never mutate flattened source submodules" FORCE)

if(CMAKE_OSX_ARCHITECTURES MATCHES "(^|;)arm64(;|$)" OR
   CMAKE_SYSTEM_PROCESSOR MATCHES "^(aarch64|arm64|ARM64)$")
  set(LINGUUM_ARM_NATIVE ON)
else()
  set(LINGUUM_ARM_NATIVE OFF)
endif()

add_subdirectory("${LINGUUM_TRANSLATIONS_SOURCE}/inference" upstream SYSTEM)

if(MSVC AND LINGUUM_INTGEMM_BASELINE_ONLY)
  # The staged source's baseline-only helper performs its UTF-16 code-unit
  # search with a scalar loop. Keep that source outside LTCG so the standard
  # library search cannot be regenerated during link-time optimization.
  set_source_files_properties(
    "${LINGUUM_TRANSLATIONS_SOURCE}/inference/marian-fork/src/data/factored_vocab.cpp"
    TARGET_DIRECTORY marian
    PROPERTIES COMPILE_OPTIONS "/Oi-;/GL-"
  )
  # Locked MSVC emitted one VEX-encoded store while optimizing the inline
  # Dense graph-construction function in this translation unit. This is not a
  # tensor compute kernel, so keep only this proven source unoptimized and
  # outside LTCG for the zero-AVX candidate.
  set_source_files_properties(
    "${LINGUUM_TRANSLATIONS_SOURCE}/inference/marian-fork/src/graph/expression_operators.cpp"
    TARGET_DIRECTORY marian
    PROPERTIES COMPILE_OPTIONS "/Od;/Oi-;/GL-"
  )
endif()

if(LINGUUM_ARM_NATIVE)
  # Pinned Marian sets these on its own target. Its sibling Bergamot target
  # also includes Marian's ARM SIMD headers, but unrelated dependencies such
  # as Eigen must not inherit the SSE preprocessor macro.
  target_compile_definitions(bergamot-translator-source PRIVATE ARM FMA SSE)
  if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    # GCC keeps its generic vector typedefs distinct from the SSE-to-NEON
    # intrinsic typedefs. The pinned SIMD layer intentionally interchanges
    # those ABI-equivalent 128-bit vectors on ARM, so scope GCC's documented
    # compatibility mode to the three targets that include that layer.
    target_compile_options(marian PRIVATE -flax-vector-conversions)
    target_compile_options(bergamot-translator-source PRIVATE -flax-vector-conversions)
  endif()
endif()

add_library(linguum_translation SHARED
  ../mozilla-adapter/src/linguum_translation.cpp
)
if(MSVC AND LINGUUM_INTGEMM_BASELINE_ONLY)
  # Keep the VC runtime static while resolving UCRT math/string functions
  # through the Windows 10+ system UCRT. The small scalar object supplies the
  # memory and STL ABI entry points that otherwise pull AVX-dispatched static
  # VC/STL archive members into this DLL.
  add_library(linguum_baseline_runtime_shims OBJECT
    baseline_runtime_shims.c
  )
  target_compile_options(linguum_baseline_runtime_shims PRIVATE
    /Od /Oi- /GL- /W4 /WX
  )
  target_sources(linguum_translation PRIVATE
    $<TARGET_OBJECTS:linguum_baseline_runtime_shims>
  )
endif()
if(LINGUUM_ARM_NATIVE)
  target_compile_definitions(linguum_translation PRIVATE ARM FMA SSE)
  if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    target_compile_options(linguum_translation PRIVATE -flax-vector-conversions)
  endif()
endif()
target_compile_definitions(linguum_translation PRIVATE
  LINGUUM_TRANSLATION_BUILD
  LINGUUM_LIBRARY_VERSION="${LINGUUM_LIBRARY_VERSION}"
  LINGUUM_FIREFOX_REVISION="${LINGUUM_FIREFOX_REVISION}"
  LINGUUM_BERGAMOT_VERSION="v0.6.0"
  LINGUUM_ACCELERATION_PROFILE="${LINGUUM_ACCELERATION_PROFILE}"
)
target_compile_options(linguum_translation PRIVATE
  $<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-Wall;-Wextra;-Wpedantic;-Werror>
  $<$<CXX_COMPILER_ID:MSVC>:/W4;/WX>
)
if(MSVC AND LINGUUM_INTGEMM_BASELINE_ONLY)
  # Keep address-to-symbol and archive-member provenance available to the
  # complete-DLL ISA audit. The map is build evidence and is not packaged.
  target_link_options(linguum_translation PRIVATE
    "/MAP:${CMAKE_CURRENT_BINARY_DIR}/linguum_translation.map"
    /MAPINFO:EXPORTS
    /NODEFAULTLIB:libucrt.lib
    /NODEFAULTLIB:msvcrt.lib
  )
endif()
target_include_directories(linguum_translation
  PUBLIC ../abi/include
)
target_include_directories(linguum_translation SYSTEM PRIVATE
  "${LINGUUM_TRANSLATIONS_SOURCE}/inference/src"
)
target_link_libraries(linguum_translation PRIVATE bergamot-translator-source)
if(MSVC AND LINGUUM_INTGEMM_BASELINE_ONLY)
  target_link_libraries(linguum_translation PRIVATE ucrt)
endif()
set_target_properties(linguum_translation PROPERTIES
  C_VISIBILITY_PRESET hidden
  CXX_VISIBILITY_PRESET hidden
  VISIBILITY_INLINES_HIDDEN YES
  OUTPUT_NAME linguum_translation
)

if(APPLE)
  target_link_options(linguum_translation PRIVATE
    "LINKER:-exported_symbols_list,${CMAKE_CURRENT_SOURCE_DIR}/exports/macos.exports"
  )
elseif(UNIX)
  target_link_options(linguum_translation PRIVATE
    "LINKER:--version-script=${CMAKE_CURRENT_SOURCE_DIR}/exports/linux.map"
  )
endif()

if(BUILD_TESTING)
  if(MSVC AND LINGUUM_INTGEMM_BASELINE_ONLY)
    add_executable(linguum_baseline_runtime_shims_test
      ../../testing/native/baseline_runtime_shims_test.c
      $<TARGET_OBJECTS:linguum_baseline_runtime_shims>
    )
    target_compile_options(linguum_baseline_runtime_shims_test PRIVATE /W4 /WX)
    add_test(NAME baseline-runtime-shims COMMAND linguum_baseline_runtime_shims_test)
  endif()

  add_executable(linguum_translation_abi_header_c ../../testing/native/abi_header_c.c)
  target_link_libraries(linguum_translation_abi_header_c PRIVATE linguum_translation)
  target_compile_options(linguum_translation_abi_header_c PRIVATE
    $<$<C_COMPILER_ID:AppleClang,Clang,GNU>:-Wall;-Wextra;-Wpedantic;-Werror>
    $<$<C_COMPILER_ID:MSVC>:/W4;/WX>
  )
  add_test(NAME abi-header-c COMMAND linguum_translation_abi_header_c)

  add_executable(linguum_translation_abi_header_cpp ../../testing/native/abi_header_cpp.cpp)
  target_link_libraries(linguum_translation_abi_header_cpp PRIVATE linguum_translation)
  target_compile_options(linguum_translation_abi_header_cpp PRIVATE
    $<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-Wall;-Wextra;-Wpedantic;-Werror>
    $<$<CXX_COMPILER_ID:MSVC>:/W4;/WX>
  )
  add_test(NAME abi-header-cpp COMMAND linguum_translation_abi_header_cpp)

  if(LINGUUM_CANARY_MODEL_DIR)
    add_executable(linguum_translation_canary ../../testing/native/canary.c)
    target_link_libraries(linguum_translation_canary PRIVATE linguum_translation)
    target_compile_options(linguum_translation_canary PRIVATE
      $<$<C_COMPILER_ID:AppleClang,Clang,GNU>:-Wall;-Wextra;-Wpedantic;-Werror>
      $<$<C_COMPILER_ID:MSVC>:/W4;/WX>
    )
    add_test(
      NAME es-en-canary
      COMMAND linguum_translation_canary
        "${LINGUUM_CANARY_MODEL_DIR}"
        "${CMAKE_CURRENT_SOURCE_DIR}/../../testing/native/fixtures/es-en.yml"
        "${LINGUUM_CANARY_ITERATIONS}"
    )
    set_tests_properties(es-en-canary PROPERTIES TIMEOUT 300)
  endif()
endif()

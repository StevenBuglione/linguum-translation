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

set(LINGUUM_TRANSLATIONS_SOURCE "" CACHE PATH "Staged Firefox-pinned translations source")
set(LINGUUM_TRANSLATIONS_REVISION "eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d" CACHE STRING "Pinned translations revision")
set(LINGUUM_FIREFOX_REVISION "48d55cf7ec80093903e2ef7f58b61a84a22ef716" CACHE STRING "Firefox source pin revision")
set(LINGUUM_LIBRARY_VERSION "0.0.0-SNAPSHOT" CACHE STRING "Linguum library version")
set(LINGUUM_ACCELERATION_PROFILE "host-unknown" CACHE STRING "Resolved native acceleration profile")
set(LINGUUM_CANARY_MODEL_DIR "" CACHE PATH "Directory containing the pinned es-en canary model")
set(LINGUUM_CANARY_ITERATIONS "100" CACHE STRING "Full canary lifecycle repetitions")

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
set(GIT_SUBMODULE OFF CACHE BOOL "Never mutate flattened source submodules" FORCE)

if(CMAKE_OSX_ARCHITECTURES MATCHES "(^|;)arm64(;|$)" OR
   CMAKE_SYSTEM_PROCESSOR MATCHES "^(aarch64|arm64|ARM64)$")
  # Pinned Marian applies these only inside its own directory, while the
  # sibling Bergamot target includes Marian's ARM SIMD headers as well.
  add_compile_definitions(ARM FMA SSE)
endif()

add_subdirectory("${LINGUUM_TRANSLATIONS_SOURCE}/inference" upstream)

add_library(linguum_translation SHARED
  ../mozilla-adapter/src/linguum_translation.cpp
)
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
target_include_directories(linguum_translation
  PUBLIC ../abi/include
  PRIVATE "${LINGUUM_TRANSLATIONS_SOURCE}/inference/src"
)
target_link_libraries(linguum_translation PRIVATE bergamot-translator-source)
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

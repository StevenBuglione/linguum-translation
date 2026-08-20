#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Offline contract tests for the M1 Windows profile proof."""

import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]


def load_script(name: str):
    path = ROOT / "scripts" / "native" / "{}.py".format(name)
    spec = importlib.util.spec_from_file_location("linguum_test_{}".format(name), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


windows_profiles = load_script("windows_profiles")
run_host_canary = load_script("run_host_canary")


class WindowsProfileLockTests(unittest.TestCase):
    def test_profile_lock_is_exact_and_baseline_excludes_high_kernels(self):
        document = windows_profiles.load_lock()
        profiles = windows_profiles.profile_map(document)
        self.assertEqual(
            ["18.8.12023.21", "18.9.12112.369"],
            document["toolchain"]["visualStudioVersions"],
        )
        self.assertEqual("14.44.35207", document["toolchain"]["msvcToolset"])
        self.assertEqual("19.44.35228", document["toolchain"]["compiler"])
        self.assertEqual(set(windows_profiles.PROFILE_IDS), set(profiles))
        self.assertEqual(["AVX2"], profiles["windows-x64-avx2"]["requiredCpuFeatures"])
        self.assertEqual("AVX2", profiles["windows-x64-avx2"]["intgemmMaximumCpu"])
        baseline = profiles["windows-x64-baseline"]
        self.assertFalse(baseline["fbgemm"])
        self.assertTrue(baseline["intgemmBaselineOnly"])
        self.assertEqual("SSSE3", baseline["intgemmMaximumCpu"])
        self.assertEqual(["SSSE3"], baseline["requiredCpuFeatures"])
        self.assertIn("AVX2", baseline["prohibitedInstructionFamilies"])

    def test_windows_cmake_profiles_are_not_host_ambiguous(self):
        with mock.patch.object(run_host_canary.platform, "system", return_value="Windows"), \
             mock.patch.object(run_host_canary.platform, "machine", return_value="AMD64"):
            build_arch, acceleration, arguments = run_host_canary.host_profile(
                "windows-x64-avx2"
            )
            self.assertEqual("native", build_arch)
            self.assertEqual("fbgemm-intgemm-avx2", acceleration)
            self.assertIn("-DUSE_FBGEMM=ON", arguments)
            self.assertIn("-DLINGUUM_INTGEMM_BASELINE_ONLY=OFF", arguments)
            self.assertIn("-DLINGUUM_INTGEMM_AVX2_ONLY=ON", arguments)

            build_arch, acceleration, arguments = run_host_canary.host_profile(
                "windows-x64-baseline"
            )
            self.assertEqual("core2", build_arch)
            self.assertIn("baseline", acceleration)
            self.assertIn("-DUSE_FBGEMM=OFF", arguments)
            self.assertIn("-DUSE_ONNX_SGEMM=ON", arguments)
            self.assertIn("-DLINGUUM_INTGEMM_BASELINE_ONLY=ON", arguments)
            self.assertIn("-DLINGUUM_INTGEMM_AVX2_ONLY=OFF", arguments)

    def test_configure_emits_compiler_commands_for_evidence(self):
        with mock.patch.object(run_host_canary.platform, "system", return_value="Windows"), \
             mock.patch.object(run_host_canary.platform, "machine", return_value="AMD64"):
            arguments, _ = run_host_canary.configure_arguments(
                Path("cmake.exe"),
                Path("ninja.exe"),
                ROOT / "build" / "source",
                ROOT / "build" / "model",
                ROOT / "build" / "native-canary" / "test",
                100,
                "windows-x64-baseline",
            )
        self.assertIn("-DCMAKE_EXPORT_COMPILE_COMMANDS=ON", arguments)

    def test_baseline_build_executes_the_scalar_runtime_test_target(self):
        common_targets = run_host_canary.build_targets("host")
        baseline_targets = run_host_canary.build_targets("windows-x64-baseline")
        self.assertNotIn("linguum_baseline_runtime_shims_test", common_targets)
        self.assertEqual(
            common_targets + ["linguum_baseline_runtime_shims_test"],
            baseline_targets,
        )

    def test_external_patch_caps_intgemm_kernels_for_locked_profiles(self):
        patch = (
            ROOT / "native" / "patches" / "0001-reproducible-flattened-source-build.patch"
        ).read_text(encoding="utf-8")
        self.assertIn("intgemm/CMakeLists.txt", patch)
        self.assertIn("if(LINGUUM_INTGEMM_BASELINE_ONLY)", patch)
        self.assertIn("elseif(LINGUUM_INTGEMM_AVX2_ONLY)", patch)
        for name in (
            "INTGEMM_COMPILER_SUPPORTS_AVX2",
            "INTGEMM_COMPILER_SUPPORTS_AVX512BW",
            "INTGEMM_COMPILER_SUPPORTS_AVX512VNNI",
        ):
            self.assertIn("set({} FALSE)".format(name), patch)
        self.assertIn("else()", patch)
        self.assertIn("try_compile(INTGEMM_COMPILER_SUPPORTS_AVX2", patch)
        self.assertIn("LINGUUM_INTGEMM_MAX_AVX2", patch)
        self.assertIn("!defined(LINGUUM_INTGEMM_MAX_AVX2)", patch)
        self.assertIn("using Integer = int8_t", patch)
        self.assertIn("using Integer = int16_t", patch)
        self.assertIn("(void)ebx", patch)

    def test_external_patch_allows_onnx_sgemm_in_native_profiles(self):
        patch = (
            ROOT / "native" / "patches" / "0001-reproducible-flattened-source-build.patch"
        ).read_text(encoding="utf-8")
        self.assertIn("option(USE_ONNX_SGEMM", patch)
        self.assertIn("BLAS_FOUND || USE_ONNX_SGEMM || USE_RUY_SGEMM", patch)
        self.assertIn("remove_definitions(-DSSE)", patch)
        self.assertIn("set(BUILD_TESTING OFF)", patch)

    def test_runtime_build_disables_vectorized_msvc_stl_only_for_baseline(self):
        cmake = (ROOT / "native" / "runtime-build" / "CMakeLists.txt").read_text(
            encoding="utf-8"
        )
        self.assertIn("if(MSVC AND LINGUUM_INTGEMM_BASELINE_ONLY)", cmake)
        self.assertIn("_USE_STD_VECTOR_ALGORITHMS=0", cmake)
        self.assertIn("LINGUUM_MSVC_BASELINE=1", cmake)
        self.assertIn("add_compile_options(/Oi-)", cmake)
        self.assertIn("TARGET_DIRECTORY marian", cmake)
        self.assertIn('PROPERTIES COMPILE_OPTIONS "/Oi-;/GL-"', cmake)
        self.assertIn("baseline_runtime_shims.c", cmake)
        self.assertIn("/Od /Oi- /GL- /W4 /WX", cmake)
        self.assertIn("/NODEFAULTLIB:libucrt.lib", cmake)
        self.assertIn("/NODEFAULTLIB:msvcrt.lib", cmake)
        self.assertIn("target_link_libraries(linguum_translation PRIVATE ucrt)", cmake)
        self.assertIn(
            '"/MAP:${CMAKE_CURRENT_BINARY_DIR}/linguum_translation.map"',
            cmake,
        )
        self.assertIn("/MAPINFO:EXPORTS", cmake)
        self.assertNotIn("/VERBOSE:LIB", cmake)

    def test_baseline_scalar_shims_cover_the_provenance_boundary(self):
        shims = (
            ROOT / "native" / "runtime-build" / "baseline_runtime_shims.c"
        ).read_text(encoding="utf-8")
        test = (
            ROOT / "testing" / "native" / "baseline_runtime_shims_test.c"
        ).read_text(encoding="utf-8")
        for name in windows_profiles.BASELINE_SCALAR_SHIM_SYMBOLS:
            self.assertIn(name, shims)
            self.assertIn(name, test)
        self.assertIn("__declspec(noinline)", shims)
        self.assertIn("baseline-runtime-shims", (
            ROOT / "native" / "runtime-build" / "CMakeLists.txt"
        ).read_text(encoding="utf-8"))

    def test_external_patch_provides_baseline_scalar_utf16_search(self):
        patch = (
            ROOT / "native" / "patches" / "0001-reproducible-flattened-source-build.patch"
        ).read_text(encoding="utf-8")
        self.assertIn("defined(LINGUUM_MSVC_BASELINE)", patch)
        self.assertIn("findUtf16CodeUnit", patch)
        self.assertIn("for (size_t index = offset; index < value.size(); ++index)", patch)
        self.assertIn("return value.find(needle, offset)", patch)
        self.assertNotIn("#pragma function(wmemchr)", patch)

    def test_profile_failures_do_not_mask_the_other_locked_profile(self):
        profiles = windows_profiles.profile_map(windows_profiles.load_lock())
        baseline_result = {"profile": "windows-x64-baseline"}
        baseline_package = {"profile": "windows-x64-baseline", "jar": "baseline.jar"}
        with mock.patch.object(
            windows_profiles.run_host_canary,
            "execute",
            side_effect=[
                windows_profiles.run_host_canary.HostCanaryError("optimized failed"),
                baseline_result,
            ],
        ) as execute_canary, mock.patch.object(
            windows_profiles,
            "package_profile",
            return_value=baseline_package,
        ) as package_profile:
            with self.assertRaisesRegex(
                windows_profiles.WindowsProfileError,
                "windows-x64-avx2: optimized failed",
            ):
                windows_profiles.execute_profile_set(
                    profiles,
                    windows_profiles.load_lock()["toolchain"],
                    ROOT / "build" / "windows-profile-test",
                    100,
                    True,
                )
        self.assertEqual(2, execute_canary.call_count)
        package_profile.assert_called_once_with(
            baseline_result,
            profiles["windows-x64-baseline"],
            windows_profiles.load_lock()["toolchain"],
            ROOT / "build" / "windows-profile-test",
        )

    def test_external_patch_selects_the_msvc_static_pcre2_filename(self):
        patch = (
            ROOT / "native" / "patches" / "0001-reproducible-flattened-source-build.patch"
        ).read_text(encoding="utf-8")
        self.assertIn("set(PCRE2_STATIC_LIBRARY_NAME pcre2-8-static)", patch)
        self.assertIn("set(PCRE2_STATIC_LIBRARY_NAME pcre2-8)", patch)
        self.assertIn("${PCRE2_STATIC_LIBRARY_NAME}${CMAKE_STATIC_LIBRARY_SUFFIX}", patch)
        self.assertIn("target_compile_definitions(ssplit PRIVATE PCRE2_STATIC)", patch)

    def test_runtime_build_disables_host_dependent_documentation(self):
        cmake = (ROOT / "native" / "runtime-build" / "CMakeLists.txt").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            'set(USE_DOXYGEN OFF CACHE BOOL "Disable host-dependent upstream documentation" FORCE)',
            cmake,
        )

    def test_runtime_build_keeps_upstream_header_warnings_outside_first_party_werror(self):
        cmake = (ROOT / "native" / "runtime-build" / "CMakeLists.txt").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            'add_subdirectory("${LINGUUM_TRANSLATIONS_SOURCE}/inference" upstream SYSTEM)',
            cmake,
        )
        self.assertIn(
            "target_include_directories(linguum_translation SYSTEM PRIVATE",
            cmake,
        )
        self.assertIn('$<$<CXX_COMPILER_ID:MSVC>:/W4;/WX>', cmake)

    def test_runtime_build_scopes_arm_simd_definitions_away_from_eigen(self):
        cmake = (ROOT / "native" / "runtime-build" / "CMakeLists.txt").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "target_compile_definitions(bergamot-translator-source PRIVATE ARM FMA SSE)",
            cmake,
        )
        self.assertIn(
            "target_compile_definitions(linguum_translation PRIVATE ARM FMA SSE)",
            cmake,
        )
        self.assertNotIn("add_compile_definitions(ARM FMA SSE)", cmake)

    def test_windows_canary_traces_the_first_lifecycle_failure_boundary(self):
        canary = (ROOT / "testing" / "native" / "canary.c").read_text(encoding="utf-8")
        self.assertIn("trace_first_windows_iteration", canary)
        self.assertIn('trace_first_windows_iteration(trace, "model-load")', canary)
        self.assertIn('trace_first_windows_iteration(trace, "translation")', canary)
        self.assertIn('trace_first_windows_iteration(trace, "cleanup-runtime")', canary)
        self.assertIn("iteration == 0L", canary)


class EvidenceParsingTests(unittest.TestCase):
    def test_environment_parser_ignores_cmd_pseudo_variables(self):
        output = "Path=C:\\Tools\r\n=ExitCode=00000000\r\nWindowsSDKVersion=10.0.26100.0\\\r\n"
        self.assertEqual(
            {"Path": "C:\\Tools", "WindowsSDKVersion": "10.0.26100.0\\"},
            windows_profiles.parse_environment(output),
        )

    def test_environment_lookup_is_case_insensitive_and_reports_related_names(self):
        environment = {
            "VCTOOLSVERSION": "14.44.35211\\",
            "WindowsSdkVersion": "10.0.26100.0\\",
        }
        self.assertEqual(
            "14.44.35211\\",
            windows_profiles.environment_value(environment, "VCToolsVersion"),
        )
        self.assertEqual(
            "10.0.26100.0\\",
            windows_profiles.environment_value(environment, "WindowsSDKVersion"),
        )
        with self.assertRaisesRegex(
            windows_profiles.WindowsProfileError,
            "related variables:.*VCTOOLSVERSION",
        ):
            windows_profiles.environment_value(environment, "VSCMD_ARG_TGT_ARCH")

    def test_compiler_version_parses_the_x64_banner_and_rejects_unknown_output(self):
        banner = "Microsoft (R) C/C++ Optimizing Compiler Version 19.44.35221 for x64"
        self.assertEqual("19.44.35221", windows_profiles.compiler_version(banner))
        with self.assertRaisesRegex(
            windows_profiles.WindowsProfileError, "unrecognized MSVC compiler banner"
        ):
            windows_profiles.compiler_version("unexpected compiler output")

    def test_vswhere_selects_the_locked_visual_studio_major(self):
        arguments = windows_profiles.vswhere_arguments({"visualStudio": "2026"})
        self.assertIn("[18.0,19.0)", arguments)
        self.assertNotIn("-latest", arguments)
        with self.assertRaises(windows_profiles.WindowsProfileError):
            windows_profiles.vswhere_arguments({"visualStudio": "future"})

    def test_vcvars_activation_uses_a_batch_script_not_inline_cmd_quoting(self):
        script = windows_profiles.vcvars_script(
            Path(
                "C:/Program Files/Microsoft Visual Studio/18/Enterprise/"
                "VC/Auxiliary/Build/vcvars64.bat"
            ),
            {"windowsSdk": "10.0.26100.0", "msvcToolset": "14.44.35207"},
        )
        self.assertIn('@call "C:', script)
        self.assertIn(" 10.0.26100.0 -vcvars_ver=14.44.35207", script)
        self.assertNotIn("-winsdk=", script)
        self.assertIn("LINGUUM_VCVARS_FAILED exit=", script)
        self.assertIn("LINGUUM_VCVARS_MISSING_VCTOOLSVERSION", script)
        self.assertIn("VC/Tools/MSVC", script.replace("\\", "/"))
        self.assertIn("LINGUUM_VCVARS_MISSING_WINDOWSSDKVERSION", script)
        self.assertIn("@set\r\n@exit /b 0", script)

    def test_baseline_disassembly_rejects_any_avx_family_instruction(self):
        safe = "  0000000180001000: mov rax,qword ptr [rcx]\n"
        result = windows_profiles.verify_isa("windows-x64-baseline", safe)
        self.assertTrue(result["baselineAvxFamilyAbsent"])

        unsafe = safe + "runtime_dispatch:\n  0000000180001004: vzeroupper\n"
        with self.assertRaisesRegex(
            windows_profiles.WindowsProfileError,
            r"1 AVX-family instructions; provenance: unavailable; "
            r"first records: runtime_dispatch -> .*vzeroupper",
        ):
            windows_profiles.verify_isa("windows-x64-baseline", unsafe)

    def test_linker_map_attributes_avx_to_the_defining_archive_object(self):
        linker_map = """
 Address         Publics by Value              Rva+Base       Lib:Object
 0001:00001000       __std_find_trivial_2      0000000180001000 f   libcpmt:vector_algorithms.obj
 entry point at        0001:00000000
 Static symbols
 0001:00002000       local_helper              0000000180002000 f i adapter.obj
"""
        symbols = windows_profiles.parse_linker_map(linker_map)
        self.assertEqual(2, len(symbols))
        self.assertEqual(
            "__std_find_trivial_2 [libcpmt:vector_algorithms.obj] +0x5b",
            windows_profiles.linker_symbol_at(0x18000105B, symbols),
        )
        unsafe = (
            "  000000018000105B: vpbroadcastw ymm0,xmm0\n"
            "  0000000180002050: vzeroupper\n"
        )
        provenance = windows_profiles.avx_provenance(
            windows_profiles.avx_records(windows_profiles.instruction_records(unsafe)),
            symbols,
        )
        self.assertEqual(2, provenance["mappedInstructionCount"])
        self.assertEqual(2, provenance["sourceCount"])
        self.assertEqual(0, provenance["unmappedInstructionCount"])
        self.assertEqual(
            {"instructionCount": 1, "source": "adapter.obj"},
            provenance["sources"][0],
        )
        with self.assertRaisesRegex(
            windows_profiles.WindowsProfileError,
            r"provenance: .*__std_find_trivial_2.*"
            r"__std_find_trivial_2 \[libcpmt:vector_algorithms.obj\] \+0x5b",
        ):
            windows_profiles.verify_isa("windows-x64-baseline", unsafe, symbols)

        with self.assertRaisesRegex(
            windows_profiles.WindowsProfileError,
            "contains no function symbols",
        ):
            windows_profiles.parse_linker_map("no symbol table here")

    def test_optimized_disassembly_requires_avx2_evidence(self):
        avx1_only = "  0000000180001000: vaddps xmm0,xmm1,xmm2\n"
        with self.assertRaises(windows_profiles.WindowsProfileError):
            windows_profiles.verify_isa("windows-x64-avx2", avx1_only)

        avx2 = avx1_only + "  0000000180001004: vpaddd ymm0,ymm1,ymm2\n"
        result = windows_profiles.verify_isa("windows-x64-avx2", avx2)
        self.assertEqual(1, len(result["avx2Evidence"]))

    def test_dependency_parser_allows_only_system_dlls(self):
        output = (
            "    api-ms-win-crt-runtime-l1-1-0.dll\n"
            "    DBGHELP.dll\n    KERNEL32.dll\n    SHLWAPI.dll\n"
        )
        self.assertEqual(
            [
                "API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL",
                "DBGHELP.DLL",
                "KERNEL32.DLL",
                "SHLWAPI.DLL",
            ],
            windows_profiles.parse_dependencies(output),
        )
        with self.assertRaises(windows_profiles.WindowsProfileError):
            windows_profiles.parse_dependencies(output + "    accidental.dll\n")

    def test_baseline_runtime_boundary_requires_all_shims_and_no_vector_archive(self):
        symbols = [
            (0x180001000 + index, name, "runtime:baseline_runtime_shims.c.obj")
            for index, name in enumerate(sorted(windows_profiles.BASELINE_SCALAR_SHIM_SYMBOLS))
        ]
        evidence = windows_profiles.baseline_runtime_boundary_evidence(symbols)
        self.assertEqual(6, evidence["scalarShimCount"])
        self.assertTrue(evidence["staticStlVectorAlgorithmsAbsent"])
        with self.assertRaisesRegex(
            windows_profiles.WindowsProfileError, "missing symbols",
        ):
            windows_profiles.baseline_runtime_boundary_evidence(symbols[:-1])
        with self.assertRaisesRegex(
            windows_profiles.WindowsProfileError, "vector-algorithm object",
        ):
            windows_profiles.baseline_runtime_boundary_evidence(symbols + [
                (0x180002000, "__std_find_trivial_4", "libcpmt:vector_algorithms.obj")
            ])

    def test_compile_command_profile_flags_are_enforced(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            commands = root / "compile_commands.json"
            commands.write_text(json.dumps([
                {
                    "command": "cl /arch:SSE2 /Oi- /D_USE_STD_VECTOR_ALGORITHMS=0 /c intgemm.cc",
                    "file": "C:/source/3rd_party/intgemm/intgemm/intgemm.cc",
                },
                {
                    "command": "cl /arch:SSE2 /Oi- /GL- /DLINGUUM_MSVC_BASELINE=1 /D_USE_STD_VECTOR_ALGORITHMS=0 /c factored_vocab.cpp",
                    "file": "C:/source/marian-fork/src/data/factored_vocab.cpp",
                },
                {
                    "command": "cl /arch:SSE2 /Oi- /D_USE_STD_VECTOR_ALGORITHMS=0 /DUSE_ONNX_SGEMM=1 /c prod.cpp",
                    "file": "C:/source/marian-fork/src/tensors/cpu/prod.cpp",
                },
                {
                    "command": "cl /arch:SSE2 /Oi- /D_USE_STD_VECTOR_ALGORITHMS=0 /c gemm.cpp",
                    "file": "C:/source/onnxjs/src/wasm-ops/gemm.cpp",
                },
            ]))
            evidence = windows_profiles.verify_compile_commands("windows-x64-baseline", root)
            self.assertTrue(evidence["hasArchSse2"])
            self.assertFalse(evidence["hasArchAvx2"])
            self.assertFalse(evidence["hasIntgemmAvx2Cap"])
            self.assertTrue(evidence["hasOnnxSgemm"])
            self.assertTrue(evidence["hasOnnxSgemmImplementation"])
            self.assertEqual(4, evidence["cppCompileCommandCount"])
            self.assertEqual(4, evidence["vectorizedStlDisabledCommandCount"])
            self.assertTrue(evidence["vectorizedStlDisabledForAllCpp"])
            self.assertEqual(4, evidence["compilerIntrinsicsDisabledCommandCount"])
            self.assertTrue(evidence["compilerIntrinsicsDisabledForAllCommands"])
            self.assertTrue(evidence["factoredVocabularyScalarSearchBoundary"])

            missing_scalar_search_boundary = json.loads(commands.read_text())
            missing_scalar_search_boundary[1]["command"] = (
                missing_scalar_search_boundary[1]["command"].replace(
                    " /DLINGUUM_MSVC_BASELINE=1", ""
                )
            )
            commands.write_text(json.dumps(missing_scalar_search_boundary))
            with self.assertRaisesRegex(
                windows_profiles.WindowsProfileError,
                "must enable the scalar search boundary",
            ):
                windows_profiles.verify_compile_commands("windows-x64-baseline", root)

            commands.write_text(json.dumps([
                {
                    "command": "cl /arch:SSE2 /Oi- /D_USE_STD_VECTOR_ALGORITHMS=0 /c intgemm.cc",
                    "file": "C:/source/3rd_party/intgemm/intgemm/intgemm.cc",
                },
                {
                    "command": "cl /arch:SSE2 /Oi- /GL- -DLINGUUM_MSVC_BASELINE=1 /D_USE_STD_VECTOR_ALGORITHMS=0 /c factored_vocab.cpp",
                    "file": "C:/source/marian-fork/src/data/factored_vocab.cpp",
                },
                {
                    "command": "cl /arch:SSE2 /Oi- /D_USE_STD_VECTOR_ALGORITHMS=0 /DUSE_ONNX_SGEMM=1 /c prod.cpp",
                    "file": "C:/source/marian-fork/src/tensors/cpu/prod.cpp",
                },
                {
                    "command": "cl /arch:SSE2 /Oi- /D_USE_STD_VECTOR_ALGORITHMS=0 /c gemm.cpp",
                    "file": "C:/source/onnxjs/src/wasm-ops/gemm.cpp",
                },
            ]))
            evidence = windows_profiles.verify_compile_commands("windows-x64-baseline", root)
            self.assertTrue(evidence["factoredVocabularyScalarSearchBoundary"])

            missing_intrinsic_boundary = json.loads(commands.read_text())
            missing_intrinsic_boundary[0]["command"] = missing_intrinsic_boundary[0][
                "command"
            ].replace(" /Oi-", "")
            commands.write_text(json.dumps(missing_intrinsic_boundary))
            with self.assertRaisesRegex(
                windows_profiles.WindowsProfileError,
                "every baseline compiler command must disable intrinsic",
            ):
                windows_profiles.verify_compile_commands("windows-x64-baseline", root)

            commands.write_text(json.dumps([
                {
                    "command": "cl /arch:SSE2 /Oi- /D_USE_STD_VECTOR_ALGORITHMS=0 /c intgemm.cc",
                    "file": "C:/source/3rd_party/intgemm/intgemm/intgemm.cc",
                },
                {
                    "command": "cl /arch:SSE2 /Oi- /GL- /DLINGUUM_MSVC_BASELINE=1 /D_USE_STD_VECTOR_ALGORITHMS=0 /c factored_vocab.cpp",
                    "file": "C:/source/marian-fork/src/data/factored_vocab.cpp",
                },
                {
                    "command": "cl /arch:SSE2 /Oi- /D_USE_STD_VECTOR_ALGORITHMS=0 /DUSE_ONNX_SGEMM=1 /c prod.cpp",
                    "file": "C:/source/marian-fork/src/tensors/cpu/prod.cpp",
                },
                {
                    "command": "cl /arch:SSE2 /Oi- /c gemm.cpp",
                    "file": "C:/source/onnxjs/src/wasm-ops/gemm.cpp",
                },
            ]))
            with self.assertRaisesRegex(
                windows_profiles.WindowsProfileError,
                "every baseline C\\+\\+ command must disable",
            ):
                windows_profiles.verify_compile_commands("windows-x64-baseline", root)

            commands.write_text(json.dumps([
                {
                    "command": "cl /arch:AVX2 /DLINGUUM_INTGEMM_MAX_AVX2 /c intgemm.cc",
                    "file": "C:/source/3rd_party/intgemm/intgemm/intgemm.cc",
                },
                {
                    "command": "cl /arch:AVX2 /c factored_vocab.cpp",
                    "file": "C:/source/marian-fork/src/data/factored_vocab.cpp",
                },
                {
                    "command": "cl /arch:AVX2 /DUSE_ONNX_SGEMM=1 /c prod.cpp",
                    "file": "C:/source/marian-fork/src/tensors/cpu/prod.cpp",
                },
                {
                    "command": "cl /arch:AVX2 /c gemm.cpp",
                    "file": "C:/source/onnxjs/src/wasm-ops/gemm.cpp",
                },
            ]))
            evidence = windows_profiles.verify_compile_commands("windows-x64-avx2", root)
            self.assertTrue(evidence["hasArchAvx2"])
            self.assertTrue(evidence["hasIntgemmAvx2Cap"])
            with self.assertRaises(windows_profiles.WindowsProfileError):
                windows_profiles.verify_compile_commands("windows-x64-baseline", root)

            optimized_with_baseline_stl = json.loads(commands.read_text())
            optimized_with_baseline_stl[0]["command"] += " /D_USE_STD_VECTOR_ALGORITHMS=0"
            commands.write_text(json.dumps(optimized_with_baseline_stl))
            with self.assertRaisesRegex(
                windows_profiles.WindowsProfileError,
                "retain the default vectorized MSVC STL",
            ):
                windows_profiles.verify_compile_commands("windows-x64-avx2", root)


class PackageTests(unittest.TestCase):
    def test_jar_creation_is_byte_reproducible_and_sorted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            entries = {"z/file": b"last", "META-INF/MANIFEST.MF": b"manifest", "a/file": b"first"}
            first = root / "first.jar"
            second = root / "second.jar"
            windows_profiles.create_jar(first, entries)
            windows_profiles.create_jar(second, entries)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(str(first)) as jar:
                self.assertEqual(sorted(entries), jar.namelist())
                self.assertEqual(b"first", jar.read("a/file"))

    def test_package_output_must_be_scoped_below_build(self):
        with self.assertRaises(windows_profiles.WindowsProfileError):
            windows_profiles.safe_output_directory(ROOT)
        with self.assertRaises(windows_profiles.WindowsProfileError):
            windows_profiles.safe_output_directory(ROOT / "build")
        expected = (ROOT / "build" / "windows-package-test").resolve()
        self.assertEqual(expected, windows_profiles.safe_output_directory(expected))


if __name__ == "__main__":
    unittest.main()

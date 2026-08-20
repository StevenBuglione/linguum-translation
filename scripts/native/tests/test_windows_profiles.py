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

        unsafe = safe + "  0000000180001004: vzeroupper\n"
        with self.assertRaises(windows_profiles.WindowsProfileError):
            windows_profiles.verify_isa("windows-x64-baseline", unsafe)

    def test_optimized_disassembly_requires_avx2_evidence(self):
        avx1_only = "  0000000180001000: vaddps xmm0,xmm1,xmm2\n"
        with self.assertRaises(windows_profiles.WindowsProfileError):
            windows_profiles.verify_isa("windows-x64-avx2", avx1_only)

        avx2 = avx1_only + "  0000000180001004: vpaddd ymm0,ymm1,ymm2\n"
        result = windows_profiles.verify_isa("windows-x64-avx2", avx2)
        self.assertEqual(1, len(result["avx2Evidence"]))

    def test_dependency_parser_allows_only_system_dlls(self):
        output = "    KERNEL32.dll\n    SHLWAPI.dll\n"
        self.assertEqual(["KERNEL32.DLL", "SHLWAPI.DLL"], windows_profiles.parse_dependencies(output))
        with self.assertRaises(windows_profiles.WindowsProfileError):
            windows_profiles.parse_dependencies(output + "    accidental.dll\n")

    def test_compile_command_profile_flags_are_enforced(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            commands = root / "compile_commands.json"
            commands.write_text(json.dumps([{
                "command": "cl /arch:SSE2 /c intgemm.cc",
                "file": "C:/source/3rd_party/intgemm/intgemm/intgemm.cc",
            }]))
            evidence = windows_profiles.verify_compile_commands("windows-x64-baseline", root)
            self.assertTrue(evidence["hasArchSse2"])
            self.assertFalse(evidence["hasArchAvx2"])
            self.assertFalse(evidence["hasIntgemmAvx2Cap"])

            commands.write_text(json.dumps([{
                "command": "cl /arch:AVX2 /DLINGUUM_INTGEMM_MAX_AVX2 /c intgemm.cc",
                "file": "C:/source/3rd_party/intgemm/intgemm/intgemm.cc",
            }]))
            evidence = windows_profiles.verify_compile_commands("windows-x64-avx2", root)
            self.assertTrue(evidence["hasArchAvx2"])
            self.assertTrue(evidence["hasIntgemmAvx2Cap"])
            with self.assertRaises(windows_profiles.WindowsProfileError):
                windows_profiles.verify_compile_commands("windows-x64-baseline", root)


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

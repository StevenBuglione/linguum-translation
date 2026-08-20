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
        self.assertEqual(set(windows_profiles.PROFILE_IDS), set(profiles))
        self.assertEqual(["AVX2"], profiles["windows-x64-avx2"]["requiredCpuFeatures"])
        baseline = profiles["windows-x64-baseline"]
        self.assertFalse(baseline["fbgemm"])
        self.assertTrue(baseline["intgemmBaselineOnly"])
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

            build_arch, acceleration, arguments = run_host_canary.host_profile(
                "windows-x64-baseline"
            )
            self.assertEqual("core2", build_arch)
            self.assertIn("baseline", acceleration)
            self.assertIn("-DUSE_FBGEMM=OFF", arguments)
            self.assertIn("-DUSE_ONNX_SGEMM=ON", arguments)
            self.assertIn("-DLINGUUM_INTGEMM_BASELINE_ONLY=ON", arguments)

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

    def test_external_patch_excludes_avx_kernels_only_for_baseline(self):
        patch = (
            ROOT / "native" / "patches" / "0001-reproducible-flattened-source-build.patch"
        ).read_text(encoding="utf-8")
        self.assertIn("intgemm/CMakeLists.txt", patch)
        self.assertIn("if(LINGUUM_INTGEMM_BASELINE_ONLY)", patch)
        for name in (
            "INTGEMM_COMPILER_SUPPORTS_AVX2",
            "INTGEMM_COMPILER_SUPPORTS_AVX512BW",
            "INTGEMM_COMPILER_SUPPORTS_AVX512VNNI",
        ):
            self.assertIn("set({} FALSE)".format(name), patch)
        self.assertIn("else()", patch)
        self.assertIn("try_compile(INTGEMM_COMPILER_SUPPORTS_AVX2", patch)


class EvidenceParsingTests(unittest.TestCase):
    def test_environment_parser_ignores_cmd_pseudo_variables(self):
        output = "Path=C:\\Tools\r\n=ExitCode=00000000\r\nWindowsSDKVersion=10.0.26100.0\\\r\n"
        self.assertEqual(
            {"Path": "C:\\Tools", "WindowsSDKVersion": "10.0.26100.0\\"},
            windows_profiles.parse_environment(output),
        )

    def test_vswhere_selects_the_locked_visual_studio_major(self):
        arguments = windows_profiles.vswhere_arguments({"visualStudio": "2026"})
        self.assertIn("[18.0,19.0)", arguments)
        self.assertNotIn("-latest", arguments)
        with self.assertRaises(windows_profiles.WindowsProfileError):
            windows_profiles.vswhere_arguments({"visualStudio": "future"})

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
            commands.write_text(json.dumps([{"command": "cl /arch:SSE2 /c adapter.cpp"}]))
            evidence = windows_profiles.verify_compile_commands("windows-x64-baseline", root)
            self.assertTrue(evidence["hasArchSse2"])
            self.assertFalse(evidence["hasArchAvx2"])

            commands.write_text(json.dumps([{"command": "cl /arch:AVX2 /c adapter.cpp"}]))
            evidence = windows_profiles.verify_compile_commands("windows-x64-avx2", root)
            self.assertTrue(evidence["hasArchAvx2"])
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

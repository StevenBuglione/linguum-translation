#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Offline contract tests for the M1 Android native profile proof."""

import importlib.util
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]


def load_script(name: str):
    path = ROOT / "scripts" / "native" / "{}.py".format(name)
    spec = importlib.util.spec_from_file_location("linguum_android_test_{}".format(name), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


android_profiles = load_script("android_profiles")


class AndroidProfileContractTests(unittest.TestCase):
    def test_lock_has_exact_abis_toolchain_backends_and_device_tiers(self):
        document = android_profiles.load_lock()
        profiles = android_profiles.profile_map(document)
        self.assertEqual(set(android_profiles.PROFILE_IDS), set(profiles))
        self.assertEqual("28.2.13676358", document["ndkVersion"])
        self.assertEqual("36.0.0", document["buildToolsVersion"])
        self.assertEqual(26, document["minSdk"])
        self.assertEqual([26, 36], document["emulatorApiLevels"])
        self.assertEqual(
            ["self-hosted", "linux", "arm64", "android-device"],
            document["physicalArm64RunnerLabels"],
        )

        arm64 = profiles["android-arm64-v8a"]
        self.assertEqual("arm64-v8a", arm64["abi"])
        self.assertEqual("aarch64", arm64["elfMachine"])
        self.assertEqual("ruy-neon-arm64", arm64["accelerationProfile"])
        self.assertEqual("Ruy", arm64["matrixMultiplicationBackend"])
        self.assertEqual(["ARMv8-A", "NEON"], arm64["requiredCpuFeatures"])
        self.assertTrue(arm64["physicalDeviceRequired"])

        x64 = profiles["android-x86_64"]
        self.assertEqual("x86_64", x64["abi"])
        self.assertEqual("x86_64", x64["elfMachine"])
        self.assertEqual("x86-64-v2", x64["buildArch"])
        self.assertEqual("intgemm-ssse3-onnx-sgemm-baseline", x64["accelerationProfile"])
        self.assertTrue(x64["intgemmBaselineOnly"])
        self.assertIn("AVX", x64["prohibitedInstructionFamilies"])

    def test_output_directory_is_confined_to_build(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "build") as temporary:
            self.assertEqual(Path(temporary).resolve(), android_profiles.safe_output_directory(Path(temporary)))
        with self.assertRaises(android_profiles.AndroidProfileError):
            android_profiles.safe_output_directory(ROOT)
        with self.assertRaises(android_profiles.AndroidProfileError):
            android_profiles.safe_output_directory(ROOT / "build")

    def test_ndk_resolution_requires_exact_pinned_revision_and_host_tag(self):
        with tempfile.TemporaryDirectory() as temporary:
            sdk = Path(temporary)
            ndk = sdk / "ndk" / "28.2.13676358"
            toolchain = ndk / "build" / "cmake" / "android.toolchain.cmake"
            toolchain.parent.mkdir(parents=True)
            toolchain.write_text("# fixture\n", encoding="utf-8")
            (ndk / "source.properties").write_text(
                "Pkg.Desc = Android NDK\nPkg.Revision = 28.2.13676358\n",
                encoding="utf-8",
            )
            bin_dir = ndk / "toolchains" / "llvm" / "prebuilt" / "linux-x86_64" / "bin"
            bin_dir.mkdir(parents=True)
            for name in ("clang++", "llvm-nm", "llvm-objdump", "llvm-readelf", "llvm-strip"):
                (bin_dir / name).write_text("fixture\n", encoding="utf-8")
            with mock.patch.object(android_profiles.platform, "system", return_value="Linux"), \
                 mock.patch.object(android_profiles.platform, "machine", return_value="x86_64"):
                evidence = android_profiles.resolve_ndk({"ANDROID_SDK_ROOT": str(sdk)})
            self.assertEqual(ndk, evidence["root"])
            self.assertEqual("linux-x86_64", evidence["hostTag"])
            self.assertEqual(toolchain, evidence["toolchain"])

            (ndk / "source.properties").write_text(
                "Pkg.Desc = Android NDK\nPkg.Revision = 28.1.0\n",
                encoding="utf-8",
            )
            with self.assertRaises(android_profiles.AndroidProfileError):
                android_profiles.validate_ndk(ndk, "linux-x86_64")

    def test_cmake_arguments_pin_api_abi_stl_and_backend_without_native_flags(self):
        profiles = android_profiles.profile_map(android_profiles.load_lock())
        ndk = {
            "root": Path("/sdk/ndk/28.2.13676358"),
            "toolchain": Path("/sdk/ndk/28.2.13676358/build/cmake/android.toolchain.cmake"),
        }
        for profile_id in android_profiles.PROFILE_IDS:
            arguments = android_profiles.cmake_arguments(
                profiles[profile_id],
                ndk,
                Path("/source"),
                Path("/build"),
            )
            joined = " ".join(str(value) for value in arguments)
            self.assertIn("-DANDROID_PLATFORM=android-26", arguments)
            self.assertIn("-DANDROID_STL=c++_static", arguments)
            self.assertIn("-DANDROID_ABI={}".format(profiles[profile_id]["abi"]), arguments)
            self.assertIn("-DBUILD_TESTING=OFF", arguments)
            self.assertNotIn("-march=native", joined)
        arm = android_profiles.cmake_arguments(profiles["android-arm64-v8a"], ndk, Path("/s"), Path("/b"))
        self.assertIn("-DUSE_RUY=ON", arm)
        self.assertIn("-DUSE_RUY_SGEMM=ON", arm)
        x64 = android_profiles.cmake_arguments(profiles["android-x86_64"], ndk, Path("/s"), Path("/b"))
        self.assertIn("-DLINGUUM_INTGEMM_BASELINE_ONLY=ON", x64)
        self.assertIn("-DUSE_FBGEMM=OFF", x64)
        self.assertIn("-DUSE_ONNX_SGEMM=ON", x64)

    def test_elf_header_requires_android_shared_object_and_exact_machine(self):
        profiles = android_profiles.profile_map(android_profiles.load_lock())
        x64 = """  Class:                             ELF64
  Type:                              DYN (Shared object file)
  Machine:                           Advanced Micro Devices X86-64
  OS/ABI:                            UNIX - System V
"""
        arm64 = x64.replace("Advanced Micro Devices X86-64", "AArch64")
        self.assertEqual(
            "x86_64",
            android_profiles.verify_elf_header(profiles["android-x86_64"], x64)["architecture"],
        )
        self.assertEqual(
            "aarch64",
            android_profiles.verify_elf_header(profiles["android-arm64-v8a"], arm64)["architecture"],
        )
        with self.assertRaises(android_profiles.AndroidProfileError):
            android_profiles.verify_elf_header(profiles["android-arm64-v8a"], x64)

    def test_dynamic_dependencies_allow_only_android_system_libraries(self):
        output = """
 0x000000000000000e (SONAME) Library soname: [liblinguum_translation_jni.so]
 0x0000000000000001 (NEEDED) Shared library: [libm.so]
 0x0000000000000001 (NEEDED) Shared library: [libdl.so]
 0x0000000000000001 (NEEDED) Shared library: [libc.so]
"""
        evidence = android_profiles.verify_dynamic_dependencies(output)
        self.assertEqual("liblinguum_translation_jni.so", evidence["soname"])
        self.assertNotIn("libc++_shared.so", evidence["needed"])
        with self.assertRaises(android_profiles.AndroidProfileError):
            android_profiles.verify_dynamic_dependencies(
                output + " 0x0001 (NEEDED) Shared library: [libbuildhost.so]\n"
            )
        with self.assertRaises(android_profiles.AndroidProfileError):
            android_profiles.verify_dynamic_dependencies(
                output + " 0x001d (RUNPATH) Library runpath: [/tmp/build]\n"
            )

    def test_exports_are_exactly_jni_on_load(self):
        output = "0000000000001234 T JNI_OnLoad\n"
        self.assertEqual(["JNI_OnLoad"], android_profiles.verify_exports(output))
        with self.assertRaises(android_profiles.AndroidProfileError):
            android_profiles.verify_exports(
                output + "0000000000004567 T linguum_translation_abi_major\n"
            )

    def test_x64_isa_rejects_any_avx_family_instruction(self):
        baseline = """
0000000000001000 <scalar>:
    1000: 66 0f 6f c1          movdqa %xmm1,%xmm0
"""
        self.assertTrue(android_profiles.verify_x64_isa(baseline)["avxFamilyAbsent"])
        with self.assertRaises(android_profiles.AndroidProfileError):
            android_profiles.verify_x64_isa(
                baseline + "    1004: c5 fd 6f c1          vmovdqa %ymm1,%ymm0\n"
            )

    def test_arm64_isa_requires_neon_evidence(self):
        evidence = android_profiles.verify_arm64_isa(
            """000000000004e030 <kernel>:
   4e030: 4e22cc20  fmla v0.4s, v1.4s, v2.4s
   4e034: d65f03c0  ret
"""
        )
        self.assertTrue(evidence["neonEvidence"])
        with self.assertRaises(android_profiles.AndroidProfileError):
            android_profiles.verify_arm64_isa("0000: d65f03c0 ret\n")

    def test_compile_commands_prove_api_backend_and_no_host_native(self):
        profiles = android_profiles.profile_map(android_profiles.load_lock())
        adapter = ROOT / "native" / "mozilla-adapter" / "src" / "linguum_translation.cpp"
        jni = ROOT / "testing" / "native" / "android_canary_jni.cpp"
        with tempfile.TemporaryDirectory() as temporary:
            build = Path(temporary)
            for profile_id, backend in (
                ("android-arm64-v8a", "-DARM -DUSE_RUY=1 -DUSE_RUY_SGEMM=1"),
                ("android-x86_64", "-DUSE_ONNX_SGEMM=1 -DUSE_INTGEMM=1 -mno-avx"),
            ):
                target = (
                    "aarch64-none-linux-android26"
                    if profile_id == "android-arm64-v8a"
                    else "x86_64-none-linux-android26"
                )
                commands = [
                    {
                        "file": str(ROOT / "source" / "graph.cpp"),
                        "command": "clang++ --target={} {} -c graph.cpp".format(target, backend),
                    },
                    {"file": str(adapter), "command": "clang++ --target={} -c adapter.cpp".format(target)},
                    {"file": str(jni), "command": "clang++ --target={} -c android_canary_jni.cpp".format(target)},
                ]
                (build / "compile_commands.json").write_text(json.dumps(commands), encoding="utf-8")
                evidence = android_profiles.verify_compile_commands(profiles[profile_id], build)
                self.assertEqual(26, evidence["nativeApiLevel"])
                self.assertFalse(evidence["hostDependentMarchNative"])
                commands[0]["command"] += " -march=native"
                (build / "compile_commands.json").write_text(json.dumps(commands), encoding="utf-8")
                with self.assertRaises(android_profiles.AndroidProfileError):
                    android_profiles.verify_compile_commands(profiles[profile_id], build)

    def test_deterministic_aar_contains_only_locked_abis_and_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            libraries = {}
            for abi in ("arm64-v8a", "x86_64"):
                library = root / abi / "liblinguum_translation_jni.so"
                library.parent.mkdir()
                library.write_bytes(abi.encode("ascii"))
                libraries[abi] = library
            classes = root / "classes.jar"
            android_profiles.write_deterministic_zip(
                classes,
                {"io/linguum/translation/internal/android/CanaryBridge.class": b"class"},
            )
            first = root / "first.aar"
            second = root / "second.aar"
            android_profiles.package_aar(libraries, classes, first)
            android_profiles.package_aar(libraries, classes, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            evidence = android_profiles.verify_aar(first)
            self.assertEqual(["arm64-v8a", "x86_64"], evidence["abis"])
            with zipfile.ZipFile(first) as archive:
                self.assertEqual(sorted(archive.namelist()), archive.namelist())
                self.assertTrue(all(item.date_time == (1980, 1, 1, 0, 0, 0) for item in archive.infolist()))
                self.assertEqual((ROOT / "LICENSE").read_bytes(), archive.read("META-INF/LICENSE"))
                self.assertEqual((ROOT / "NOTICE").read_bytes(), archive.read("META-INF/NOTICE"))
                self.assertEqual(
                    (ROOT / "THIRD_PARTY_LICENSES.md").read_bytes(),
                    archive.read("META-INF/THIRD_PARTY_LICENSES.md"),
                )
                self.assertEqual(
                    (ROOT / "native" / "UPSTREAM_LOCK.json").read_bytes(),
                    archive.read("META-INF/linguum/UPSTREAM_LOCK.json"),
                )
                self.assertEqual(
                    (ROOT / "native" / "SOURCE_TREE.sha256").read_bytes(),
                    archive.read("META-INF/linguum/SOURCE_TREE.sha256"),
                )

    def test_aar_rejects_missing_or_extra_abi(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            classes = root / "classes.jar"
            android_profiles.write_deterministic_zip(
                classes,
                {"io/linguum/translation/internal/android/CanaryBridge.class": b"class"},
            )
            library = root / "x86_64" / "liblinguum_translation_jni.so"
            library.parent.mkdir()
            library.write_bytes(b"x64")
            with self.assertRaises(android_profiles.AndroidProfileError):
                android_profiles.package_aar({"x86_64": library}, classes, root / "invalid.aar")

    def test_device_properties_distinguish_emulator_and_physical_arm64(self):
        emulator = """ro.product.cpu.abi=x86_64
ro.build.version.sdk=26
ro.kernel.qemu=1
"""
        self.assertEqual(
            "x86_64",
            android_profiles.verify_device_properties(emulator, "x86_64", 26, physical=False)["abi"],
        )
        physical = """ro.product.cpu.abi=arm64-v8a
ro.build.version.sdk=36
ro.kernel.qemu=0
"""
        self.assertTrue(
            android_profiles.verify_device_properties(physical, "arm64-v8a", 26, physical=True)["physical"]
        )
        with self.assertRaises(android_profiles.AndroidProfileError):
            android_profiles.verify_device_properties(emulator, "arm64-v8a", 26, physical=True)

    def test_native_and_java_bridge_use_registered_jni_and_one_library(self):
        cmake = (ROOT / "native" / "runtime-build" / "CMakeLists.txt").read_text(encoding="utf-8")
        exports = (ROOT / "native" / "runtime-build" / "exports" / "android.map").read_text(encoding="utf-8")
        jni = (ROOT / "testing" / "native" / "android_canary_jni.cpp").read_text(encoding="utf-8")
        bridge = (
            ROOT
            / "testing"
            / "platform-smoke"
            / "android-canary"
            / "bridge"
            / "CanaryBridge.java"
        ).read_text(encoding="utf-8")
        self.assertIn("add_library(linguum_translation_jni SHARED", cmake)
        self.assertIn("JNI_OnLoad", exports)
        self.assertNotIn("linguum_translation_", exports)
        self.assertIn("RegisterNatives", jni)
        self.assertNotIn("Java_io_linguum", jni)
        self.assertIn('System.loadLibrary("linguum_translation_jni")', bridge)

    def test_android_x64_portability_patch_and_compile_flags_are_locked(self):
        cmake = (ROOT / "native" / "runtime-build" / "CMakeLists.txt").read_text(encoding="utf-8")
        patch = (
            ROOT / "native" / "patches" / "0001-reproducible-flattened-source-build.patch"
        ).read_text(encoding="utf-8")
        self.assertIn('CMAKE_SYSTEM_PROCESSOR MATCHES "^(x86_64|amd64|AMD64)$"', cmake)
        self.assertIn("add_compile_options(-mno-avx -mno-avx2)", cmake)
        self.assertIn(
            "diff --git a/inference/marian-fork/src/3rd_party/faiss/VectorTransform.cpp",
            patch,
        )
        self.assertIn("+#if defined(__SSE__)", patch)
        self.assertIn("+#include <immintrin.h>", patch)

    def test_workflows_build_both_abis_emulate_minimum_and_require_physical_arm64(self):
        pr = (ROOT / ".github" / "workflows" / "pr.yml").read_text(encoding="utf-8")
        nightly = (ROOT / ".github" / "workflows" / "nightly.yml").read_text(encoding="utf-8")
        release = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        scope = (ROOT / "scripts" / "ci" / "verify-scope.sh").read_text(encoding="utf-8")
        runners = (ROOT / "toolchains" / "ci-runners.lock.yaml").read_text(encoding="utf-8")
        self.assertIn("LINGUUM_ANDROID_EMULATOR_API: 26", pr)
        self.assertIn("--profile all", scope)
        self.assertIn("android-arm64-v8a", scope)
        self.assertIn("android-x86_64", scope)
        for workflow in (nightly, release):
            self.assertIn("android-device", workflow)
            self.assertIn("--device-mode physical", workflow)
            self.assertIn("arm64-v8a", workflow)
        self.assertIn("android_physical_arm64", runners)
        self.assertIn("android-device", runners)

    def test_canary_is_an_isolated_feasibility_build_not_a_production_module(self):
        settings = (ROOT / "settings.gradle.kts").read_text(encoding="utf-8")
        plugin = (
            ROOT
            / "build-logic"
            / "src"
            / "main"
            / "kotlin"
            / "io"
            / "linguum"
            / "translation"
            / "buildlogic"
            / "ArchitecturePlugin.kt"
        ).read_text(encoding="utf-8")
        consumer = (
            ROOT / "testing" / "platform-smoke" / "android-canary" / "app" / "build.gradle.kts"
        ).read_text(encoding="utf-8")
        manifest = (
            ROOT
            / "testing"
            / "platform-smoke"
            / "android-canary"
            / "app"
            / "src"
            / "main"
            / "AndroidManifest.xml"
        ).read_text(encoding="utf-8")
        self.assertNotIn(":platform:android", settings)
        self.assertNotIn(":testing:platform-smoke:android-canary", settings)
        self.assertIn('"testing/platform-smoke/android-canary/**"', plugin)
        self.assertIn("assets.directories.add(canaryAssets.get())", consumer)
        self.assertNotIn("assets.srcDir", consumer)
        self.assertNotIn("extractNativeLibs", manifest)
        self.assertFalse((ROOT / "platform" / "android").exists())

    def test_android_artifact_name_matches_the_locked_platform_contract(self):
        source = (ROOT / "scripts" / "native" / "android_profiles.py").read_text(encoding="utf-8")
        self.assertIn('"translation-android-0.1.0-M1.aar"', source)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Offline contract tests for the M1 Linux native profile proof."""

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
    spec = importlib.util.spec_from_file_location("linguum_linux_test_{}".format(name), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


linux_profiles = load_script("linux_profiles")
run_host_canary = load_script("run_host_canary")


class LinuxProfileContractTests(unittest.TestCase):
    def test_lock_has_exact_profiles_baseline_runners_and_backends(self):
        document = linux_profiles.load_lock()
        profiles = linux_profiles.profile_map(document)
        self.assertEqual(set(linux_profiles.PROFILE_IDS), set(profiles))
        self.assertEqual("ubuntu-22.04", document["buildBaseline"])
        self.assertEqual("2.35", document["glibcFloor"])
        self.assertEqual(
            ["ubuntu-22.04", "ubuntu-24.04"],
            document["compatibilityRunners"],
        )
        self.assertEqual(["address", "undefined"], document["sanitizers"])

        optimized = profiles["linux-x64-avx2"]
        self.assertEqual("haswell", optimized["buildArch"])
        self.assertEqual("FBGEMM", optimized["matrixMultiplicationBackend"])
        self.assertEqual(["AVX2"], optimized["requiredCpuFeatures"])
        self.assertIn("AVX-512", optimized["prohibitedInstructionFamilies"])

        baseline = profiles["linux-x64-baseline"]
        self.assertEqual("nehalem", baseline["buildArch"])
        self.assertFalse(baseline["fbgemm"])
        self.assertTrue(baseline["intgemmBaselineOnly"])
        self.assertIn("AVX", baseline["prohibitedInstructionFamilies"])

        arm64 = profiles["linux-arm64"]
        self.assertEqual("ubuntu-22.04-arm", arm64["runner"])
        self.assertEqual("armv8-a", arm64["buildArch"])
        self.assertEqual("Ruy", arm64["matrixMultiplicationBackend"])
        self.assertEqual("Ruy", arm64["quantizedBackend"])
        self.assertTrue(arm64["realArm64Execution"])

    def test_explicit_profiles_are_host_independent(self):
        with mock.patch.object(run_host_canary.platform, "system", return_value="Linux"), \
             mock.patch.object(run_host_canary.platform, "machine", return_value="x86_64"):
            optimized = run_host_canary.host_profile("linux-x64-avx2")
            baseline = run_host_canary.host_profile("linux-x64-baseline")
        self.assertEqual("haswell", optimized[0])
        self.assertEqual("fbgemm-intgemm-avx2", optimized[1])
        self.assertIn("-DUSE_FBGEMM=ON", optimized[2])
        self.assertIn("-DLINGUUM_INTGEMM_AVX2_ONLY=ON", optimized[2])
        self.assertEqual("nehalem", baseline[0])
        self.assertEqual("intgemm-ssse3-onnx-sgemm-baseline", baseline[1])
        self.assertIn("-DUSE_FBGEMM=OFF", baseline[2])
        self.assertIn("-DLINGUUM_INTGEMM_BASELINE_ONLY=ON", baseline[2])
        for arguments in (optimized[2], baseline[2]):
            self.assertIn("-DUSE_RUY=OFF", arguments)
            self.assertNotIn("-march=native", " ".join(arguments))

        with mock.patch.object(run_host_canary.platform, "system", return_value="Linux"), \
             mock.patch.object(run_host_canary.platform, "machine", return_value="aarch64"):
            arm64 = run_host_canary.host_profile("linux-arm64")
        self.assertEqual("armv8-a", arm64[0])
        self.assertEqual("ruy-neon-arm64", arm64[1])
        self.assertIn("-DUSE_RUY=ON", arm64[2])
        self.assertIn("-DUSE_RUY_SGEMM=ON", arm64[2])
        self.assertIn("-DUSE_FBGEMM=OFF", arm64[2])

    def test_explicit_linux_profile_rejects_wrong_system_or_architecture(self):
        with mock.patch.object(run_host_canary.platform, "system", return_value="Darwin"), \
             mock.patch.object(run_host_canary.platform, "machine", return_value="arm64"):
            with self.assertRaises(run_host_canary.HostCanaryError):
                run_host_canary.host_profile("linux-arm64")
        with mock.patch.object(run_host_canary.platform, "system", return_value="Linux"), \
             mock.patch.object(run_host_canary.platform, "machine", return_value="aarch64"):
            with self.assertRaises(run_host_canary.HostCanaryError):
                run_host_canary.host_profile("linux-x64-avx2")

    def test_glibc_parser_and_required_symbol_ceiling_fail_closed(self):
        self.assertEqual((2, 35), linux_profiles.parse_glibc_version("glibc 2.35\n"))
        versions = linux_profiles.parse_required_symbol_versions(
            """  0x0010: Name: GLIBC_2.17  Flags: none  Version: 9
  0x0020: Name: GLIBC_2.35  Flags: none  Version: 8
  0x0030: Name: GLIBCXX_3.4.29  Flags: none  Version: 7
  0x0040: Name: CXXABI_1.3.13  Flags: none  Version: 6
"""
        )
        evidence = linux_profiles.verify_symbol_version_ceilings(versions, "2.35")
        self.assertEqual("2.35", evidence["maximumRequiredGlibc"])
        self.assertEqual("3.4.29", evidence["maximumRequiredGlibcxx"])
        with self.assertRaises(linux_profiles.LinuxProfileError):
            linux_profiles.verify_symbol_version_ceilings(
                linux_profiles.parse_required_symbol_versions("Name: GLIBC_2.36"),
                "2.35",
            )
        with self.assertRaises(linux_profiles.LinuxProfileError):
            linux_profiles.parse_glibc_version("musl libc")

    def test_dynamic_dependencies_require_soname_and_only_system_libraries(self):
        output = """
 0x000000000000000e (SONAME)             Library soname: [liblinguum_translation.so]
 0x0000000000000001 (NEEDED)             Shared library: [libstdc++.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [libm.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [libgcc_s.so.1]
 0x0000000000000001 (NEEDED)             Shared library: [libc.so.6]
"""
        evidence = linux_profiles.parse_dynamic_dependencies(output)
        self.assertEqual("liblinguum_translation.so", evidence["soname"])
        self.assertEqual(4, len(evidence["needed"]))
        self.assertFalse(evidence["hasRuntimeSearchPath"])
        with self.assertRaises(linux_profiles.LinuxProfileError):
            linux_profiles.parse_dynamic_dependencies(
                output + " 0x0001 (NEEDED) Shared library: [libbuildhost.so]\n"
            )
        with self.assertRaises(linux_profiles.LinuxProfileError):
            linux_profiles.parse_dynamic_dependencies(
                output + " 0x001d (RUNPATH) Library runpath: [/tmp/build]\n"
            )

    def test_elf_header_requires_exact_architecture_and_shared_object(self):
        x64 = """  Class:                             ELF64
  Type:                              DYN (Shared object file)
  Machine:                           Advanced Micro Devices X86-64
"""
        arm64 = x64.replace("Advanced Micro Devices X86-64", "AArch64")
        profiles = linux_profiles.profile_map(linux_profiles.load_lock())
        self.assertEqual(
            "x86_64",
            linux_profiles.verify_elf_header(profiles["linux-x64-avx2"], x64)["architecture"],
        )
        self.assertEqual(
            "aarch64",
            linux_profiles.verify_elf_header(profiles["linux-arm64"], arm64)["architecture"],
        )
        with self.assertRaises(linux_profiles.LinuxProfileError):
            linux_profiles.verify_elf_header(profiles["linux-arm64"], x64)

    def test_x64_isa_rejects_avx_baseline_and_avx512_optimized(self):
        baseline = """
0000000000001000 <scalar>:
    1000: 66 0f 6f c1          movdqa %xmm1,%xmm0
"""
        evidence = linux_profiles.verify_x64_isa("linux-x64-baseline", baseline)
        self.assertTrue(evidence["baselineAvxFamilyAbsent"])
        with self.assertRaises(linux_profiles.LinuxProfileError):
            linux_profiles.verify_x64_isa(
                "linux-x64-baseline",
                baseline + "    1004: c5 fd 6f c1          vmovdqa %ymm1,%ymm0\n",
            )
        optimized = baseline + "    1004: c4 e2 75 04 c2       vpmaddubsw %ymm2,%ymm1,%ymm0\n"
        self.assertTrue(
            linux_profiles.verify_x64_isa("linux-x64-avx2", optimized)["avx2Evidence"]
        )
        with self.assertRaises(linux_profiles.LinuxProfileError):
            linux_profiles.verify_x64_isa(
                "linux-x64-avx2",
                optimized + "    1009: 62 f1 7d 48 6f c1    vmovdqa32 %zmm1,%zmm0\n",
            )

    def test_arm64_isa_accepts_word_encoded_neon_disassembly(self):
        evidence = linux_profiles.verify_arm64_isa(
            """000000000004e030 <kernel>:
   4e030: 4e22cc20  fmla v0.4s, v1.4s, v2.4s
   4e034: d65f03c0  ret
"""
        )
        self.assertTrue(evidence["neonEvidence"])

    def test_compile_evidence_rejects_native_and_proves_backends(self):
        profiles = linux_profiles.profile_map(linux_profiles.load_lock())
        adapter = ROOT / "native" / "mozilla-adapter" / "src" / "linguum_translation.cpp"
        with tempfile.TemporaryDirectory() as temporary:
            build = Path(temporary)
            for profile_id, backend_definition in (
                ("linux-x64-avx2", "-DUSE_FBGEMM=1 -DUSE_INTGEMM=1"),
                ("linux-x64-baseline", "-DUSE_ONNX_SGEMM=1 -DUSE_INTGEMM=1"),
                ("linux-arm64", "-DARM -DUSE_RUY=1 -DUSE_RUY_SGEMM=1"),
            ):
                profile = profiles[profile_id]
                common = "g++ -march={} -DLINGUUM_ACCELERATION_PROFILE=\\\"{}\\\"".format(
                    profile["buildArch"], profile["accelerationProfile"]
                )
                commands = [
                    {
                        "file": str(ROOT / "source" / "marian-fork" / "src" / "graph.cpp"),
                        "command": "{} {} -c graph.cpp".format(common, backend_definition),
                    },
                    {"file": str(adapter), "command": "{} -c adapter.cpp".format(common)},
                ]
                (build / "compile_commands.json").write_text(
                    json.dumps(commands), encoding="utf-8"
                )
                evidence = linux_profiles.verify_compile_commands(profile, build)
                self.assertEqual(profile["buildArch"], evidence["buildArch"])
                self.assertFalse(evidence["hostDependentMarchNative"])
                commands[0]["command"] = commands[0]["command"].replace(
                    "-march={}".format(profile["buildArch"]), "-march=native"
                )
                (build / "compile_commands.json").write_text(
                    json.dumps(commands), encoding="utf-8"
                )
                with self.assertRaises(linux_profiles.LinuxProfileError):
                    linux_profiles.verify_compile_commands(profile, build)

    def test_gnu_arm_vector_compatibility_is_scoped_to_native_targets(self):
        cmake = (ROOT / "native" / "runtime-build" / "CMakeLists.txt").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "target_compile_options(marian PRIVATE -flax-vector-conversions)", cmake
        )
        self.assertIn(
            "target_compile_options(bergamot-translator-source PRIVATE -flax-vector-conversions)",
            cmake,
        )
        self.assertIn(
            "target_compile_options(linguum_translation PRIVATE -flax-vector-conversions)",
            cmake,
        )
        self.assertNotIn("add_compile_options(-flax-vector-conversions)", cmake)

    def test_deterministic_jar_has_sorted_epoch_entries(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first.jar"
            second = root / "second.jar"
            entries = {"z/file": b"last", "a/file": b"first"}
            linux_profiles.create_jar(first, entries)
            linux_profiles.create_jar(second, entries)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(str(first)) as jar:
                self.assertEqual(["a/file", "z/file"], jar.namelist())
                self.assertTrue(
                    all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in jar.infolist())
                )

    def test_compatibility_manifest_authenticates_identity_and_executable_mode(self):
        profile = linux_profiles.profile_map(linux_profiles.load_lock())[
            "linux-x64-baseline"
        ]
        manifest = {
            "schemaVersion": 1,
            "profile": profile,
            "abi": "1.0",
            "canaryMode": "0755",
            "canarySha256": "a" * 64,
            "librarySha256": "b" * 64,
            "sourceTreeSha256": linux_profiles.source_tree_sha256(),
        }
        linux_profiles.verify_compatibility_manifest(manifest, profile)
        for key, value in (
            ("abi", "2.0"),
            ("canaryMode", "0644"),
            ("sourceTreeSha256", "0" * 64),
            ("librarySha256", "not-a-digest"),
        ):
            changed = dict(manifest)
            changed[key] = value
            with self.assertRaises(linux_profiles.LinuxProfileError):
                linux_profiles.verify_compatibility_manifest(changed, profile)
        with tempfile.TemporaryDirectory() as temporary:
            canary = Path(temporary) / "canary"
            canary.write_bytes(b"exact transported bytes")
            canary.chmod(0o644)
            self.assertEqual(0o644, os.stat(canary).st_mode & 0o777)
            linux_profiles.restore_compatibility_canary_mode(canary, manifest)
            self.assertEqual(0o755, os.stat(canary).st_mode & 0o777)

    def test_output_directory_is_confined_to_build(self):
        with self.assertRaises(linux_profiles.LinuxProfileError):
            linux_profiles.safe_output_directory(ROOT)
        with self.assertRaises(linux_profiles.LinuxProfileError):
            linux_profiles.safe_output_directory(ROOT / "build")
        expected = (ROOT / "build" / "linux-package-test").resolve()
        self.assertEqual(expected, linux_profiles.safe_output_directory(expected))

    def test_sanitizer_environment_preserves_the_build_path(self):
        with mock.patch.dict(linux_profiles.os.environ, {"PATH": "/locked/path"}, clear=True):
            environment = linux_profiles.sanitizer_environment(("address", "undefined"))
        self.assertEqual("/locked/path", environment["PATH"])
        self.assertEqual("2", environment["CMAKE_BUILD_PARALLEL_LEVEL"])
        self.assertIn("detect_leaks=1", environment["ASAN_OPTIONS"])
        self.assertIn("halt_on_error=1", environment["UBSAN_OPTIONS"])
        with mock.patch.dict(
            run_host_canary.os.environ,
            {"CMAKE_BUILD_PARALLEL_LEVEL": environment["CMAKE_BUILD_PARALLEL_LEVEL"]},
            clear=True,
        ):
            command = run_host_canary.build_command(
                Path("cmake"), Path("build/native"), "linux-arm64"
            )
        self.assertEqual(["--parallel", "2"], command[3:5])

    def test_external_patch_uses_alignment_safe_quantization_multiplier_access(self):
        patch = (
            ROOT
            / "native"
            / "patches"
            / "0001-reproducible-flattened-source-build.patch"
        ).read_text(encoding="utf-8")
        metadata = json.loads(
            (ROOT / "native" / "patches" / "PATCHES.yaml").read_text(
                encoding="utf-8"
            )
        )
        path = "inference/marian-fork/src/tensors/cpu/integer_common.h"
        self.assertIn("diff --git a/{0} b/{0}".format(path), patch)
        self.assertIn(path, metadata["affectedPaths"])
        self.assertIn(
            "std::memcpy(&quantMult, input + sizeof(Integer) * item.shape.elements(),",
            patch,
        )
        self.assertIn(
            "std::memcpy(reinterpret_cast<char *>(output_tensor) +",
            patch,
        )
        self.assertNotIn(
            "+    float quantMult = *(reinterpret_cast<const float *>", patch
        )

    def test_external_patch_structurally_caps_optimized_backends_at_avx2(self):
        patch = (
            ROOT
            / "native"
            / "patches"
            / "0001-reproducible-flattened-source-build.patch"
        ).read_text(encoding="utf-8")
        self.assertGreaterEqual(
            patch.count("+  set(INTGEMM_COMPILER_SUPPORTS_AVX512BW FALSE)"), 2
        )
        self.assertGreaterEqual(
            patch.count("+  set(INTGEMM_COMPILER_SUPPORTS_AVX512VNNI FALSE)"), 2
        )
        self.assertIn("LINGUUM_FBGEMM_MAX_AVX2", patch)
        self.assertIn("set(FBGEMM_AVX512_OBJECTS)", patch)
        self.assertIn("${FBGEMM_AVX512_OBJECTS}", patch)
        self.assertIn("#ifndef LINGUUM_FBGEMM_MAX_AVX2", patch)

    def test_workflows_prove_x64_arm64_compatibility_and_sanitizers(self):
        workflow = (ROOT / ".github" / "workflows" / "pr.yml").read_text(encoding="utf-8")
        native_safety = (
            ROOT / ".github" / "workflows" / "native-safety.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("runs-on: ubuntu-22.04", workflow)
        self.assertIn("LINGUUM_LINUX_PROFILE: linux-x64", workflow)
        self.assertNotIn("PR / Linux arm64 native integration", workflow)
        self.assertIn("runs-on: ubuntu-22.04-arm", native_safety)
        self.assertIn("runs-on: ubuntu-24.04-arm", native_safety)
        for profile_id in linux_profiles.PROFILE_IDS:
            self.assertIn("--profile {}".format(profile_id), native_safety + workflow)
        self.assertIn("--sanitizers address,undefined", native_safety)
        self.assertIn("--verify-only", native_safety)


if __name__ == "__main__":
    unittest.main()

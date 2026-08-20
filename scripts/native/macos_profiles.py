#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build, inspect, run, and package one locked M1 macOS native profile."""

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Mapping, Sequence

SCRIPT_DIRECTORY = Path(__file__).resolve().parent
if str(SCRIPT_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIRECTORY))

import run_host_canary


ROOT = Path(__file__).resolve().parents[2]
LOCK_PATH = ROOT / "toolchains" / "macos-native-profiles.lock.json"
DEFAULT_OUTPUT = ROOT / "build" / "native-packages" / "macos"
PROFILE_IDS = ("macos-arm64", "macos-x64")
EXPECTED_RUNNERS = {
    "macos-arm64": "macos-15",
    "macos-x64": "macos-15-intel",
}


class MacosProfileError(RuntimeError):
    """A macOS profile build or evidence invariant failed."""


def load_lock(path: Path = LOCK_PATH) -> Dict[str, object]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schemaVersion") != 1 or document.get("deploymentTarget") != "13.0":
        raise MacosProfileError("unsupported macOS profile lock identity")
    toolchain = document.get("toolchain")
    profiles = document.get("profiles")
    if not isinstance(toolchain, dict) or not isinstance(profiles, list):
        raise MacosProfileError("macOS profile lock is missing toolchain or profiles")
    if set(toolchain) != {
        "compilerVendor", "sdk", "xcodeSelection", "cmake", "ninja"
    }:
        raise MacosProfileError("macOS profile toolchain keys differ from the contract")
    if (
        toolchain.get("compilerVendor") != "AppleClang"
        or toolchain.get("sdk") != "macosx"
        or toolchain.get("xcodeSelection") != "runner-default"
    ):
        raise MacosProfileError("macOS profile toolchain selection is not supported")
    by_id = {
        profile.get("id"): profile
        for profile in profiles
        if isinstance(profile, dict)
    }
    if tuple(sorted(by_id)) != tuple(sorted(PROFILE_IDS)) or len(profiles) != len(by_id):
        raise MacosProfileError("macOS profile IDs must be exact and unique")
    for profile_id, architecture, namespace, build_arch in (
        ("macos-arm64", "arm64", "aarch64", "armv8-a"),
        ("macos-x64", "x86_64", "x86_64", "nehalem"),
    ):
        profile = by_id[profile_id]
        if (
            profile.get("runner") != EXPECTED_RUNNERS[profile_id]
            or profile.get("architecture") != architecture
            or profile.get("binaryNamespace") != namespace
            or profile.get("buildArch") != build_arch
            or profile.get("matrixMultiplicationBackend") != "Accelerate"
        ):
            raise MacosProfileError("{} differs from the locked contract".format(profile_id))
    if (
        by_id["macos-arm64"].get("accelerationProfile") != "apple-accelerate-arm64"
        or by_id["macos-arm64"].get("minimumCpuFeatures") != ["ARMv8-A"]
        or by_id["macos-arm64"].get("quantizedBackend") != "Ruy"
        or by_id["macos-arm64"].get("intgemmRuntimeDispatch") is not False
    ):
        raise MacosProfileError("macOS arm64 must use the locked Ruy quantized path")
    if (
        by_id["macos-x64"].get("accelerationProfile")
        != "apple-accelerate-intgemm-runtime-x64"
        or by_id["macos-x64"].get("minimumCpuFeatures") != ["SSE4.2"]
        or by_id["macos-x64"].get("quantizedBackend") != "intgemm-runtime-dispatch"
        or by_id["macos-x64"].get("intgemmRuntimeDispatch") is not True
    ):
        raise MacosProfileError("macOS x64 must retain intgemm runtime dispatch")
    return document


def profile_map(document: Mapping[str, object]) -> Dict[str, Mapping[str, object]]:
    return {str(profile["id"]): profile for profile in document["profiles"]}


def safe_output_directory(path: Path) -> Path:
    resolved = path.resolve()
    build_root = (ROOT / "build").resolve()
    try:
        resolved.relative_to(build_root)
    except ValueError as error:
        raise MacosProfileError(
            "macOS package output must be below {}".format(build_root)
        ) from error
    if resolved == build_root:
        raise MacosProfileError("macOS package output cannot be the build root")
    return resolved


def capture(command: Sequence[str]) -> str:
    completed = subprocess.run(
        list(command),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if completed.returncode != 0:
        raise MacosProfileError(
            "command failed ({}): {}\n{}".format(
                completed.returncode, command, completed.stdout.strip()
            )
        )
    return completed.stdout


def verify_host(profile: Mapping[str, object]) -> None:
    if platform.system().lower() != "darwin":
        raise MacosProfileError("macOS is required")
    machine = platform.machine().lower()
    architecture = profile["architecture"]
    if architecture == "arm64" and machine not in {"arm64", "aarch64"}:
        raise MacosProfileError("macos-arm64 execution requires Apple Silicon")
    if architecture == "x86_64" and machine not in {"x86_64", "amd64", "arm64", "aarch64"}:
        raise MacosProfileError("macos-x64 execution requires Intel macOS or Rosetta")
    if architecture == "x86_64" and machine in {"arm64", "aarch64"}:
        capture(["/usr/bin/arch", "-x86_64", "/usr/bin/true"])


def toolchain_evidence(toolchain: Mapping[str, object]) -> Dict[str, object]:
    cmake, ninja = run_host_canary.bootstrap_tools.bootstrap()
    cmake_version = capture([str(cmake), "--version"]).splitlines()[0]
    ninja_version = capture([str(ninja), "--version"]).strip()
    if cmake_version != "cmake version {}".format(toolchain["cmake"]):
        raise MacosProfileError("CMake does not match the macOS profile lock")
    if ninja_version != toolchain["ninja"]:
        raise MacosProfileError("Ninja does not match the macOS profile lock")
    compiler = capture(["xcrun", "--sdk", "macosx", "clang", "--version"])
    if "Apple clang version" not in compiler:
        raise MacosProfileError("the selected compiler is not AppleClang")
    compiler_match = re.search(r"Apple clang version ([^\s]+)", compiler)
    if compiler_match is None:
        raise MacosProfileError("AppleClang version could not be parsed")
    xcode_lines = capture(["xcodebuild", "-version"]).splitlines()
    if len(xcode_lines) < 2 or not xcode_lines[0].startswith("Xcode "):
        raise MacosProfileError("Xcode identity could not be parsed")
    return {
        **toolchain,
        "appleClangVersion": compiler_match.group(1),
        "cmakeVersionLine": cmake_version,
        "hostArchitecture": platform.machine().lower(),
        "macosBuild": capture(["sw_vers", "-buildVersion"]).strip(),
        "macosVersion": capture(["sw_vers", "-productVersion"]).strip(),
        "ninjaVersion": ninja_version,
        "sdkVersion": capture(["xcrun", "--sdk", "macosx", "--show-sdk-version"]).strip(),
        "xcodeBuild": xcode_lines[1].removeprefix("Build version ").strip(),
        "xcodeVersion": xcode_lines[0].removeprefix("Xcode ").strip(),
    }


def parse_dependencies(output: str) -> List[str]:
    dependencies = []
    saw_self_identity = False
    for line in output.splitlines()[1:]:
        line = line.strip()
        if not line:
            continue
        dependency = line.split(" (compatibility version", 1)[0].strip()
        if dependency == "@rpath/liblinguum_translation.dylib":
            saw_self_identity = True
            continue
        if dependency:
            dependencies.append(dependency)
    dependencies = sorted(set(dependencies))
    if not saw_self_identity:
        raise MacosProfileError("the dylib install name is not the locked @rpath identity")
    unexpected = [
        dependency
        for dependency in dependencies
        if not dependency.startswith(("/usr/lib/", "/System/Library/Frameworks/"))
    ]
    if unexpected:
        raise MacosProfileError(
            "non-system dylib dependencies found: {}".format(unexpected)
        )
    if not any("/Accelerate.framework/" in dependency for dependency in dependencies):
        raise MacosProfileError("Accelerate is not a linked runtime dependency")
    return dependencies


def macho_architectures(output: str) -> List[str]:
    text = output.strip()
    if re.fullmatch(r"(?:arm64|x86_64)(?:\s+(?:arm64|x86_64))*", text):
        return sorted(set(text.split()))
    match = re.search(r"(?:are:|architecture:)\s+(.+?)\s*$", text)
    if match is None:
        raise MacosProfileError("lipo architecture output could not be parsed")
    architectures = sorted(set(match.group(1).split()))
    if not architectures or not all(value in {"arm64", "x86_64"} for value in architectures):
        raise MacosProfileError("lipo reported unsupported architectures: {}".format(architectures))
    return architectures


def verify_compile_commands(
    profile: Mapping[str, object], build_directory: Path
) -> Dict[str, object]:
    path = build_directory / "compile_commands.json"
    commands = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(commands, list) or not commands:
        raise MacosProfileError("compile_commands.json must contain commands")
    command_texts = [str(entry.get("command", "")) for entry in commands]
    expected_arch = str(profile["architecture"])
    deployment = "-mmacosx-version-min=13.0"
    if not all(re.search(r"(?:^|\s)-arch\s+{}(?:\s|$)".format(expected_arch), text) for text in command_texts):
        raise MacosProfileError("not every compile command targets {}".format(expected_arch))
    if not all(deployment in text for text in command_texts):
        raise MacosProfileError("not every compile command targets macOS 13.0")
    marian_commands = [
        text for entry, text in zip(commands, command_texts)
        if "/marian-fork/" in str(entry.get("file", "")).replace("\\", "/")
    ]
    adapter_source = (
        ROOT / "native" / "mozilla-adapter" / "src" / "linguum_translation.cpp"
    ).resolve()
    adapter_commands = [
        text for entry, text in zip(commands, command_texts)
        if Path(str(entry.get("file", ""))).resolve() == adapter_source
    ]
    if not marian_commands or len(adapter_commands) != 1:
        raise MacosProfileError("compile evidence is missing Marian or the native adapter")
    if not any("-DBLAS_FOUND=1" in text for text in marian_commands):
        raise MacosProfileError("Marian commands do not select the Accelerate BLAS path")
    acceleration = str(profile["accelerationProfile"])
    if 'LINGUUM_ACCELERATION_PROFILE=\\"{}\\"'.format(acceleration) not in adapter_commands[0]:
        raise MacosProfileError("native adapter acceleration identity differs from the lock")
    expected_build_arch = str(profile["buildArch"])
    march_commands = [text for text in command_texts if " -march=" in text]
    if not march_commands or not all(
        "-march={}".format(expected_build_arch) in text for text in march_commands
    ):
        raise MacosProfileError("compile commands do not use the locked BUILD_ARCH")
    if any("-march=native" in text for text in command_texts):
        raise MacosProfileError("host-dependent -march=native is forbidden")
    if expected_arch == "arm64":
        if not any("-DARM" in text for text in marian_commands):
            raise MacosProfileError("arm64 Marian commands do not select the ARM path")
    else:
        if not any("-DUSE_INTGEMM=1" in text for text in marian_commands):
            raise MacosProfileError("x64 Marian commands do not retain intgemm dispatch")
        if not any("-march=nehalem" in text for text in marian_commands):
            raise MacosProfileError("x64 Marian commands do not establish the SSE4.2 floor")
    return {
        "compileCommandCount": len(commands),
        "compileCommandsSha256": run_host_canary.file_sha256(path),
        "allCommandsTargetArchitecture": True,
        "allCommandsTargetMacos13": True,
        "buildArch": expected_build_arch,
        "hasAccelerateBlasDefinition": True,
        "hasArmPath": expected_arch == "arm64",
        "hasIntgemmRuntimeDispatch": expected_arch == "x86_64",
        "hostDependentMarchNative": False,
    }


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def source_tree_sha256() -> str:
    value = (ROOT / "native" / "SOURCE_TREE.sha256").read_text(
        encoding="utf-8"
    ).strip()
    match = re.fullmatch(
        r"([0-9a-f]{64})\s+upstream/mozilla-translations", value
    )
    if match is None:
        raise MacosProfileError("native source tree hash file is malformed")
    return match.group(1)


def create_jar(path: Path, entries: Mapping[str, bytes]) -> None:
    partial = path.with_name(path.name + ".part")
    partial.unlink(missing_ok=True)
    with zipfile.ZipFile(
        str(partial), "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as jar:
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            jar.writestr(info, entries[name])
    os.replace(str(partial), str(path))


def package_profile(
    result: Mapping[str, object],
    profile: Mapping[str, object],
    toolchain: Mapping[str, object],
    output: Path,
) -> Dict[str, object]:
    profile_id = str(profile["id"])
    library = Path(str(result["artifact"]))
    build_directory = Path(str(result["buildDirectory"]))
    if result["cmake"] != "cmake version {}".format(toolchain["cmake"]):
        raise MacosProfileError("build CMake does not match the profile lock")
    if result["ninja"] != toolchain["ninja"]:
        raise MacosProfileError("build Ninja does not match the profile lock")
    architectures = macho_architectures(capture(["lipo", "-archs", str(library)]))
    if architectures != [profile["architecture"]]:
        raise MacosProfileError(
            "Mach-O architectures differ: expected {}, got {}".format(
                profile["architecture"], architectures
            )
        )
    dependencies = parse_dependencies(capture(["otool", "-L", str(library)]))
    commands = verify_compile_commands(profile, build_directory)
    manifest = {
        "schemaVersion": 1,
        "profile": profile,
        "abi": result["abi"],
        "artifact": {
            "fileName": library.name,
            "sha256": result["artifactSha256"],
            "size": library.stat().st_size,
        },
        "canary": {
            "languagePair": "es-en",
            "iterations": result["iterations"],
            "exactMatch": True,
        },
        "commands": commands,
        "dependencies": dependencies,
        "exports": sorted(result["exports"]),
        "machO": {
            "architectures": architectures,
            "minimumMacosVersions": result["minimumVersions"],
        },
        "source": {
            "firefoxRevision": result["firefoxRevision"],
            "translationsRevision": result["translationsRevision"],
            "sourceTreeSha256": source_tree_sha256(),
        },
        "toolchain": toolchain,
    }
    metadata_root = "META-INF/linguum/native"
    binary_path = "linguum/native/macos/{}/linguum_translation.dylib".format(
        profile["binaryNamespace"]
    )
    entries = {
        "META-INF/MANIFEST.MF": b"Manifest-Version: 1.0\r\nCreated-By: Linguum Translation M1\r\n\r\n",
        "META-INF/LICENSE": (ROOT / "LICENSE").read_bytes(),
        "META-INF/NOTICE": (ROOT / "NOTICE").read_bytes(),
        "META-INF/THIRD_PARTY_LICENSES.md": (
            ROOT / "THIRD_PARTY_LICENSES.md"
        ).read_bytes(),
        "META-INF/licenses/MPL-2.0.txt": (
            ROOT / "native" / "upstream" / "mozilla-translations" / "LICENSE"
        ).read_bytes(),
        "{}/profile.json".format(metadata_root): json_bytes(manifest),
        "{}/UPSTREAM.json".format(metadata_root): (
            ROOT / "native" / "UPSTREAM.json"
        ).read_bytes(),
        "{}/UPSTREAM_LOCK.json".format(metadata_root): (
            ROOT / "native" / "UPSTREAM_LOCK.json"
        ).read_bytes(),
        "{}/PATCHES.yaml".format(metadata_root): (
            ROOT / "native" / "patches" / "PATCHES.yaml"
        ).read_bytes(),
        "linguum/native/include/linguum_translation.h": (
            ROOT / "native" / "abi" / "include" / "linguum_translation.h"
        ).read_bytes(),
        binary_path: library.read_bytes(),
    }
    output.mkdir(parents=True, exist_ok=True)
    jar = output / "linguum-translation-native-{}-0.1.0-M1.jar".format(profile_id)
    create_jar(jar, entries)
    first_hash = run_host_canary.file_sha256(jar)
    reproduction = output / "{}.reproduction".format(jar.name)
    try:
        create_jar(reproduction, entries)
        reproduction_hash = run_host_canary.file_sha256(reproduction)
    finally:
        reproduction.unlink(missing_ok=True)
    if reproduction_hash != first_hash:
        raise MacosProfileError("deterministic JAR reproduction differs")
    return {
        "dylibSha256": result["artifactSha256"],
        "jar": str(jar),
        "jarSha256": first_hash,
        "jarSize": jar.stat().st_size,
        "manifest": manifest,
        "profile": profile_id,
        "reproducibleJar": True,
    }


PROFILE_ERRORS = (
    MacosProfileError,
    run_host_canary.HostCanaryError,
    OSError,
    subprocess.SubprocessError,
    ValueError,
    json.JSONDecodeError,
)


def execute(
    profile_id: str, output: Path, iterations: int, clean: bool
) -> Dict[str, object]:
    output = safe_output_directory(output)
    document = load_lock()
    profiles = profile_map(document)
    if profile_id not in profiles:
        raise MacosProfileError("unsupported macOS profile: {}".format(profile_id))
    profile = profiles[profile_id]
    verify_host(profile)
    evidence = toolchain_evidence(document["toolchain"])
    result = run_host_canary.execute(
        ROOT / "build" / "native-canary" / profile_id,
        iterations,
        clean,
        profile_id,
    )
    package = package_profile(result, profile, evidence, output)
    summary = {"profile": package, "toolchain": evidence}
    output.mkdir(parents=True, exist_ok=True)
    result_path = output / "M1-WP04-{}-result.json".format(profile_id)
    result_path.write_bytes(json_bytes(summary))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=PROFILE_IDS, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--clean", action="store_true")
    arguments = parser.parse_args()
    try:
        execute(arguments.profile, arguments.output, arguments.iterations, arguments.clean)
    except PROFILE_ERRORS as error:
        print("macOS native profile gate failed: {}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

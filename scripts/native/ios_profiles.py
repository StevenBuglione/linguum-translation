#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build, inspect, package, and execute the locked M1 iOS native profiles."""

import argparse
import hashlib
import json
import os
import platform
import plistlib
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Mapping, MutableMapping, Optional, Sequence


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
if str(SCRIPT_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIRECTORY))

import bootstrap_tools
import fetch_canary_model
import stage_source


ROOT = Path(__file__).resolve().parents[2]
LOCK_PATH = ROOT / "toolchains" / "ios-native-profiles.lock.json"
DEFAULT_OUTPUT = ROOT / "build" / "native-packages" / "ios"
FIXTURE = ROOT / "testing" / "platform-smoke" / "ios-canary"
HEADER_DIRECTORY = ROOT / "native" / "abi" / "include"
PROFILE_IDS = ("ios-arm64", "ios-simulator-arm64", "ios-simulator-x64")
TRANSLATIONS_REVISION = "eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d"
FIREFOX_REVISION = "48d55cf7ec80093903e2ef7f58b61a84a22ef716"
EXPECTED_C_ABI_SYMBOLS = (
    "linguum_translation_abi_major",
    "linguum_translation_abi_minor",
    "linguum_translation_runtime_create",
    "linguum_translation_runtime_info_create",
    "linguum_translation_runtime_destroy",
    "linguum_translation_model_load",
    "linguum_translation_model_destroy",
    "linguum_translation_translator_create",
    "linguum_translation_translator_destroy",
    "linguum_translation_translator_translate",
    "linguum_translation_result_text",
    "linguum_translation_result_destroy",
    "linguum_translation_error_code",
    "linguum_translation_error_message",
    "linguum_translation_error_destroy",
    "linguum_translation_runtime_info_library_version",
    "linguum_translation_runtime_info_firefox_revision",
    "linguum_translation_runtime_info_bergamot_version",
    "linguum_translation_runtime_info_acceleration_profile",
    "linguum_translation_runtime_info_destroy",
)


class IosProfileError(RuntimeError):
    """An iOS profile build or evidence invariant failed."""


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_lock(path: Path = LOCK_PATH) -> Dict[str, object]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if (
        document.get("schemaVersion") != 1
        or document.get("deploymentTarget") != "15.0"
        or document.get("kotlinVersion") != "2.4.10"
        or document.get("xcodeSelection") != "runner-default"
    ):
        raise IosProfileError("unsupported iOS profile lock identity")
    toolchain = document.get("toolchain")
    profiles = document.get("profiles")
    if toolchain != {
        "compilerVendor": "AppleClang",
        "cmake": "4.0.2",
        "ninja": "1.13.2",
    }:
        raise IosProfileError("iOS toolchain lock differs from the contract")
    if document.get("dependencies") != {
        "pcre2": {
            "archive": "pcre2-10.39.tar.gz",
            "sha256": "0781bd2536ef5279b1943471fdcdbd9961a2845e1d2c9ad849b9bd98ba1a9bd4",
            "url": "https://github.com/PCRE2Project/pcre2/releases/download/pcre2-10.39/pcre2-10.39.tar.gz",
            "version": "10.39",
        }
    }:
        raise IosProfileError("iOS PCRE2 dependency lock differs from the contract")
    if document.get("physicalArm64RunnerLabels") != [
        "self-hosted",
        "macos",
        "arm64",
        "ios-device",
    ]:
        raise IosProfileError("physical iOS runner labels differ from the contract")
    if not isinstance(profiles, list):
        raise IosProfileError("iOS profiles must be a list")
    by_id = {
        profile.get("id"): profile
        for profile in profiles
        if isinstance(profile, dict)
    }
    if tuple(sorted(by_id)) != tuple(sorted(PROFILE_IDS)) or len(profiles) != len(by_id):
        raise IosProfileError("iOS profile IDs must be exact and unique")
    expected = {
        "ios-arm64": ("iosArm64", "iphoneos", "IOS", "arm64", "macos-15"),
        "ios-simulator-arm64": (
            "iosSimulatorArm64",
            "iphonesimulator",
            "IOSSIMULATOR",
            "arm64",
            "macos-15",
        ),
        "ios-simulator-x64": (
            "iosX64",
            "iphonesimulator",
            "IOSSIMULATOR",
            "x86_64",
            "macos-15-intel",
        ),
    }
    for profile_id, values in expected.items():
        profile = by_id[profile_id]
        actual = tuple(
            profile.get(key)
            for key in ("kotlinTarget", "sdk", "platform", "architecture", "runner")
        )
        if actual != values or profile.get("matrixMultiplicationBackend") != "Accelerate":
            raise IosProfileError("{} differs from the locked target contract".format(profile_id))
    for profile_id in ("ios-arm64", "ios-simulator-arm64"):
        profile = by_id[profile_id]
        if (
            profile.get("buildArch") != "armv8-a"
            or profile.get("accelerationProfile") != "apple-accelerate-ruy-arm64"
            or profile.get("quantizedBackend") != "Ruy"
            or profile.get("requiredCpuFeatures") != ["ARMv8-A", "NEON"]
        ):
            raise IosProfileError("{} must use the locked Ruy/NEON path".format(profile_id))
    x64 = by_id["ios-simulator-x64"]
    if (
        x64.get("buildArch") != "nehalem"
        or x64.get("accelerationProfile")
        != "apple-accelerate-intgemm-runtime-x64"
        or x64.get("quantizedBackend") != "intgemm-runtime-dispatch"
        or x64.get("requiredCpuFeatures") != ["SSE4.2"]
    ):
        raise IosProfileError("ios-simulator-x64 differs from the locked Intel path")
    if by_id["ios-arm64"].get("physicalDeviceExecutionRequired") is not True:
        raise IosProfileError("ios-arm64 physical execution must remain required")
    if (
        by_id["ios-arm64"].get("runInPullRequest") is not False
        or by_id["ios-simulator-arm64"].get("runInPullRequest") is not True
        or by_id["ios-simulator-x64"].get("runInPullRequest") is not False
    ):
        raise IosProfileError("iOS pull-request execution tiers differ from the contract")
    if any(
        by_id[profile_id].get("physicalDeviceExecutionRequired") is not False
        for profile_id in ("ios-simulator-arm64", "ios-simulator-x64")
    ):
        raise IosProfileError("simulator profiles cannot require physical execution")
    return document


def profile_map(document: Mapping[str, object]) -> Dict[str, Mapping[str, object]]:
    return {str(profile["id"]): profile for profile in document["profiles"]}


def safe_output_directory(path: Path) -> Path:
    resolved = path.resolve()
    build_root = (ROOT / "build").resolve()
    try:
        resolved.relative_to(build_root)
    except ValueError as error:
        raise IosProfileError(
            "iOS package output must be below {}".format(build_root)
        ) from error
    if resolved == build_root:
        raise IosProfileError("iOS package output cannot be the build root")
    return resolved


def materialize_locked_pcre2(
    document: Mapping[str, object], source: Path
) -> Dict[str, object]:
    """Seed the staged iOS source from a verified cache before CMake runs."""
    dependency = document["dependencies"]["pcre2"]
    version = str(dependency["version"])
    archive_name = str(dependency["archive"])
    expected_sha256 = str(dependency["sha256"])
    cache = (
        ROOT
        / "build"
        / "native-dependencies"
        / "locked"
        / "pcre2-{}".format(version)
        / archive_name
    ).resolve()
    bootstrap_tools.download(str(dependency["url"]), cache, expected_sha256)
    actual_sha256 = file_sha256(cache)
    if actual_sha256 != expected_sha256:
        raise IosProfileError("cached PCRE2 archive differs from the iOS lock")

    parent = (
        source
        / "inference"
        / "3rd_party"
        / "ssplit-cpp"
        / "src"
        / "3rd-party"
    ).resolve()
    build_root = (ROOT / "build").resolve()
    try:
        parent.relative_to(build_root)
    except ValueError as error:
        raise IosProfileError("staged PCRE2 destination must remain below build") from error
    target = parent / "pcre2-{}".format(version)
    temporary = parent / ".linguum-pcre2-{}-extract".format(version)
    if temporary.exists():
        shutil.rmtree(str(temporary))
    temporary.mkdir(parents=True, exist_ok=False)
    try:
        bootstrap_tools.extract_archive(cache, temporary)
        extracted = temporary / "pcre2-{}".format(version)
        if sorted(path.name for path in temporary.iterdir()) != [extracted.name]:
            raise IosProfileError("PCRE2 archive must contain exactly one locked root")
        configure = extracted / "configure"
        if extracted.is_symlink() or not configure.is_file() or configure.is_symlink():
            raise IosProfileError("PCRE2 archive lacks the expected regular configure file")
        if target.exists():
            shutil.rmtree(str(target))
        os.replace(str(extracted), str(target))
    finally:
        if temporary.exists():
            shutil.rmtree(str(temporary))
    return {
        "archive": archive_name,
        "sha256": actual_sha256,
        "source": "verified-cache",
        "version": version,
    }


def run(
    command: Sequence[object],
    *,
    cwd: Path = ROOT,
    environment: Mapping[str, str] = None,
) -> None:
    printable = [str(value) for value in command]
    print("+ {}".format(" ".join(printable)), flush=True)
    subprocess.run(
        printable,
        cwd=str(cwd),
        env=None if environment is None else dict(environment),
        check=True,
    )


def capture(
    command: Sequence[object],
    *,
    cwd: Path = ROOT,
    environment: Mapping[str, str] = None,
    timeout_seconds: Optional[int] = None,
) -> str:
    completed = subprocess.run(
        [str(value) for value in command],
        cwd=str(cwd),
        env=None if environment is None else dict(environment),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout_seconds,
    )
    if completed.returncode != 0:
        raise IosProfileError(
            "command failed ({}): {}\n{}".format(
                completed.returncode,
                " ".join(str(value) for value in command),
                completed.stdout.strip(),
            )
        )
    return completed.stdout


def verify_host() -> None:
    if platform.system().lower() != "darwin":
        raise IosProfileError("iOS native profiles require macOS and Xcode")
    capture(["xcrun", "--find", "clang"])
    capture(["xcrun", "--find", "simctl"])


def toolchain_evidence(
    document: Mapping[str, object], cmake: Path, ninja: Path
) -> Dict[str, object]:
    compiler = capture(["xcrun", "clang", "--version"])
    match = re.search(r"Apple clang version ([^\s]+)", compiler)
    if match is None:
        raise IosProfileError("the selected iOS compiler is not AppleClang")
    xcode = capture(["xcodebuild", "-version"]).splitlines()
    if len(xcode) < 2 or not xcode[0].startswith("Xcode "):
        raise IosProfileError("Xcode identity could not be parsed")
    cmake_line = capture([cmake, "--version"]).splitlines()[0]
    ninja_version = capture([ninja, "--version"]).strip()
    if cmake_line != "cmake version {}".format(document["toolchain"]["cmake"]):
        raise IosProfileError("CMake differs from the iOS toolchain lock")
    if ninja_version != document["toolchain"]["ninja"]:
        raise IosProfileError("Ninja differs from the iOS toolchain lock")
    return {
        "appleClangVersion": match.group(1),
        "cmakeVersionLine": cmake_line,
        "hostArchitecture": platform.machine().lower(),
        "kotlinVersion": document["kotlinVersion"],
        "ninjaVersion": ninja_version,
        "xcodeBuild": xcode[1].removeprefix("Build version ").strip(),
        "xcodeSelection": document["xcodeSelection"],
        "xcodeVersion": xcode[0].removeprefix("Xcode ").strip(),
    }


def cmake_arguments(
    profile: Mapping[str, object],
    source: Path,
    build_directory: Path,
    cmake: Path,
    ninja: Path,
    sdk_root: Optional[Path] = None,
) -> List[str]:
    arm64 = profile["architecture"] == "arm64"
    selected_sdk = sdk_root if sdk_root is not None else profile["sdk"]
    arguments = [
        str(cmake),
        "-S",
        str(ROOT / "native" / "runtime-build"),
        "-B",
        str(build_directory),
        "-G",
        "Ninja",
        "-DCMAKE_MAKE_PROGRAM={}".format(ninja),
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        "-DCMAKE_SYSTEM_NAME=iOS",
        "-DCMAKE_OSX_DEPLOYMENT_TARGET=15.0",
        "-DCMAKE_OSX_SYSROOT={}".format(selected_sdk),
        "-DCMAKE_OSX_ARCHITECTURES={}".format(profile["architecture"]),
        "-DBUILD_TESTING=OFF",
        "-DBUILD_ARCH={}".format(profile["buildArch"]),
        "-DLINGUUM_APPLE_STATIC=ON",
        "-DLINGUUM_TRANSLATIONS_SOURCE={}".format(source),
        "-DLINGUUM_TRANSLATIONS_REVISION={}".format(TRANSLATIONS_REVISION),
        "-DLINGUUM_FIREFOX_REVISION={}".format(FIREFOX_REVISION),
        "-DLINGUUM_LIBRARY_VERSION=0.1.0-M1",
        "-DLINGUUM_ACCELERATION_PROFILE={}".format(
            profile["accelerationProfile"]
        ),
        "-DUSE_APPLE_ACCELERATE=ON",
        "-DUSE_FBGEMM=OFF",
        "-DUSE_ONNX_SGEMM=OFF",
        "-DUSE_RUY={}".format("ON" if arm64 else "OFF"),
        "-DUSE_RUY_SGEMM=OFF",
        "-DLINGUUM_INTGEMM_BASELINE_ONLY=OFF",
        "-DLINGUUM_INTGEMM_AVX2_ONLY=OFF",
    ]
    return arguments


def verify_compile_commands(
    profile: Mapping[str, object], build_directory: Path
) -> Dict[str, object]:
    path = build_directory / "compile_commands.json"
    commands = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(commands, list) or not commands:
        raise IosProfileError("compile_commands.json must contain iOS commands")
    texts = [str(entry.get("command", "")) for entry in commands]
    architecture = str(profile["architecture"])
    simulator = profile["platform"] == "IOSSIMULATOR"
    target = "{}-apple-ios15.0{}".format(
        architecture, "-simulator" if simulator else ""
    )
    deployment_flag = (
        "-mios-simulator-version-min=15.0"
        if simulator
        else "-miphoneos-version-min=15.0"
    )
    target_proven = all(
        re.search(r"(?:^|\s)-target\s+{}(?:\s|$)".format(re.escape(target)), text)
        is not None
        or (
            re.search(
                r"(?:^|\s)-arch\s+{}(?:\s|$)".format(re.escape(architecture)),
                text,
            )
            is not None
            and deployment_flag in text
        )
        for text in texts
    )
    if not target_proven:
        raise IosProfileError("not every compile command targets {}".format(target))
    if any("-march=native" in text for text in texts):
        raise IosProfileError("host-dependent -march=native is forbidden")
    expected_sdk_platform = (
        "iPhoneSimulator.platform" if simulator else "iPhoneOS.platform"
    )
    if any("MacOSX.sdk" in text for text in texts) or not all(
        expected_sdk_platform in text for text in texts
    ):
        raise IosProfileError(
            "iOS compile commands do not use the selected target SDK exclusively"
        )
    adapter = (
        ROOT / "native" / "mozilla-adapter" / "src" / "linguum_translation.cpp"
    ).resolve()
    adapter_commands = [
        text
        for entry, text in zip(commands, texts)
        if Path(str(entry.get("file", ""))).resolve() == adapter
    ]
    marian_commands = [
        text
        for entry, text in zip(commands, texts)
        if "/marian-fork/" in str(entry.get("file", "")).replace("\\", "/")
    ]
    if len(adapter_commands) != 1 or not marian_commands:
        raise IosProfileError("iOS compile evidence is missing adapter or Marian commands")
    acceleration = str(profile["accelerationProfile"])
    if 'LINGUUM_ACCELERATION_PROFILE=\\"{}\\"'.format(acceleration) not in adapter_commands[0]:
        raise IosProfileError("adapter acceleration profile differs from the lock")
    if not any("-DBLAS_FOUND=1" in text for text in marian_commands):
        raise IosProfileError("Marian does not select the Accelerate BLAS path")
    if profile["architecture"] == "arm64":
        normalized_files = [
            str(entry.get("file", "")).replace("\\", "/") for entry in commands
        ]
        ruy_arm_sources = {
            path.rsplit("/", 1)[-1]
            for path in normalized_files
            if "/3rd_party/ruy/ruy/" in path
            and path.rsplit("/", 1)[-1] in {"kernel_arm64.cc", "pack_arm.cc"}
        }
        if not any("-DARM" in text for text in marian_commands) or ruy_arm_sources != {
            "kernel_arm64.cc",
            "pack_arm.cc",
        }:
            raise IosProfileError("arm64 iOS does not prove the Ruy/NEON path")
    elif not any("-DUSE_INTGEMM=1" in text for text in marian_commands):
        raise IosProfileError("x64 iOS Simulator does not prove intgemm")
    return {
        "adapterCompiled": True,
        "deploymentTarget": "15.0",
        "hostDependentMarchNative": False,
        "hostMacosSdkReferences": False,
        "ruyArmSourcesCompiled": profile["architecture"] == "arm64",
        "targetSdkPlatform": expected_sdk_platform,
        "targetTriple": target,
    }


def macho_architectures(output: str) -> List[str]:
    values = sorted(set(output.strip().split()))
    if not values or not all(value in {"arm64", "x86_64"} for value in values):
        raise IosProfileError("lipo reported unsupported architectures: {}".format(values))
    return values


def verify_macho_identity(
    profile: Mapping[str, object], arch_output: str, build_output: str
) -> Dict[str, object]:
    architectures = macho_architectures(arch_output)
    expected_architecture = str(profile["architecture"])
    if architectures != [expected_architecture]:
        raise IosProfileError(
            "Mach-O architecture differs: expected {}, got {}".format(
                expected_architecture, architectures
            )
        )
    platforms = sorted(
        set(re.findall(r"^\s*platform\s+([A-Za-z0-9_]+)\s*$", build_output, re.MULTILINE))
    )
    minimums = sorted(
        set(re.findall(r"^\s*minos\s+([0-9]+(?:\.[0-9]+)+)\s*$", build_output, re.MULTILINE))
    )
    expected_platform = str(profile["platform"])
    if platforms != [expected_platform] or minimums != ["15.0"]:
        raise IosProfileError(
            "Mach-O platform/minimum differs: platforms={}, minimums={}".format(
                platforms, minimums
            )
        )
    return {
        "architectures": architectures,
        "minimumIosVersions": minimums,
        "platform": expected_platform,
    }


def verify_static_symbols(output: str) -> Dict[str, object]:
    symbols = sorted(
        set(
            match.group(1)
            for match in re.finditer(
                r"(?:^|\s)_((?:linguum_translation_)[A-Za-z0-9_]+)\s*$",
                output,
                re.MULTILINE,
            )
        )
    )
    missing = sorted(set(EXPECTED_C_ABI_SYMBOLS) - set(symbols))
    if missing:
        raise IosProfileError("merged iOS archive is missing C ABI symbols: {}".format(missing))
    return {"cAbiSymbols": sorted(EXPECTED_C_ABI_SYMBOLS)}


def verify_cinterop_output(output: str, target: str, iterations: int) -> Dict[str, object]:
    if "LINGUUM_IOS_CANARY_FAIL" in output:
        raise IosProfileError("iOS cinterop canary emitted a failure marker")
    start = "LINGUUM_IOS_CANARY_START target={} iterations={}".format(
        target, iterations
    )
    passed = "LINGUUM_IOS_CANARY_PASS target={} iterations={} abi=1.0".format(
        target, iterations
    )
    if output.count(start) != 1 or output.count(passed) != 1:
        raise IosProfileError("iOS cinterop output lacks exact target-correlated markers")
    return {"abi": "1.0", "iterations": iterations, "target": target}


def write_deterministic_zip(path: Path, entries: Mapping[str, bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name("{}.partial".format(path.name))
    partial.unlink(missing_ok=True)
    try:
        with zipfile.ZipFile(partial, "w", allowZip64=True) as archive:
            for name in sorted(entries):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, entries[name])
        os.replace(str(partial), str(path))
    finally:
        partial.unlink(missing_ok=True)


def package_entries(
    profile: Mapping[str, object], static_archive: Path
) -> Dict[str, bytes]:
    namespace = str(profile["binaryNamespace"])
    return {
        "META-INF/LICENSE": (ROOT / "LICENSE").read_bytes(),
        "META-INF/NOTICE": (ROOT / "NOTICE").read_bytes(),
        "META-INF/THIRD_PARTY_LICENSES.md": (
            ROOT / "THIRD_PARTY_LICENSES.md"
        ).read_bytes(),
        "META-INF/linguum/PATCHES.yaml": (
            ROOT / "native" / "patches" / "PATCHES.yaml"
        ).read_bytes(),
        "META-INF/linguum/SOURCE_TREE.sha256": (
            ROOT / "native" / "SOURCE_TREE.sha256"
        ).read_bytes(),
        "META-INF/linguum/UPSTREAM.json": (
            ROOT / "native" / "UPSTREAM.json"
        ).read_bytes(),
        "META-INF/linguum/UPSTREAM_LOCK.json": (
            ROOT / "native" / "UPSTREAM_LOCK.json"
        ).read_bytes(),
        "META-INF/linguum/ios-native-profiles.lock.json": LOCK_PATH.read_bytes(),
        "linguum/native/include/linguum_translation.h": (
            HEADER_DIRECTORY / "linguum_translation.h"
        ).read_bytes(),
        "linguum/native/ios/{}/liblinguum_translation.a".format(
            namespace
        ): static_archive.read_bytes(),
    }


def package_profile(
    profile: Mapping[str, object], static_archive: Path, destination: Path
) -> None:
    write_deterministic_zip(destination, package_entries(profile, static_archive))


def verify_profile_package(
    profile: Mapping[str, object], package: Path
) -> Dict[str, object]:
    with zipfile.ZipFile(package) as archive:
        names = archive.namelist()
        namespace = str(profile["binaryNamespace"])
        locked = sorted(
            [
                "META-INF/LICENSE",
                "META-INF/NOTICE",
                "META-INF/THIRD_PARTY_LICENSES.md",
                "META-INF/linguum/PATCHES.yaml",
                "META-INF/linguum/SOURCE_TREE.sha256",
                "META-INF/linguum/UPSTREAM.json",
                "META-INF/linguum/UPSTREAM_LOCK.json",
                "META-INF/linguum/ios-native-profiles.lock.json",
                "linguum/native/include/linguum_translation.h",
                "linguum/native/ios/{}/liblinguum_translation.a".format(namespace),
            ]
        )
        if names != locked:
            raise IosProfileError("iOS profile package entries differ from the lock")
        if any(item.date_time != (1980, 1, 1, 0, 0, 0) for item in archive.infolist()):
            raise IosProfileError("iOS profile package timestamps are not deterministic")
    return {"deterministicEpoch": True, "entries": locked}


def merge_static_archives(build_directory: Path, destination: Path) -> List[str]:
    candidates = sorted(
        path
        for path in build_directory.rglob("*.a")
        if path.resolve() != destination.resolve()
    )
    if not candidates:
        raise IosProfileError("the iOS native build produced no static archives")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.unlink(missing_ok=True)
    run(["xcrun", "libtool", "-static", "-D", "-o", destination, *candidates])
    run(["xcrun", "ranlib", "-D", destination])
    return [str(path.relative_to(build_directory)) for path in candidates]


def verify_deterministic_archive_metadata(archive: Path) -> Dict[str, object]:
    payload = archive.read_bytes()
    if not payload.startswith(b"!<arch>\n"):
        raise IosProfileError("merged iOS output is not an ar archive")
    position = 8
    members = 0
    while position < len(payload):
        header = payload[position : position + 60]
        if len(header) != 60 or header[58:60] != b"`\n":
            raise IosProfileError("merged iOS archive has a malformed member header")
        try:
            size = int(header[48:58].decode("ascii").strip())
        except (UnicodeDecodeError, ValueError) as error:
            raise IosProfileError("merged iOS archive has an invalid member size") from error
        timestamp = header[16:28].strip()
        owner = header[28:34].strip()
        group = header[34:40].strip()
        if timestamp not in {b"0", b"1"} or owner != b"0" or group != b"0":
            raise IosProfileError(
                "merged iOS archive retains non-deterministic time or owner metadata"
            )
        position += 60 + size + (size % 2)
        if position > len(payload):
            raise IosProfileError("merged iOS archive member exceeds the file boundary")
        members += 1
    if position != len(payload) or members == 0:
        raise IosProfileError("merged iOS archive is empty or has trailing data")
    return {"archiveMembers": members, "normalizedArchiveHeaders": True}


def build_cinterop(
    profile: Mapping[str, object], static_archive: Path, clean: bool
) -> Path:
    build_directory = ROOT / "build" / "native-canary" / "ios-cinterop" / str(
        profile["id"]
    )
    if clean and build_directory.exists():
        shutil.rmtree(str(build_directory))
    task = "linkReleaseExecutable{}".format(profile["kotlinTarget"])
    command = [
        ROOT / "gradlew",
        "-p",
        FIXTURE,
        "--no-daemon",
        "--warning-mode=fail",
        "--no-build-cache",
        "--rerun-tasks",
        "--no-configuration-cache",
        task,
        "-PlinguumIosProfile={}".format(profile["id"]),
        "-PlinguumIosArchive={}".format(static_archive),
        "-PlinguumIosHeaders={}".format(HEADER_DIRECTORY),
        "-PlinguumIosBuildDirectory={}".format(build_directory),
    ]
    run(command)
    executables = sorted(
        path
        for path in build_directory.rglob("*")
        if path.is_file()
        and os.access(str(path), os.X_OK)
        and (path.suffix == ".kexe" or "releaseExecutable" in path.parts)
    )
    if len(executables) != 1:
        raise IosProfileError(
            "expected one Kotlin/Native executable for {}, found {}".format(
                profile["id"], executables
            )
        )
    return executables[0]


def select_simulator() -> Dict[str, object]:
    document = json.loads(capture(["xcrun", "simctl", "list", "devices", "available", "--json"]))
    candidates = []
    for runtime, devices in document.get("devices", {}).items():
        if not runtime.startswith("com.apple.CoreSimulator.SimRuntime.iOS-"):
            continue
        version_text = runtime.rsplit("iOS-", 1)[-1].replace("-", ".")
        try:
            version = tuple(int(value) for value in version_text.split("."))
        except ValueError:
            continue
        if version < (15, 0):
            continue
        for device in devices:
            if device.get("isAvailable") is True:
                candidates.append((device.get("state") != "Booted", tuple(-v for v in version), device))
    if not candidates:
        raise IosProfileError("no available iOS 15+ simulator exists")
    _, _, selected = sorted(candidates, key=lambda value: (value[0], value[1], value[2]["name"]))[0]
    return selected


def build_app_bundle(
    profile: Mapping[str, object],
    executable: Path,
    model_directory: Path,
    configuration: Path,
    bundle_identifier: str,
) -> Path:
    if re.fullmatch(r"[A-Za-z0-9.-]+", bundle_identifier) is None:
        raise IosProfileError("iOS canary bundle identifier is malformed")
    bundle = (
        ROOT
        / "build"
        / "native-canary"
        / "ios-app"
        / str(profile["id"])
        / "LinguumIosCanary.app"
    )
    if bundle.exists():
        shutil.rmtree(str(bundle))
    model_resources = bundle / "Models"
    model_resources.mkdir(parents=True)
    bundled_executable = bundle / "LinguumIosCanary"
    shutil.copy2(str(executable), str(bundled_executable))
    bundled_executable.chmod(0o755)
    required_model_files = (
        "lex.50.50.esen.s2t.bin",
        "model.esen.intgemm.alphas.bin",
        "vocab.esen.spm",
    )
    for name in required_model_files:
        source = model_directory / name
        if not source.is_file() or source.is_symlink():
            raise IosProfileError("fixed iOS canary model resource is missing: {}".format(name))
        shutil.copy2(str(source), str(model_resources / name))
    if not configuration.is_file() or configuration.is_symlink():
        raise IosProfileError("fixed iOS canary configuration is missing")
    shutil.copy2(str(configuration), str(bundle / "es-en.yml"))
    platform_name = (
        "iPhoneSimulator" if profile["platform"] == "IOSSIMULATOR" else "iPhoneOS"
    )
    info = {
        "CFBundleDevelopmentRegion": "en",
        "CFBundleExecutable": "LinguumIosCanary",
        "CFBundleIdentifier": bundle_identifier,
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": "Linguum iOS Canary",
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleSupportedPlatforms": [platform_name],
        "CFBundleVersion": "1",
        "LSRequiresIPhoneOS": True,
        "MinimumOSVersion": "15.0",
        "UIDeviceFamily": [1, 2],
        "UILaunchScreen": {},
    }
    with (bundle / "Info.plist").open("wb") as stream:
        plistlib.dump(info, stream, fmt=plistlib.FMT_BINARY, sort_keys=True)
    return bundle


def run_simulator_canary(
    profile: Mapping[str, object],
    executable: Path,
    model_directory: Path,
    configuration: Path,
    iterations: int,
) -> Dict[str, object]:
    machine = platform.machine().lower()
    expected_machine = "x86_64" if profile["architecture"] == "x86_64" else "arm64"
    if expected_machine == "x86_64" and machine not in {"x86_64", "amd64"}:
        raise IosProfileError("x64 simulator execution requires an Intel macOS runner")
    if expected_machine == "arm64" and machine not in {"arm64", "aarch64"}:
        raise IosProfileError("arm64 simulator execution requires Apple Silicon")
    simulator = select_simulator()
    udid = str(simulator["udid"])
    bundle_identifier = "io.linguum.translation.canary.{}".format(
        str(profile["id"]).replace("-", ".")
    )
    app_bundle = build_app_bundle(
        profile,
        executable,
        model_directory,
        configuration,
        bundle_identifier,
    )
    booted_here = simulator.get("state") != "Booted"
    try:
        if booted_here:
            run(["xcrun", "simctl", "boot", udid])
        run(["xcrun", "simctl", "bootstatus", udid, "-b"])
        run(["xcrun", "simctl", "install", udid, app_bundle])
        output = capture(
            [
                "xcrun",
                "simctl",
                "launch",
                "--console",
                "--terminate-running-process",
                udid,
                bundle_identifier,
                profile["kotlinTarget"],
                "@bundle/Models",
                "@bundle/es-en.yml",
                str(iterations),
            ],
            timeout_seconds=900,
        )
    finally:
        subprocess.run(
            ["xcrun", "simctl", "uninstall", udid, bundle_identifier],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        if booted_here:
            run(["xcrun", "simctl", "shutdown", udid])
    evidence = verify_cinterop_output(output, str(profile["kotlinTarget"]), iterations)
    return {
        **evidence,
        "deviceName": simulator["name"],
        "simulatorUdid": udid,
    }


def run_physical_canary(
    profile: Mapping[str, object],
    executable: Path,
    model_directory: Path,
    configuration: Path,
    iterations: int,
) -> Dict[str, object]:
    required = (
        "LINGUUM_IOS_DEVICE_UDID",
        "LINGUUM_IOS_SIGNING_IDENTITY",
        "LINGUUM_IOS_PROVISIONING_PROFILE",
        "LINGUUM_IOS_BUNDLE_ID",
    )
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise IosProfileError(
            "physical iOS execution requires the locked signed-device runner inputs: {}".format(
                ", ".join(missing)
            )
        )
    udid = os.environ["LINGUUM_IOS_DEVICE_UDID"]
    identity = os.environ["LINGUUM_IOS_SIGNING_IDENTITY"]
    provisioning_profile = Path(os.environ["LINGUUM_IOS_PROVISIONING_PROFILE"]).resolve()
    bundle_identifier = os.environ["LINGUUM_IOS_BUNDLE_ID"]
    if not provisioning_profile.is_file() or provisioning_profile.is_symlink():
        raise IosProfileError("physical iOS provisioning profile is not a regular file")
    app_bundle = build_app_bundle(
        profile,
        executable,
        model_directory,
        configuration,
        bundle_identifier,
    )
    profile_document = plistlib.loads(
        subprocess.check_output(
            ["security", "cms", "-D", "-i", str(provisioning_profile)]
        )
    )
    entitlements = dict(profile_document.get("Entitlements", {}))
    team_identifiers = profile_document.get("TeamIdentifier", [])
    if not team_identifiers or not isinstance(entitlements, dict):
        raise IosProfileError("physical iOS provisioning profile lacks team entitlements")
    team_identifier = str(team_identifiers[0])
    application_identifier = "{}.{}".format(team_identifier, bundle_identifier)
    allowed_identifier = str(entitlements.get("application-identifier", ""))
    if not (
        allowed_identifier == application_identifier
        or (
            allowed_identifier.endswith(".*")
            and application_identifier.startswith(allowed_identifier[:-1])
        )
    ):
        raise IosProfileError("physical iOS bundle identifier is outside the provisioning profile")
    entitlements["application-identifier"] = application_identifier
    entitlements["com.apple.developer.team-identifier"] = team_identifier
    if isinstance(entitlements.get("keychain-access-groups"), list):
        entitlements["keychain-access-groups"] = [
            application_identifier if str(value).endswith(".*") else value
            for value in entitlements["keychain-access-groups"]
        ]
    shutil.copy2(
        str(provisioning_profile), str(app_bundle / "embedded.mobileprovision")
    )
    entitlements_path = app_bundle.parent / "canary-entitlements.plist"
    with entitlements_path.open("wb") as stream:
        plistlib.dump(entitlements, stream, fmt=plistlib.FMT_XML, sort_keys=True)
    run(
        [
            "codesign",
            "--force",
            "--sign",
            identity,
            "--entitlements",
            entitlements_path,
            "--generate-entitlement-der",
            app_bundle,
        ]
    )
    run(["codesign", "--verify", "--strict", app_bundle])
    try:
        run(
            [
                "xcrun",
                "devicectl",
                "device",
                "install",
                "app",
                "--device",
                udid,
                "--timeout",
                "300",
                app_bundle,
            ]
        )
        output = capture(
            [
                "xcrun",
                "devicectl",
                "device",
                "process",
                "launch",
                "--device",
                udid,
                "--console",
                "--terminate-existing",
                "--timeout",
                "900",
                bundle_identifier,
                profile["kotlinTarget"],
                "@bundle/Models",
                "@bundle/es-en.yml",
                str(iterations),
            ],
            timeout_seconds=930,
        )
    finally:
        subprocess.run(
            [
                "xcrun",
                "devicectl",
                "device",
                "uninstall",
                "app",
                "--device",
                udid,
                "--timeout",
                "300",
                bundle_identifier,
            ],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
    evidence = verify_cinterop_output(output, str(profile["kotlinTarget"]), iterations)
    return {**evidence, "bundleIdentifier": bundle_identifier, "deviceUdid": udid}


def build_profile(
    profile: Mapping[str, object],
    source: Path,
    cmake: Path,
    ninja: Path,
    output: Path,
    clean: bool,
) -> Dict[str, object]:
    profile_id = str(profile["id"])
    build_directory = ROOT / "build" / "native-canary" / profile_id
    if clean and build_directory.exists():
        shutil.rmtree(str(build_directory))
    sdk_root = Path(
        capture(["xcrun", "--sdk", profile["sdk"], "--show-sdk-path"]).strip()
    ).resolve()
    expected_platform = (
        "iPhoneSimulator.platform"
        if profile["platform"] == "IOSSIMULATOR"
        else "iPhoneOS.platform"
    )
    if not sdk_root.is_dir() or expected_platform not in sdk_root.parts:
        raise IosProfileError("xcrun returned an unexpected iOS SDK root")
    run(
        cmake_arguments(
            profile,
            source,
            build_directory,
            cmake,
            ninja,
            sdk_root=sdk_root,
        )
    )
    build_command = [cmake, "--build", build_directory, "--parallel"]
    parallel = os.environ.get("CMAKE_BUILD_PARALLEL_LEVEL")
    if parallel:
        if re.fullmatch(r"[1-9][0-9]*", parallel) is None:
            raise IosProfileError("CMAKE_BUILD_PARALLEL_LEVEL must be positive")
        build_command.append(parallel)
    build_command.extend(["--target", "linguum_translation"])
    run(build_command)
    static_archive = output / "archives" / profile_id / "liblinguum_translation.a"
    merged = merge_static_archives(build_directory, static_archive)
    reproducibility = verify_deterministic_archive_metadata(static_archive)
    architectures = macho_architectures(capture(["xcrun", "lipo", "-archs", static_archive]))
    if architectures != [profile["architecture"]]:
        raise IosProfileError("merged static archive architecture differs from the lock")
    symbols = verify_static_symbols(capture(["xcrun", "nm", "-gU", static_archive]))
    commands = verify_compile_commands(profile, build_directory)
    package = output / "translation-ios-{}-0.1.0-M1.zip".format(profile_id)
    package_profile(profile, static_archive, package)
    first_hash = file_sha256(package)
    reproduction = output / "{}.reproduction".format(package.name)
    package_profile(profile, static_archive, reproduction)
    try:
        if reproduction.read_bytes() != package.read_bytes():
            raise IosProfileError("deterministic iOS package reproduction differs")
    finally:
        reproduction.unlink(missing_ok=True)
    package_evidence = verify_profile_package(profile, package)
    executable = build_cinterop(profile, static_archive, clean)
    macho = verify_macho_identity(
        profile,
        capture(["xcrun", "lipo", "-archs", executable]),
        capture(["xcrun", "vtool", "-show-build", executable]),
    )
    return {
        "archive": str(static_archive),
        "archiveSha256": file_sha256(static_archive),
        "archiveSize": static_archive.stat().st_size,
        "cinteropExecutable": str(executable),
        "cinteropExecutableSha256": file_sha256(executable),
        "commands": commands,
        "machO": macho,
        "mergedArchives": merged,
        "package": str(package),
        "packageSha256": first_hash,
        "packageSize": package.stat().st_size,
        "packageVerified": package_evidence,
        "profile": profile,
        "reproducibility": reproducibility,
        "symbols": symbols,
    }


def source_tree_sha256() -> str:
    value = (ROOT / "native" / "SOURCE_TREE.sha256").read_text(encoding="utf-8").strip()
    match = re.fullmatch(r"([0-9a-f]{64})\s+upstream/mozilla-translations", value)
    if match is None:
        raise IosProfileError("native source tree hash file is malformed")
    return match.group(1)


def execute(
    selected_profile: str,
    output: Path,
    iterations: int,
    clean: bool,
    execution_tier: str,
) -> Dict[str, object]:
    if iterations < 1 or iterations > 1000:
        raise IosProfileError("iterations must be between 1 and 1000")
    verify_host()
    output = safe_output_directory(output)
    if clean and output.exists():
        shutil.rmtree(str(output))
    output.mkdir(parents=True, exist_ok=True)
    document = load_lock()
    profiles = profile_map(document)
    profile_ids = PROFILE_IDS if selected_profile == "all" else (selected_profile,)
    if any(profile_id not in profiles for profile_id in profile_ids):
        raise IosProfileError("unsupported iOS profile selection")
    run([sys.executable, "scripts/upstream/snapshot.py", "prepare"])
    run([sys.executable, "scripts/upstream/snapshot.py", "verify"])
    source = stage_source.stage(force=clean)
    dependencies = {"pcre2": materialize_locked_pcre2(document, source)}
    model = fetch_canary_model.fetch()
    cmake, ninja = bootstrap_tools.bootstrap()
    toolchain = toolchain_evidence(document, cmake, ninja)
    results: MutableMapping[str, object] = {}
    for profile_id in profile_ids:
        results[profile_id] = build_profile(
            profiles[profile_id], source, cmake, ninja, output, clean
        )
    execution = None
    tier_profile = {
        "simulator-arm64": "ios-simulator-arm64",
        "simulator-x64": "ios-simulator-x64",
        "physical-arm64": "ios-arm64",
    }.get(execution_tier)
    if execution_tier != "none":
        if tier_profile is None or tier_profile not in results:
            raise IosProfileError(
                "execution tier {} requires profile {} in this invocation".format(
                    execution_tier, tier_profile
                )
            )
        result = results[tier_profile]
        executable = Path(str(result["cinteropExecutable"]))
        configuration = ROOT / "testing" / "native" / "fixtures" / "es-en.yml"
        if execution_tier == "physical-arm64":
            execution = run_physical_canary(
                profiles[tier_profile], executable, model, configuration, iterations
            )
        else:
            execution = run_simulator_canary(
                profiles[tier_profile], executable, model, configuration, iterations
            )
    evidence = {
        "deploymentTarget": document["deploymentTarget"],
        "dependencies": dependencies,
        "execution": execution,
        "evidencePath": str(output / "M1-WP07-ios-evidence.json"),
        "profiles": results,
        "source": {
            "firefoxRevision": FIREFOX_REVISION,
            "sourceTreeSha256": source_tree_sha256(),
            "translationsRevision": TRANSLATIONS_REVISION,
        },
        "toolchain": toolchain,
    }
    evidence_path = output / "M1-WP07-ios-evidence.json"
    evidence_path.write_bytes(json_bytes(evidence))
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return evidence


PROFILE_ERRORS = (
    IosProfileError,
    bootstrap_tools.ToolBootstrapError,
    fetch_canary_model.ModelFetchError,
    stage_source.SourceStageError,
    json.JSONDecodeError,
    OSError,
    subprocess.SubprocessError,
    ValueError,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("all", *PROFILE_IDS), required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--clean", action="store_true")
    parser.add_argument(
        "--execution-tier",
        choices=("none", "simulator-arm64", "simulator-x64", "physical-arm64"),
        default="none",
    )
    arguments = parser.parse_args()
    try:
        execute(
            arguments.profile,
            arguments.output,
            arguments.iterations,
            arguments.clean,
            arguments.execution_tier,
        )
    except PROFILE_ERRORS as error:
        print("iOS native profile gate failed: {}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

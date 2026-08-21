#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build, inspect, package, and device-test the locked Android profiles."""

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import Dict, List, Mapping, Sequence


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
if str(SCRIPT_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIRECTORY))

import bootstrap_tools
import fetch_canary_model
import stage_source


ROOT = Path(__file__).resolve().parents[2]
LOCK_PATH = ROOT / "toolchains" / "android-native-profiles.lock.json"
DEFAULT_OUTPUT = ROOT / "build" / "native-packages" / "android"
PROFILE_IDS = ("android-arm64-v8a", "android-x86_64")
EXPECTED_NDK_VERSION = "28.2.13676358"
EXPECTED_BUILD_TOOLS_VERSION = "36.0.0"
EXPECTED_MIN_SDK = 26
EXPECTED_EMULATOR_APIS = [26, 36]
EXPECTED_PHYSICAL_LABELS = ["self-hosted", "linux", "arm64", "android-device"]
EXPECTED_ABIS = ("arm64-v8a", "x86_64")
JNI_LIBRARY_NAME = "liblinguum_translation_jni.so"
TRANSLATIONS_REVISION = "eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d"
FIREFOX_REVISION = "48d55cf7ec80093903e2ef7f58b61a84a22ef716"
CANARY_MARKER = "LINGUUM_ANDROID_CANARY_PASS"
CANARY_FAILURE_MARKER = "LINGUUM_ANDROID_CANARY_FAIL"
ANDROID_SYSTEM_LIBRARIES = {
    "libandroid.so",
    "libc.so",
    "libdl.so",
    "liblog.so",
    "libm.so",
}
DETERMINISTIC_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
AAR_METADATA_SOURCES = {
    "META-INF/LICENSE": ROOT / "LICENSE",
    "META-INF/NOTICE": ROOT / "NOTICE",
    "META-INF/THIRD_PARTY_LICENSES.md": ROOT / "THIRD_PARTY_LICENSES.md",
    "META-INF/linguum/PATCHES.yaml": ROOT / "native" / "patches" / "PATCHES.yaml",
    "META-INF/linguum/SOURCE_TREE.sha256": ROOT / "native" / "SOURCE_TREE.sha256",
    "META-INF/linguum/UPSTREAM.json": ROOT / "native" / "UPSTREAM.json",
    "META-INF/linguum/UPSTREAM_LOCK.json": ROOT / "native" / "UPSTREAM_LOCK.json",
    "META-INF/linguum/android-native-profiles.lock.json": LOCK_PATH,
}


class AndroidProfileError(RuntimeError):
    """An Android profile, artifact, or device invariant failed."""


def load_lock(path: Path = LOCK_PATH) -> Dict[str, object]:
    """Load and strictly validate the Android feasibility lock."""
    document = json.loads(path.read_text(encoding="utf-8"))
    if set(document) != {
        "schemaVersion",
        "ndkVersion",
        "buildToolsVersion",
        "minSdk",
        "emulatorApiLevels",
        "physicalArm64RunnerLabels",
        "profiles",
    }:
        raise AndroidProfileError("Android profile lock keys differ from the contract")
    if (
        document.get("schemaVersion") != 1
        or document.get("ndkVersion") != EXPECTED_NDK_VERSION
        or document.get("buildToolsVersion") != EXPECTED_BUILD_TOOLS_VERSION
        or document.get("minSdk") != EXPECTED_MIN_SDK
        or document.get("emulatorApiLevels") != EXPECTED_EMULATOR_APIS
        or document.get("physicalArm64RunnerLabels") != EXPECTED_PHYSICAL_LABELS
    ):
        raise AndroidProfileError("unsupported Android profile lock identity")
    profiles = profile_map(document)
    arm64 = profiles["android-arm64-v8a"]
    x64 = profiles["android-x86_64"]
    if (
        arm64.get("abi") != "arm64-v8a"
        or arm64.get("elfMachine") != "aarch64"
        or arm64.get("buildArch") != "armv8-a"
        or arm64.get("accelerationProfile") != "ruy-neon-arm64"
        or arm64.get("matrixMultiplicationBackend") != "Ruy"
        or arm64.get("requiredCpuFeatures") != ["ARMv8-A", "NEON"]
        or arm64.get("physicalDeviceRequired") is not True
        or arm64.get("intgemmBaselineOnly") is not False
        or arm64.get("prohibitedInstructionFamilies") != []
    ):
        raise AndroidProfileError("android-arm64-v8a differs from the locked contract")
    if (
        x64.get("abi") != "x86_64"
        or x64.get("elfMachine") != "x86_64"
        or x64.get("buildArch") != "x86-64-v2"
        or x64.get("accelerationProfile") != "intgemm-ssse3-onnx-sgemm-baseline"
        or x64.get("matrixMultiplicationBackend") != "ONNX-SGEMM"
        or x64.get("requiredCpuFeatures") != ["SSE4.2", "POPCNT"]
        or x64.get("physicalDeviceRequired") is not False
        or x64.get("intgemmBaselineOnly") is not True
        or x64.get("prohibitedInstructionFamilies") != ["AVX", "AVX2", "AVX-512"]
    ):
        raise AndroidProfileError("android-x86_64 differs from the locked contract")
    return document


def profile_map(document: Mapping[str, object]) -> Dict[str, Mapping[str, object]]:
    """Return profiles keyed by their exact locked IDs."""
    entries = document.get("profiles")
    if not isinstance(entries, list):
        raise AndroidProfileError("Android profile lock is missing profiles")
    profiles = {
        entry.get("id"): entry
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }
    if set(profiles) != set(PROFILE_IDS) or len(entries) != len(profiles):
        raise AndroidProfileError("Android profile IDs must be exact and unique")
    return profiles


def safe_output_directory(path: Path) -> Path:
    """Require generated Android state to live below, but not at, build/."""
    resolved = path.resolve()
    build = (ROOT / "build").resolve()
    if resolved == build or build not in resolved.parents:
        raise AndroidProfileError("Android output directory must be a child of build/")
    return resolved


def _host_tag() -> str:
    host = (platform.system().lower(), platform.machine().lower())
    tags = {
        ("linux", "x86_64"): "linux-x86_64",
        ("darwin", "x86_64"): "darwin-x86_64",
        ("darwin", "arm64"): "darwin-x86_64",
        ("windows", "amd64"): "windows-x86_64",
        ("windows", "x86_64"): "windows-x86_64",
    }
    try:
        return tags[host]
    except KeyError as error:
        raise AndroidProfileError("unsupported Android NDK host {} {}".format(*host)) from error


def validate_ndk(ndk: Path, host_tag: str) -> Dict[str, object]:
    """Validate the exact NDK revision and every inspection tool used by CI."""
    properties = ndk / "source.properties"
    toolchain = ndk / "build" / "cmake" / "android.toolchain.cmake"
    if not properties.is_file() or not toolchain.is_file():
        raise AndroidProfileError("Android NDK is incomplete at {}".format(ndk))
    revision_match = re.search(
        r"^Pkg\.Revision\s*=\s*([^\s]+)\s*$",
        properties.read_text(encoding="utf-8"),
        flags=re.MULTILINE,
    )
    if revision_match is None or revision_match.group(1) != EXPECTED_NDK_VERSION:
        raise AndroidProfileError("Android NDK revision must be {}".format(EXPECTED_NDK_VERSION))
    suffix = ".exe" if host_tag.startswith("windows-") else ""
    bin_directory = ndk / "toolchains" / "llvm" / "prebuilt" / host_tag / "bin"
    tools = {}
    for name in ("clang++", "llvm-nm", "llvm-objdump", "llvm-readelf", "llvm-strip"):
        executable = bin_directory / (name + suffix)
        if not executable.is_file():
            raise AndroidProfileError("Android NDK tool is missing: {}".format(executable))
        tools[name] = executable
    return {
        "root": ndk,
        "hostTag": host_tag,
        "revision": revision_match.group(1),
        "toolchain": toolchain,
        "tools": tools,
    }


def resolve_ndk(environment: Mapping[str, str] = os.environ) -> Dict[str, object]:
    """Resolve only the exact side-by-side NDK or an exact direct NDK root."""
    host_tag = _host_tag()
    candidates = []
    for variable in ("ANDROID_SDK_ROOT", "ANDROID_HOME"):
        sdk = environment.get(variable)
        if sdk:
            candidates.append(Path(sdk) / "ndk" / EXPECTED_NDK_VERSION)
    direct = environment.get("ANDROID_NDK_HOME")
    if direct:
        candidates.append(Path(direct))
    rejected = []
    for candidate in candidates:
        if candidate.is_dir():
            try:
                return validate_ndk(candidate, host_tag)
            except AndroidProfileError as error:
                rejected.append("{}: {}".format(candidate, error))
    if rejected:
        raise AndroidProfileError(
            "Android NDK {} was not found as a valid candidate; rejected {}".format(
                EXPECTED_NDK_VERSION,
                "; ".join(rejected),
            )
        )
    raise AndroidProfileError(
        "Android NDK {} was not found via ANDROID_NDK_HOME, ANDROID_SDK_ROOT, or ANDROID_HOME".format(
            EXPECTED_NDK_VERSION
        )
    )


def cmake_arguments(
    profile: Mapping[str, object],
    ndk: Mapping[str, object],
    source_directory: Path,
    build_directory: Path,
) -> Sequence[str]:
    """Create the locked, host-independent CMake configure arguments."""
    profile_id = profile.get("id")
    if profile_id not in PROFILE_IDS:
        raise AndroidProfileError("unsupported Android profile {}".format(profile_id))
    arguments = [
        "-S", str(ROOT / "native" / "runtime-build"),
        "-B", str(build_directory),
        "-G", "Ninja",
        "-DCMAKE_TOOLCHAIN_FILE={}".format(ndk["toolchain"]),
        "-DANDROID_ABI={}".format(profile["abi"]),
        "-DANDROID_PLATFORM=android-{}".format(EXPECTED_MIN_SDK),
        "-DANDROID_STL=c++_static",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        "-DBUILD_TESTING=OFF",
        "-DBUILD_ARCH={}".format(profile["buildArch"]),
        "-DLINGUUM_TRANSLATIONS_SOURCE={}".format(source_directory),
        "-DLINGUUM_TRANSLATIONS_REVISION={}".format(TRANSLATIONS_REVISION),
        "-DLINGUUM_FIREFOX_REVISION={}".format(FIREFOX_REVISION),
        "-DLINGUUM_LIBRARY_VERSION=0.1.0-M1",
        "-DLINGUUM_ACCELERATION_PROFILE={}".format(profile["accelerationProfile"]),
    ]
    if profile_id == "android-arm64-v8a":
        arguments.extend(["-DUSE_RUY=ON", "-DUSE_RUY_SGEMM=ON", "-DUSE_FBGEMM=OFF"])
    else:
        arguments.extend(
            [
                "-DLINGUUM_INTGEMM_BASELINE_ONLY=ON",
                "-DUSE_FBGEMM=OFF",
                "-DUSE_ONNX_SGEMM=ON",
                "-DCMAKE_C_FLAGS_RELEASE=-O3 -DNDEBUG -march=x86-64-v2 -mno-avx -mno-avx2",
                "-DCMAKE_CXX_FLAGS_RELEASE=-O3 -DNDEBUG -march=x86-64-v2 -mno-avx -mno-avx2",
            ]
        )
    if any("-march=native" in value for value in arguments):
        raise AndroidProfileError("host-dependent -march=native is forbidden")
    return arguments


def verify_elf_header(profile: Mapping[str, object], output: str) -> Dict[str, object]:
    """Require an ELF64 shared object for the locked target machine."""
    if "Class:" not in output or "ELF64" not in output or not re.search(r"Type:\s+DYN\b", output):
        raise AndroidProfileError("Android JNI artifact must be an ELF64 shared object")
    machine_match = re.search(r"Machine:\s+(.+?)\s*$", output, flags=re.MULTILINE)
    if machine_match is None:
        raise AndroidProfileError("Android JNI artifact has no ELF machine evidence")
    machine = machine_match.group(1).strip().lower()
    architecture = "aarch64" if machine == "aarch64" else "x86_64" if "x86-64" in machine else machine
    if architecture != profile.get("elfMachine"):
        raise AndroidProfileError(
            "Android JNI artifact is {} instead of {}".format(architecture, profile.get("elfMachine"))
        )
    return {"architecture": architecture, "elfClass": "ELF64", "sharedObject": True}


def verify_dynamic_dependencies(output: str) -> Dict[str, object]:
    """Reject build-host leakage, shared C++ runtime, rpaths, and extra dependencies."""
    if re.search(r"\((?:RPATH|RUNPATH)\)", output):
        raise AndroidProfileError("Android JNI artifact must not contain RPATH or RUNPATH")
    sonames = re.findall(r"\(SONAME\).*?\[([^]]+)\]", output)
    needed = sorted(set(re.findall(r"\(NEEDED\).*?\[([^]]+)\]", output)))
    if sonames != [JNI_LIBRARY_NAME]:
        raise AndroidProfileError("Android JNI artifact SONAME must be {}".format(JNI_LIBRARY_NAME))
    unexpected = set(needed) - ANDROID_SYSTEM_LIBRARIES
    if unexpected:
        raise AndroidProfileError("unexpected Android JNI dependencies: {}".format(sorted(unexpected)))
    if "libc++_shared.so" in needed:
        raise AndroidProfileError("Android JNI artifact must statically link the C++ runtime")
    return {"soname": sonames[0], "needed": needed, "runpathAbsent": True}


def verify_exports(output: str) -> Sequence[str]:
    """Require exactly JNI_OnLoad as the dynamic bridge entry point."""
    exports = []
    for line in output.splitlines():
        gnu = re.search(r"^[0-9a-fA-F]+\s+[TW]\s+(\S+)\s*$", line.strip())
        posix = re.search(r"^(\S+)\s+[TW]\s+[0-9a-fA-F]+(?:\s+[0-9a-fA-F]+)?$", line.strip())
        match = gnu or posix
        if match is not None:
            exports.append(match.group(1))
    exports.sort()
    if exports != ["JNI_OnLoad"]:
        raise AndroidProfileError("Android JNI exports must be exactly JNI_OnLoad: {}".format(exports))
    return exports


def verify_x64_isa(output: str) -> Dict[str, object]:
    """Reject VEX/EVEX AVX-family instructions from the emulator artifact."""
    for line in output.splitlines():
        match = re.search(r"\s([a-z][a-z0-9.]*)\s+(?:[%$*()]|[a-z0-9.-])", line.lower())
        if match is not None and match.group(1).startswith("v"):
            raise AndroidProfileError("AVX-family instruction found: {}".format(match.group(1)))
    if re.search(r"\b(?:ymm|zmm)[0-9]+\b", output.lower()):
        raise AndroidProfileError("AVX-family vector register found")
    return {"avxFamilyAbsent": True, "buildArch": "x86-64-v2"}


def verify_arm64_isa(output: str) -> Dict[str, object]:
    """Require executable Advanced SIMD/NEON evidence in the arm64 artifact."""
    neon = re.search(
        r"\b(?:fmla|fmls|fmul|fadd|add|mul|ld1|st1)\s+v[0-9]+(?:\.[0-9]+[bhsd])?",
        output.lower(),
    ) is not None
    if not neon:
        raise AndroidProfileError("arm64 Android artifact has no executable NEON evidence")
    return {"neonEvidence": True, "buildArch": "armv8-a"}


def verify_compile_commands(profile: Mapping[str, object], build_directory: Path) -> Dict[str, object]:
    """Prove target API, adapter/JNI inclusion, backend, and absence of host-native flags."""
    path = build_directory / "compile_commands.json"
    entries = json.loads(path.read_text(encoding="utf-8"))
    commands = "\n".join(str(entry.get("command", "")) for entry in entries)
    files = {Path(str(entry.get("file", ""))).resolve() for entry in entries}
    adapter = (ROOT / "native" / "mozilla-adapter" / "src" / "linguum_translation.cpp").resolve()
    jni = (ROOT / "testing" / "native" / "android_canary_jni.cpp").resolve()
    if adapter not in files or jni not in files:
        raise AndroidProfileError("Android compile database must include the adapter and JNI bridge")
    if "-march=native" in commands or "-mtune=native" in commands:
        raise AndroidProfileError("host-native compilation is forbidden")
    target = "aarch64-none-linux-android26" if profile.get("abi") == "arm64-v8a" else "x86_64-none-linux-android26"
    if target not in commands:
        raise AndroidProfileError("Android compile database does not prove target {}".format(target))
    if profile.get("abi") == "arm64-v8a":
        required = ("-DARM", "-DUSE_RUY_SGEMM=1")
        has_ruy = "-DUSE_RUY=1" in commands or any(
            "/3rd_party/ruy/ruy/" in str(entry.get("file", "")).replace("\\", "/")
            for entry in entries
        )
        if not has_ruy:
            raise AndroidProfileError("Android arm64 compile evidence is missing Ruy")
    else:
        required = ("-DUSE_ONNX_SGEMM=1", "-DUSE_INTGEMM=1", "-mno-avx")
    missing = [value for value in required if value not in commands]
    if missing:
        raise AndroidProfileError("Android backend compile evidence is missing {}".format(missing))
    return {
        "nativeApiLevel": EXPECTED_MIN_SDK,
        "hostDependentMarchNative": False,
        "adapterCompiled": True,
        "jniBridgeCompiled": True,
    }


def write_deterministic_zip(path: Path, entries: Mapping[str, bytes]) -> None:
    """Write sorted, stored ZIP entries with a constant epoch and permissions."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, DETERMINISTIC_ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, entries[name])


def package_aar(libraries: Mapping[str, Path], classes_jar: Path, output: Path) -> Path:
    """Package the exact two JNI ABIs as a deterministic one-dependency AAR."""
    if set(libraries) != set(EXPECTED_ABIS):
        raise AndroidProfileError("Android AAR libraries must contain exactly {}".format(EXPECTED_ABIS))
    if not classes_jar.is_file():
        raise AndroidProfileError("Android AAR classes.jar is missing")
    entries = {
        "AndroidManifest.xml": (
            b'<manifest xmlns:android="http://schemas.android.com/apk/res/android" '
            b'package="io.linguum.translation.internal.android" />\n'
        ),
        "classes.jar": classes_jar.read_bytes(),
    }
    for name, source in AAR_METADATA_SOURCES.items():
        if not source.is_file():
            raise AndroidProfileError("Android AAR metadata source is missing: {}".format(source))
        entries[name] = source.read_bytes()
    for abi in EXPECTED_ABIS:
        library = libraries[abi]
        if not library.is_file():
            raise AndroidProfileError("Android JNI library is missing for {}".format(abi))
        entries["jni/{}/{}".format(abi, JNI_LIBRARY_NAME)] = library.read_bytes()
    write_deterministic_zip(output, entries)
    verify_aar(output)
    return output


def verify_aar(path: Path) -> Dict[str, object]:
    """Verify exact AAR layout, deterministic metadata, and nested classes.jar."""
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        expected = [
            "AndroidManifest.xml",
            "classes.jar",
            "jni/arm64-v8a/{}".format(JNI_LIBRARY_NAME),
            "jni/x86_64/{}".format(JNI_LIBRARY_NAME),
        ] + list(AAR_METADATA_SOURCES)
        if names != sorted(expected):
            raise AndroidProfileError("Android AAR entries differ from the locked layout")
        if any(item.date_time != DETERMINISTIC_ZIP_TIMESTAMP for item in archive.infolist()):
            raise AndroidProfileError("Android AAR contains a non-deterministic timestamp")
        for name, source in AAR_METADATA_SOURCES.items():
            if archive.read(name) != source.read_bytes():
                raise AndroidProfileError("Android AAR metadata differs from {}".format(source))
        classes = archive.read("classes.jar")
    try:
        from io import BytesIO
        with zipfile.ZipFile(BytesIO(classes)) as nested:
            class_name = "io/linguum/translation/internal/android/CanaryBridge.class"
            if class_name not in nested.namelist():
                raise AndroidProfileError("Android AAR classes.jar is missing CanaryBridge")
    except zipfile.BadZipFile as error:
        raise AndroidProfileError("Android AAR classes.jar is invalid") from error
    return {"abis": list(EXPECTED_ABIS), "entries": sorted(expected), "deterministicEpoch": True}


def verify_device_properties(
    output: str,
    expected_abi: str,
    min_sdk: int,
    physical: bool,
) -> Dict[str, object]:
    """Distinguish emulator evidence from a genuine arm64 physical-device proof."""
    properties = {}
    for line in output.splitlines():
        key, separator, value = line.partition("=")
        if separator:
            properties[key.strip()] = value.strip()
    try:
        sdk = int(properties["ro.build.version.sdk"])
    except (KeyError, ValueError) as error:
        raise AndroidProfileError("Android device API property is missing or invalid") from error
    abi = properties.get("ro.product.cpu.abi")
    qemu = properties.get("ro.kernel.qemu")
    if abi != expected_abi or sdk < min_sdk:
        raise AndroidProfileError("Android device does not meet the locked ABI/API contract")
    is_physical = qemu == "0"
    if physical and (expected_abi != "arm64-v8a" or not is_physical):
        raise AndroidProfileError("physical Android proof requires arm64-v8a with ro.kernel.qemu=0")
    if not physical and qemu != "1":
        raise AndroidProfileError("Android emulator proof requires ro.kernel.qemu=1")
    return {"abi": abi, "sdk": sdk, "physical": is_physical, "qemu": qemu}


def run(command: Sequence[object], cwd: Path = ROOT, environment: Mapping[str, str] = None) -> None:
    """Run a visible command and fail closed on any non-zero status."""
    rendered = [str(part) for part in command]
    print("+ {}".format(" ".join(rendered)), flush=True)
    subprocess.run(
        rendered,
        cwd=str(cwd),
        check=True,
        env=None if environment is None else dict(environment),
    )


def capture(
    command: Sequence[object],
    cwd: Path = ROOT,
    environment: Mapping[str, str] = None,
) -> str:
    """Capture a checked command's combined output."""
    completed = subprocess.run(
        [str(part) for part in command],
        cwd=str(cwd),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=None if environment is None else dict(environment),
    )
    if completed.returncode != 0:
        raise AndroidProfileError(
            "command failed ({}): {}\n{}".format(
                completed.returncode,
                " ".join(str(part) for part in command),
                completed.stdout.strip(),
            )
        )
    return completed.stdout


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_tree_sha256() -> str:
    value = (ROOT / "native" / "SOURCE_TREE.sha256").read_text(encoding="utf-8").strip()
    match = re.fullmatch(r"([0-9a-f]{64})\s+upstream/mozilla-translations", value)
    if match is None:
        raise AndroidProfileError("native source tree hash file is malformed")
    return match.group(1)


def locate_library(build_directory: Path) -> Path:
    matches = sorted(
        path
        for path in build_directory.rglob(JNI_LIBRARY_NAME)
        if path.is_file() and not path.is_symlink()
    )
    if len(matches) != 1:
        raise AndroidProfileError(
            "expected exactly one {} under {}, found {}".format(
                JNI_LIBRARY_NAME, build_directory, matches
            )
        )
    return matches[0]


def inspect_library(
    profile: Mapping[str, object],
    library: Path,
    ndk: Mapping[str, object],
    build_directory: Path,
) -> Dict[str, object]:
    tools = ndk["tools"]
    elf = verify_elf_header(profile, capture([tools["llvm-readelf"], "-h", library]))
    dynamic = verify_dynamic_dependencies(
        capture([tools["llvm-readelf"], "-d", library])
    )
    exports = verify_exports(
        capture([tools["llvm-nm"], "-D", "--defined-only", "--format=posix", library])
    )
    disassembly = capture([tools["llvm-objdump"], "-d", library])
    isa = (
        verify_arm64_isa(disassembly)
        if profile["abi"] == "arm64-v8a"
        else verify_x64_isa(disassembly)
    )
    commands = verify_compile_commands(profile, build_directory)
    return {
        "compileCommands": commands,
        "dynamic": dynamic,
        "elf": elf,
        "exports": list(exports),
        "isa": isa,
        "sha256": file_sha256(library),
        "size": library.stat().st_size,
    }


def compile_bridge(classes_jar: Path) -> None:
    javac = shutil.which("javac")
    if javac is None:
        raise AndroidProfileError("JDK javac is required to build the Android bridge")
    classes = classes_jar.parent / "classes"
    if classes.exists():
        shutil.rmtree(str(classes))
    classes.mkdir(parents=True)
    source = (
        ROOT
        / "testing"
        / "platform-smoke"
        / "android-canary"
        / "bridge"
        / "CanaryBridge.java"
    )
    run([javac, "--release", "17", "-Xlint:all", "-Werror", "-d", classes, source])
    class_file = classes / "io" / "linguum" / "translation" / "internal" / "android" / "CanaryBridge.class"
    if not class_file.is_file():
        raise AndroidProfileError("javac did not produce CanaryBridge.class")
    write_deterministic_zip(
        classes_jar,
        {"io/linguum/translation/internal/android/CanaryBridge.class": class_file.read_bytes()},
    )


def profile_build(
    profile: Mapping[str, object],
    source: Path,
    cmake: Path,
    ninja: Path,
    ndk: Mapping[str, object],
    output: Path,
    clean: bool,
) -> Dict[str, object]:
    profile_id = str(profile["id"])
    build_directory = ROOT / "build" / "native-canary" / profile_id
    safe_output_directory(build_directory)
    if clean and build_directory.exists():
        shutil.rmtree(str(build_directory))
    arguments = [str(cmake)] + list(cmake_arguments(profile, ndk, source, build_directory))
    arguments.append("-DCMAKE_MAKE_PROGRAM={}".format(ninja))
    run(arguments)
    command: List[object] = [cmake, "--build", build_directory, "--parallel"]
    parallel_level = os.environ.get("CMAKE_BUILD_PARALLEL_LEVEL")
    if parallel_level:
        if re.fullmatch(r"[1-9][0-9]*", parallel_level) is None:
            raise AndroidProfileError("CMAKE_BUILD_PARALLEL_LEVEL must be a positive integer")
        command.append(parallel_level)
    command.extend(["--target", "linguum_translation_jni"])
    run(command)
    built_library = locate_library(build_directory)
    artifact_directory = output / "jni" / str(profile["abi"])
    artifact_directory.mkdir(parents=True, exist_ok=True)
    artifact = artifact_directory / JNI_LIBRARY_NAME
    shutil.copy2(str(built_library), str(artifact))
    run([ndk["tools"]["llvm-strip"], "--strip-unneeded", artifact])
    inspection = inspect_library(profile, artifact, ndk, build_directory)
    return {
        "artifact": artifact,
        "buildDirectory": build_directory,
        "inspection": inspection,
        "profile": profile,
    }


def prepare_consumer_assets(model_directory: Path, output: Path) -> Path:
    assets = output / "consumer-assets"
    if assets.exists():
        shutil.rmtree(str(assets))
    assets.mkdir(parents=True)
    names = (
        "model.esen.intgemm.alphas.bin",
        "lex.50.50.esen.s2t.bin",
        "vocab.esen.spm",
    )
    for name in names:
        source = model_directory / name
        if not source.is_file():
            raise AndroidProfileError("canary model asset is missing: {}".format(source))
        shutil.copy2(str(source), str(assets / name))
    shutil.copy2(
        str(ROOT / "testing" / "native" / "fixtures" / "es-en.yml"),
        str(assets / "es-en.yml"),
    )
    return assets


def build_consumer(aar: Path, assets: Path, output: Path) -> Path:
    project = ROOT / "testing" / "platform-smoke" / "android-canary"
    environment = dict(os.environ)
    environment["LINGUUM_ANDROID_AAR"] = str(aar)
    environment["LINGUUM_ANDROID_ASSETS"] = str(assets)
    environment["LINGUUM_ANDROID_APK_OUTPUT"] = str(output / "consumer-build")
    run(
        [
            ROOT / "gradlew",
            "--no-daemon",
            "-p",
            project,
            "clean",
            ":app:assembleDebug",
            "--warning-mode=fail",
        ],
        environment=environment,
    )
    matches = sorted((output / "consumer-build").rglob("*.apk"))
    if len(matches) != 1:
        raise AndroidProfileError("clean Android consumer must produce exactly one APK: {}".format(matches))
    return matches[0]


def adb_command(serial: str, *arguments: str) -> List[str]:
    adb = shutil.which("adb")
    if adb is None:
        sdk = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
        candidate = Path(sdk) / "platform-tools" / "adb" if sdk else None
        if candidate is None or not candidate.is_file():
            raise AndroidProfileError("adb is required for Android device proof")
        adb = str(candidate)
    command = [adb]
    if serial:
        command.extend(["-s", serial])
    command.extend(arguments)
    return command


def resolve_device_serial(requested: str) -> str:
    if requested:
        return requested
    output = capture(adb_command("", "devices"))
    devices = [
        line.split("\t", 1)[0]
        for line in output.splitlines()[1:]
        if line.endswith("\tdevice")
    ]
    if len(devices) != 1:
        raise AndroidProfileError(
            "Android device proof requires exactly one authorized device or --device-serial: {}".format(
                devices
            )
        )
    return devices[0]


def device_properties(serial: str) -> str:
    values = []
    for name in ("ro.product.cpu.abi", "ro.build.version.sdk", "ro.kernel.qemu"):
        value = capture(adb_command(serial, "shell", "getprop", name)).strip()
        values.append("{}={}".format(name, value))
    return "\n".join(values) + "\n"


def run_device_canary(
    apk: Path,
    mode: str,
    serial: str,
    iterations: int,
) -> Dict[str, object]:
    serial = resolve_device_serial(serial)
    expected_abi = "arm64-v8a" if mode == "physical" else "x86_64"
    properties = verify_device_properties(
        device_properties(serial),
        expected_abi,
        EXPECTED_MIN_SDK,
        physical=mode == "physical",
    )
    run(adb_command(serial, "logcat", "-c"))
    run(adb_command(serial, "install", "-r", "-t", apk))
    component = "io.linguum.translation.canary/.CanaryActivity"
    run(
        adb_command(
            serial,
            "shell",
            "am",
            "start",
            "-W",
            "-n",
            component,
            "--ei",
            "iterations",
            str(iterations),
        )
    )
    deadline = time.monotonic() + 600.0
    last_output = ""
    while time.monotonic() < deadline:
        last_output = capture(
            adb_command(
                serial,
                "logcat",
                "-d",
                "-s",
                "LinguumAndroidCanary:I",
                "*:S",
            )
        )
        if CANARY_FAILURE_MARKER in last_output:
            raise AndroidProfileError("Android canary reported failure:\n{}".format(last_output))
        if CANARY_MARKER in last_output:
            break
        time.sleep(1.0)
    else:
        raise AndroidProfileError("Android canary timed out:\n{}".format(last_output))
    run(adb_command(serial, "shell", "am", "force-stop", "io.linguum.translation.canary"))
    return {
        "iterations": iterations,
        "marker": CANARY_MARKER,
        "mode": mode,
        "properties": properties,
        "serial": serial,
    }


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def execute(
    selected: str,
    output: Path,
    iterations: int,
    clean: bool,
    device_mode: str,
    device_serial_value: str,
) -> Dict[str, object]:
    if iterations < 1 or iterations > 100:
        raise AndroidProfileError("iterations must be between 1 and 100")
    output = safe_output_directory(output)
    if clean and output.exists():
        shutil.rmtree(str(output))
    run([sys.executable, "scripts/upstream/snapshot.py", "prepare"])
    run([sys.executable, "scripts/upstream/snapshot.py", "verify"])
    document = load_lock()
    profiles = profile_map(document)
    profile_ids = PROFILE_IDS if selected == "all" else (selected,)
    if device_mode != "none" and set(profile_ids) != set(PROFILE_IDS):
        raise AndroidProfileError("device proof requires --profile all and the exact two-ABI AAR")
    source = stage_source.stage(force=clean)
    model = fetch_canary_model.fetch()
    cmake, ninja = bootstrap_tools.bootstrap()
    ndk = resolve_ndk()
    builds = [
        profile_build(profiles[profile_id], source, cmake, ninja, ndk, output, clean)
        for profile_id in profile_ids
    ]
    summary: Dict[str, object] = {
        "buildToolsVersion": document["buildToolsVersion"],
        "cmake": capture([cmake, "--version"]).splitlines()[0],
        "minSdk": document["minSdk"],
        "ndkVersion": ndk["revision"],
        "ninja": capture([ninja, "--version"]).strip(),
        "profiles": {
            str(build["profile"]["id"]): build["inspection"] for build in builds
        },
        "source": {
            "firefoxRevision": FIREFOX_REVISION,
            "sourceTreeSha256": source_tree_sha256(),
            "translationsRevision": TRANSLATIONS_REVISION,
        },
    }
    if set(profile_ids) == set(PROFILE_IDS):
        classes_jar = output / "classes.jar"
        compile_bridge(classes_jar)
        libraries = {str(build["profile"]["abi"]): build["artifact"] for build in builds}
        aar = output / "translation-android-0.1.0-M1.aar"
        package_aar(libraries, classes_jar, aar)
        reproduction = output / "translation-android-0.1.0-M1.reproduction.aar"
        try:
            package_aar(libraries, classes_jar, reproduction)
            if aar.read_bytes() != reproduction.read_bytes():
                raise AndroidProfileError("deterministic Android AAR reproduction differs")
        finally:
            reproduction.unlink(missing_ok=True)
        assets = prepare_consumer_assets(model, output)
        apk = build_consumer(aar, assets, output)
        summary["aar"] = {
            "path": str(aar),
            "sha256": file_sha256(aar),
            "size": aar.stat().st_size,
            "verified": verify_aar(aar),
        }
        summary["consumer"] = {
            "apk": str(apk),
            "sha256": file_sha256(apk),
            "oneDependency": True,
        }
        if device_mode != "none":
            summary["device"] = run_device_canary(
                apk, device_mode, device_serial_value, iterations
            )
    evidence_path = output / "M1-WP06-android-evidence.json"
    summary["evidencePath"] = str(evidence_path)
    write_json(evidence_path, summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


PROFILE_ERRORS = (
    AndroidProfileError,
    bootstrap_tools.ToolBootstrapError,
    fetch_canary_model.ModelFetchError,
    stage_source.SourceStageError,
    json.JSONDecodeError,
    OSError,
    subprocess.SubprocessError,
    ValueError,
    zipfile.BadZipFile,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=PROFILE_IDS + ("all",), required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--clean", action="store_true")
    parser.add_argument(
        "--device-mode", choices=("none", "emulator", "physical"), default="none"
    )
    parser.add_argument("--device-serial", default=os.environ.get("LINGUUM_ANDROID_DEVICE_SERIAL", ""))
    arguments = parser.parse_args()
    try:
        execute(
            arguments.profile,
            arguments.output,
            arguments.iterations,
            arguments.clean,
            arguments.device_mode,
            arguments.device_serial,
        )
    except PROFILE_ERRORS as error:
        print("Android native profile gate failed: {}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

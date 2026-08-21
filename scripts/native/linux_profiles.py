#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build, inspect, run, package, and compatibility-test locked Linux profiles."""

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
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

SCRIPT_DIRECTORY = Path(__file__).resolve().parent
if str(SCRIPT_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIRECTORY))

import run_host_canary


ROOT = Path(__file__).resolve().parents[2]
LOCK_PATH = ROOT / "toolchains" / "linux-native-profiles.lock.json"
DEFAULT_OUTPUT = ROOT / "build" / "native-packages" / "linux"
PROFILE_IDS = ("linux-x64-avx2", "linux-x64-baseline", "linux-arm64")
COMPATIBILITY_MANIFEST_KEYS = {
    "abi",
    "canaryMode",
    "canarySha256",
    "librarySha256",
    "profile",
    "schemaVersion",
    "sourceTreeSha256",
}
EXPECTED_RUNNERS = {
    "linux-x64-avx2": "ubuntu-22.04",
    "linux-x64-baseline": "ubuntu-22.04",
    "linux-arm64": "ubuntu-22.04-arm",
}
SYSTEM_LIBRARIES = {
    "ld-linux-aarch64.so.1",
    "ld-linux-x86-64.so.2",
    "libc.so.6",
    "libdl.so.2",
    "libgcc_s.so.1",
    "libm.so.6",
    "libpthread.so.0",
    "librt.so.1",
    "libstdc++.so.6",
}
NON_AVX_V_MNEMONICS = {"verr", "verw", "vmcall", "vmlaunch", "vmresume", "vmxoff"}


class LinuxProfileError(RuntimeError):
    """A Linux profile build or evidence invariant failed."""


def load_lock(path: Path = LOCK_PATH) -> Dict[str, object]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if (
        document.get("schemaVersion") != 1
        or document.get("buildBaseline") != "ubuntu-22.04"
        or document.get("glibcFloor") != "2.35"
        or document.get("compatibilityRunners") != ["ubuntu-22.04", "ubuntu-24.04"]
        or document.get("sanitizers") != ["address", "undefined"]
    ):
        raise LinuxProfileError("unsupported Linux profile lock identity")
    toolchain = document.get("toolchain")
    profiles = document.get("profiles")
    if not isinstance(toolchain, dict) or not isinstance(profiles, list):
        raise LinuxProfileError("Linux profile lock is missing toolchain or profiles")
    if set(toolchain) != {
        "compilerVendor",
        "compilerSelection",
        "binutilsSelection",
        "cmake",
        "ninja",
    }:
        raise LinuxProfileError("Linux profile toolchain keys differ from the contract")
    if (
        toolchain.get("compilerVendor") != "GNU"
        or toolchain.get("compilerSelection") != "runner-default"
        or toolchain.get("binutilsSelection") != "runner-default"
    ):
        raise LinuxProfileError("Linux toolchain selection is not supported")
    by_id = {
        profile.get("id"): profile
        for profile in profiles
        if isinstance(profile, dict)
    }
    if tuple(sorted(by_id)) != tuple(sorted(PROFILE_IDS)) or len(profiles) != len(by_id):
        raise LinuxProfileError("Linux profile IDs must be exact and unique")
    for profile_id, architecture, namespace, build_arch in (
        ("linux-x64-avx2", "x86_64", "x86_64/avx2", "haswell"),
        ("linux-x64-baseline", "x86_64", "x86_64/baseline", "nehalem"),
        ("linux-arm64", "aarch64", "aarch64/ruy", "armv8-a"),
    ):
        profile = by_id[profile_id]
        if (
            profile.get("runner") != EXPECTED_RUNNERS[profile_id]
            or profile.get("architecture") != architecture
            or profile.get("binaryNamespace") != namespace
            or profile.get("buildArch") != build_arch
        ):
            raise LinuxProfileError("{} differs from the locked contract".format(profile_id))
    optimized = by_id["linux-x64-avx2"]
    if (
        optimized.get("accelerationProfile") != "fbgemm-intgemm-avx2"
        or optimized.get("matrixMultiplicationBackend") != "FBGEMM"
        or optimized.get("requiredCpuFeatures") != ["AVX2"]
        or optimized.get("intgemmMaximumCpu") != "AVX2"
        or optimized.get("fbgemm") is not True
    ):
        raise LinuxProfileError("Linux optimized profile must be the locked AVX2 path")
    baseline = by_id["linux-x64-baseline"]
    if (
        baseline.get("accelerationProfile")
        != "intgemm-ssse3-onnx-sgemm-baseline"
        or baseline.get("fbgemm") is not False
        or baseline.get("onnxSgemm") is not True
        or baseline.get("intgemmBaselineOnly") is not True
        or baseline.get("intgemmMaximumCpu") != "SSSE3"
        or "AVX" not in baseline.get("prohibitedInstructionFamilies", [])
    ):
        raise LinuxProfileError("Linux fallback profile must exclude AVX-family code")
    arm64 = by_id["linux-arm64"]
    if (
        arm64.get("accelerationProfile") != "ruy-neon-arm64"
        or arm64.get("matrixMultiplicationBackend") != "Ruy"
        or arm64.get("quantizedBackend") != "Ruy"
        or arm64.get("ruy") is not True
        or arm64.get("realArm64Execution") is not True
        or arm64.get("requiredCpuFeatures") != ["ARMv8-A", "NEON"]
    ):
        raise LinuxProfileError("Linux arm64 must use the locked real Ruy/NEON path")
    return document


def profile_map(document: Mapping[str, object]) -> Dict[str, Mapping[str, object]]:
    return {str(profile["id"]): profile for profile in document["profiles"]}


def safe_output_directory(path: Path) -> Path:
    resolved = path.resolve()
    build_root = (ROOT / "build").resolve()
    try:
        resolved.relative_to(build_root)
    except ValueError as error:
        raise LinuxProfileError(
            "Linux package output must be below {}".format(build_root)
        ) from error
    if resolved == build_root:
        raise LinuxProfileError("Linux package output cannot be the build root")
    return resolved


def capture(command: Sequence[str], env: Mapping[str, str] = None) -> str:
    completed = subprocess.run(
        list(command),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=None if env is None else dict(env),
    )
    if completed.returncode != 0:
        raise LinuxProfileError(
            "command failed ({}): {}\n{}".format(
                completed.returncode, command, completed.stdout.strip()
            )
        )
    return completed.stdout


def parse_os_release(contents: str) -> Dict[str, str]:
    values = {}
    for line in contents.splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        values[name] = value.strip().strip('"')
    return values


def parse_glibc_version(output: str) -> Tuple[int, int]:
    match = re.fullmatch(r"\s*(?:glibc|GNU libc)\s+([0-9]+)\.([0-9]+)\s*", output)
    if match is None:
        raise LinuxProfileError("GNU glibc version output could not be parsed")
    return int(match.group(1)), int(match.group(2))


def host_cpu_features() -> List[str]:
    cpuinfo = Path("/proc/cpuinfo")
    if not cpuinfo.is_file():
        raise LinuxProfileError("/proc/cpuinfo is required for native CPU evidence")
    values = set()
    for line in cpuinfo.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.lower().startswith(("flags", "features")) and ":" in line:
            values.update(line.split(":", 1)[1].lower().split())
    if not values:
        raise LinuxProfileError("host CPU features could not be parsed")
    return sorted(values)


def verify_host(
    profile: Mapping[str, object], require_build_baseline: bool
) -> Dict[str, object]:
    if platform.system().lower() != "linux":
        raise LinuxProfileError("Linux is required")
    machine = platform.machine().lower()
    normalized = (
        "x86_64" if machine in {"x86_64", "amd64"}
        else "aarch64" if machine in {"aarch64", "arm64"}
        else machine
    )
    if normalized != profile["architecture"]:
        raise LinuxProfileError(
            "{} execution requires {}, found {}".format(
                profile["id"], profile["architecture"], normalized
            )
        )
    release_path = Path("/etc/os-release")
    if not release_path.is_file():
        raise LinuxProfileError("/etc/os-release is required")
    release = parse_os_release(release_path.read_text(encoding="utf-8"))
    version = release.get("VERSION_ID")
    if release.get("ID") != "ubuntu" or version not in {"22.04", "24.04"}:
        raise LinuxProfileError("Ubuntu 22.04 or 24.04 is required")
    if require_build_baseline and version != "22.04":
        raise LinuxProfileError("release Linux artifacts must be built on Ubuntu 22.04")
    glibc = parse_glibc_version(capture(["getconf", "GNU_LIBC_VERSION"]))
    if glibc < (2, 35):
        raise LinuxProfileError("glibc 2.35 or newer is required for execution")
    if require_build_baseline and glibc != (2, 35):
        raise LinuxProfileError("Ubuntu 22.04 build evidence must use glibc 2.35")
    features = host_cpu_features()
    if profile["id"] == "linux-x64-avx2" and "avx2" not in features:
        raise LinuxProfileError("linux-x64-avx2 requires host AVX2 execution")
    if profile["id"] == "linux-arm64" and not ({"asimd", "neon"} & set(features)):
        raise LinuxProfileError("linux-arm64 requires real NEON/ASIMD execution")
    return {
        "architecture": normalized,
        "cpuFeatures": features,
        "distribution": release.get("ID"),
        "distributionVersion": version,
        "glibc": "{}.{}".format(*glibc),
    }


def toolchain_evidence(toolchain: Mapping[str, object]) -> Dict[str, object]:
    cmake, ninja = run_host_canary.bootstrap_tools.bootstrap()
    cmake_version = capture([str(cmake), "--version"]).splitlines()[0]
    ninja_version = capture([str(ninja), "--version"]).strip()
    if cmake_version != "cmake version {}".format(toolchain["cmake"]):
        raise LinuxProfileError("CMake does not match the Linux profile lock")
    if ninja_version != toolchain["ninja"]:
        raise LinuxProfileError("Ninja does not match the Linux profile lock")
    compiler = shutil.which("c++")
    if compiler is None:
        raise LinuxProfileError("the runner-default GNU C++ compiler is unavailable")
    compiler_banner = capture([compiler, "--version"])
    compiler_identity = compiler_banner.lower()
    if (
        "clang" in compiler_identity
        or not any(
            marker in compiler_identity
            for marker in ("g++", "gcc", "free software foundation", "c++ (ubuntu")
        )
    ):
        raise LinuxProfileError("the selected compiler is not GNU C++")
    compiler_version = capture([compiler, "-dumpfullversion", "-dumpversion"]).strip()
    if re.fullmatch(r"[0-9]+(?:\.[0-9]+)+", compiler_version) is None:
        raise LinuxProfileError("GNU compiler version could not be parsed")
    readelf = shutil.which("readelf")
    objdump = shutil.which("objdump")
    if readelf is None or objdump is None:
        raise LinuxProfileError("GNU readelf and objdump are required")
    binutils_line = capture([readelf, "--version"]).splitlines()[0]
    if "GNU readelf" not in binutils_line:
        raise LinuxProfileError("the selected ELF inspector is not GNU readelf")
    return {
        **toolchain,
        "binutilsVersionLine": binutils_line,
        "cmakeVersionLine": cmake_version,
        "compilerExecutable": compiler,
        "compilerVersion": compiler_version,
        "hostArchitecture": platform.machine().lower(),
        "ninjaVersion": ninja_version,
        "objdumpVersionLine": capture([objdump, "--version"]).splitlines()[0],
    }


def parse_required_symbol_versions(output: str) -> Dict[str, List[str]]:
    versions = {"GLIBC": set(), "GLIBCXX": set(), "CXXABI": set()}
    for family, version in re.findall(
        r"\b(GLIBCXX|GLIBC|CXXABI)_([0-9]+(?:\.[0-9]+)+)\b", output
    ):
        versions[family].add(version)
    return {
        family: sorted(values, key=lambda value: tuple(int(part) for part in value.split(".")))
        for family, values in versions.items()
    }


def verify_symbol_version_ceilings(
    versions: Mapping[str, Sequence[str]], glibc_floor: str
) -> Dict[str, object]:
    glibc = list(versions.get("GLIBC", []))
    if not glibc:
        raise LinuxProfileError("ELF version requirements contain no GLIBC identity")
    maximum = max(glibc, key=lambda value: tuple(int(part) for part in value.split(".")))
    ceiling = tuple(int(part) for part in glibc_floor.split("."))
    if tuple(int(part) for part in maximum.split(".")) > ceiling:
        raise LinuxProfileError(
            "required GLIBC_{} exceeds the GLIBC_{} build ceiling".format(
                maximum, glibc_floor
            )
        )
    glibcxx = list(versions.get("GLIBCXX", []))
    cxxabi = list(versions.get("CXXABI", []))
    return {
        "maximumRequiredGlibc": maximum,
        "maximumRequiredGlibcxx": glibcxx[-1] if glibcxx else None,
        "maximumRequiredCxxabi": cxxabi[-1] if cxxabi else None,
        "requiredVersions": {key: list(value) for key, value in versions.items()},
    }


def parse_dynamic_dependencies(
    output: str, sanitizer_libraries: Sequence[str] = ()
) -> Dict[str, object]:
    sonames = re.findall(r"\(SONAME\).*?\[([^]]+)\]", output)
    if sonames != ["liblinguum_translation.so"]:
        raise LinuxProfileError("ELF SONAME must be exactly liblinguum_translation.so")
    needed = sorted(set(re.findall(r"\(NEEDED\).*?\[([^]]+)\]", output)))
    allowed = SYSTEM_LIBRARIES | set(sanitizer_libraries)
    unexpected = set(needed) - allowed
    if unexpected:
        raise LinuxProfileError(
            "non-system shared library dependencies found: {}".format(sorted(unexpected))
        )
    has_search_path = re.search(r"\((?:RPATH|RUNPATH)\)", output) is not None
    if has_search_path:
        raise LinuxProfileError("release ELF must not contain RPATH or RUNPATH")
    return {
        "hasRuntimeSearchPath": False,
        "needed": needed,
        "soname": sonames[0],
    }


def verify_ldd(output: str) -> List[Dict[str, str]]:
    if "not found" in output.lower():
        raise LinuxProfileError("ldd reports an unresolved dependency")
    dependencies = []
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("linux-vdso.so"):
            continue
        if "=>" in stripped:
            name, target = (part.strip() for part in stripped.split("=>", 1))
            resolved = target.split(" (", 1)[0].strip()
        else:
            resolved = stripped.split(" (", 1)[0].strip()
            name = Path(resolved).name
        if not resolved.startswith(("/lib/", "/lib64/", "/usr/lib/", "/usr/lib64/")):
            raise LinuxProfileError(
                "dependency {} resolves outside system library roots: {}".format(name, resolved)
            )
        dependencies.append({"name": name, "resolved": resolved})
    if not dependencies:
        raise LinuxProfileError("ldd produced no resolved system dependencies")
    return dependencies


def verify_elf_header(profile: Mapping[str, object], output: str) -> Dict[str, object]:
    fields = {}
    for name in ("Class", "Type", "Machine"):
        match = re.search(r"^\s*{}:\s*(.+?)\s*$".format(name), output, re.MULTILINE)
        if match is None:
            raise LinuxProfileError("ELF header is missing {}".format(name))
        fields[name] = match.group(1)
    if fields["Class"] != "ELF64" or not fields["Type"].startswith("DYN"):
        raise LinuxProfileError("native artifact must be an ELF64 shared object")
    architecture = (
        "x86_64" if fields["Machine"] == "Advanced Micro Devices X86-64"
        else "aarch64" if fields["Machine"] == "AArch64"
        else "unknown"
    )
    if architecture != profile["architecture"]:
        raise LinuxProfileError(
            "ELF architecture differs: expected {}, got {}".format(
                profile["architecture"], architecture
            )
        )
    return {"architecture": architecture, "class": fields["Class"], "type": fields["Type"]}


def instruction_records(disassembly: str) -> List[Tuple[str, str, str, str]]:
    records = []
    pattern = re.compile(
        r"^\s*[0-9A-Fa-f]+:\s+((?:(?:[0-9A-Fa-f]{2}\s+)+|[0-9A-Fa-f]{8}\s+))"
        r"([A-Za-z][A-Za-z0-9.]*)\s*(.*)$"
    )
    for line in disassembly.splitlines():
        match = pattern.match(line)
        if match:
            records.append(
                (match.group(2).lower(), match.group(3).lower(), line.strip(), match.group(1).strip())
            )
    return records


def avx_records(
    records: Iterable[Tuple[str, str, str, str]]
) -> List[Tuple[str, str, str, str]]:
    return [
        record
        for record in records
        if (
            (record[0].startswith("v") and record[0] not in NON_AVX_V_MNEMONICS)
            or re.search(r"\b[yz]mm[0-9]+\b|\{k[0-7]\}", record[1])
        )
    ]


def verify_x64_isa(profile_id: str, disassembly: str) -> Dict[str, object]:
    records = instruction_records(disassembly)
    if not records:
        raise LinuxProfileError("objdump produced no disassembly records")
    avx = avx_records(records)
    avx512 = [
        record
        for record in avx
        if record[3].lower().startswith("62 ")
        or re.search(r"\bzmm[0-9]+\b|\{k[0-7]\}", record[1])
    ]
    if profile_id == "linux-x64-baseline" and avx:
        raise LinuxProfileError(
            "baseline ELF contains {} AVX-family instructions; first records: {}".format(
                len(avx), "; ".join(record[2] for record in avx[:20])
            )
        )
    if profile_id == "linux-x64-avx2" and avx512:
        raise LinuxProfileError(
            "AVX2 ELF contains {} AVX-512/EVEX instructions; first records: {}".format(
                len(avx512), "; ".join(record[2] for record in avx512[:20])
            )
        )
    avx2 = [
        record
        for record in avx
        if re.search(r"\bymm[0-9]+\b", record[1])
        and record[0].startswith(("vp", "vgather"))
    ]
    if profile_id == "linux-x64-avx2" and not avx2:
        raise LinuxProfileError("optimized ELF has no executable AVX2 evidence")
    return {
        "disassembledInstructionCount": len(records),
        "avxFamilyInstructionCount": len(avx),
        "avx2Evidence": [record[2] for record in avx2[:20]],
        "avx512InstructionCount": len(avx512),
        "baselineAvxFamilyAbsent": profile_id != "linux-x64-baseline" or not avx,
    }


def verify_arm64_isa(disassembly: str) -> Dict[str, object]:
    records = instruction_records(disassembly)
    if not records:
        raise LinuxProfileError("objdump produced no arm64 disassembly records")
    neon = [
        record
        for record in records
        if re.search(r"\bv[0-9]+\.(?:[0-9]+)?[bhsd]\b|\bq[0-9]+\b", record[1])
        or record[0] in {"sdot", "udot", "fmla", "fmul", "addv", "saddlv"}
    ]
    if not neon:
        raise LinuxProfileError("arm64 ELF has no executable NEON/ASIMD evidence")
    return {
        "disassembledInstructionCount": len(records),
        "neonEvidence": [record[2] for record in neon[:20]],
    }


def verify_compile_commands(
    profile: Mapping[str, object], build_directory: Path
) -> Dict[str, object]:
    path = build_directory / "compile_commands.json"
    commands = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(commands, list) or not commands:
        raise LinuxProfileError("compile_commands.json must contain commands")
    texts = [
        str(entry.get("command", " ".join(entry.get("arguments", []))))
        for entry in commands
    ]
    if any("-march=native" in text for text in texts):
        raise LinuxProfileError("host-dependent -march=native is forbidden")
    expected_arch = str(profile["buildArch"])
    march_commands = [text for text in texts if "-march=" in text]
    if not march_commands or not all("-march={}".format(expected_arch) in text for text in march_commands):
        raise LinuxProfileError("compile commands do not use the locked BUILD_ARCH")
    marian = [
        text
        for entry, text in zip(commands, texts)
        if "/marian-fork/" in str(entry.get("file", "")).replace("\\", "/")
    ]
    adapter_source = (
        ROOT / "native" / "mozilla-adapter" / "src" / "linguum_translation.cpp"
    ).resolve()
    adapter = [
        text
        for entry, text in zip(commands, texts)
        if Path(str(entry.get("file", ""))).resolve() == adapter_source
    ]
    if not marian or len(adapter) != 1:
        raise LinuxProfileError("compile evidence is missing Marian or the native adapter")
    acceleration = str(profile["accelerationProfile"])
    if (
        'LINGUUM_ACCELERATION_PROFILE=\\"{}\\"'.format(acceleration) not in adapter[0]
        and 'LINGUUM_ACCELERATION_PROFILE=\"{}\"'.format(acceleration) not in adapter[0]
    ):
        raise LinuxProfileError("native adapter acceleration identity differs from the lock")
    combined = "\n".join(marian)
    profile_id = str(profile["id"])
    has_fbgemm = "USE_FBGEMM=1" in combined
    has_onnx = "USE_ONNX_SGEMM=1" in combined
    has_intgemm = "USE_INTGEMM=1" in combined
    has_arm = re.search(r"(?:^|\s)-DARM(?:=1)?(?:\s|$)", combined) is not None
    has_ruy_sources = any(
        "/3rd_party/ruy/ruy/" in str(entry.get("file", "")).replace("\\", "/")
        for entry in commands
    )
    has_ruy = "USE_RUY_SGEMM=1" in combined and (
        "USE_RUY=1" in combined or has_ruy_sources
    )
    if profile_id == "linux-x64-avx2" and not (has_fbgemm and has_intgemm):
        raise LinuxProfileError("optimized compile commands do not prove FBGEMM and intgemm")
    if profile_id == "linux-x64-baseline" and (has_fbgemm or not has_onnx or not has_intgemm):
        raise LinuxProfileError("baseline compile commands do not prove ONNX SGEMM/intgemm fallback")
    if profile_id == "linux-arm64" and (not has_arm or not has_ruy or has_fbgemm):
        raise LinuxProfileError("arm64 compile commands do not prove ARM/NEON/Ruy selection")
    sanitizer_flags = sorted(
        set(
            match.group(1)
            for text in texts
            for match in re.finditer(r"-fsanitize=([^\s]+)", text)
        )
    )
    return {
        "buildArch": expected_arch,
        "compileCommandCount": len(commands),
        "compileCommandsSha256": run_host_canary.file_sha256(path),
        "hasArmPath": has_arm,
        "hasFbgemm": has_fbgemm,
        "hasIntgemm": has_intgemm,
        "hasOnnxSgemm": has_onnx,
        "hasRuy": has_ruy,
        "hasRuySources": has_ruy_sources,
        "hostDependentMarchNative": False,
        "sanitizerFlags": sanitizer_flags,
    }


def source_tree_sha256() -> str:
    value = (ROOT / "native" / "SOURCE_TREE.sha256").read_text(encoding="utf-8").strip()
    match = re.fullmatch(r"([0-9a-f]{64})\s+upstream/mozilla-translations", value)
    if match is None:
        raise LinuxProfileError("native source tree hash file is malformed")
    return match.group(1)


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


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


def sanitizer_runtime_libraries(sanitizers: Sequence[str]) -> List[str]:
    libraries = []
    if "address" in sanitizers:
        libraries.extend(["libasan.so.6", "libasan.so.8"])
    if "undefined" in sanitizers:
        libraries.extend(["libubsan.so.1"])
    if "thread" in sanitizers:
        libraries.extend(["libtsan.so.0", "libtsan.so.2"])
    return libraries


def verify_library(
    profile: Mapping[str, object],
    library: Path,
    sanitizers: Sequence[str] = (),
) -> Dict[str, object]:
    elf = verify_elf_header(profile, capture(["readelf", "-h", str(library)]))
    dynamic = parse_dynamic_dependencies(
        capture(["readelf", "-d", str(library)]),
        sanitizer_runtime_libraries(sanitizers),
    )
    symbol_versions = verify_symbol_version_ceilings(
        parse_required_symbol_versions(capture(["readelf", "--version-info", str(library)])),
        "2.35",
    )
    dependencies = verify_ldd(capture(["ldd", str(library)]))
    exports = run_host_canary.verify_exports(library)
    disassembly = capture(["objdump", "-d", str(library)])
    isa = (
        verify_x64_isa(str(profile["id"]), disassembly)
        if profile["architecture"] == "x86_64"
        else verify_arm64_isa(disassembly)
    )
    return {
        "dependencies": dependencies,
        "dynamic": dynamic,
        "elf": elf,
        "exports": exports,
        "isaAudit": isa,
        "symbolVersions": symbol_versions,
    }


def locate_canary(build_directory: Path) -> Path:
    matches = sorted(
        path
        for path in build_directory.rglob("linguum_translation_canary")
        if path.is_file()
    )
    if len(matches) != 1:
        raise LinuxProfileError("expected exactly one Linux canary executable")
    return matches[0]


def create_compatibility_bundle(
    profile: Mapping[str, object], result: Mapping[str, object], output: Path
) -> Dict[str, object]:
    bundle = output / "compatibility" / str(profile["id"])
    if bundle.exists():
        shutil.rmtree(str(bundle))
    bundle.mkdir(parents=True)
    library = Path(str(result["artifact"]))
    canary = locate_canary(Path(str(result["buildDirectory"])))
    library_copy = bundle / "liblinguum_translation.so"
    canary_copy = bundle / "linguum_translation_canary"
    shutil.copy2(str(library), str(library_copy))
    shutil.copy2(str(canary), str(canary_copy))
    canary_copy.chmod(0o755)
    manifest = {
        "schemaVersion": 1,
        "profile": profile,
        "abi": result["abi"],
        "canaryMode": "0755",
        "canarySha256": run_host_canary.file_sha256(canary_copy),
        "librarySha256": run_host_canary.file_sha256(library_copy),
        "sourceTreeSha256": source_tree_sha256(),
    }
    (bundle / "compatibility.json").write_bytes(json_bytes(manifest))
    return {"directory": str(bundle), **manifest}


def verify_compatibility_manifest(
    manifest: Mapping[str, object], profile: Mapping[str, object]
) -> None:
    if set(manifest) != COMPATIBILITY_MANIFEST_KEYS:
        raise LinuxProfileError("compatibility manifest keys differ from the contract")
    if (
        manifest.get("schemaVersion") != 1
        or manifest.get("profile") != profile
        or manifest.get("abi") != "1.0"
        or manifest.get("canaryMode") != "0755"
        or manifest.get("sourceTreeSha256") != source_tree_sha256()
    ):
        raise LinuxProfileError("compatibility manifest differs from the locked profile")
    for name in ("canarySha256", "librarySha256"):
        value = manifest.get(name)
        if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
            raise LinuxProfileError("compatibility manifest has an invalid {}".format(name))


def restore_compatibility_canary_mode(
    canary: Path, manifest: Mapping[str, object]
) -> None:
    if manifest.get("canaryMode") != "0755":
        raise LinuxProfileError("compatibility canary mode is not authenticated")
    canary.chmod(0o755)
    if canary.stat().st_mode & 0o777 != 0o755:
        raise LinuxProfileError("compatibility canary executable mode could not be restored")


def package_profile(
    result: Mapping[str, object],
    profile: Mapping[str, object],
    toolchain: Mapping[str, object],
    host: Mapping[str, object],
    output: Path,
) -> Dict[str, object]:
    library = Path(str(result["artifact"]))
    build_directory = Path(str(result["buildDirectory"]))
    if result["cmake"] != "cmake version {}".format(toolchain["cmake"]):
        raise LinuxProfileError("build CMake does not match the Linux profile lock")
    if result["ninja"] != toolchain["ninja"]:
        raise LinuxProfileError("build Ninja does not match the Linux profile lock")
    commands = verify_compile_commands(profile, build_directory)
    inspection = verify_library(profile, library)
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
            "exactMatch": True,
            "iterations": result["iterations"],
            "languagePair": "es-en",
        },
        "commands": commands,
        "host": host,
        "inspection": inspection,
        "source": {
            "firefoxRevision": result["firefoxRevision"],
            "sourceTreeSha256": source_tree_sha256(),
            "translationsRevision": result["translationsRevision"],
        },
        "toolchain": toolchain,
    }
    metadata_root = "META-INF/linguum/native"
    binary_path = "linguum/native/linux/{}/liblinguum_translation.so".format(
        profile["binaryNamespace"]
    )
    entries = {
        "META-INF/MANIFEST.MF": b"Manifest-Version: 1.0\r\nCreated-By: Linguum Translation M1\r\n\r\n",
        "META-INF/LICENSE": (ROOT / "LICENSE").read_bytes(),
        "META-INF/NOTICE": (ROOT / "NOTICE").read_bytes(),
        "META-INF/THIRD_PARTY_LICENSES.md": (ROOT / "THIRD_PARTY_LICENSES.md").read_bytes(),
        "META-INF/licenses/MPL-2.0.txt": (
            ROOT / "native" / "upstream" / "mozilla-translations" / "LICENSE"
        ).read_bytes(),
        "{}/profile.json".format(metadata_root): json_bytes(manifest),
        "{}/UPSTREAM.json".format(metadata_root): (ROOT / "native" / "UPSTREAM.json").read_bytes(),
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
    profile_id = str(profile["id"])
    jar = output / "linguum-translation-native-{}-0.1.0-M1.jar".format(profile_id)
    create_jar(jar, entries)
    first_hash = run_host_canary.file_sha256(jar)
    reproduction = output / "{}.reproduction".format(jar.name)
    try:
        create_jar(reproduction, entries)
        if run_host_canary.file_sha256(reproduction) != first_hash:
            raise LinuxProfileError("deterministic JAR reproduction differs")
    finally:
        reproduction.unlink(missing_ok=True)
    compatibility = create_compatibility_bundle(profile, result, output)
    return {
        "compatibility": compatibility,
        "jar": str(jar),
        "jarSha256": first_hash,
        "jarSize": jar.stat().st_size,
        "manifest": manifest,
        "profile": profile_id,
        "reproducibleJar": True,
        "sharedObjectSha256": result["artifactSha256"],
    }


def sanitizer_environment(sanitizers: Sequence[str]) -> Dict[str, str]:
    environment = dict(os.environ)
    # Sanitizer instrumentation materially increases peak compiler memory.
    # Keep clean hosted builds below the standard-runner memory ceiling.
    environment["CMAKE_BUILD_PARALLEL_LEVEL"] = "2"
    if "address" in sanitizers:
        environment["ASAN_OPTIONS"] = "detect_leaks=1:halt_on_error=1:strict_string_checks=1"
    if "undefined" in sanitizers:
        environment["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
    if "thread" in sanitizers:
        environment["TSAN_OPTIONS"] = "halt_on_error=1:second_deadlock_stack=1"
    return environment


def execute_build(
    profile_id: str,
    output: Path,
    iterations: int,
    clean: bool,
    sanitizers: Sequence[str],
) -> Dict[str, object]:
    document = load_lock()
    profiles = profile_map(document)
    if profile_id not in profiles:
        raise LinuxProfileError("unsupported Linux profile: {}".format(profile_id))
    profile = profiles[profile_id]
    host = verify_host(profile, require_build_baseline=True)
    tools = toolchain_evidence(document["toolchain"])
    suffix = "-{}".format("-".join(sanitizers)) if sanitizers else ""
    build_directory = ROOT / "build" / "native-canary" / "{}{}".format(profile_id, suffix)
    additional = []
    previous_environment = dict(os.environ)
    try:
        if sanitizers:
            sanitizer_value = ",".join(sanitizers)
            if sanitizer_value not in {"address,undefined", "thread"}:
                raise LinuxProfileError("unsupported sanitizer selection: {}".format(sanitizer_value))
            additional.append("-DLINGUUM_SANITIZERS={}".format(sanitizer_value))
            selected_environment = sanitizer_environment(sanitizers)
            os.environ.clear()
            os.environ.update(selected_environment)
        result = run_host_canary.execute(
            build_directory,
            iterations,
            clean,
            profile_id,
            additional,
        )
    finally:
        if sanitizers:
            os.environ.clear()
            os.environ.update(previous_environment)
    commands = verify_compile_commands(profile, build_directory)
    inspection = verify_library(profile, Path(str(result["artifact"])), sanitizers)
    if sanitizers:
        expected_flag = ",".join(sanitizers)
        if expected_flag not in commands["sanitizerFlags"]:
            raise LinuxProfileError("compile commands do not prove the requested sanitizers")
        summary = {
            "profile": profile_id,
            "sanitizers": list(sanitizers),
            "canaryIterations": result["iterations"],
            "commands": commands,
            "host": host,
            "inspection": inspection,
            "toolchain": tools,
        }
    else:
        package = package_profile(result, profile, tools, host, output)
        summary = {"profile": package, "toolchain": tools}
    output.mkdir(parents=True, exist_ok=True)
    qualifier = "-{}".format("-".join(sanitizers)) if sanitizers else ""
    result_path = output / "M1-WP05-{}{}-result.json".format(profile_id, qualifier)
    result_path.write_bytes(json_bytes(summary))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def execute_verify_only(
    profile_id: str, bundle: Path, iterations: int
) -> Dict[str, object]:
    document = load_lock()
    profiles = profile_map(document)
    if profile_id not in profiles:
        raise LinuxProfileError("unsupported Linux profile: {}".format(profile_id))
    profile = profiles[profile_id]
    host = verify_host(profile, require_build_baseline=False)
    bundle = bundle.resolve()
    manifest_path = bundle / "compatibility.json"
    library = bundle / "liblinguum_translation.so"
    canary = bundle / "linguum_translation_canary"
    if not manifest_path.is_file() or not library.is_file() or not canary.is_file():
        raise LinuxProfileError("compatibility bundle is incomplete")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise LinuxProfileError("compatibility manifest must be an object")
    verify_compatibility_manifest(manifest, profile)
    if run_host_canary.file_sha256(library) != manifest.get("librarySha256"):
        raise LinuxProfileError("compatibility shared-object digest differs")
    if run_host_canary.file_sha256(canary) != manifest.get("canarySha256"):
        raise LinuxProfileError("compatibility canary digest differs")
    # upload-artifact/download-artifact intentionally normalizes regular files
    # to 0644. Restore only the authenticated executable mode after verifying
    # the transported bytes, then execute the exact canary.
    restore_compatibility_canary_mode(canary, manifest)
    inspection = verify_library(profile, library)
    model = run_host_canary.fetch_canary_model.fetch()
    environment = dict(os.environ)
    environment["LD_LIBRARY_PATH"] = str(bundle)
    capture(
        [
            str(canary),
            str(model),
            str(ROOT / "testing" / "native" / "fixtures" / "es-en.yml"),
            str(iterations),
        ],
        environment,
    )
    summary = {
        "artifactBuiltOn": "ubuntu-22.04",
        "canaryIterations": iterations,
        "host": host,
        "inspection": inspection,
        "profile": profile_id,
        "verifiedBundle": str(bundle),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


PROFILE_ERRORS = (
    LinuxProfileError,
    run_host_canary.HostCanaryError,
    OSError,
    subprocess.SubprocessError,
    ValueError,
    json.JSONDecodeError,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=PROFILE_IDS, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--sanitizers", default="")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--artifact", type=Path)
    arguments = parser.parse_args()
    if arguments.iterations < 1 or arguments.iterations > 1000:
        parser.error("--iterations must be between 1 and 1000")
    if arguments.verify_only != (arguments.artifact is not None):
        parser.error("--verify-only and --artifact must be supplied together")
    sanitizers = tuple(value for value in arguments.sanitizers.split(",") if value)
    try:
        if arguments.verify_only:
            if sanitizers:
                raise LinuxProfileError("verify-only compatibility runs do not accept sanitizers")
            execute_verify_only(arguments.profile, arguments.artifact, arguments.iterations)
        else:
            execute_build(
                arguments.profile,
                safe_output_directory(arguments.output),
                arguments.iterations,
                arguments.clean,
                sanitizers,
            )
    except PROFILE_ERRORS as error:
        print("Linux native profile gate failed: {}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build, inspect, and package the locked M1 Windows native profiles."""

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
LOCK_PATH = ROOT / "toolchains" / "windows-native-profiles.lock.json"
DEFAULT_OUTPUT = ROOT / "build" / "native-packages" / "windows"
PROFILE_IDS = ("windows-x64-avx2", "windows-x64-baseline")
SYSTEM_DLLS = {
    "ADVAPI32.DLL",
    "BCRYPT.DLL",
    "KERNEL32.DLL",
    "OLE32.DLL",
    "SHELL32.DLL",
    "SHLWAPI.DLL",
    "USER32.DLL",
    "VERSION.DLL",
    "WS2_32.DLL",
}
NON_AVX_V_MNEMONICS = {"verr", "verw", "vmcall", "vmlaunch", "vmresume", "vmxoff"}


class WindowsProfileError(RuntimeError):
    """A Windows profile build or evidence invariant failed."""


def load_lock(path: Path = LOCK_PATH) -> Dict[str, object]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schemaVersion") != 1 or document.get("runner") != "windows-2025":
        raise WindowsProfileError("unsupported Windows profile lock identity")
    toolchain = document.get("toolchain")
    profiles = document.get("profiles")
    if not isinstance(toolchain, dict) or not isinstance(profiles, list):
        raise WindowsProfileError("Windows profile lock is missing toolchain or profiles")
    required_tools = {
        "visualStudio", "visualStudioVersion", "msvcToolset", "compiler",
        "windowsSdk", "cmake", "ninja"
    }
    if set(toolchain) != required_tools:
        raise WindowsProfileError("Windows profile toolchain keys differ from the contract")
    by_id = {profile.get("id"): profile for profile in profiles if isinstance(profile, dict)}
    if tuple(sorted(by_id)) != tuple(sorted(PROFILE_IDS)) or len(profiles) != len(by_id):
        raise WindowsProfileError("Windows profile IDs must be exact and unique")
    if by_id["windows-x64-avx2"].get("requiredCpuFeatures") != ["AVX2"]:
        raise WindowsProfileError("optimized Windows profile must require AVX2")
    baseline = by_id["windows-x64-baseline"]
    if baseline.get("fbgemm") is not False or baseline.get("intgemmBaselineOnly") is not True:
        raise WindowsProfileError("baseline profile must exclude FBGEMM and high intgemm kernels")
    return document


def safe_output_directory(path: Path) -> Path:
    resolved = path.resolve()
    build_root = (ROOT / "build").resolve()
    try:
        resolved.relative_to(build_root)
    except ValueError as error:
        raise WindowsProfileError("Windows package output must be below {}".format(build_root)) from error
    if resolved == build_root:
        raise WindowsProfileError("Windows package output cannot be the build root")
    return resolved


def capture(command: Sequence[str], allow_failure: bool = False) -> str:
    completed = subprocess.run(
        list(command),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if completed.returncode != 0 and not allow_failure:
        raise WindowsProfileError(
            "command failed ({}): {}\n{}".format(
                completed.returncode, command, completed.stdout.strip()
            )
        )
    return completed.stdout


def parse_environment(output: str) -> Dict[str, str]:
    environment = {}
    for line in output.splitlines():
        if "=" not in line or line.startswith("="):
            continue
        name, value = line.split("=", 1)
        if name:
            environment[name] = value
    return environment


def vswhere_arguments(
    toolchain: Mapping[str, object], property_name: str = "installationPath"
) -> List[str]:
    versions = {"2022": "[17.0,18.0)", "2026": "[18.0,19.0)"}
    version_range = versions.get(str(toolchain.get("visualStudio")))
    if version_range is None:
        raise WindowsProfileError("unsupported Visual Studio lock identity")
    return [
        "-products", "*", "-version", version_range, "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", property_name,
    ]


def activate_msvc(toolchain: Mapping[str, object]) -> Dict[str, str]:
    if os.name != "nt":
        raise WindowsProfileError("MSVC activation requires Windows")
    program_files = os.environ.get("ProgramFiles(x86)")
    if not program_files:
        raise WindowsProfileError("ProgramFiles(x86) is unavailable")
    vswhere = Path(program_files) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    installation = capture([str(vswhere)] + vswhere_arguments(toolchain)).strip()
    installation_version = capture(
        [str(vswhere)] + vswhere_arguments(toolchain, "installationVersion")
    ).strip()
    if installation_version != toolchain["visualStudioVersion"]:
        raise WindowsProfileError(
            "Visual Studio mismatch: expected {}, got {}".format(
                toolchain["visualStudioVersion"], installation_version
            )
        )
    vcvars = Path(installation) / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
    command = 'call "{}" -vcvars_ver=14.44 -winsdk={} >nul && set'.format(
        vcvars, toolchain["windowsSdk"]
    )
    environment = parse_environment(capture(["cmd.exe", "/d", "/s", "/c", command]))
    os.environ.update(environment)
    actual_toolset = environment.get("VCToolsVersion", "").rstrip("\\/")
    actual_sdk = environment.get("WindowsSDKVersion", "").rstrip("\\/")
    if actual_toolset != toolchain["msvcToolset"]:
        raise WindowsProfileError(
            "MSVC toolset mismatch: expected {}, got {}".format(
                toolchain["msvcToolset"], actual_toolset
            )
        )
    if actual_sdk != toolchain["windowsSdk"]:
        raise WindowsProfileError(
            "Windows SDK mismatch: expected {}, got {}".format(toolchain["windowsSdk"], actual_sdk)
        )
    compiler_output = capture(["cl.exe"], allow_failure=True)
    match = re.search(r"Compiler Version ([0-9.]+) for x64", compiler_output)
    if match is None or match.group(1) != toolchain["compiler"]:
        raise WindowsProfileError("MSVC compiler identity does not match the lock")
    for executable in ("cl.exe", "dumpbin.exe", "link.exe"):
        if shutil.which(executable) is None:
            raise WindowsProfileError("{} is unavailable after MSVC activation".format(executable))
    return {
        "compiler": match.group(1),
        "msvcToolset": actual_toolset,
        "visualStudioInstallation": installation,
        "visualStudioVersion": installation_version,
        "windowsSdk": actual_sdk,
    }


def instruction_records(disassembly: str) -> List[Tuple[str, str, str]]:
    records = []
    pattern = re.compile(r"^\s*[0-9A-Fa-f`]+:\s+([A-Za-z][A-Za-z0-9.]*)\s*(.*)$")
    for line in disassembly.splitlines():
        match = pattern.match(line)
        if match:
            records.append((match.group(1).lower(), match.group(2).lower(), line.strip()))
    return records


def avx_records(records: Iterable[Tuple[str, str, str]]) -> List[Tuple[str, str, str]]:
    return [
        record for record in records
        if (
            (record[0].startswith("v") and record[0] not in NON_AVX_V_MNEMONICS)
            or re.search(r"\b[yz]mm[0-9]+\b|\{k[0-7]\}", record[1])
        )
    ]


def verify_isa(profile_id: str, disassembly: str) -> Dict[str, object]:
    records = instruction_records(disassembly)
    if not records:
        raise WindowsProfileError("dumpbin produced no disassembly records")
    avx = avx_records(records)
    if profile_id == "windows-x64-baseline" and avx:
        raise WindowsProfileError("baseline DLL contains AVX-family instructions")
    avx2 = [
        record for record in avx
        if "ymm" in record[1] and (record[0].startswith("vp") or record[0].startswith("vgather"))
    ]
    if profile_id == "windows-x64-avx2" and not avx2:
        raise WindowsProfileError("optimized DLL has no executable AVX2 evidence")
    evidence = avx2 if profile_id == "windows-x64-avx2" else []
    return {
        "disassembledInstructionCount": len(records),
        "avxFamilyInstructionCount": len(avx),
        "avx2Evidence": [record[2] for record in evidence[:20]],
        "baselineAvxFamilyAbsent": profile_id != "windows-x64-baseline" or not avx,
    }


def parse_dependencies(output: str) -> List[str]:
    dependencies = sorted({
        match.group(1).upper()
        for line in output.splitlines()
        for match in [re.fullmatch(r"\s*([A-Za-z0-9_.-]+\.dll)\s*", line, re.IGNORECASE)]
        if match is not None
    })
    unexpected = set(dependencies) - SYSTEM_DLLS
    if unexpected:
        raise WindowsProfileError("non-system DLL dependencies found: {}".format(sorted(unexpected)))
    return dependencies


def verify_compile_commands(profile_id: str, build_directory: Path) -> Dict[str, object]:
    path = build_directory / "compile_commands.json"
    commands = json.loads(path.read_text(encoding="utf-8"))
    command_text = "\n".join(
        entry.get("command", " ".join(entry.get("arguments", []))) for entry in commands
    )
    has_avx2 = re.search(r"(?:^|\s)/arch:AVX2(?:\s|$)", command_text, re.IGNORECASE) is not None
    has_sse2 = re.search(r"(?:^|\s)/arch:SSE2(?:\s|$)", command_text, re.IGNORECASE) is not None
    if profile_id == "windows-x64-avx2" and not has_avx2:
        raise WindowsProfileError("optimized compiler commands do not contain /arch:AVX2")
    if profile_id == "windows-x64-baseline" and (has_avx2 or not has_sse2):
        raise WindowsProfileError("baseline compiler commands are not restricted to /arch:SSE2")
    return {
        "compileCommandCount": len(commands),
        "compileCommandsSha256": run_host_canary.file_sha256(path),
        "hasArchAvx2": has_avx2,
        "hasArchSse2": has_sse2,
    }


def profile_map(document: Mapping[str, object]) -> Dict[str, Mapping[str, object]]:
    return {profile["id"]: profile for profile in document["profiles"]}


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def create_jar(path: Path, entries: Mapping[str, bytes]) -> None:
    partial = path.with_name(path.name + ".part")
    partial.unlink(missing_ok=True)
    with zipfile.ZipFile(str(partial), "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as jar:
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
    exports = sorted(result["exports"])
    expected_cmake = "cmake version {}".format(toolchain["cmake"])
    if result["cmake"] != expected_cmake or result["ninja"] != toolchain["ninja"]:
        raise WindowsProfileError("packaged build tools do not match the Windows profile lock")
    disassembly = capture(["dumpbin.exe", "/nologo", "/DISASM:NOBYTES", str(library)])
    isa = verify_isa(profile_id, disassembly)
    dependencies = parse_dependencies(
        capture(["dumpbin.exe", "/nologo", "/DEPENDENTS", str(library)])
    )
    headers = capture(["dumpbin.exe", "/nologo", "/HEADERS", str(library)])
    if re.search(r"\b8664 machine \(x64\)", headers, re.IGNORECASE) is None:
        raise WindowsProfileError("DLL is not PE x64")
    commands = verify_compile_commands(profile_id, build_directory)
    manifest = {
        "schemaVersion": 1,
        "profile": profile,
        "abi": result["abi"],
        "artifact": {
            "fileName": library.name,
            "sha256": result["artifactSha256"],
            "size": library.stat().st_size,
        },
        "canary": {"languagePair": "es-en", "iterations": result["iterations"], "exactMatch": True},
        "commands": commands,
        "dependencies": dependencies,
        "exports": exports,
        "isaAudit": isa,
        "source": {
            "firefoxRevision": result["firefoxRevision"],
            "translationsRevision": result["translationsRevision"],
            "sourceTreeSha256": (ROOT / "native" / "SOURCE_TREE.sha256").read_text().strip(),
        },
        "toolchain": toolchain,
    }
    profile_suffix = profile_id.removeprefix("windows-x64-")
    binary_path = "linguum/native/windows/x86_64/{}/linguum_translation.dll".format(profile_suffix)
    metadata_root = "META-INF/linguum/native"
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
        "{}/UPSTREAM_LOCK.json".format(metadata_root): (ROOT / "native" / "UPSTREAM_LOCK.json").read_bytes(),
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
    return {
        "dllSha256": result["artifactSha256"],
        "jar": str(jar),
        "jarSha256": run_host_canary.file_sha256(jar),
        "jarSize": jar.stat().st_size,
        "manifest": manifest,
        "profile": profile_id,
    }


def execute(output: Path, iterations: int, clean: bool) -> Dict[str, object]:
    if platform.system().lower() != "windows" or platform.machine().lower() not in {"amd64", "x86_64"}:
        raise WindowsProfileError("Windows x64 is required")
    output = safe_output_directory(output)
    document = load_lock()
    toolchain = document["toolchain"]
    activated = activate_msvc(toolchain)
    toolchain_evidence = dict(toolchain)
    toolchain_evidence.update(activated)
    if clean and output.exists():
        shutil.rmtree(str(output))
    packages = []
    profiles = profile_map(document)
    for profile_id in PROFILE_IDS:
        result = run_host_canary.execute(
            ROOT / "build" / "native-canary" / profile_id,
            iterations,
            clean,
            profile_id,
        )
        packages.append(package_profile(result, profiles[profile_id], toolchain_evidence, output))
    summary = {"profiles": packages, "toolchain": toolchain_evidence}
    (output / "M1-WP03-result.json").write_bytes(json_bytes(summary))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--clean", action="store_true")
    arguments = parser.parse_args()
    try:
        execute(arguments.output, arguments.iterations, arguments.clean)
    except (
        WindowsProfileError,
        run_host_canary.HostCanaryError,
        OSError,
        subprocess.SubprocessError,
        ValueError,
        json.JSONDecodeError,
    ) as error:
        print("Windows native profile gate failed: {}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

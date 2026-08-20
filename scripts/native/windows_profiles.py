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
import tempfile
import zipfile
from bisect import bisect_right
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

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
    "API-MS-WIN-CRT-CONIO-L1-1-0.DLL",
    "API-MS-WIN-CRT-CONVERT-L1-1-0.DLL",
    "API-MS-WIN-CRT-ENVIRONMENT-L1-1-0.DLL",
    "API-MS-WIN-CRT-FILESYSTEM-L1-1-0.DLL",
    "API-MS-WIN-CRT-HEAP-L1-1-0.DLL",
    "API-MS-WIN-CRT-LOCALE-L1-1-0.DLL",
    "API-MS-WIN-CRT-MATH-L1-1-0.DLL",
    "API-MS-WIN-CRT-MULTIBYTE-L1-1-0.DLL",
    "API-MS-WIN-CRT-PRIVATE-L1-1-0.DLL",
    "API-MS-WIN-CRT-PROCESS-L1-1-0.DLL",
    "API-MS-WIN-CRT-RUNTIME-L1-1-0.DLL",
    "API-MS-WIN-CRT-STDIO-L1-1-0.DLL",
    "API-MS-WIN-CRT-STRING-L1-1-0.DLL",
    "API-MS-WIN-CRT-TIME-L1-1-0.DLL",
    "API-MS-WIN-CRT-UTILITY-L1-1-0.DLL",
    "BCRYPT.DLL",
    "DBGHELP.DLL",
    "KERNEL32.DLL",
    "OLE32.DLL",
    "SHELL32.DLL",
    "SHLWAPI.DLL",
    "USER32.DLL",
    "UCRTBASE.DLL",
    "VERSION.DLL",
    "WS2_32.DLL",
}
BASELINE_SCALAR_SHIM_SYMBOLS = {
    "__std_find_trivial_1",
    "__std_find_trivial_2",
    "__std_reverse_trivially_swappable_1",
    "memcpy",
    "memmove",
    "memset",
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
        "visualStudio", "visualStudioVersions", "msvcToolset", "compiler",
        "windowsSdk", "cmake", "ninja"
    }
    if set(toolchain) != required_tools:
        raise WindowsProfileError("Windows profile toolchain keys differ from the contract")
    visual_studio_versions = toolchain["visualStudioVersions"]
    if (
        not isinstance(visual_studio_versions, list)
        or not visual_studio_versions
        or len(set(visual_studio_versions)) != len(visual_studio_versions)
        or not all(isinstance(version, str) and version for version in visual_studio_versions)
    ):
        raise WindowsProfileError("Visual Studio versions must be a non-empty unique string list")
    by_id = {profile.get("id"): profile for profile in profiles if isinstance(profile, dict)}
    if tuple(sorted(by_id)) != tuple(sorted(PROFILE_IDS)) or len(profiles) != len(by_id):
        raise WindowsProfileError("Windows profile IDs must be exact and unique")
    optimized = by_id["windows-x64-avx2"]
    if (
        optimized.get("requiredCpuFeatures") != ["AVX2"]
        or optimized.get("intgemmMaximumCpu") != "AVX2"
    ):
        raise WindowsProfileError("optimized Windows profile must cap intgemm at AVX2")
    baseline = by_id["windows-x64-baseline"]
    if (
        baseline.get("fbgemm") is not False
        or baseline.get("intgemmBaselineOnly") is not True
        or baseline.get("intgemmMaximumCpu") != "SSSE3"
    ):
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


def environment_value(environment: Mapping[str, str], name: str) -> str:
    """Read a Windows environment variable without assuming output key casing."""
    matches = [value for key, value in environment.items() if key.casefold() == name.casefold()]
    if len(matches) != 1:
        related = sorted(
            key for key in environment
            if key.upper().startswith(("VC", "WINDOWSSDK"))
        )
        raise WindowsProfileError(
            "Windows environment variable {} is unavailable or ambiguous; "
            "related variables: {}".format(name, related)
        )
    return matches[0]


def compiler_version(output: str) -> str:
    match = re.search(r"Compiler Version ([0-9.]+) for x64", output, re.IGNORECASE)
    if match is None:
        banner = " ".join(output.split())[:240]
        raise WindowsProfileError("unrecognized MSVC compiler banner: {!r}".format(banner))
    return match.group(1)


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


def vcvars_script(vcvars: Path, toolchain: Mapping[str, object]) -> str:
    toolset_directory = vcvars.parents[2] / "Tools" / "MSVC"
    return (
        "@call \"{}\" {} -vcvars_ver={}\r\n"
        "@set \"LINGUUM_VCVARS_EXIT=%errorlevel%\"\r\n"
        "@if not \"%LINGUUM_VCVARS_EXIT%\"==\"0\" goto :vcvars_failed\r\n"
        "@if not defined VCToolsVersion goto :toolset_missing\r\n"
        "@if not defined WindowsSDKVersion goto :sdk_missing\r\n"
        "@set\r\n"
        "@exit /b 0\r\n"
        ":vcvars_failed\r\n"
        "@echo LINGUUM_VCVARS_FAILED exit=%LINGUUM_VCVARS_EXIT%\r\n"
        "@exit /b 81\r\n"
        ":toolset_missing\r\n"
        "@echo LINGUUM_VCVARS_MISSING_VCTOOLSVERSION installed-toolsets:\r\n"
        "@dir /b \"{}\" 2>nul\r\n"
        "@exit /b 82\r\n"
        ":sdk_missing\r\n"
        "@echo LINGUUM_VCVARS_MISSING_WINDOWSSDKVERSION\r\n"
        "@exit /b 83\r\n"
    ).format(
        vcvars,
        toolchain["windowsSdk"],
        toolchain["msvcToolset"],
        toolset_directory,
    )


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
    if installation_version not in toolchain["visualStudioVersions"]:
        raise WindowsProfileError(
            "Visual Studio mismatch: expected one of {}, got {}".format(
                toolchain["visualStudioVersions"], installation_version
            )
        )
    vcvars = Path(installation) / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
    with tempfile.TemporaryDirectory(prefix="linguum-msvc-") as temporary:
        activation = Path(temporary) / "activate.cmd"
        activation.write_text(vcvars_script(vcvars, toolchain), encoding="utf-8", newline="")
        environment = parse_environment(capture(["cmd.exe", "/d", "/c", str(activation)]))
    os.environ.update(environment)
    actual_toolset = environment_value(environment, "VCToolsVersion").rstrip("\\/")
    actual_sdk = environment_value(environment, "WindowsSDKVersion").rstrip("\\/")
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
    actual_compiler = compiler_version(compiler_output)
    if actual_compiler != toolchain["compiler"]:
        raise WindowsProfileError(
            "MSVC compiler mismatch: expected {}, got {}".format(
                toolchain["compiler"], actual_compiler
            )
        )
    for executable in ("cl.exe", "dumpbin.exe", "link.exe"):
        if shutil.which(executable) is None:
            raise WindowsProfileError("{} is unavailable after MSVC activation".format(executable))
    return {
        "compiler": actual_compiler,
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


def avx_diagnostics(
    disassembly: str,
    records: Sequence[Tuple[str, str, str]],
    linker_symbols: Sequence[Tuple[int, str, str]] = (),
    limit: int = 20,
) -> List[str]:
    wanted = {record[2] for record in records[:limit]}
    diagnostics = []
    current_symbol = "<unknown-symbol>"
    instruction_pattern = re.compile(r"^\s*[0-9A-Fa-f`]+:\s+[A-Za-z][A-Za-z0-9.]*")
    for line in disassembly.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if instruction_pattern.match(line):
            if stripped in wanted:
                address_match = re.match(r"^\s*([0-9A-Fa-f`]+):", line)
                mapped_symbol = None
                if address_match is not None and linker_symbols:
                    address = int(address_match.group(1).replace("`", ""), 16)
                    mapped_symbol = linker_symbol_at(address, linker_symbols)
                diagnostics.append("{} -> {}".format(mapped_symbol or current_symbol, stripped))
            continue
        if stripped.endswith(":"):
            current_symbol = stripped[:-1]
    return diagnostics


def parse_linker_map(contents: str) -> List[Tuple[int, str, str]]:
    """Return function addresses, names, and defining objects from an MSVC map."""
    symbols = []
    pattern = re.compile(
        r"^\s*[0-9A-Fa-f]+:[0-9A-Fa-f]+\s+"
        r"(?P<name>\S+)\s+(?P<address>[0-9A-Fa-f`]{8,17})\s+"
        r"(?:(?P<flags>[fi](?:\s+[fi])*)\s+)?(?P<source>\S.*)\s*$",
        re.IGNORECASE,
    )
    for line in contents.splitlines():
        match = pattern.match(line)
        if match is None:
            continue
        flags = (match.group("flags") or "").casefold().split()
        if "f" not in flags:
            continue
        symbols.append((
            int(match.group("address").replace("`", ""), 16),
            match.group("name"),
            match.group("source").strip(),
        ))
    symbols = sorted(set(symbols))
    if not symbols:
        raise WindowsProfileError("MSVC linker map contains no function symbols")
    return symbols


def linker_symbol_at(
    address: int,
    symbols: Sequence[Tuple[int, str, str]],
) -> Optional[str]:
    """Resolve an instruction to the closest preceding mapped function."""
    index = bisect_right([symbol[0] for symbol in symbols], address) - 1
    if index < 0:
        return None
    symbol_address, name, source = symbols[index]
    return "{} [{}] +0x{:x}".format(name, source, address - symbol_address)


def avx_provenance(
    records: Sequence[Tuple[str, str, str]],
    symbols: Sequence[Tuple[int, str, str]],
    limit: int = 25,
) -> Dict[str, object]:
    """Summarize every rejected instruction by closest mapped symbol/object."""
    addresses = [symbol[0] for symbol in symbols]
    source_counts = Counter()
    symbol_counts = Counter()
    unmapped_count = 0
    for _, _, line in records:
        address_match = re.match(r"^\s*([0-9A-Fa-f`]+):", line)
        if address_match is None:
            unmapped_count += 1
            continue
        address = int(address_match.group(1).replace("`", ""), 16)
        index = bisect_right(addresses, address) - 1
        if index < 0:
            unmapped_count += 1
            continue
        _, name, source = symbols[index]
        source_counts[source] += 1
        symbol_counts[(name, source)] += 1

    ordered_sources = sorted(
        source_counts.items(), key=lambda item: (-item[1], item[0])
    )
    ordered_symbols = sorted(
        symbol_counts.items(), key=lambda item: (-item[1], item[0][1], item[0][0])
    )
    return {
        "mappedInstructionCount": sum(source_counts.values()),
        "sourceCount": len(ordered_sources),
        "sources": [
            {"instructionCount": count, "source": source}
            for source, count in ordered_sources[:limit]
        ],
        "sourcesOmitted": max(0, len(ordered_sources) - limit),
        "symbolCount": len(ordered_symbols),
        "symbols": [
            {"instructionCount": count, "source": source, "symbol": name}
            for (name, source), count in ordered_symbols[:limit]
        ],
        "symbolsOmitted": max(0, len(ordered_symbols) - limit),
        "unmappedInstructionCount": unmapped_count,
    }


def verify_isa(
    profile_id: str,
    disassembly: str,
    linker_symbols: Sequence[Tuple[int, str, str]] = (),
) -> Dict[str, object]:
    records = instruction_records(disassembly)
    if not records:
        raise WindowsProfileError("dumpbin produced no disassembly records")
    avx = avx_records(records)
    if profile_id == "windows-x64-baseline" and avx:
        provenance = avx_provenance(avx, linker_symbols) if linker_symbols else None
        raise WindowsProfileError(
            "baseline DLL contains {} AVX-family instructions; provenance: {}; "
            "first records: {}".format(
                len(avx),
                json.dumps(provenance, sort_keys=True, separators=(",", ":"))
                if provenance is not None else "unavailable",
                "; ".join(avx_diagnostics(disassembly, avx, linker_symbols)),
            )
        )
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


def baseline_runtime_boundary_evidence(
    symbols: Sequence[Tuple[int, str, str]],
) -> Dict[str, object]:
    shim_sources = {
        name: source
        for _, name, source in symbols
        if name in BASELINE_SCALAR_SHIM_SYMBOLS
        and "baseline_runtime_shims.c.obj" in source.casefold()
    }
    missing = BASELINE_SCALAR_SHIM_SYMBOLS - set(shim_sources)
    if missing:
        raise WindowsProfileError(
            "baseline scalar runtime boundary is missing symbols: {}".format(sorted(missing))
        )
    vector_algorithms = sorted({
        name
        for _, name, source in symbols
        if "vector_algorithms.obj" in source.casefold()
    })
    if vector_algorithms:
        raise WindowsProfileError(
            "baseline still links the static STL vector-algorithm object: {}".format(
                vector_algorithms
            )
        )
    return {
        "scalarShimCount": len(shim_sources),
        "scalarShimSymbols": sorted(shim_sources),
        "staticStlVectorAlgorithmsAbsent": True,
    }


def verify_compile_commands(profile_id: str, build_directory: Path) -> Dict[str, object]:
    path = build_directory / "compile_commands.json"
    commands = json.loads(path.read_text(encoding="utf-8"))
    command_texts = [
        entry.get("command", " ".join(entry.get("arguments", []))) for entry in commands
    ]
    command_text = "\n".join(command_texts)
    cpp_command_texts = [
        text
        for entry, text in zip(commands, command_texts)
        if str(entry.get("file", "")).replace("\\", "/").lower().endswith(
            (".cc", ".cpp", ".cxx", ".c++")
        )
    ]
    if not cpp_command_texts:
        raise WindowsProfileError("compile database contains no C++ commands")
    intgemm_command_texts = [
        text
        for entry, text in zip(commands, command_texts)
        if str(entry.get("file", "")).replace("\\", "/").lower().endswith(
            "/3rd_party/intgemm/intgemm/intgemm.cc"
        )
    ]
    if len(intgemm_command_texts) != 1:
        raise WindowsProfileError("compile database must contain exactly one intgemm.cc command")
    prod_command_texts = [
        text
        for entry, text in zip(commands, command_texts)
        if str(entry.get("file", "")).replace("\\", "/").lower().endswith(
            "/marian-fork/src/tensors/cpu/prod.cpp"
        )
    ]
    onnx_gemm_command_texts = [
        text
        for entry, text in zip(commands, command_texts)
        if str(entry.get("file", "")).replace("\\", "/").lower().endswith(
            "/onnxjs/src/wasm-ops/gemm.cpp"
        )
    ]
    if len(prod_command_texts) != 1 or len(onnx_gemm_command_texts) != 1:
        raise WindowsProfileError(
            "compile database must contain the native product and ONNX SGEMM implementations"
        )
    factored_vocab_command_texts = [
        text
        for entry, text in zip(commands, command_texts)
        if str(entry.get("file", "")).replace("\\", "/").lower().endswith(
            "/marian-fork/src/data/factored_vocab.cpp"
        )
    ]
    if len(factored_vocab_command_texts) != 1:
        raise WindowsProfileError(
            "compile database must contain exactly one factored vocabulary command"
        )
    expression_operators_command_texts = [
        text
        for entry, text in zip(commands, command_texts)
        if str(entry.get("file", "")).replace("\\", "/").lower().endswith(
            "/marian-fork/src/graph/expression_operators.cpp"
        )
    ]
    if len(expression_operators_command_texts) != 1:
        raise WindowsProfileError(
            "compile database must contain exactly one expression operators command"
        )
    has_avx2 = re.search(r"(?:^|\s)/arch:AVX2(?:\s|$)", command_text, re.IGNORECASE) is not None
    has_sse2 = re.search(r"(?:^|\s)/arch:SSE2(?:\s|$)", command_text, re.IGNORECASE) is not None
    has_intgemm_avx2_cap = re.search(
        r"(?:^|\s)(?:/D|-D)LINGUUM_INTGEMM_MAX_AVX2(?:=1)?(?:\s|$)",
        intgemm_command_texts[0],
        re.IGNORECASE,
    ) is not None
    has_onnx_sgemm = re.search(
        r"(?:^|\s)(?:/D|-D)USE_ONNX_SGEMM=1(?:\s|$)",
        prod_command_texts[0],
        re.IGNORECASE,
    ) is not None
    vectorized_stl_disabled_pattern = re.compile(
        r"(?:^|\s)(?:/D|-D)_USE_STD_VECTOR_ALGORITHMS=0(?:\s|$)",
        re.IGNORECASE,
    )
    vectorized_stl_definition_pattern = re.compile(
        r"(?:^|\s)(?:/D|-D)_USE_STD_VECTOR_ALGORITHMS(?:=[^\s]+)?(?:\s|$)",
        re.IGNORECASE,
    )
    vectorized_stl_disabled_count = sum(
        vectorized_stl_disabled_pattern.search(text) is not None
        for text in cpp_command_texts
    )
    has_vectorized_stl_definition = any(
        vectorized_stl_definition_pattern.search(text) is not None
        for text in cpp_command_texts
    )
    compiler_intrinsics_disabled_pattern = re.compile(
        r"(?:^|\s)/Oi-(?:\s|$)", re.IGNORECASE
    )
    compiler_intrinsics_disabled_count = sum(
        compiler_intrinsics_disabled_pattern.search(text) is not None
        for text in command_texts
    )
    factored_vocab_scalar_search_boundary = (
        re.search(
            r"(?:^|\s)/Oi-(?:\s|$)",
            factored_vocab_command_texts[0],
            re.IGNORECASE,
        )
        is not None
        and re.search(
            r"(?:^|\s)/GL-(?:\s|$)",
            factored_vocab_command_texts[0],
            re.IGNORECASE,
        )
        is not None
        and re.search(
            r"(?:^|\s)(?:/D|-D)LINGUUM_MSVC_BASELINE=1(?:\s|$)",
            factored_vocab_command_texts[0],
            re.IGNORECASE,
        )
        is not None
    )
    dense_graph_scalar_boundary = all(
        flag in expression_operators_command_texts[0].casefold()
        for flag in ("/od", "/oi-", "/gl-")
    )
    if not has_onnx_sgemm:
        raise WindowsProfileError("native product command must enable the ONNX SGEMM backend")
    if profile_id == "windows-x64-avx2" and (not has_avx2 or not has_intgemm_avx2_cap):
        raise WindowsProfileError(
            "optimized compiler commands must contain /arch:AVX2 and the intgemm AVX2 cap"
        )
    if profile_id == "windows-x64-avx2" and has_vectorized_stl_definition:
        raise WindowsProfileError(
            "optimized compiler commands must retain the default vectorized MSVC STL"
        )
    if profile_id == "windows-x64-avx2" and compiler_intrinsics_disabled_count:
        raise WindowsProfileError(
            "optimized compiler commands must retain intrinsic substitution"
        )
    if profile_id == "windows-x64-baseline" and (
        has_avx2 or not has_sse2 or has_intgemm_avx2_cap
    ):
        raise WindowsProfileError("baseline compiler commands are not restricted to /arch:SSE2")
    if (
        profile_id == "windows-x64-baseline"
        and vectorized_stl_disabled_count != len(cpp_command_texts)
    ):
        raise WindowsProfileError(
            "every baseline C++ command must disable the vectorized MSVC STL"
        )
    if (
        profile_id == "windows-x64-baseline"
        and compiler_intrinsics_disabled_count != len(command_texts)
    ):
        raise WindowsProfileError(
            "every baseline compiler command must disable intrinsic substitution"
        )
    if (
        profile_id == "windows-x64-baseline"
        and not factored_vocab_scalar_search_boundary
    ):
        raise WindowsProfileError(
            "baseline factored vocabulary command must enable the scalar search boundary"
        )
    if profile_id == "windows-x64-baseline" and not dense_graph_scalar_boundary:
        raise WindowsProfileError(
            "baseline expression operators command must enable the scalar graph boundary"
        )
    return {
        "compileCommandCount": len(commands),
        "cppCompileCommandCount": len(cpp_command_texts),
        "compileCommandsSha256": run_host_canary.file_sha256(path),
        "compilerIntrinsicsDisabledCommandCount": compiler_intrinsics_disabled_count,
        "compilerIntrinsicsDisabledForAllCommands": (
            compiler_intrinsics_disabled_count == len(command_texts)
        ),
        "hasArchAvx2": has_avx2,
        "hasArchSse2": has_sse2,
        "hasIntgemmAvx2Cap": has_intgemm_avx2_cap,
        "factoredVocabularyScalarSearchBoundary": (
            factored_vocab_scalar_search_boundary
        ),
        "denseGraphScalarBoundary": dense_graph_scalar_boundary,
        "hasOnnxSgemm": has_onnx_sgemm,
        "hasOnnxSgemmImplementation": True,
        "vectorizedStlDisabledCommandCount": vectorized_stl_disabled_count,
        "vectorizedStlDisabledForAllCpp": (
            vectorized_stl_disabled_count == len(cpp_command_texts)
        ),
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
    commands = verify_compile_commands(profile_id, build_directory)
    print(json.dumps(
        {"compileEvidence": commands, "profile": profile_id},
        indent=2,
        sort_keys=True,
    ))
    linker_symbols = []
    linker_map_evidence = None
    baseline_boundary_evidence = None
    if profile_id == "windows-x64-baseline":
        linker_map_path = build_directory / "linguum_translation.map"
        if not linker_map_path.is_file():
            raise WindowsProfileError("baseline MSVC linker map is missing")
        linker_symbols = parse_linker_map(
            linker_map_path.read_text(encoding="utf-8-sig")
        )
        baseline_boundary_evidence = baseline_runtime_boundary_evidence(linker_symbols)
        linker_map_evidence = {
            "fileName": linker_map_path.name,
            "functionSymbolCount": len(linker_symbols),
            "sha256": run_host_canary.file_sha256(linker_map_path),
            "vectorAlgorithmsFunctionCount": sum(
                "vector_algorithms.obj" in source.casefold()
                for _, _, source in linker_symbols
            ),
            "vectorAlgorithmsFunctions": sorted({
                name
                for _, name, source in linker_symbols
                if "vector_algorithms.obj" in source.casefold()
            }),
            "runtimeBoundary": baseline_boundary_evidence,
        }
        print(json.dumps(
            {"linkerMapEvidence": linker_map_evidence, "profile": profile_id},
            indent=2,
            sort_keys=True,
        ))
    disassembly = capture(["dumpbin.exe", "/nologo", "/DISASM:NOBYTES", str(library)])
    isa = verify_isa(profile_id, disassembly, linker_symbols)
    dependencies = parse_dependencies(
        capture(["dumpbin.exe", "/nologo", "/DEPENDENTS", str(library)])
    )
    if profile_id == "windows-x64-baseline" and not any(
        dependency == "UCRTBASE.DLL" or dependency.startswith("API-MS-WIN-CRT-")
        for dependency in dependencies
    ):
        raise WindowsProfileError("baseline DLL does not resolve through the system UCRT")
    headers = capture(["dumpbin.exe", "/nologo", "/HEADERS", str(library)])
    if re.search(r"\b8664 machine \(x64\)", headers, re.IGNORECASE) is None:
        raise WindowsProfileError("DLL is not PE x64")
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
    if linker_map_evidence is not None:
        manifest["linkerMapAudit"] = linker_map_evidence
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


PROFILE_EXECUTION_ERRORS = (
    WindowsProfileError,
    run_host_canary.HostCanaryError,
    OSError,
    subprocess.SubprocessError,
    ValueError,
    json.JSONDecodeError,
)


def execute_profile_set(
    profiles: Mapping[str, Mapping[str, object]],
    toolchain: Mapping[str, object],
    output: Path,
    iterations: int,
    clean: bool,
) -> List[Dict[str, object]]:
    packages = []
    failures = []
    for profile_id in PROFILE_IDS:
        try:
            result = run_host_canary.execute(
                ROOT / "build" / "native-canary" / profile_id,
                iterations,
                clean,
                profile_id,
            )
            packages.append(package_profile(result, profiles[profile_id], toolchain, output))
        except PROFILE_EXECUTION_ERRORS as error:
            failures.append("{}: {}".format(profile_id, error))
            print("Windows native profile failed: {}: {}".format(profile_id, error), file=sys.stderr)
    if failures:
        raise WindowsProfileError("; ".join(failures))
    return packages


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
    profiles = profile_map(document)
    packages = execute_profile_set(profiles, toolchain_evidence, output, iterations, clean)
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
    except PROFILE_EXECUTION_ERRORS as error:
        print("Windows native profile gate failed: {}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

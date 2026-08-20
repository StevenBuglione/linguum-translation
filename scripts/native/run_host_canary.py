#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build and run the M1 minimal-ABI canary on the current desktop host."""

import argparse
import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Set, Tuple

SCRIPT_DIRECTORY = Path(__file__).resolve().parent
if str(SCRIPT_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIRECTORY))

import bootstrap_tools
import fetch_canary_model
import stage_source


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BUILD = ROOT / "build" / "native-canary" / "host"
EXPECTED_EXPORTS = ROOT / "testing" / "native" / "expected-exports.txt"
TRANSLATIONS_REVISION = "eea6e5a80aa4ddd86d9cc35ce9a65b79aa3ab96d"
FIREFOX_REVISION = "48d55cf7ec80093903e2ef7f58b61a84a22ef716"


class HostCanaryError(RuntimeError):
    """The complete host canary gate did not pass."""


def run(command: Sequence[str], cwd: Path = ROOT) -> None:
    print("+ {}".format(" ".join(str(part) for part in command)), flush=True)
    subprocess.run([str(part) for part in command], cwd=str(cwd), check=True)


def capture(command: Sequence[str], cwd: Path = ROOT) -> str:
    completed = subprocess.run(
        [str(part) for part in command],
        cwd=str(cwd),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return completed.stdout


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_build_directory(path: Path) -> Path:
    resolved = path.resolve()
    build_root = (ROOT / "build").resolve()
    try:
        resolved.relative_to(build_root)
    except ValueError as error:
        raise HostCanaryError("native canary build directory must be under {}".format(build_root)) from error
    if resolved == build_root:
        raise HostCanaryError("native canary build directory cannot be the build root")
    return resolved


def host_profile(profile_name: str = "host") -> Tuple[str, str, List[str]]:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if profile_name.startswith("windows-") and system != "windows":
        raise HostCanaryError("{} requires Windows".format(profile_name))
    if profile_name.startswith("macos-") and system != "darwin":
        raise HostCanaryError("{} requires macOS".format(profile_name))
    if profile_name == "macos-arm64":
        return "armv8-a", "apple-accelerate-arm64", [
            "-DCMAKE_OSX_ARCHITECTURES=arm64",
            "-DCMAKE_OSX_DEPLOYMENT_TARGET=13.0",
            "-DCMAKE_OSX_SYSROOT=macosx",
            "-DUSE_APPLE_ACCELERATE=ON",
            "-DUSE_ONNX_SGEMM=OFF",
            "-DUSE_RUY=ON",
            "-DUSE_RUY_SGEMM=OFF",
        ]
    if profile_name == "macos-x64":
        return "nehalem", "apple-accelerate-intgemm-runtime-x64", [
            "-DCMAKE_OSX_ARCHITECTURES=x86_64",
            "-DCMAKE_OSX_DEPLOYMENT_TARGET=13.0",
            "-DCMAKE_OSX_SYSROOT=macosx",
            "-DUSE_APPLE_ACCELERATE=ON",
            "-DUSE_ONNX_SGEMM=OFF",
            "-DUSE_RUY=OFF",
            "-DUSE_RUY_SGEMM=OFF",
        ]
    if system == "darwin" and machine in {"arm64", "aarch64"}:
        return "armv8-a", "apple-accelerate-arm64", [
            "-DCMAKE_OSX_ARCHITECTURES=arm64",
            "-DCMAKE_OSX_DEPLOYMENT_TARGET=13.0",
        ]
    if system == "darwin" and machine in {"x86_64", "amd64"}:
        return "native", "apple-accelerate-x64-host", [
            "-DCMAKE_OSX_ARCHITECTURES=x86_64",
            "-DCMAKE_OSX_DEPLOYMENT_TARGET=13.0",
        ]
    if system == "linux" and machine in {"arm64", "aarch64"}:
        return "armv8-a", "linux-arm64-host", []
    if system == "linux" and machine in {"x86_64", "amd64"}:
        return "native", "linux-x64-host-native", []
    if system == "windows" and machine in {"x86_64", "amd64"}:
        requested = "windows-x64-avx2" if profile_name == "host" else profile_name
        if requested == "windows-x64-avx2":
            return "native", "fbgemm-intgemm-avx2", [
                "-DUSE_FBGEMM=ON",
                "-DUSE_ONNX_SGEMM=ON",
                "-DLINGUUM_INTGEMM_BASELINE_ONLY=OFF",
                "-DLINGUUM_INTGEMM_AVX2_ONLY=ON",
            ]
        if requested == "windows-x64-baseline":
            return "core2", "intgemm-ssse3-onnx-sgemm-baseline", [
                "-DUSE_FBGEMM=OFF",
                "-DUSE_ONNX_SGEMM=ON",
                "-DLINGUUM_INTGEMM_BASELINE_ONLY=ON",
                "-DLINGUUM_INTGEMM_AVX2_ONLY=OFF",
            ]
        raise HostCanaryError("unsupported Windows native profile: {}".format(requested))
    raise HostCanaryError("unsupported desktop canary host: {} {}".format(system, machine))


def expected_exports() -> Set[str]:
    return {
        line.strip()
        for line in EXPECTED_EXPORTS.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def locate_library(build_directory: Path) -> Path:
    system = platform.system().lower()
    names = {
        "darwin": {"liblinguum_translation.dylib"},
        "linux": {"liblinguum_translation.so"},
        "windows": {"linguum_translation.dll"},
    }.get(system, set())
    matches = sorted(path for path in build_directory.rglob("*") if path.is_file() and path.name in names)
    if len(matches) != 1:
        raise HostCanaryError("expected exactly one native library, found {}".format(matches))
    return matches[0]


def defined_exports(library: Path) -> Set[str]:
    system = platform.system().lower()
    if system == "darwin":
        output = capture(["nm", "-gjU", str(library)])
        return {line.strip().lstrip("_") for line in output.splitlines() if line.strip()}
    if system == "linux":
        output = capture(["nm", "-D", "--defined-only", "--format=posix", str(library)])
        return {line.split()[0].split("@", 1)[0] for line in output.splitlines() if line.strip()}
    if system == "windows":
        dumpbin = shutil.which("dumpbin")
        if dumpbin is None:
            raise HostCanaryError("dumpbin is required to inspect Windows exports")
        output = capture([dumpbin, "/nologo", "/exports", str(library)])
        return {
            match.group(1)
            for line in output.splitlines()
            for match in [re.search(r"\s+[0-9A-F]+\s+[0-9A-F]+\s+[0-9A-F]+\s+(\S+)\s*$", line)]
            if match is not None
        }
    raise HostCanaryError("export inspection is unsupported on this host")


def verify_exports(library: Path) -> List[str]:
    expected = expected_exports()
    actual = defined_exports(library)
    prefixed = {name for name in actual if name.startswith("linguum_translation_")}
    allowed_non_api = {"LINGUUM_TRANSLATION_1.0"} if platform.system().lower() == "linux" else set()
    unexpected = actual - prefixed - allowed_non_api
    if prefixed != expected or unexpected:
        raise HostCanaryError(
            "native exports differ: missing={}, extra_api={}, extra={}".format(
                sorted(expected - prefixed), sorted(prefixed - expected), sorted(unexpected)
            )
        )
    return sorted(prefixed)


def verify_macos_minimum(library: Path) -> List[str]:
    if platform.system().lower() != "darwin":
        return []
    output = capture(["otool", "-l", str(library)])
    versions = sorted(set(re.findall(r"\bminos\s+([0-9]+(?:\.[0-9]+)+)", output)))
    if versions != ["13.0"]:
        raise HostCanaryError("unexpected macOS minimum version(s): {}".format(versions))
    return versions


def configure_arguments(
    cmake: Path,
    ninja: Path,
    source: Path,
    model: Path,
    build_directory: Path,
    iterations: int,
    profile_name: str = "host",
) -> Tuple[List[str], str]:
    build_arch, acceleration, platform_arguments = host_profile(profile_name)
    arguments = [
        str(cmake),
        "-S", str(ROOT / "native" / "runtime-build"),
        "-B", str(build_directory),
        "-G", "Ninja",
        "-DCMAKE_MAKE_PROGRAM={}".format(ninja),
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        "-DBUILD_TESTING=ON",
        "-DBUILD_ARCH={}".format(build_arch),
        "-DLINGUUM_TRANSLATIONS_SOURCE={}".format(source),
        "-DLINGUUM_TRANSLATIONS_REVISION={}".format(TRANSLATIONS_REVISION),
        "-DLINGUUM_FIREFOX_REVISION={}".format(FIREFOX_REVISION),
        "-DLINGUUM_LIBRARY_VERSION=0.1.0-M1",
        "-DLINGUUM_ACCELERATION_PROFILE={}".format(acceleration),
        "-DLINGUUM_CANARY_MODEL_DIR={}".format(model),
        "-DLINGUUM_CANARY_ITERATIONS={}".format(iterations),
    ]
    arguments.extend(platform_arguments)
    return arguments, acceleration


def execute(
    build_directory: Path,
    iterations: int,
    clean: bool,
    profile_name: str = "host",
) -> Dict[str, object]:
    if iterations < 1 or iterations > 1000:
        raise HostCanaryError("iterations must be between 1 and 1000")
    build_directory = safe_build_directory(build_directory)
    if clean and build_directory.exists():
        shutil.rmtree(str(build_directory))

    run([sys.executable, "scripts/upstream/snapshot.py", "prepare"])
    run([sys.executable, "scripts/upstream/snapshot.py", "verify"])
    source = stage_source.stage(force=clean)
    model = fetch_canary_model.fetch()
    cmake, ninja = bootstrap_tools.bootstrap()
    configure, acceleration = configure_arguments(
        cmake, ninja, source, model, build_directory, iterations, profile_name
    )
    run(configure)
    run([
        str(cmake), "--build", str(build_directory), "--parallel", "--target",
    ] + build_targets(profile_name))
    ctest_name = "ctest.exe" if platform.system().lower() == "windows" else "ctest"
    ctest = cmake.parent / ctest_name
    run([str(ctest), "--test-dir", str(build_directory), "--output-on-failure", "-C", "Release"])

    library = locate_library(build_directory)
    exports = verify_exports(library)
    minimum_versions = verify_macos_minimum(library)
    result = {
        "accelerationProfile": acceleration,
        "abi": "1.0",
        "artifact": str(library),
        "artifactSha256": file_sha256(library),
        "buildDirectory": str(build_directory),
        "cmake": capture([str(cmake), "--version"]).splitlines()[0],
        "exports": exports,
        "firefoxRevision": FIREFOX_REVISION,
        "host": "{}-{}".format(platform.system().lower(), platform.machine().lower()),
        "iterations": iterations,
        "minimumVersions": minimum_versions,
        "ninja": capture([str(ninja), "--version"]).strip(),
        "profile": profile_name if profile_name != "host" else acceleration,
        "translationsRevision": TRANSLATIONS_REVISION,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


def build_targets(profile_name: str) -> List[str]:
    targets = [
        "linguum_translation",
        "linguum_translation_abi_header_c",
        "linguum_translation_abi_header_cpp",
        "linguum_translation_canary",
    ]
    if profile_name == "windows-x64-baseline":
        targets.append("linguum_baseline_runtime_shims_test")
    return targets


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--clean", action="store_true")
    parser.add_argument(
        "--profile",
        choices=(
            "host",
            "windows-x64-avx2",
            "windows-x64-baseline",
            "macos-arm64",
            "macos-x64",
        ),
        default="host",
    )
    arguments = parser.parse_args()
    try:
        execute(
            arguments.build_dir,
            arguments.iterations,
            arguments.clean,
            arguments.profile,
        )
    except (
        HostCanaryError,
        bootstrap_tools.ToolBootstrapError,
        fetch_canary_model.ModelFetchError,
        stage_source.SourceStageError,
        OSError,
        subprocess.CalledProcessError,
        ValueError,
    ) as error:
        print("host native canary failed: {}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Jason Stys: source-bound portable app packaging with actual runtime notices and fresh outputs.

No accounts, credentials, runtime data, release tokens or provider settings enter
the distribution. This script builds only; publication has separate exact-main
workflow/security/download gates. Symbol indexes are generated before release.
"""

# Index: annotations@10, argparse@12, hashlib@13, json@14, os@15, platform@16, posixpath@17, shutil@18, subprocess@19, sys@20, sysconfig@21, tarfile@22, tomllib@23, uuid@24, zipfile@25, Path@26, VERSION@28, WINDOWS_PYTHON_SHA256@29, bounded_bytes@29, ui_files@29, collect@30, ROOT@32, packaged_library@35, packaged_library.binary@35, packaged_library.name@35, packaged_library.CArchiveReader@37, packaged_library.archive@39, packaged_library.seen@40, packaged_library._@41, packaged_library._flag@45, packaged_library._offset@45, packaged_library.compressed@45, packaged_library.expanded@45, packaged_library.kind@45, packaged_library.data@48, packaged_library.target@52, packaged_library.name@53, runtime_library@63, main@76, main.argv@76, main.parser@78, main.args@83, main.git@93, main.source@96, main.dirty@97, main.output@100, main.resources@105, main.notices@112, main.versions@112, main.library_name@113, main.library_path@113, main.library_bytes@114, main.library_digest@115, main.scratch@118, main.notice_file@121, main.data@123, main.name@123, main.metadata@128, main.metadata_file@146, main.command@150, main.command@172, main.source_file@173, main.target@173, main.command@179, main.module@180, main.command@186, main.module@187, main.command@188, main.binary@190, main.attempt@195, main.cooked@202, main.cooked_digest@203, main.CArchiveReader@209, main.stem@222, main.files@223, main.archive@231, main.target@232, main.file@233, main.name@233, main.archive@236, main.target@237, main.file@238, main.name@238, main.hashes@240, main.file@241, main.stream@242

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import posixpath
import shutil
import subprocess
import sys
import sysconfig
import tarfile
import tomllib
import uuid
import zipfile
from pathlib import Path

from app import VERSION
from app.native_identity import WINDOWS_PYTHON_SHA256, bounded_bytes, ui_files
from scripts.native_notices import collect

ROOT = Path(__file__).resolve().parents[1]


def packaged_library(binary: Path, name: str) -> bytes:
    """Read actual bounded frozen library bytes, following only internal CArchive framework aliases."""
    from PyInstaller.archive.readers import CArchiveReader

    archive = CArchiveReader(str(binary))
    seen = set()
    for _ in range(8):
        if name in seen or name not in archive.toc:
            raise ValueError("Frozen Python library alias is missing or cyclic")
        seen.add(name)
        _offset, compressed, expanded, _flag, kind = archive.toc[name]
        if not 0 < expanded <= 64 * 1024 * 1024 or not 0 < compressed <= 64 * 1024 * 1024:
            raise ValueError("Frozen Python library exceeds its bound")
        data = archive.extract(name)
        if kind == "n":
            if len(data) > 4096 or not data.endswith(b"\0") or b"\0" in data[:-1]:
                raise ValueError("Invalid frozen framework alias")
            target = data[:-1].decode("utf-8")
            name = posixpath.normpath(posixpath.join(posixpath.dirname(name), target))
            if name.startswith(("/", "../")) or name == ".." or "\\" in name:
                raise ValueError("Frozen framework alias escapes the package")
        else:
            if kind != "b" or len(data) != expanded:
                raise ValueError("Frozen Python library payload differs")
            return data
    raise ValueError("Frozen framework alias chain exceeds its bound")


def runtime_library() -> tuple[str, Path]:
    """Locate the actual selected interpreter library without searching another installed Python."""
    if sys.platform == "win32":
        return "python314.dll", Path(sys.base_prefix) / "python314.dll"
    if sys.platform == "darwin":
        return "Python", Path(
            sysconfig.get_config_var("PYTHONFRAMEWORKPREFIX")
        ) / "Python.framework/Versions/3.14/Python"
    if sys.platform == "linux":
        return "libpython3.14.so.1.0", Path(sysconfig.get_config_var("LIBDIR")) / "libpython3.14.so.1.0"
    raise ValueError("Review another native platform before packaging")


def main(argv=None) -> None:
    """Freeze the real private browser app and native owner window; never overwrite an earlier candidate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=ROOT / "release")
    parser.add_argument(
        "--allow-dirty", action="store_true", help="Label a local development candidate; forbidden in CI"
    )
    args = parser.parse_args(argv)
    if sys.version_info[:3] != (3, 14, 10) or sys.version_info.releaselevel != "final":
        raise ValueError("Native packaging requires final patched CPython3.14.10")
    if args.allow_dirty and os.environ.get("CI", "").lower() in {"1", "true"}:
        raise ValueError("CI cannot label dirty source as a portable candidate")
    if (
        tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"] != VERSION
        or json.loads((ROOT / "package.json").read_text())["version"] != VERSION
    ):
        raise ValueError("Python/UI/native version coherence failed")
    git = shutil.which("git")
    if git is None:
        raise ValueError("The trusted build environment must provide Git")
    source = subprocess.check_output([git, "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()  # noqa: S603 -- resolved trusted build tool and literal Git arguments
    dirty = bool(subprocess.check_output([git, "status", "--porcelain"], cwd=ROOT).strip())  # noqa: S603 -- resolved trusted build tool, no shell/input code
    if dirty and not args.allow_dirty:
        raise ValueError("Native distribution requires clean reviewed source")
    output = args.output_root.resolve()
    if not output.is_relative_to(ROOT.resolve()) or output.exists():
        raise ValueError(
            "Choose a fresh build directory within this repository; existing outputs are preserved"
        )
    resources = ui_files(ROOT)
    subprocess.run(  # noqa: S603 -- fixed owned interpreter and literal test module
        [sys.executable, "-m", "pytest", "tests/test_native_notices.py", "--capture=sys", "-q"],
        cwd=ROOT,
        check=True,
        timeout=45,
    )
    versions, notices = collect(ROOT)
    library_name, library_path = runtime_library()
    library_bytes = bounded_bytes(library_path.resolve(), 64 * 1024 * 1024)
    library_digest = hashlib.sha256(library_bytes).hexdigest()
    if sys.platform == "win32" and library_digest != WINDOWS_PYTHON_SHA256:
        raise ValueError("The Windows Python runtime differs from the independently reviewed SDK")
    scratch = ROOT / ".runtime/native-package-stage" / uuid.uuid4().hex
    scratch.mkdir(parents=True)
    output.mkdir(parents=True)
    notice_file = scratch / "NATIVE_NOTICES.txt"
    notice_file.write_bytes(notices)
    for name, data in (
        ("LICENSE", bounded_bytes(ROOT / "LICENSE", 1024 * 1024)),
        (notice_file.name, notices),
    ):
        resources[name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    metadata = {
        "schema": 1,
        "product": "applicant-evidence-studio",
        "version": VERSION,
        "source": source,
        "source_dirty": dirty,
        "python": platform.python_version(),
        "platform": sys.platform,
        "machine": platform.machine(),
        **versions,
        "runtime_library": {
            "file": library_name,
            "bytes": len(library_bytes),
            "sha256": library_digest,
            "sdk_sha256": library_digest,
        },
        "resources": resources,
    }
    metadata_file = scratch / "NATIVE_SOURCE.json"
    metadata_file.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(metadata_file, output / metadata_file.name)
    shutil.copy2(notice_file, output / notice_file.name)
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--noupx",
        "--onefile",
        "--name",
        "ApplicantEvidenceStudio",
        "--distpath",
        str(output / "bin"),
        "--workpath",
        str(scratch / "build"),
        "--specpath",
        str(scratch),
        "--paths",
        str(ROOT),
    ]
    if sys.platform == "win32":
        # Console-mode pipes remain usable for scoped acceptance; PyInstaller
        # hides only its own normal console, never a user's inherited terminal.
        command += ["--hide-console", "hide-early"]
    for source_file, target in (
        (ROOT / "dist", "dist"),
        (ROOT / "LICENSE", "."),
        (notice_file, "."),
        (metadata_file, "."),
    ):
        command += ["--add-data", str(source_file) + os.pathsep + target]
    for module in (
        "uvicorn.logging",
        "uvicorn.loops.asyncio",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.lifespan.on",
    ):
        command += ["--hidden-import", module]
    for module in ("pytest", "pip", "setuptools", "ruff"):
        command += ["--exclude-module", module]
    command.append(str(ROOT / "app/desktop.py"))
    binary = (
        output
        / "bin"
        / ("ApplicantEvidenceStudio.exe" if sys.platform == "win32" else "ApplicantEvidenceStudio")
    )
    for attempt in range(2):
        subprocess.run(  # noqa: S603 -- fixed trusted freezer argv, no shell or uploaded source
            command,
            cwd=ROOT,
            check=True,
            env={**os.environ, "PYINSTALLER_CONFIG_DIR": str(scratch / "cache")},
        )
        cooked = packaged_library(binary, library_name)
        cooked_digest = hashlib.sha256(cooked).hexdigest()
        if sys.platform == "win32" and cooked_digest != WINDOWS_PYTHON_SHA256:
            raise ValueError("Windows freezing changed the independently pinned Python DLL")
        if metadata["runtime_library"]["sha256"] == cooked_digest and metadata["runtime_library"][
            "bytes"
        ] == len(cooked):
            from PyInstaller.archive.readers import CArchiveReader

            if CArchiveReader(str(binary)).extract("NATIVE_SOURCE.json") != metadata_file.read_bytes():
                raise ValueError("Actual embedded source metadata differs from the archive sidecar")
            break
        if attempt:
            raise ValueError("Processed Python runtime changed across source-binding passes")
        # macOS load-path repair and ad-hoc signing legitimately change SDK
        # library bytes. Bind the measured cooked payload on a second pass,
        # retaining the original SDK digest separately; never waive the check.
        metadata["runtime_library"].update(bytes=len(cooked), sha256=cooked_digest)
        metadata_file.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        shutil.copy2(metadata_file, output / metadata_file.name)
    stem = f"ApplicantEvidenceStudio-{VERSION}-{platform.system().lower()}-{platform.machine().lower()}"
    files = [
        (binary, binary.name),
        (ROOT / "LICENSE", "LICENSE"),
        (ROOT / "docs/install.md", "INSTALL.md"),
        (metadata_file, metadata_file.name),
        (notice_file, notice_file.name),
    ]
    if sys.platform == "win32":
        archive = output / (stem + ".zip")
        with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED) as target:
            for file, name in files:
                target.write(file, name)
    else:
        archive = output / (stem + ".tar.gz")
        with tarfile.open(archive, "x:gz") as target:
            for file, name in files:
                target.add(file, arcname=name, recursive=False)
    hashes = []
    for file in (archive, binary):
        with file.open("rb") as stream:
            hashes.append(hashlib.file_digest(stream, "sha256").hexdigest() + "  " + file.name)
    (output / (stem + ".sha256")).write_text("\n".join(hashes) + "\n", encoding="ascii")
    print(
        f"Built unsigned portable candidate {archive.name}; source_dirty={dirty}. No publication or installation performed."
    )


if __name__ == "__main__":
    main()

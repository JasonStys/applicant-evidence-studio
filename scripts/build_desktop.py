"""Jason Stys: reproducible native local launcher archives and SHA-256 release manifest."""

# Index: hashlib@4, platform@5, subprocess@6, sys@7, tarfile@8, zipfile@9, Path@10, VERSION@12, main@15, main.output@19, main.command@21, main.binary@54, main.stem@59, main.files@67, main.archive@69, main.bundle@70, main.name@71, main.path@71, main.archive@74, main.bundle@75, main.name@76, main.path@76, main.manifest@78, main.hashes@79, main.name@80, main.path@80, main.source@81
import hashlib
import platform
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

from app import VERSION


def main():
    """Bundle only built UI and account code; never runtime data, credentials or real resumes."""
    if not Path("dist/index.html").is_file():
        raise SystemExit("Run npm ci and npm run build first")
    output = Path("release")
    output.mkdir(exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--name",
        "ApplicantEvidenceStudio",
        "--distpath",
        "release/bin",
        "--workpath",
        "build/pyinstaller",
        "--specpath",
        "build",
        "--add-data",
        str(Path("dist").resolve()) + ":dist",
        "--hidden-import",
        "uvicorn.logging",
        "--hidden-import",
        "uvicorn.loops.auto",
        "--hidden-import",
        "uvicorn.protocols.http.auto",
        "--hidden-import",
        "uvicorn.protocols.http.h11_impl",
        "--hidden-import",
        "uvicorn.protocols.websockets.auto",
        "--hidden-import",
        "uvicorn.lifespan.on",
        "--exclude-module",
        "pytest",
        "app/desktop.py",
    ]
    subprocess.run(command, check=True)  # noqa: S603 -- fixed trusted build command, no shell/user code
    binary = (
        output
        / "bin"
        / ("ApplicantEvidenceStudio.exe" if sys.platform == "win32" else "ApplicantEvidenceStudio")
    )
    stem = (
        "ApplicantEvidenceStudio-"
        + VERSION
        + "-"
        + platform.system().lower()
        + "-"
        + platform.machine().lower()
    )
    files = [(binary, binary.name), (Path("LICENSE"), "LICENSE"), (Path("docs/install.md"), "INSTALL.md")]
    if sys.platform == "win32":
        archive = output / (stem + ".zip")
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
            for path, name in files:
                bundle.write(path, name)
    else:
        archive = output / (stem + ".tar.gz")
        with tarfile.open(archive, "w:gz") as bundle:
            for path, name in files:
                bundle.add(path, arcname=name, recursive=False)
    manifest = output / (stem + ".sha256")
    hashes = []
    for path, name in [(archive, archive.name), (binary, binary.name)]:
        with path.open("rb") as source:
            hashes.append(hashlib.file_digest(source, "sha256").hexdigest() + "  " + name)
    manifest.write_text("\n".join(hashes) + "\n", encoding="utf-8")
    print(f"Built {archive.name}; unsigned portable application. Verify {manifest.name}.")


if __name__ == "__main__":
    main()

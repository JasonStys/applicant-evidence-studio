"""Jason Stys: exclusive native ownership of a private account directory.

DesktopOwnership admits an ordinary external directory and retains one OS lock
until the local service has stopped. Existing account/vault files are not read,
rewritten, migrated or removed here. Symbol/parameter locations are generated
by scripts/code_index.py into this file's source index before publication.
"""

# Index: annotations@11, os@13, stat@14, sys@15, Path@16, external_directory@19, external_directory.directory@19, external_directory.forbidden_roots@19, external_directory.absolute@21, external_directory.part@22, external_directory.selected@24, external_directory.root@25, DesktopOwnership@30, DesktopOwnership.__init__@33, DesktopOwnership.__init__.directory@33, DesktopOwnership.__init__.forbidden_roots@33, DesktopOwnership.__init__.self@33, DesktopOwnership.__init__.name@40, DesktopOwnership.__init__.candidate@46, DesktopOwnership.__init__.info@48, DesktopOwnership.__init__.target@58, DesktopOwnership.__init__.flags@61, DesktopOwnership.__init__.flags@62, DesktopOwnership.__init__.descriptor@63, DesktopOwnership.__init__.named@65, DesktopOwnership.__init__.opened@65, DesktopOwnership.__init__.msvcrt@80, DesktopOwnership.__init__.fcntl@84, DesktopOwnership.close@92, DesktopOwnership.close.self@92, DesktopOwnership.__enter__@98, DesktopOwnership.__enter__.self@98, DesktopOwnership.__exit__@102, DesktopOwnership.__exit__._error@102, DesktopOwnership.__exit__.self@102

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path


def external_directory(directory: Path, forbidden_roots: tuple[Path, ...] = ()) -> Path:
    """Reject linked ancestors and installation/resource destinations before any write."""
    absolute = directory.absolute()
    if any(part.is_symlink() or part.is_junction() for part in (absolute, *absolute.parents)):
        raise ValueError("Choose an ordinary private directory without links or junctions")
    selected = absolute.resolve()
    if any(selected.is_relative_to(root.resolve()) for root in forbidden_roots):
        raise ValueError("Account data must remain outside the application installation")
    return selected


class DesktopOwnership:
    """Retain one nonblocking process owner without changing the existing vault format."""

    def __init__(self, directory: Path, forbidden_roots: tuple[Path, ...] = ()) -> None:
        """Admit a new/existing private directory and acquire only this product's regular lock file."""
        self.directory = external_directory(directory, forbidden_roots)
        self.descriptor = -1
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Refuse aliases before creating the lock or letting SQLite initialize.
        # Ordinary existing journals are retained for SQLite's own recovery.
        for name in (
            "private-accounts.db",
            "private-accounts.db-journal",
            "private-accounts.db-wal",
            "private-accounts.db-shm",
        ):
            candidate = self.directory / name
            try:
                info = candidate.lstat()
            except FileNotFoundError:
                continue
            if (
                candidate.is_symlink()
                or candidate.is_junction()
                or not stat.S_ISREG(info.st_mode)
                or info.st_nlink != 1
            ):
                raise ValueError("Account database and recovery files must be ordinary single-link files")
        target = self.directory / ".aes-native-owner.lock"
        if target.is_symlink() or target.is_junction():
            raise ValueError("Native ownership file must not be linked")
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
        flags |= getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_BINARY", 0)
        descriptor = os.open(target, flags, 0o600)
        try:
            opened, named = os.fstat(descriptor), target.lstat()
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_nlink != 1
                or (opened.st_dev, opened.st_ino) != (named.st_dev, named.st_ino)
                or opened.st_size not in (0, 1)
            ):
                raise ValueError("Native ownership requires an ordinary one-link lock file")
            if opened.st_size == 0:
                os.write(descriptor, b"0")
            os.lseek(descriptor, 0, os.SEEK_SET)
            if os.read(descriptor, 2) != b"0":
                raise ValueError("Unknown native ownership marker was preserved")
            os.lseek(descriptor, 0, os.SEEK_SET)
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.descriptor = descriptor
        except BaseException:
            os.close(descriptor)
            raise

    def close(self) -> None:
        """Release only this instance's descriptor after retained service work is complete."""
        if self.descriptor >= 0:
            os.close(self.descriptor)
            self.descriptor = -1

    def __enter__(self) -> DesktopOwnership:
        """Retain ownership throughout the complete local service/window context."""
        return self

    def __exit__(self, *_error: object) -> None:
        """Release the descriptor on ordinary shutdown or startup failure; never delete account data."""
        self.close()

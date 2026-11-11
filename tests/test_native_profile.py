"""Jason Stys: actual native lock contention and file-preserving profile boundary controls."""

# Index: os@5, stat@6, subprocess@7, sys@8, tempfile@9, Path@10, pytest@12, DesktopOwnership@14, external_directory@14, test_actual_owned_system_temp_root_admission_keeps_alias_refusal@17, test_actual_owned_system_temp_root_admission_keeps_alias_refusal.temporary@19, test_actual_owned_system_temp_root_admission_keeps_alias_refusal.original@20, test_actual_owned_system_temp_root_admission_keeps_alias_refusal.canonical@21, test_actual_owned_system_temp_root_admission_keeps_alias_refusal.linked_ancestor@23, test_actual_owned_system_temp_root_admission_keeps_alias_refusal.path@28, test_fixed_sqlite_aliases_refused_before_lock_or_account_writes@48, test_fixed_sqlite_aliases_refused_before_lock_or_account_writes.name@48, test_fixed_sqlite_aliases_refused_before_lock_or_account_writes.tmp_path@48, test_fixed_sqlite_aliases_refused_before_lock_or_account_writes.profile@50, test_fixed_sqlite_aliases_refused_before_lock_or_account_writes.original@52, test_ordinary_recovery_files_are_retained_without_being_opened@61, test_ordinary_recovery_files_are_retained_without_being_opened.tmp_path@61, test_ordinary_recovery_files_are_retained_without_being_opened.profile@63, test_ordinary_recovery_files_are_retained_without_being_opened.expected@65, test_ordinary_recovery_files_are_retained_without_being_opened.name@66, test_ordinary_recovery_files_are_retained_without_being_opened.name@70, test_ordinary_recovery_files_are_retained_without_being_opened.raw@70, test_real_process_owner_refuses_duplicate_then_reopens_same_existing_accounts@73, test_real_process_owner_refuses_duplicate_then_reopens_same_existing_accounts.tmp_path@73, test_real_process_owner_refuses_duplicate_then_reopens_same_existing_accounts.directory@75, test_real_process_owner_refuses_duplicate_then_reopens_same_existing_accounts.protected@77, test_real_process_owner_refuses_duplicate_then_reopens_same_existing_accounts.before@79, test_real_process_owner_refuses_duplicate_then_reopens_same_existing_accounts.program@80, test_real_process_owner_refuses_duplicate_then_reopens_same_existing_accounts.first@81, test_real_process_owner_refuses_duplicate_then_reopens_same_existing_accounts.child@82, test_actual_installation_boundary_refuses_before_creating_descendants@98, test_actual_installation_boundary_refuses_before_creating_descendants.nested@98, test_actual_installation_boundary_refuses_before_creating_descendants.tmp_path@98, test_actual_installation_boundary_refuses_before_creating_descendants.installation@100, test_actual_installation_boundary_refuses_before_creating_descendants.target@102, test_unknown_lock_and_hardlink_are_preserved_without_mutating_account_files@109, test_unknown_lock_and_hardlink_are_preserved_without_mutating_account_files.tmp_path@109, test_unknown_lock_and_hardlink_are_preserved_without_mutating_account_files.directory@111, test_unknown_lock_and_hardlink_are_preserved_without_mutating_account_files.marker@113, test_unknown_lock_and_hardlink_are_preserved_without_mutating_account_files.original@119, test_actual_directory_alias_refused_without_following_or_creating_account_data@127, test_actual_directory_alias_refused_without_following_or_creating_account_data.tmp_path@127, test_actual_directory_alias_refused_without_following_or_creating_account_data.destination@129, test_actual_directory_alias_refused_without_following_or_creating_account_data.important@131, test_actual_directory_alias_refused_without_following_or_creating_account_data.alias@133, test_context_failure_releases_owner_without_resetting_existing_directory@157, test_context_failure_releases_owner_without_resetting_existing_directory.tmp_path@157, test_context_failure_releases_owner_without_resetting_existing_directory.reopened@161

import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from app.native_profile import DesktopOwnership, external_directory


def test_actual_owned_system_temp_root_admission_keeps_alias_refusal():
    """Use canonical owned test paths on macOS without teaching production admission to follow aliases."""
    with tempfile.TemporaryDirectory(prefix="aes-canonical-system-temp-") as temporary:
        original = Path(temporary)
        canonical = original.resolve()
        assert canonical.is_dir() and external_directory(canonical, ()) == canonical
        linked_ancestor = any(
            path.is_symlink()
            or path.is_junction()
            or getattr(path.lstat(), "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            for path in (original, *original.parents)
        )
        if linked_ancestor:
            with pytest.raises(ValueError):
                external_directory(original, ())
        else:
            # Windows may expand a harmless DOS short name without a link.
            # Different spelling is not itself evidence of redirection.
            assert external_directory(original, ()).samefile(canonical)


@pytest.mark.parametrize(
    "name",
    [
        "private-accounts.db",
        "private-accounts.db-journal",
        "private-accounts.db-wal",
        "private-accounts.db-shm",
    ],
)
def test_fixed_sqlite_aliases_refused_before_lock_or_account_writes(tmp_path, name):
    """An actual hard-linked database/recovery name cannot redirect native initialization writes."""
    profile = tmp_path / "profile"
    profile.mkdir()
    original = tmp_path / "retain.bin"
    original.write_bytes(b"private fixture retained exactly")
    os.link(original, profile / name)
    with pytest.raises(ValueError, match="ordinary single-link"):
        DesktopOwnership(profile)
    assert original.read_bytes() == b"private fixture retained exactly"
    assert not (profile / ".aes-native-owner.lock").exists()


def test_ordinary_recovery_files_are_retained_without_being_opened(tmp_path):
    """Native ownership does not discard ordinary recovery evidence or reinterpret SQLite content."""
    profile = tmp_path / "profile"
    profile.mkdir()
    expected = {}
    for name in ("private-accounts.db-journal", "private-accounts.db-wal", "private-accounts.db-shm"):
        expected[name] = ("retained " + name).encode()
        (profile / name).write_bytes(expected[name])
    with DesktopOwnership(profile):
        assert all((profile / name).read_bytes() == raw for name, raw in expected.items())


def test_real_process_owner_refuses_duplicate_then_reopens_same_existing_accounts(tmp_path):
    """A second real interpreter cannot own the profile; closing preserves exact existing bytes."""
    directory = tmp_path / "accounts"
    directory.mkdir()
    protected = directory / "existing-vault.encrypted.json"
    protected.write_bytes(b"synthetic opaque encrypted archive bytes")
    before = protected.read_bytes()
    program = "from pathlib import Path; import sys; from app.native_profile import DesktopOwnership; DesktopOwnership(Path(sys.argv[1]))"
    with DesktopOwnership(directory) as first:
        child = subprocess.run(  # noqa: S603 -- fixed trusted interpreter and literal contract probe; no user code.
            [sys.executable, "-c", program, str(directory)],
            capture_output=True,
            timeout=10,
            cwd=Path(__file__).resolve().parents[1],
            check=False,
        )
        assert child.returncode != 0
        assert first.descriptor >= 0
        assert protected.read_bytes() == before
    with DesktopOwnership(directory):
        assert protected.read_bytes() == before
    assert protected.read_bytes() == before


@pytest.mark.parametrize("nested", ["data", "child/data"])
def test_actual_installation_boundary_refuses_before_creating_descendants(tmp_path, nested):
    """Profile admission cannot create account data in the installed payload or resource tree."""
    installation = tmp_path / "installation"
    installation.mkdir()
    target = installation / nested
    with pytest.raises(ValueError, match="outside"):
        DesktopOwnership(target, (installation,))
    assert not target.exists()
    assert list(installation.iterdir()) == []


def test_unknown_lock_and_hardlink_are_preserved_without_mutating_account_files(tmp_path):
    """Unknown ownership content and aliased files cannot silently become a native profile lock."""
    directory = tmp_path / "accounts"
    directory.mkdir()
    marker = directory / ".aes-native-owner.lock"
    marker.write_bytes(b"important unknown file")
    with pytest.raises(ValueError):
        DesktopOwnership(directory)
    assert marker.read_bytes() == b"important unknown file"
    marker.unlink()
    original = tmp_path / "original"
    original.write_bytes(b"0")
    os.link(original, marker)
    with pytest.raises(ValueError):
        DesktopOwnership(directory)
    assert marker.read_bytes() == original.read_bytes() == b"0"


def test_actual_directory_alias_refused_without_following_or_creating_account_data(tmp_path):
    """Use a real Windows junction or POSIX symlink, not a mocked Path predicate."""
    destination = tmp_path / "preserve"
    destination.mkdir()
    important = destination / "important"
    important.write_bytes(b"preserve exactly")
    alias = tmp_path / "alias"
    if sys.platform == "win32":
        subprocess.run(  # noqa: S603 -- literal mklink/J uses only pytest-owned paths, no deletion or user content.
            [
                str(Path(os.environ.get("SystemRoot", "C:/Windows")) / "System32/cmd.exe"),
                "/d",
                "/c",
                "mklink",
                "/J",
                str(alias),
                str(destination),
            ],
            check=True,
            capture_output=True,
            timeout=10,
        )
    else:
        alias.symlink_to(destination, target_is_directory=True)
    with pytest.raises(ValueError, match="links or junctions"):
        external_directory(alias / "new-profile")
    assert important.read_bytes() == b"preserve exactly"
    assert not (destination / "new-profile").exists()


def test_context_failure_releases_owner_without_resetting_existing_directory(tmp_path):
    """A genuine startup exception releases this process's lock, allowing a later normal launch."""
    with pytest.raises(RuntimeError, match="synthetic startup failure"), DesktopOwnership(tmp_path):
        raise RuntimeError("synthetic startup failure")
    with DesktopOwnership(tmp_path) as reopened:
        assert reopened.descriptor >= 0
    # Windows byte-range ownership correctly prevents an unrelated read while
    # held. Verify marker bytes after the second ordinary owner has closed.
    assert (tmp_path / ".aes-native-owner.lock").read_bytes() == b"0"

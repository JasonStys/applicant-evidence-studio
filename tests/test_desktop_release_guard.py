"""Jason Stys: independent exact-source, draft and portable-asset publication boundaries."""

# Index: copy@4, json@5, Path@6, pytest@8, guard@10, accepted_build@12, assets_ready@13, draft_ready@14, security_ready@15, successful_source_run@16, names_for@18, SOURCE@20, run_fixture@23, test_source_run_requires_exact_completed_main_identity@42, test_source_run_rejects_unrelated_or_unfinished_metadata@62, test_source_run_rejects_unrelated_or_unfinished_metadata.field@62, test_source_run_rejects_unrelated_or_unfinished_metadata.value@62, test_source_run_rejects_unrelated_or_unfinished_metadata.data@64, test_empty_duplicate_and_incomplete_run_pages_fail_closed@70, test_empty_duplicate_and_incomplete_run_pages_fail_closed.data@72, test_draft_never_accepts_published_or_different_source@91, test_draft_never_accepts_published_or_different_source.change@91, test_draft_never_accepts_published_or_different_source.data@93, assets_fixture@99, assets_fixture.names@101, assets_fixture.machine@103, assets_fixture.system@103, assets_fixture.name@104, assets_fixture.name@106, test_publication_requires_all_six_platform_assets@109, test_publication_requires_all_six_platform_assets.data@111, test_publication_requires_all_six_platform_assets.partial@113, test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes.r@122, test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes.r@123, test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes.r@124, test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes.r@125, test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes.r@126, test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes@129, test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes.mutation@129, test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes.data@131, analyses_fixture@137, analyses_fixture.language@150, test_actual_processed_security_records_are_required@154, test_actual_processed_security_records_are_required.rows@156, test_actual_processed_security_records_are_required.changed@158, test_actual_processed_security_records_are_required.row@158, test_partial_foreign_and_failed_security_results_fail_closed@177, test_partial_foreign_and_failed_security_results_fail_closed.changed@177, test_partial_foreign_and_failed_security_results_fail_closed.rows@179, test_latest_failed_same_source_analysis_cannot_be_hidden_by_an_older_success@185, test_latest_failed_same_source_analysis_cannot_be_hidden_by_an_older_success.rows@187, test_latest_failed_same_source_analysis_cannot_be_hidden_by_an_older_success.failed@188, built_fixture@193, test_upload_rejects_old_dirty_or_source_server_acceptance@209, test_upload_rejects_old_dirty_or_source_server_acceptance.change@212, test_upload_rejects_old_dirty_or_source_server_acceptance.change@221, test_upload_rejects_old_dirty_or_source_server_acceptance.report@227, unpublished_release@233, test_unpublished_draft_uses_listing_and_verified_id_without_published_tag@245, test_unpublished_draft_uses_listing_and_verified_id_without_published_tag.monkeypatch@245, test_unpublished_draft_uses_listing_and_verified_id_without_published_tag.release@247, test_unpublished_draft_uses_listing_and_verified_id_without_published_tag.calls@248, test_unpublished_draft_uses_listing_and_verified_id_without_published_tag.provider@250, test_unpublished_draft_uses_listing_and_verified_id_without_published_tag.provider.endpoint@250, test_ambiguous_incomplete_or_malformed_release_pages_fail_closed@271, test_ambiguous_incomplete_or_malformed_release_pages_fail_closed.rows@271, test_id_resolution_rejects_changed_published_or_different_source@288, test_id_resolution_rejects_changed_published_or_different_source.change@288, test_id_resolution_rejects_changed_published_or_different_source.monkeypatch@288, test_id_resolution_rejects_changed_published_or_different_source.endpoint@293, test_prepare_resumes_equal_draft_without_writes_or_retarget@299, test_prepare_resumes_equal_draft_without_writes_or_retarget.monkeypatch@299, test_prepare_resumes_equal_draft_without_writes_or_retarget.source@301, test_prepare_resumes_equal_draft_without_writes_or_retarget.endpoint@303, test_prepare_resumes_equal_draft_without_writes_or_retarget._args@305, test_prepare_creates_only_missing_draft_with_literal_structured_notes@309, test_prepare_creates_only_missing_draft_with_literal_structured_notes.monkeypatch@309, test_prepare_creates_only_missing_draft_with_literal_structured_notes.tmp_path@309, test_prepare_creates_only_missing_draft_with_literal_structured_notes.notes@311, test_prepare_creates_only_missing_draft_with_literal_structured_notes.content@313, test_prepare_creates_only_missing_draft_with_literal_structured_notes._source@316, test_prepare_creates_only_missing_draft_with_literal_structured_notes.created@317, test_prepare_creates_only_missing_draft_with_literal_structured_notes.provider@319, test_prepare_creates_only_missing_draft_with_literal_structured_notes.provider.endpoint@319, test_prepare_creates_only_missing_draft_with_literal_structured_notes.command@322, test_prepare_creates_only_missing_draft_with_literal_structured_notes.command.arguments@322, test_prepare_creates_only_missing_draft_with_literal_structured_notes.command.payload@330
import copy
import json
from pathlib import Path

import pytest

from scripts import desktop_release_guard as guard
from scripts.desktop_release_guard import (
    accepted_build,
    assets_ready,
    draft_ready,
    security_ready,
    successful_source_run,
)
from scripts.portable_acceptance import names_for

SOURCE = "a" * 40


def run_fixture():
    """A complete main-push record, independent of query filtering and workflow code."""
    return {
        "total_count": 1,
        "workflow_runs": [
            {
                "id": 123,
                "head_sha": SOURCE,
                "head_branch": "main",
                "event": "push",
                "path": ".github/workflows/validate.yml",
                "html_url": "https://github.com/JasonStys/applicant-evidence-studio/actions/runs/123",
                "status": "completed",
                "conclusion": "success",
            }
        ],
    }


def test_source_run_requires_exact_completed_main_identity():
    """Passing unrelated jobs cannot stand in for this exact source workflow."""
    successful_source_run(run_fixture(), SOURCE, "validate.yml")


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", True),
        ("id", 0),
        ("head_sha", "b" * 40),
        ("head_branch", "feature"),
        ("event", "workflow_dispatch"),
        ("path", ".github/workflows/other.yml"),
        ("html_url", "https://github.com/Other/repo/actions/runs/123"),
        ("status", "in_progress"),
        ("conclusion", "failure"),
        ("conclusion", "skipped"),
    ],
)
def test_source_run_rejects_unrelated_or_unfinished_metadata(field, value):
    """No guessed branch, event, completion, URL or skip substitutions."""
    data = run_fixture()
    data["workflow_runs"][0][field] = value
    with pytest.raises(ValueError):
        successful_source_run(data, SOURCE, "validate.yml")


def test_empty_duplicate_and_incomplete_run_pages_fail_closed():
    """An ambiguous response is not reduced to a convenient successful entry."""
    for data in (
        {"total_count": 0, "workflow_runs": []},
        {"total_count": 2, "workflow_runs": run_fixture()["workflow_runs"]},
        {"total_count": 2, "workflow_runs": run_fixture()["workflow_runs"] * 2},
    ):
        with pytest.raises(ValueError):
            successful_source_run(data, SOURCE, "validate.yml")


@pytest.mark.parametrize(
    "change",
    [
        {"draft": False},
        {"prerelease": True},
        {"target_commitish": "main"},
        {"target_commitish": "b" * 40},
        {"tag_name": "v0.2.0"},
    ],
)
def test_draft_never_accepts_published_or_different_source(change):
    """Old/public release assets cannot become an upload target."""
    data = {"draft": True, "prerelease": False, "tag_name": "v0.3.0", "target_commitish": SOURCE}
    draft_ready(data, SOURCE, "0.3.0")
    with pytest.raises(ValueError):
        draft_ready({**data, **change}, SOURCE, "0.3.0")


def assets_fixture():
    """Six distinct current platform artifacts, each with an independent provider digest."""
    names = [
        name
        for system, machine in (("windows", "amd64"), ("linux", "x86_64"), ("darwin", "arm64"))
        for name in names_for(system, machine, "0.3.0")
    ]
    return {"assets": [{"name": name, "size": 42, "digest": "sha256:" + "a" * 64} for name in names]}


def test_publication_requires_all_six_platform_assets():
    """Partial drafts are resumable, but cannot be published as complete releases."""
    data = assets_fixture()
    assert len(assets_ready(data, "0.3.0", complete=True)) == 6
    partial = {"assets": data["assets"][:2]}
    assert len(assets_ready(partial, "0.3.0", complete=False)) == 2
    with pytest.raises(ValueError):
        assets_ready(partial, "0.3.0", complete=True)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r["assets"].append(copy.deepcopy(r["assets"][0])),
        lambda r: r["assets"][0].update(name="unexpected.exe"),
        lambda r: r["assets"][0].update(size=True),
        lambda r: r["assets"][0].update(digest=None),
        lambda r: r["assets"][0].update(size=0),
    ],
)
def test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes(mutation):
    """Never infer a valid bundle from asset count alone."""
    data = assets_fixture()
    mutation(data)
    with pytest.raises(ValueError):
        assets_ready(data, "0.3.0", complete=True)


def analyses_fixture():
    """Three processed analyzer records; no workflow-success proxy or fabricated empty result count."""
    return [
        {
            "ref": "refs/heads/main",
            "commit_sha": SOURCE,
            "analysis_key": ".github/workflows/codeql.yml:analyze",
            "category": "/language:" + language,
            "error": "",
            "warning": "",
            "rules_count": 100,
            "tool": {"name": "CodeQL"},
        }
        for language in ("python", "javascript-typescript", "actions")
    ]


def test_actual_processed_security_records_are_required():
    """Passing jobs without every exact-source language result cannot authorize a draft."""
    rows = analyses_fixture()
    security_ready(rows, [], SOURCE)
    for changed in (rows[:-1], [], [{**row, "commit_sha": "b" * 40} for row in rows]):
        with pytest.raises(ValueError):
            security_ready(changed, [], SOURCE)
    with pytest.raises(ValueError):
        security_ready(rows, [{"state": "open"}], SOURCE)


@pytest.mark.parametrize(
    "changed",
    [
        {"ref": "refs/pull/1/merge"},
        {"analysis_key": "other.yml:analyze"},
        {"tool": {"name": "Other"}},
        {"error": "failed to extract"},
        {"warning": "missing source"},
        {"rules_count": 0},
        {"rules_count": True},
    ],
)
def test_partial_foreign_and_failed_security_results_fail_closed(changed):
    """Unrelated or incomplete scans are never substituted for the required current scan."""
    rows = analyses_fixture()
    rows[0].update(changed)
    with pytest.raises(ValueError):
        security_ready(rows, [], SOURCE)


def test_latest_failed_same_source_analysis_cannot_be_hidden_by_an_older_success():
    """Preserve the API's newest-first semantics when the same source is analyzed twice."""
    rows = analyses_fixture()
    failed = {**rows[0], "error": "analysis interrupted"}
    with pytest.raises(ValueError):
        security_ready([failed, *rows], [], SOURCE)


def built_fixture():
    """A current archive report with actual native lifecycle and embedded-source observations."""
    return {
        "mode": "built",
        "version": "0.3.1",
        "built_source": SOURCE,
        "source_dirty": False,
        "native_ui": {
            "compiled_native": True,
            "normal_owned_exit": True,
            "normal_exit_code": 0,
            "embedded_identity_matches_archive": True,
        },
    }


def test_upload_rejects_old_dirty_or_source_server_acceptance():
    """Real byte identity, native execution and normal Quit are all required together."""
    accepted_build(built_fixture(), SOURCE, "0.3.1")
    for change in (
        {"mode": "published"},
        {"version": "0.3.0"},
        {"built_source": "b" * 40},
        {"source_dirty": True},
        {"source_dirty": None},
    ):
        with pytest.raises(ValueError):
            accepted_build({**built_fixture(), **change}, SOURCE, "0.3.1")
    for change in (
        {"compiled_native": False},
        {"normal_owned_exit": False},
        {"normal_exit_code": 1},
        {"embedded_identity_matches_archive": False},
    ):
        report = built_fixture()
        report["native_ui"].update(change)
        with pytest.raises(ValueError):
            accepted_build(report, SOURCE, "0.3.1")


def unpublished_release():
    """A real-shaped draft with a version but no published Git-tag endpoint."""
    return {
        "id": 123,
        "tag_name": "v0.3.1",
        "target_commitish": SOURCE,
        "draft": True,
        "prerelease": False,
        "assets": [],
    }


def test_unpublished_draft_uses_listing_and_verified_id_without_published_tag(monkeypatch):
    """Regression for actual GitHub404 after successful draft creation."""
    release = unpublished_release()
    calls = []

    def provider(endpoint):
        calls.append(endpoint)
        assert "/tags/" not in endpoint
        return [release] if endpoint == "releases?per_page=100" else release

    monkeypatch.setattr(guard, "api", provider)
    assert guard.load_draft(SOURCE, "0.3.1") == release
    assert calls == ["releases?per_page=100", "releases/123"]


@pytest.mark.parametrize(
    "rows",
    [
        [unpublished_release(), unpublished_release()],
        [unpublished_release()] * 100,
        [{**unpublished_release(), "id": True}],
        [{**unpublished_release(), "id": -1}],
        {"releases": []},
        [None],
    ],
)
def test_ambiguous_incomplete_or_malformed_release_pages_fail_closed(rows):
    """Do not guess a draft from an ambiguous page or invalid identity."""
    with pytest.raises(ValueError):
        guard.release_for_version(rows, "0.3.1")


@pytest.mark.parametrize(
    "change",
    [
        {"id": 124},
        {"id": True},
        {"draft": False},
        {"prerelease": True},
        {"tag_name": "v0.3.0"},
        {"target_commitish": "b" * 40},
    ],
)
def test_id_resolution_rejects_changed_published_or_different_source(monkeypatch, change):
    """Both the authenticated listing and fresh ID response must describe the same unpublished source."""
    monkeypatch.setattr(
        guard,
        "api",
        lambda endpoint: [unpublished_release()] if "?" in endpoint else {**unpublished_release(), **change},
    )
    with pytest.raises(ValueError):
        guard.load_draft(SOURCE, "0.3.1")


def test_prepare_resumes_equal_draft_without_writes_or_retarget(monkeypatch):
    """An existing reviewed version is a read-only resume, never a force/clobber operation."""
    monkeypatch.setattr(guard, "source_ready", lambda source: source == SOURCE or pytest.fail("wrong source"))
    monkeypatch.setattr(
        guard, "api", lambda endpoint: [unpublished_release()] if "?" in endpoint else unpublished_release()
    )
    monkeypatch.setattr(guard, "command", lambda _args: pytest.fail("Existing release must not be rewritten"))
    guard.prepare_draft(SOURCE, "0.3.1")


def test_prepare_creates_only_missing_draft_with_literal_structured_notes(tmp_path, monkeypatch):
    """Notes containing quotes/newlines/shell-like text stay JSON data rather than shell commands."""
    notes = tmp_path / "docs/releases/v0.3.1.md"
    notes.parent.mkdir(parents=True)
    content = 'Authored notes\n"quoted" and $(literal) `text`\n'
    notes.write_text(content)
    monkeypatch.setattr(guard, "ROOT", tmp_path)
    monkeypatch.setattr(guard, "source_ready", lambda _source: None)
    created = []

    def provider(endpoint):
        return ([unpublished_release()] if created else []) if "?" in endpoint else unpublished_release()

    def command(arguments):
        assert arguments[:5] == [
            "gh",
            "api",
            "repos/JasonStys/applicant-evidence-studio/releases",
            "--method",
            "POST",
        ]
        payload = json.loads(Path(arguments[-1]).read_text())
        assert payload == {
            "tag_name": "v0.3.1",
            "target_commitish": SOURCE,
            "name": "Applicant Evidence Studio 0.3.1",
            "body": content,
            "draft": True,
            "prerelease": False,
        }
        created.append(payload)
        return json.dumps(unpublished_release())

    monkeypatch.setattr(guard, "api", provider)
    monkeypatch.setattr(guard, "command", command)
    guard.prepare_draft(SOURCE, "0.3.1")
    assert len(created) == 1

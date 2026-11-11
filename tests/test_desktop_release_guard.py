"""Jason Stys: independent exact-source, draft and portable-asset publication boundaries."""

# Index: copy@4, pytest@6, accepted_build@9, assets_ready@10, draft_ready@11, security_ready@12, successful_source_run@13, names_for@15, SOURCE@17, run_fixture@20, test_source_run_requires_exact_completed_main_identity@39, test_source_run_rejects_unrelated_or_unfinished_metadata@59, test_source_run_rejects_unrelated_or_unfinished_metadata.field@59, test_source_run_rejects_unrelated_or_unfinished_metadata.value@59, test_source_run_rejects_unrelated_or_unfinished_metadata.data@61, test_empty_duplicate_and_incomplete_run_pages_fail_closed@67, test_empty_duplicate_and_incomplete_run_pages_fail_closed.data@69, test_draft_never_accepts_published_or_different_source@88, test_draft_never_accepts_published_or_different_source.change@88, test_draft_never_accepts_published_or_different_source.data@90, assets_fixture@96, assets_fixture.names@98, assets_fixture.machine@100, assets_fixture.system@100, assets_fixture.name@101, assets_fixture.name@103, test_publication_requires_all_six_platform_assets@106, test_publication_requires_all_six_platform_assets.data@108, test_publication_requires_all_six_platform_assets.partial@110, test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes.r@119, test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes.r@120, test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes.r@121, test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes.r@122, test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes.r@123, test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes@126, test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes.mutation@126, test_portable_metadata_rejects_duplicates_foreign_and_missing_hashes.data@128, analyses_fixture@134, analyses_fixture.language@147, test_actual_processed_security_records_are_required@151, test_actual_processed_security_records_are_required.rows@153, test_actual_processed_security_records_are_required.changed@155, test_actual_processed_security_records_are_required.row@155, test_partial_foreign_and_failed_security_results_fail_closed@174, test_partial_foreign_and_failed_security_results_fail_closed.changed@174, test_partial_foreign_and_failed_security_results_fail_closed.rows@176, test_latest_failed_same_source_analysis_cannot_be_hidden_by_an_older_success@182, test_latest_failed_same_source_analysis_cannot_be_hidden_by_an_older_success.rows@184, test_latest_failed_same_source_analysis_cannot_be_hidden_by_an_older_success.failed@185, built_fixture@190, test_upload_rejects_old_dirty_or_source_server_acceptance@206, test_upload_rejects_old_dirty_or_source_server_acceptance.change@209, test_upload_rejects_old_dirty_or_source_server_acceptance.change@218, test_upload_rejects_old_dirty_or_source_server_acceptance.report@224
import copy

import pytest

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

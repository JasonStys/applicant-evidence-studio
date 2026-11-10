"""Jason Stys: exact-source draft-only uploads and complete portable publication.

Called only by the trusted main-branch release workflow. Never overwrites an
existing asset, accepts a published release, or logs token/environment values.
"""

# Index: argparse@8, json@9, os@10, platform@11, re@12, tomllib@13, MAX_DOWNLOAD@17, REPO@18, ROOT@19, command@20, digest@21, names_for@22, read_manifest@23, require@24, MAX_DOWNLOAD@28, REPO@29, ROOT@30, command@31, digest@32, names_for@33, read_manifest@34, require@35, version@39, version.value@41, api@46, api.endpoint@46, successful_source_run@51, successful_source_run.data@51, successful_source_run.source@51, successful_source_run.workflow@51, successful_source_run.rows@57, successful_source_run.run@59, source_ready@78, source_ready.source@78, source_ready.workflow@81, source_ready.data@82, draft_ready@86, draft_ready.product_version@86, draft_ready.release@86, draft_ready.source@86, assets_ready@98, assets_ready.complete@98, assets_ready.product_version@98, assets_ready.release@98, assets_ready.expected@100, assets_ready.machine@101, assets_ready.system@101, assets_ready.assets@103, assets_ready.result@105, assets_ready.asset@106, assets_ready.name@107, main@124, main.parser@126, main.args@128, main.source@129, main.product_version@137, main.tag@138, main.release@142, main.attached@144, main.machine@146, main.system@146, main.names@147, main.report@148, main.files@157, main.name@157, main.file@158, main.binary@168, main.manifest@169, main.file@175, main.fresh@179, main.actual@181
import argparse
import json
import os
import platform
import re
import tomllib

if __package__:
    from .portable_acceptance import (
        MAX_DOWNLOAD,
        REPO,
        ROOT,
        command,
        digest,
        names_for,
        read_manifest,
        require,
    )
else:
    from portable_acceptance import (
        MAX_DOWNLOAD,
        REPO,
        ROOT,
        command,
        digest,
        names_for,
        read_manifest,
        require,
    )


def version():
    """Read data-only product metadata without importing or executing the service."""
    value = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    require(bool(re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value)), "Invalid release version")
    return value


def api(endpoint):
    """Read only fixed repository metadata; writes use explicit gh subcommands below."""
    return json.loads(command(["gh", "api", f"repos/{REPO}/{endpoint}"]))


def successful_source_run(data, source, workflow):
    """Require returned identity/status as well as server-side query filters."""
    require(
        isinstance(data, dict) and isinstance(data.get("workflow_runs"), list),
        "Malformed source workflow response",
    )
    rows = data["workflow_runs"]
    require(len(rows) == 1 and data.get("total_count") == 1, "Exactly one complete main-push run is required")
    run = rows[0]
    require(type(run.get("id")) is int and 0 < run["id"] < 2**63, "Invalid source workflow identity")
    require(
        run.get("head_sha") == source and run.get("head_branch") == "main" and run.get("event") == "push",
        "Source run does not match the requested main commit",
    )
    require(
        run.get("path") in {f".github/workflows/{workflow}", f".github/workflows/{workflow}@refs/heads/main"},
        "Wrong validation workflow",
    )
    require(
        run.get("html_url") == f"https://github.com/{REPO}/actions/runs/{run['id']}", "Foreign source run URL"
    )
    require(
        run.get("status") == "completed" and run.get("conclusion") == "success",
        "Source validation must complete successfully",
    )


def source_ready(source):
    """Both source validation and real published-package acceptance must pass at this exact main."""
    require(api("git/ref/heads/main")["object"]["sha"] == source, "Main moved during release preparation")
    for workflow in ("validate.yml", "published-acceptance.yml"):
        data = api(f"actions/workflows/{workflow}/runs?branch=main&event=push&head_sha={source}&per_page=100")
        successful_source_run(data, source, workflow)


def draft_ready(release, source, product_version):
    """Reject published or retargeted releases immediately before every upload/publication."""
    require(
        release.get("draft") is True and release.get("prerelease") is False,
        "A stable unpublished draft is required; published bytes are immutable",
    )
    require(
        release.get("tag_name") == "v" + product_version and release.get("target_commitish") == source,
        "Draft tag/version/source differs from this checked workflow",
    )


def assets_ready(release, product_version, *, complete):
    """Only the documented six platform artifacts may be attached to this draft."""
    expected = set()
    for system, machine in (("windows", "amd64"), ("linux", "x86_64"), ("darwin", "arm64")):
        expected.update(names_for(system, machine, product_version))
    assets = release.get("assets")
    require(isinstance(assets, list), "Missing draft asset metadata")
    result = {}
    for asset in assets:
        name = asset.get("name")
        require(name in expected and name not in result, "Unexpected or duplicate draft asset")
        require(
            type(asset.get("size")) is int and 0 < asset["size"] <= MAX_DOWNLOAD, "Invalid draft asset size"
        )
        require(
            isinstance(asset.get("digest"), str)
            and bool(re.fullmatch(r"sha256:[0-9a-f]{64}", asset["digest"])),
            "Provider SHA-256 digest is required",
        )
        result[name] = asset
    require(
        not complete or set(result) == expected, "All three verified platform packages/checksums are required"
    )
    return result


def main():
    """Perform one explicitly named release operation; there is no force/clobber path."""
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("source", "draft", "upload", "publish"))
    args = parser.parse_args()
    source = os.environ.get("GITHUB_SHA", "")
    require(
        os.environ.get("GITHUB_ACTIONS") == "true"
        and os.environ.get("GITHUB_REF") == "refs/heads/main"
        and os.environ.get("GITHUB_REPOSITORY") == REPO,
        "Release operations require the trusted main workflow",
    )
    require(bool(re.fullmatch(r"[0-9a-f]{40}", source)), "Exact workflow source SHA required")
    product_version = version()
    tag = "v" + product_version
    if args.operation == "source":
        source_ready(source)
        return
    release = api("releases/tags/" + tag)
    draft_ready(release, source, product_version)
    attached = assets_ready(release, product_version, complete=args.operation == "publish")
    if args.operation == "upload":
        system, machine = platform.system().lower(), platform.machine().lower()
        names = names_for(system, machine, product_version)
        report = json.loads(
            (ROOT / "artifacts" / f"portable-acceptance-{system}.json").read_text(encoding="utf-8")
        )
        require(
            report.get("mode") == "built"
            and report.get("version") == product_version
            and report.get("native_ui", {}).get("compiled_native") is True,
            "Actual extracted native UI acceptance is required",
        )
        files = [(ROOT / "release" / name) for name in names]
        for file in files:
            require(file.is_file() and not file.is_symlink(), "Release asset must be a regular built file")
            require(file.stat().st_size <= MAX_DOWNLOAD, "Built asset exceeds release budget")
            if file.name in attached:
                require(
                    attached[file.name]["size"] == file.stat().st_size
                    and attached[file.name]["digest"] == "sha256:" + digest(file),
                    "Existing draft asset differs; refusing replacement",
                )
        require(digest(files[0]) == report.get("archive_sha256"), "Package changed after native acceptance")
        binary = "ApplicantEvidenceStudio" + (".exe" if system == "windows" else "")
        manifest = read_manifest(files[1], files[0].name, binary)
        require(
            manifest[files[0].name] == report["archive_sha256"]
            and manifest[binary] == report["binary_sha256"],
            "Checksum sidecar changed after native acceptance",
        )
        for file in files:
            if file.name not in attached:
                draft_ready(api("releases/tags/" + tag), source, product_version)
                command(["gh", "release", "upload", tag, str(file), "--repo", REPO])
            fresh = api("releases/tags/" + tag)
            draft_ready(fresh, source, product_version)
            actual = assets_ready(fresh, product_version, complete=False)[file.name]
            require(
                actual["digest"] == "sha256:" + digest(file) and actual["size"] == file.stat().st_size,
                "Provider asset differs from accepted local bytes",
            )
    elif args.operation == "publish":
        source_ready(source)
        command(["gh", "release", "edit", tag, "--repo", REPO, "--draft=false"])


if __name__ == "__main__":
    main()

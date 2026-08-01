import hashlib
import json
import re
import sys
from pathlib import Path


ALLOWED_VERDICTS = {"VERIFIED", "FALSIFIED", "BLOCKED"}
ALLOWED_CONFIDENCE = {"HIGH", "MEDIUM", "LOW"}
REQUIRED_EVIDENCE_FIELDS = ["code", "raw", "checker", "control", "environment"]
TEXT_SUFFIXES = {"", ".css", ".html", ".js", ".json", ".md", ".py", ".toml", ".txt", ".lock"}
SECRET_PATTERNS = [
    re.compile(r"hf_[A-Za-z0-9]{24,}"),
    re.compile(r"ghp_[A-Za-z0-9]{24,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{24,}"),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def flatten(node: dict) -> list[dict]:
    return [node, *[descendant for child in node.get("children", []) for descendant in flatten(child)]]


def linked_paths(markdown_path: Path, candidate: Path) -> set[str]:
    links = set()
    for destination in re.findall(r"\[[^]]*\]\(([^)]+)\)", markdown_path.read_text()):
        destination = destination.split("#", 1)[0]
        if not destination or destination.startswith(("http://", "https://", "mailto:", "#/")):
            continue
        resolved = (markdown_path.parent / destination).resolve()
        resolved.relative_to(candidate.resolve())
        links.add(resolved.relative_to(candidate.resolve()).as_posix())
    return links


def main() -> None:
    candidate = Path(sys.argv[1]).resolve()
    judged_manifest = json.loads(Path(sys.argv[2]).read_text())
    judged_files = judged_manifest["files"]
    candidate_files = {
        path.relative_to(candidate).as_posix(): path
        for path in candidate.rglob("*")
        if path.is_file() and ".cache" not in path.parts
    }
    assert set(judged_files) <= set(candidate_files)

    mutable = set(judged_manifest["mutable_root_paths"])
    revision = judged_manifest["revision"]
    for relative, expected_sha in judged_files.items():
        if relative not in mutable:
            assert sha256(candidate_files[relative]) == expected_sha
            continue
        archived = candidate / "historical" / f"judged-{revision}" / relative
        assert archived.is_file()
        assert sha256(archived) == expected_sha

    logbook = json.loads((candidate / "logbook.json").read_text())
    archived_logbook = json.loads(
        (candidate / "historical" / f"judged-{revision}" / "logbook.json").read_text()
    )
    nodes = flatten(logbook["root"])
    assert len({node["slug"] for node in nodes}) == len(nodes)
    assert all((candidate / node["file"]).is_file() for node in nodes)
    assert logbook["root"]["children"][0]["slug"] == "current-verification"
    historical = [node for node in nodes if node["title"] == "Historical rejected baseline"]
    assert len(historical) == 1
    assert historical[0]["children"] == [archived_logbook["root"]]

    visibility_path = candidate / "evidence" / "release" / "visibility_matrix.json"
    visibility = json.loads(visibility_path.read_text())
    rows = visibility["rows"]
    assert [row["claim"] for row in rows] == [1, 2, 3, 4, 5, 6]
    tree_files = {node["file"] for node in nodes}
    for row in rows:
        assert row["reviewer_verdict"] in ALLOWED_VERDICTS
        assert row["canonical_page"] in tree_files
        assert row["data_inline"] is True
        assert row["exact_claim_tested"] is True
        assert row["limitations_inline"] is True
        assert row["source_quantifiers_inline"] is True
        assert row["judge_criticism_answered"] is True
        page = candidate / row["canonical_page"]
        direct_links = linked_paths(page, candidate)
        for field in REQUIRED_EVIDENCE_FIELDS:
            assert row[field]
            for relative in row[field]:
                assert relative in candidate_files
                assert relative in direct_links

    release_report = json.loads((candidate / "evidence" / "release" / "release_report.json").read_text())
    assert release_report["previous_live_judged_score"] == "5/12"
    assert release_report["current_hf_head"] == revision
    assert release_report["current_judge_head"] == revision
    assert release_report["conservative_projected_score_range"]
    assert release_report["best_supported_possible_new_score"]
    assert release_report["best_supported_possible_new_score_is_forecast"] is True
    assert release_report["publication_action"] == "update existing Space DineshAI/uhNn8S6rEb via text-only API"
    claim_rows = release_report["claims"]
    assert [row["claim"] for row in claim_rows] == [1, 2, 3, 4, 5, 6]
    for row in claim_rows:
        assert {"current_points", "possible_points", "confidence", "evidence_status", "basis_and_remaining_risk"} <= set(row)
        assert row["confidence"] in ALLOWED_CONFIDENCE
        assert row["evidence_status"] in ALLOWED_VERDICTS
        if row["confidence"] == "LOW":
            assert len(row["verification_routes"]) >= 3
            assert len(row["falsification_routes"]) >= 1

    red_team = json.loads((candidate / "evidence" / "release" / "red_team.json").read_text())
    assert red_team["scope"] == "downloaded candidate only"
    assert red_team["canonical_entrypoint"] == logbook["root"]["file"]
    assert len(red_team["rounds"]) >= 2
    for review_round in red_team["rounds"]:
        assert review_round["files_opened"]
        assert all(relative in candidate_files for relative in review_round["files_opened"])
        assert [review["claim"] for review in review_round["claim_reviews"]] == [1, 2, 3, 4, 5, 6]
    final_review = red_team["rounds"][-1]
    assert final_review["missing_or_unverifiable"] == []
    assert all(review["current_verifier_located"] is True for review in final_review["claim_reviews"])
    assert all(review["conclusion"] in ALLOWED_VERDICTS for review in final_review["claim_reviews"])

    root_file = candidate / logbook["root"]["file"]
    root_text = root_file.read_text()
    assert "Previous live judged score: `5/12`" in root_text
    assert "forecast" in root_text.lower()
    assert "awaiting judge" not in root_text.lower()
    assert "12/12" not in root_text or "forecast" in root_text.lower()

    allowlist_relative = "evidence/release/upload_allowlist.json"
    hashes_relative = "evidence/release/upload_manifest.sha256"
    changed = {
        relative
        for relative, path in candidate_files.items()
        if relative not in judged_files or sha256(path) != judged_files[relative]
    }
    assert all(candidate_files[relative].suffix.lower() in TEXT_SUFFIXES for relative in changed)
    allowlist = json.loads((candidate / allowlist_relative).read_text())
    assert allowlist["paths"] == sorted(set(allowlist["paths"]))
    assert set(allowlist["paths"]) == changed
    manifest = {}
    for line in (candidate / hashes_relative).read_text().splitlines():
        digest, relative = line.split("  ", 1)
        assert re.fullmatch(r"[0-9a-f]{64}", digest)
        manifest[relative] = digest
    assert set(manifest) == changed - {hashes_relative}
    assert all(sha256(candidate / relative) == digest for relative, digest in manifest.items())

    scanned = 0
    for relative, path in candidate_files.items():
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(errors="replace")
        assert not any(pattern.search(text) for pattern in SECRET_PATTERNS), relative
        scanned += 1

    print(
        json.dumps(
            {
                "verdict": "PASS",
                "judged_file_subset": True,
                "unchanged_historical_files": len(judged_files) - len(mutable),
                "archived_mutable_files": len(mutable),
                "navigation_nodes": len(nodes),
                "current_verification_first": True,
                "visibility_rows_complete": len(rows),
                "release_forecast_rows": len(claim_rows),
                "red_team_rounds": len(red_team["rounds"]),
                "text_upload_paths": len(changed),
                "upload_manifest_verified": True,
                "text_files_scanned_for_secrets": scanned,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

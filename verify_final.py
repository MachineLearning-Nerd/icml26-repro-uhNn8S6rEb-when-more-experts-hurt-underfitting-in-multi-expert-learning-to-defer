#!/usr/bin/env python3
"""Verify this dossier and the live normalized GitHub state."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CANONICAL = (
    "MachineLearning-Nerd",
    "MachineLearning-Nerd@users.noreply.github.com",
)
REPOSITORY = "icml26-when-more-experts-hurt-underfitting-in-multi-expert-learning-to-defer"
EXPECTED_OVERALL_VERDICT = "PARTIAL_CLAIMS_1_TO_3_VERIFIED_SCOPED_CLAIM_4_LITERAL_THEOREM_FALSIFIED_CLAIM_5_SOURCE_TABLE_FALSIFIED_CLAIM_6_BLOCKED"
EXPECTED_PUBLICATION_BOUNDARY = "HISTORICAL_5_OF_12_NO_CURRENT_SCORE_CLAIM_6_BLOCKED_NO_FULL_REPRODUCTION"
REQUIRED_PATHS = [
    "README.md",
    "branch-audit.md",
    "BRANCH_AUDIT.md",
    "CLAIM_EVIDENCE.md",
    "SOURCE_AUDIT.md",
    "ENVIRONMENT.md",
    "REPORT.md",
    "AUTHOR_THANK_YOU.md",
    "CITATION.cff",
    "claims.json",
    "STATUS.md",
    "reproduction_verdicts.json",
    "EVIDENCE_MANIFEST.json",
    "AUTONOMOUS_STATE.json",
    "verify_final.py",
]
AUDIT_BRANCHES = {
    "audit/baseline-exact-theorem",
    "audit/channels-last-micebone-shard",
    "audit/micebone-annotations",
    "audit/micebone-majority-tie-rules",
    "audit/micebone-shard-pipeline",
    "audit/micebone-target-labels",
    "audit/micebone-target-vote-pools",
    "audit/official-micebone-release",
    "audit/table-2-consistency-claim",
}
RELEASE_BRANCHES = {
    "release/claim-6-aggregate-preregistered",
    "release/exact-theory-evidence",
    "release/universal-theory-certificates",
}
EXTRA_EXPERIMENT_BRANCHES = {
    "experiment/micebone-corrected-cpu-training",
    "experiment/micebone-cpu-training",
    "experiment/micebone-figure-2-sweep",
}
EXPECTED_BRANCHES = {"main"} | AUDIT_BRANCHES | RELEASE_BRANCHES | EXTRA_EXPERIMENT_BRANCHES
for _j in (2, 4, 6, 8):
    for _method in ("ce", "ova", "picce-ce", "picce-ova"):
        for _seed in (260217144, 260217145, 260217146):
            EXPECTED_BRANCHES.add(
                f"experiment/micebone-j{_j}-{_method}-seed-{_seed}"
            )


def fail(message: str) -> None:
    print(f"FINAL_AUDIT=FAILED {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def run(*args: str) -> str:
    result = subprocess.run(
        args,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        fail(f"command failed: {' '.join(args)}\n{result.stderr.strip()}")
    return result.stdout


def tracked_exists(path: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"HEAD:{path}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    return result.returncode == 0


def current_bytes(path: str) -> bytes:
    local = ROOT / path
    if local.exists():
        return local.read_bytes()
    result = subprocess.run(
        ["git", "show", f"HEAD:{path}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    if result.returncode:
        fail(f"main-branch path is unavailable: {path}")
    return result.stdout


def git_object_bytes(ref: str, path: str) -> bytes:
    for candidate in (ref, f"origin/{ref}"):
        result = subprocess.run(
            ["git", "show", f"{candidate}:{path}"],
            cwd=ROOT,
            check=False,
            capture_output=True,
        )
        if result.returncode == 0:
            return result.stdout
    fail(f"branch evidence is unavailable: {ref}:{path}")
    return b""


def json_bytes(raw: bytes, label: str) -> object:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {label}: {exc}")
    return None


def current_json(path: str) -> object:
    return json_bytes(current_bytes(path), path)


def branch_json(ref: str, path: str) -> object:
    return json_bytes(git_object_bytes(ref, path), f"{ref}:{path}")


def verify_manifest() -> None:
    manifest = current_json("EVIDENCE_MANIFEST.json")
    require(isinstance(manifest, dict), "manifest must be an object")
    require(manifest.get("schema_version") == 1, "unsupported manifest schema")
    require(manifest.get("hash_algorithm") == "sha256", "manifest hash algorithm changed")
    entries = manifest.get("entries")
    require(isinstance(entries, list) and entries, "evidence manifest is empty")
    seen = set()
    for entry in entries:
        require(isinstance(entry, dict), "manifest entry is not an object")
        path = entry.get("path")
        expected = entry.get("sha256")
        require(isinstance(path, str), "manifest entry has no path")
        require(isinstance(expected, str) and len(expected) == 64, f"bad hash for {path}")
        key = (entry.get("ref"), path)
        require(key not in seen, f"duplicate manifest entry: {key}")
        seen.add(key)
        raw = (
            git_object_bytes(entry["ref"], path)
            if entry.get("ref")
            else current_bytes(path)
        )
        actual = hashlib.sha256(raw).hexdigest()
        require(actual == expected, f"hash mismatch for {key}")


def main() -> None:
    origin = run("git", "config", "--get", "remote.origin.url").strip()
    require(
        origin in {
            f"https://github.com/MachineLearning-Nerd/{REPOSITORY}.git",
            f"git@github.com:MachineLearning-Nerd/{REPOSITORY}.git",
        },
        f"unexpected origin: {origin}",
    )

    symref = run("git", "ls-remote", "--symref", "origin", "HEAD")
    require("ref: refs/heads/main\tHEAD" in symref, "origin/HEAD is not main")

    remote_lines = run("git", "ls-remote", "--heads", "origin").splitlines()
    remote_heads = {}
    for line in remote_lines:
        commit, ref = line.split("\t", 1)
        require(ref.startswith("refs/heads/"), f"unexpected remote ref: {ref}")
        remote_heads[ref.removeprefix("refs/heads/")] = commit
    require(len(EXPECTED_BRANCHES) == 64, "verifier branch contract is malformed")
    require(set(remote_heads) == EXPECTED_BRANCHES, "remote branch set is not the normalized 64-branch set")
    require("orx/" not in "\n".join(remote_heads), "legacy orx branch remains live")
    require("work/" not in "\n".join(remote_heads), "legacy work branch remains live")
    require(
        remote_heads["main"] == run("git", "rev-parse", "origin/main").strip(),
        "local origin/main disagrees with live origin",
    )

    local_heads = set(
        run("git", "for-each-ref", "--format=%(refname:strip=2)", "refs/heads")
        .splitlines()
    )
    require(local_heads <= EXPECTED_BRANCHES, "unexpected local branch name")
    refs = run("git", "for-each-ref", "--format=%(refname)", "refs").splitlines()
    require(not any("refs/original/" in ref for ref in refs), "refs/original remains")

    identities = set()
    for line in run("git", "log", "--all", "--format=%an\t%ae\t%cn\t%ce").splitlines():
        if line.strip():
            identities.add(tuple(line.split("\t")))
    require(
        identities == {(CANONICAL[0], CANONICAL[1], CANONICAL[0], CANONICAL[1])},
        f"non-canonical reachable identity: {sorted(identities)}",
    )
    require(
        "co-authored-by:" not in run("git", "log", "--all", "--format=%B").lower(),
        "co-author trailer found",
    )
    commit_count = int(run("git", "rev-list", "--count", "--all").strip())
    require(commit_count >= 102, f"unexpectedly short history: {commit_count}")

    for path in REQUIRED_PATHS:
        require(
            (ROOT / path).exists() or tracked_exists(path),
            f"required path missing: {path}",
        )

    claims = current_json("claims.json")
    require(isinstance(claims, dict), "claims.json must be an object")
    require(claims.get("repository") == f"MachineLearning-Nerd/{REPOSITORY}", "claims repository mismatch")
    require(claims.get("overall_verdict") == EXPECTED_OVERALL_VERDICT, "claims overall verdict changed")
    require(claims.get("publication_boundary") == EXPECTED_PUBLICATION_BOUNDARY, "claims publication boundary changed")
    require(claims.get("publication_allowed") is False, "publication block changed")
    require(claims.get("score_claim") is False, "score claim boundary changed")
    require(claims.get("official_author_endorsement") is False, "author endorsement boundary changed")
    rows = claims.get("claims", [])
    require(len(rows) == 6, "claims.json must contain six claims")
    statuses = [row.get("status") for row in rows]
    require(
        statuses
        == [
            "verified_scoped",
            "verified_scoped",
            "verified_scoped",
            "falsified_literal_theorem_formula",
            "falsified_source_table",
            "blocked_source_faithful_empirical",
        ],
        f"unexpected claim statuses: {statuses}",
    )
    official = claims.get("official_rejudge", {})
    require(official.get("score") == "5/12", "historical score record changed")
    require(official.get("current_score_not_claimed") is True, "current score is being implied")

    reproduction = current_json("reproduction_verdicts.json")
    require(isinstance(reproduction, dict), "reproduction verdicts must be an object")
    require(reproduction.get("repository") == f"MachineLearning-Nerd/{REPOSITORY}", "reproduction repository mismatch")
    require(reproduction.get("overall_verdict") == EXPECTED_OVERALL_VERDICT, "reproduction overall verdict changed")
    require(reproduction.get("publication_boundary") == EXPECTED_PUBLICATION_BOUNDARY, "reproduction publication boundary changed")
    require(reproduction.get("publication_allowed") is False, "reproduction publication block changed")
    require(reproduction.get("score_claim") is False, "reproduction score boundary changed")
    require(reproduction.get("official_author_endorsement") is False, "reproduction endorsement boundary changed")
    reproduction_rows = reproduction.get("verdicts", {})
    require(
        [reproduction_rows[str(i)].get("verdict") for i in range(1, 7)]
        == statuses,
        "reproduction verdict rows changed",
    )

    state = current_json("AUTONOMOUS_STATE.json")
    require(state.get("phase") == "published_scoped_partial_audit_historical_5_of_12_claim_6_blocked", "state is not final")
    require(state.get("branch_count") == 64, "state branch count changed")
    require(state.get("default_branch") == "main", "state default branch changed")
    require(state.get("publication_allowed") is False, "state publication block changed")
    require(state.get("overall_verdict") == EXPECTED_OVERALL_VERDICT, "state overall verdict changed")
    require(state.get("publication_boundary") == EXPECTED_PUBLICATION_BOUNDARY, "state publication boundary changed")
    require(state.get("score_claim") is False, "state score boundary changed")
    require(state.get("official_author_endorsement") is False, "state endorsement boundary changed")
    require(state.get("verified_reachable_commits") == 102, "state commit count changed")
    require(state.get("attribution") == {
        "name": "MachineLearning-Nerd",
        "email": "MachineLearning-Nerd@users.noreply.github.com",
    }, "state attribution changed")
    require(isinstance(state.get("last_known_git_commit"), str) and len(state["last_known_git_commit"]) == 40, "state has no recorded dossier commit")

    readme = current_bytes("README.md").decode("utf-8")
    status = current_bytes("STATUS.md").decode("utf-8")
    report = current_bytes("REPORT.md").decode("utf-8")
    for marker in (
        EXPECTED_OVERALL_VERDICT,
        EXPECTED_PUBLICATION_BOUNDARY,
        "publication_allowed=false",
        "score_claim=false",
        "official_author_endorsement=false",
        "reproduction_verdicts.json",
    ):
        require(marker in readme, f"README missing status marker: {marker}")
    for marker in (
        EXPECTED_OVERALL_VERDICT,
        EXPECTED_PUBLICATION_BOUNDARY,
        "publication_allowed=false",
        "score_claim=false",
        "official_author_endorsement=false",
        "reproduction_verdicts.json",
    ):
        require(marker in status, f"STATUS missing status marker: {marker}")
    for marker in (EXPECTED_OVERALL_VERDICT, "publication_allowed=false", "score_claim=false", "official_author_endorsement=false"):
        require(marker in report, f"REPORT missing status marker: {marker}")

    contract = branch_json(
        "release/universal-theory-certificates",
        ".openresearch/artifacts/claim_contract.json",
    )
    require(
        [contract[str(i)]["result"] for i in range(1, 7)]
        == ["VERIFIED", "VERIFIED", "VERIFIED", "FALSIFIED", "FALSIFIED", "BLOCKED"],
        "release claim contract changed",
    )
    theory = branch_json(
        "release/universal-theory-certificates",
        ".openresearch/artifacts/theory_results.json",
    )
    require(theory["claims"]["1"]["aggregation_identity"] == "A_J = 3J/4", "C1 certificate changed")
    require(theory["claims"]["2"]["exhaustive_correlated_checks"] == 873, "C2 check count changed")
    require(
        theory["claims"]["3"]["consistency_certificate"]["ce_population_minimizer"]
        == "q_y=eta_y/(1+V); normalizing q_1..q_K recovers eta exactly",
        "C3 certificate changed",
    )
    require(
        theory["claims"]["4"]["ce_risk_minimizer_u_j_star"] == {"denominator": 5, "numerator": 2},
        "C4 exact CE optimum changed",
    )
    require(
        theory["claims"]["4"]["theorem_6a_printed_u_j_star"]
        == {"denominator": 20, "numerator": 7},
        "C4 printed value changed",
    )
    require(
        theory["claims"]["4"]["absolute_contradiction"]
        == {"denominator": 20, "numerator": 1},
        "C4 discrepancy changed",
    )
    require(
        theory["claims"]["5"]["reported_values"]["vanilla_ce_error"]
        == {"denominator": 100, "numerator": 1517}
        and theory["claims"]["5"]["reported_values"]["picce_ce_error"]
        == {"denominator": 100, "numerator": 1523},
        "C5 source-table values changed",
    )
    source = git_object_bytes(
        "release/universal-theory-certificates",
        "source_audit.md",
    ).decode("utf-8")
    require(
        "d381ed2e443e7f2cdb48f51bf0e8cf8d07333bd4ae484fc6a0e4c0922bf67fdc" in source,
        "source hash is not pinned",
    )
    compact_source = source.replace(" ", "")
    require("(15.17,60.92)" in compact_source and "(15.23,69.28)" in compact_source, "Table 2 audit changed")

    verifier = branch_json(
        "release/universal-theory-certificates",
        ".openresearch/artifacts/verifier_output.json",
    )
    independent = branch_json(
        "release/universal-theory-certificates",
        ".openresearch/artifacts/independent_checker_output.json",
    )
    require(verifier.get("exit_code") == 0 and verifier.get("stdout", "").startswith("PASS:"), "primary verifier did not pass")
    require(independent.get("exit_code") == 0 and independent.get("stdout", "").startswith("PASS:"), "independent verifier did not pass")
    for path in ("proof_certificates.py", "independent_proof_check.py", "verify_proof_certificates.py"):
        git_object_bytes("release/universal-theory-certificates", path)

    claim6_contract = branch_json(
        "release/claim-6-aggregate-preregistered",
        ".openresearch/artifacts/claim6_contract.json",
    )
    require(claim6_contract["primary_metric"] == "final-epoch test classifier accuracy percent", "Claim 6 metric changed")
    calibration = branch_json(
        "release/claim-6-aggregate-preregistered",
        ".openresearch/artifacts/micebone_training_j2_ce_seed260217144.json",
    )
    require(calibration["accepted_scientific_result"] is False, "calibration was promoted to evidence")
    require(calibration["training_contract"]["epochs"] == 1, "calibration epoch count changed")
    rerun = branch_json(
        "release/claim-6-aggregate-preregistered",
        ".openresearch/artifacts/rerun_manifest.json",
    )
    stop = rerun["campaign_stop"]
    require(stop["publication_performed"] is False, "stopped campaign was published")
    require(stop["scientific_verdict_from_partial_runs"] is None, "partial Claim 6 verdict was asserted")

    verify_manifest()
    statuses_text = ",".join(
        f"{row['id']}:{row['status']}" for row in rows
    )
    print(
        f"FINAL_AUDIT=VERIFIED branches={len(remote_heads)} commits={commit_count} "
        f"claims={statuses_text} historical_score={official['score']} c6=blocked"
    )


if __name__ == "__main__":
    main()

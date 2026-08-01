import hashlib
import json
import math
import statistics
from pathlib import Path


EXPERT_COUNTS = [2, 4, 6, 8]
METHODS = ["ce", "picce_ce", "ova", "picce_ova"]
SEEDS = [260217144, 260217145, 260217146]
TARGET = "complete_annotator_majority_priority_g_ug_nr"
T_CRITICAL_95_DF2 = 4.302652729911275


def load_dataset_audit(artifacts: Path) -> dict:
    inventory_path = artifacts / "micebone_inventory.json"
    annotations_path = artifacts / "micebone_annotations.json"
    targets_path = artifacts / "micebone_targets.json"
    inventory = json.loads(inventory_path.read_text())
    annotations = json.loads(annotations_path.read_text())
    targets = json.loads(targets_path.read_text())
    assert inventory["source_url"] == "https://zenodo.org/records/8115942/files/MiceBone.zip?download=1"
    assert inventory["record_id"] == 8115942
    assert inventory["archive_bytes"] == 680_507_926
    assert inventory["archive_md5"] == "8a4026c22f07373f022d9ab4818089ec"
    assert inventory["zip_crc_all_members_pass"] is True
    assert inventory["image_count"] == 7240
    assert inventory["paper_contract"]["train_images"] == 5697
    assert inventory["paper_contract"]["test_images"] == 1543
    assert annotations["unique_image_count"] == 7240
    assert annotations["fold_counts"] == {
        "fold1": 1540,
        "fold2": 1513,
        "fold3": 1325,
        "fold4": 1319,
        "fold5": 1543,
    }
    assert annotations["complete_annotator_count"] == 8
    assert [expert["expert_id"] for expert in targets["experts"]] == [
        "047", "290", "533", "534", "580", "581", "966", "745"
    ]
    best = targets["global_priority_tie_rules_ranked_by_table_3_mae"][0]
    assert best["vote_pool"] == "complete_annotators"
    assert best["priority"] == ["g", "ug", "nr"]
    assert best["exact_rounded_matches_out_of_16"] == 14
    assert math.isclose(best["mean_absolute_error_percentage_points"], 0.009665244970945785)
    assert math.isclose(best["maximum_absolute_error_percentage_points"], 0.10635773213972755)
    return {
        "official_record": "Zenodo 8115942",
        "archive_bytes": inventory["archive_bytes"],
        "archive_md5": inventory["archive_md5"],
        "zip_crc_all_members_pass": inventory["zip_crc_all_members_pass"],
        "images": inventory["image_count"],
        "fold_counts": annotations["fold_counts"],
        "train_images": 5697,
        "test_images": 1543,
        "expert_ids": [expert["expert_id"] for expert in targets["experts"]],
        "target_vote_pool": best["vote_pool"],
        "target_priority": best["priority"],
        "table3_exact_rounded_matches_out_of_16": best["exact_rounded_matches_out_of_16"],
        "table3_mae_percentage_points": best["mean_absolute_error_percentage_points"],
        "table3_max_error_percentage_points": best["maximum_absolute_error_percentage_points"],
        "files": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [inventory_path, annotations_path, targets_path]
        },
    }


def load_job_accounting(artifacts: Path, shard_manifest: dict) -> dict:
    path = artifacts / "job_accounting.json"
    accounting = json.loads(path.read_text())
    assert accounting["pricing_source"] == "https://huggingface.co/docs/hub/jobs-pricing"
    assert accounting["cpu_upgrade_hourly_usd"] == 0.03
    assert accounting["cpu_upgrade_per_minute_usd"] == 0.0005
    assert accounting["billing_unit"] == "minute"
    expected = {shard["job_id"]: shard for shard in shard_manifest["shards"]}
    observed = {job["job_id"]: job for job in accounting["jobs"]}
    assert set(observed) == set(expected)
    for job_id, job in observed.items():
        shard = expected[job_id]
        assert job["run_id"] == shard["run_id"]
        assert (job["j"], job["method"], job["seed"]) == (shard["j"], shard["method"], shard["seed"])
        assert job["status"] == "COMPLETED"
        assert job["flavor"] == "cpu-upgrade"
        assert job["running_seconds"] > 0
        assert job["billed_minutes"] == math.ceil(job["running_seconds"] / 60)
        assert math.isclose(job["cost_usd"], job["billed_minutes"] * 0.0005)
    total_running_seconds = sum(job["running_seconds"] for job in observed.values())
    total_billed_minutes = sum(job["billed_minutes"] for job in observed.values())
    total_cost_usd = sum(job["cost_usd"] for job in observed.values())
    assert accounting["job_count"] == 48
    assert accounting["total_running_seconds"] == total_running_seconds
    assert accounting["total_billed_minutes"] == total_billed_minutes
    assert math.isclose(accounting["total_cost_usd"], total_cost_usd)
    return {
        "job_count": 48,
        "pricing_source": accounting["pricing_source"],
        "pricing_retrieved_at": accounting["pricing_retrieved_at"],
        "cpu_upgrade_hourly_usd": accounting["cpu_upgrade_hourly_usd"],
        "total_running_seconds": total_running_seconds,
        "total_running_hours": total_running_seconds / 3600,
        "total_billed_minutes": total_billed_minutes,
        "total_cost_usd": total_cost_usd,
        "raw_file": path.name,
        "raw_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def load_rows(artifacts: Path) -> list[dict]:
    rows = []
    for experts in EXPERT_COUNTS:
        for method in METHODS:
            for seed in SEEDS:
                name = f"micebone_training_j{experts}_{method}_seed{seed}.json"
                path = artifacts / name
                suffix = f"j{experts}_{method}_seed{seed}"
                environment_path = artifacts / f"environment_{suffix}.json"
                verifier_path = artifacts / f"shard_verifier_{suffix}.json"
                negative_path = artifacts / f"shard_negative_{suffix}.json"
                negative_output_path = artifacts / f"shard_negative_output_{suffix}.json"
                payload = json.loads(path.read_text())
                environment = json.loads(environment_path.read_text())
                verifier = json.loads(verifier_path.read_text())
                negative_output = json.loads(negative_output_path.read_text())
                contract = payload["training_contract"]
                assert payload["accepted_scientific_result"] is True
                assert contract == {
                    "epochs": 100,
                    "expert_counts": [experts],
                    "methods": [method],
                    "seeds": [seed],
                    "target": TARGET,
                    "cpu_memory_format": "channels_last",
                    "accepted_scientific_result": True,
                }
                assert len(payload["runs"]) == 1
                run = payload["runs"][0]
                assert (run["experts"], run["method"], run["seed"], run["epochs"]) == (
                    experts,
                    method,
                    seed,
                    100,
                )
                assert [epoch["epoch"] for epoch in run["history"]] == list(range(1, 101))
                assert all(epoch["samples"] == 1543 for epoch in run["history"])
                assert all(
                    math.isfinite(epoch[key])
                    for epoch in run["history"]
                    for key in ["train_loss", "classifier_accuracy_percent", "system_error_percent", "coverage_percent"]
                )
                accuracy = run["history"][-1]["classifier_accuracy_percent"]
                assert math.isfinite(accuracy)
                assert run["runtime_seconds"] > 0
                assert environment["fixed_command"] == "uv run --frozen python run.py"
                assert environment["seed"] == seed
                assert environment["estimated_cores"] == 8
                assert environment["selected_flavor"] == "cpu-upgrade"
                assert environment["container_image"] == "ghcr.io/astral-sh/uv:python3.12-bookworm-slim"
                assert environment["effective_cpu_quota"] == 8
                assert environment["cuda_available"] is False
                assert environment["cuda_device_count"] == 0
                assert environment["stage"] == "micebone-training-shard"
                assert environment["runtime_seconds"] >= run["runtime_seconds"]
                assert verifier["exit_code"] == 0
                assert negative_output["exit_code"] != 0
                assert negative_path.is_file()
                rows.append(
                    {
                        "experts": experts,
                        "method": method,
                        "seed": seed,
                        "final_epoch": 100,
                        "test_samples": 1543,
                        "classifier_accuracy_percent": accuracy,
                        "raw_file": name,
                        "raw_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "training_runtime_seconds": run["runtime_seconds"],
                        "environment_file": environment_path.name,
                        "environment_sha256": hashlib.sha256(environment_path.read_bytes()).hexdigest(),
                        "git_sha": environment["git_sha"],
                        "selected_flavor": environment["selected_flavor"],
                        "actual_logical_cpus": environment["actual_logical_cpus"],
                        "actual_cpu_affinity": environment["actual_cpu_affinity"],
                        "effective_cpu_quota": environment["effective_cpu_quota"],
                        "cuda_available": environment["cuda_available"],
                        "environment_runtime_seconds": environment["runtime_seconds"],
                        "shard_verifier_file": verifier_path.name,
                        "shard_verifier_sha256": hashlib.sha256(verifier_path.read_bytes()).hexdigest(),
                        "shard_verifier_exit": verifier["exit_code"],
                        "negative_control_file": negative_path.name,
                        "negative_control_sha256": hashlib.sha256(negative_path.read_bytes()).hexdigest(),
                        "negative_control_output_file": negative_output_path.name,
                        "negative_control_output_sha256": hashlib.sha256(negative_output_path.read_bytes()).hexdigest(),
                        "negative_control_exit": negative_output["exit_code"],
                    }
                )
    assert len(rows) == 48
    return rows


def aggregate_claim6(artifacts: Path) -> dict:
    manifest_path = artifacts.parents[1] / "shard_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest_cells = {
        (shard["j"], shard["method"], shard["seed"])
        for shard in manifest["shards"]
    }
    assert manifest["integrity"] == {
        "shard_count": 48,
        "unique_cells": 48,
        "unique_experiments": 48,
        "unique_runs": 48,
        "unique_jobs": 48,
    }
    assert manifest_cells == {
        (experts, method, seed)
        for experts in EXPERT_COUNTS
        for method in METHODS
        for seed in SEEDS
    }
    dataset_audit = load_dataset_audit(artifacts)
    job_accounting = load_job_accounting(artifacts, manifest)
    rows = load_rows(artifacts)
    values = {
        (row["method"], row["experts"], row["seed"]): row["classifier_accuracy_percent"]
        for row in rows
    }
    means = {
        method: {
            str(experts): statistics.mean(values[method, experts, seed] for seed in SEEDS)
            for experts in EXPERT_COUNTS
        }
        for method in METHODS
    }

    degradation = {}
    for method in ["ce", "ova"]:
        adjacent = [
            {
                "from_experts": left,
                "to_experts": right,
                "decrease_percentage_points": means[method][str(left)] - means[method][str(right)],
                "passed": means[method][str(left)] > means[method][str(right)],
            }
            for left, right in zip(EXPERT_COUNTS, EXPERT_COUNTS[1:])
        ]
        endpoint_drop = means[method]["2"] - means[method]["8"]
        degradation[method] = {
            "adjacent": adjacent,
            "endpoint_drop_percentage_points": endpoint_drop,
            "endpoint_drop_at_least_2pp": endpoint_drop >= 2.0,
            "passed": all(item["passed"] for item in adjacent) and endpoint_drop >= 2.0,
        }

    stability = {}
    for method in ["picce_ce", "picce_ova"]:
        spread = max(means[method].values()) - min(means[method].values())
        stability[method] = {
            "range_percentage_points": spread,
            "threshold_percentage_points": 2.0,
            "passed": spread <= 2.0,
        }

    paired = {}
    for vanilla, picce in [("ce", "picce_ce"), ("ova", "picce_ova")]:
        differences = [values[picce, 8, seed] - values[vanilla, 8, seed] for seed in SEEDS]
        mean_difference = statistics.mean(differences)
        standard_deviation = statistics.stdev(differences)
        margin = T_CRITICAL_95_DF2 * standard_deviation / math.sqrt(len(differences))
        paired[f"{picce}_minus_{vanilla}"] = {
            "seeds": SEEDS,
            "differences_percentage_points": differences,
            "mean_difference_percentage_points": mean_difference,
            "sample_standard_deviation": standard_deviation,
            "t_critical_95_df2": T_CRITICAL_95_DF2,
            "ci95_percentage_points": [mean_difference - margin, mean_difference + margin],
            "passed": means[picce]["8"] > means[vanilla]["8"],
        }

    all_passed = (
        all(item["passed"] for item in degradation.values())
        and all(item["passed"] for item in stability.values())
        and all(item["passed"] for item in paired.values())
    )
    return {
        "schema_version": 1,
        "claim": "On MiceBone, vanilla classifier accuracy drops as J increases while PiCCE remains stable.",
        "source_scope": "Figure 2 MiceBone panel and Appendix D.2",
        "primary_metric": "final-epoch test classifier accuracy percent",
        "target": TARGET,
        "expert_counts": EXPERT_COUNTS,
        "methods": METHODS,
        "seeds": SEEDS,
        "grid_size": len(rows),
        "dataset_audit": dataset_audit,
        "job_accounting": job_accounting,
        "shard_manifest_file": "shard_manifest.json",
        "shard_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "rows": rows,
        "seed_means_percent": means,
        "clauses": {
            "vanilla_degradation": degradation,
            "picce_stability": stability,
            "j8_paired_formulation_comparison": paired,
        },
        "verdict": "VERIFIED" if all_passed else "FALSIFIED",
        "limitations": [
            "The verdict is scoped to the MiceBone panel; it does not establish the trend on every dataset.",
            "The source leaves clean targets, tie handling, augmentation, normalization, and initialization unspecified; the preregistered reconstruction is reported explicitly.",
            "The 95% paired t intervals are descriptive because the paper reports three-trial means.",
        ],
    }


def render_claim6_report(result: dict) -> str:
    lines = [
        "# Claim 6 — MiceBone expert-count sweep",
        "",
        f"**Verdict: {result['verdict']}** under the preregistered MiceBone contract.",
        "",
        "The primary metric is final-epoch test classifier accuracy, averaged across the three fixed seeds. "
        "All 48 cells use the paper's MiceBone folds, ResNet-18, AdamW, 100 epochs, and Hugging Face `cpu-upgrade` without a GPU.",
        "",
        "## Dataset fidelity",
        "",
        f"- Official archive: Zenodo 8115942, {result['dataset_audit']['archive_bytes']} bytes, MD5 "
        f"`{result['dataset_audit']['archive_md5']}`; every ZIP member passed CRC.",
        f"- Images: {result['dataset_audit']['images']}; folds 1–4 train: {result['dataset_audit']['train_images']}; "
        f"fold 5 test: {result['dataset_audit']['test_images']}.",
        f"- Experts in paper order: `{', '.join(result['dataset_audit']['expert_ids'])}`.",
        f"- Fixed target: `{result['dataset_audit']['target_vote_pool']}` votes with priority "
        f"`{' > '.join(result['dataset_audit']['target_priority'])}`; reproduced "
        f"{result['dataset_audit']['table3_exact_rounded_matches_out_of_16']}/16 Table 3 values after rounding "
        f"(MAE {result['dataset_audit']['table3_mae_percentage_points']:.6f} pp; "
        f"max {result['dataset_audit']['table3_max_error_percentage_points']:.6f} pp).",
        "- Downloadable audits: [inventory](micebone_inventory.json), [annotations](micebone_annotations.json), "
        "[target reconstruction](micebone_targets.json).",
        "",
        "## Remote compute and cost",
        "",
        f"The {result['job_accounting']['job_count']} accepted `cpu-upgrade` jobs used "
        f"{result['job_accounting']['total_running_hours']:.6f} aggregate Hub-reported running hours "
        f"({result['job_accounting']['total_billed_minutes']} billed minutes). At the documented "
        f"${result['job_accounting']['cpu_upgrade_hourly_usd']:.2f}/hour rate, the computed cost is "
        f"${result['job_accounting']['total_cost_usd']:.6f}. See "
        f"[job_accounting.json]({result['job_accounting']['raw_file']}) and the "
        f"[official pricing source]({result['job_accounting']['pricing_source']}).",
        "",
        "## Seed means (%)",
        "",
        "| Method | J=2 | J=4 | J=6 | J=8 |",
        "|---|---:|---:|---:|---:|",
    ]
    for method in METHODS:
        means = result["seed_means_percent"][method]
        lines.append(f"| `{method}` | {means['2']:.6f} | {means['4']:.6f} | {means['6']:.6f} | {means['8']:.6f} |")

    lines.extend(["", "## Preregistered clauses", "", "| Clause | Result | Value |", "|---|---|---|"])
    for method in ["ce", "ova"]:
        clause = result["clauses"]["vanilla_degradation"][method]
        adjacent = ", ".join(f"{item['decrease_percentage_points']:.6f}" for item in clause["adjacent"])
        lines.append(
            f"| `{method}`: every adjacent mean decreases and J=2−J=8 ≥ 2 pp | "
            f"{'PASS' if clause['passed'] else 'FAIL'} | adjacent drops {adjacent} pp; endpoint {clause['endpoint_drop_percentage_points']:.6f} pp |"
        )
    for method in ["picce_ce", "picce_ova"]:
        clause = result["clauses"]["picce_stability"][method]
        lines.append(
            f"| `{method}`: range across J ≤ 2 pp | {'PASS' if clause['passed'] else 'FAIL'} | "
            f"range {clause['range_percentage_points']:.6f} pp |"
        )
    for key, clause in result["clauses"]["j8_paired_formulation_comparison"].items():
        lower, upper = clause["ci95_percentage_points"]
        lines.append(
            f"| J=8 `{key}` mean > 0 | {'PASS' if clause['passed'] else 'FAIL'} | "
            f"mean {clause['mean_difference_percentage_points']:.6f} pp; descriptive 95% t CI [{lower:.6f}, {upper:.6f}] |"
        )

    lines.extend(
        [
            "",
            "## Exact final-epoch rows",
            "",
            "| J | Method | Seed | Accuracy (%) | Runtime (s) | Raw | Environment | Verifier | Control |",
            "|---:|---|---:|---:|---:|---|---|---|---|",
        ]
    )
    for row in result["rows"]:
        lines.append(
            f"| {row['experts']} | `{row['method']}` | {row['seed']} | {row['classifier_accuracy_percent']:.12f} | "
            f"{row['training_runtime_seconds']:.3f} | [JSON]({row['raw_file']}) | [JSON]({row['environment_file']}) | "
            f"[output]({row['shard_verifier_file']}) | [tampered]({row['negative_control_file']}), "
            f"[output]({row['negative_control_output_file']}) |"
        )

    lines.extend(
        [
            "",
            "## Reproduction and safeguards",
            "",
            "- Fixed command: `uv run --frozen python run.py`.",
            "- Exact mapping: [shard manifest](../../shard_manifest.json).",
            "- Aggregate data: [claim6_results.json](claim6_results.json).",
            "- Positive verifier: [claim6_verifier_output.json](claim6_verifier_output.json).",
            "- Independent recomputation: [claim6_independent_output.json](claim6_independent_output.json).",
            "- Tampered aggregate and expected failure: [input](claim6_negative_control.json), [output](claim6_negative_control_output.json).",
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {limitation}" for limitation in result["limitations"])
    return "\n".join(lines) + "\n"

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
                accuracy = run["history"][-1]["classifier_accuracy_percent"]
                assert math.isfinite(accuracy)
                assert environment["selected_flavor"] == "cpu-upgrade"
                assert environment["effective_cpu_quota"] > 0
                assert environment["cuda_available"] is False
                assert environment["cuda_device_count"] == 0
                assert environment["stage"] == "micebone-training-shard"
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

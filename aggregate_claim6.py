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
                payload = json.loads(path.read_text())
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

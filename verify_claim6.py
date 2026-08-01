import hashlib
import json
import math
import statistics
import sys
from pathlib import Path


EXPERT_COUNTS = [2, 4, 6, 8]
METHODS = ["ce", "picce_ce", "ova", "picce_ova"]
SEEDS = [260217144, 260217145, 260217146]
TARGET = "complete_annotator_majority_priority_g_ug_nr"
T_CRITICAL_95_DF2 = 4.302652729911275


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12)


def main() -> None:
    result_path = Path(sys.argv[1])
    artifacts = result_path.parent
    result = json.loads(result_path.read_text())
    manifest_path = artifacts.parents[1] / result["shard_manifest_file"]
    manifest = json.loads(manifest_path.read_text())
    assert result["shard_manifest_sha256"] == hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    expected_cells = {
        (experts, method, seed)
        for experts in EXPERT_COUNTS
        for method in METHODS
        for seed in SEEDS
    }
    expected_files = {
        f"micebone_training_j{experts}_{method}_seed{seed}.json"
        for experts, method, seed in expected_cells
    }
    assert {
        (shard["j"], shard["method"], shard["seed"])
        for shard in manifest["shards"]
    } == expected_cells
    assert len({shard["experiment_id"] for shard in manifest["shards"]}) == 48
    assert len({shard["run_id"] for shard in manifest["shards"]}) == 48
    assert len({shard["job_id"] for shard in manifest["shards"]}) == 48
    assert {path.name for path in artifacts.glob("micebone_training_j*_seed*.json")} == expected_files
    assert result["grid_size"] == 48
    assert result["expert_counts"] == EXPERT_COUNTS
    assert result["methods"] == METHODS
    assert result["seeds"] == SEEDS
    assert result["target"] == TARGET
    assert len(result["rows"]) == 48

    reported = {
        (row["experts"], row["method"], row["seed"]): row
        for row in result["rows"]
    }
    assert set(reported) == expected_cells
    values = {}
    for experts, method, seed in sorted(expected_cells):
        name = f"micebone_training_j{experts}_{method}_seed{seed}.json"
        path = artifacts / name
        raw = json.loads(path.read_text())
        contract = raw["training_contract"]
        assert raw["accepted_scientific_result"] is True
        assert contract["epochs"] == 100
        assert contract["expert_counts"] == [experts]
        assert contract["methods"] == [method]
        assert contract["seeds"] == [seed]
        assert contract["target"] == TARGET
        assert contract["cpu_memory_format"] == "channels_last"
        assert contract["accepted_scientific_result"] is True
        assert len(raw["runs"]) == 1
        run = raw["runs"][0]
        assert (run["experts"], run["method"], run["seed"], run["epochs"]) == (
            experts,
            method,
            seed,
            100,
        )
        assert [epoch["epoch"] for epoch in run["history"]] == list(range(1, 101))
        assert all(epoch["samples"] == 1543 for epoch in run["history"])
        value = run["history"][-1]["classifier_accuracy_percent"]
        assert math.isfinite(value)
        row = reported[experts, method, seed]
        assert row["raw_file"] == name
        assert row["raw_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
        assert row["final_epoch"] == 100
        assert row["test_samples"] == 1543
        assert close(row["classifier_accuracy_percent"], value)
        values[method, experts, seed] = value

    means = {
        method: {
            str(experts): statistics.mean(values[method, experts, seed] for seed in SEEDS)
            for experts in EXPERT_COUNTS
        }
        for method in METHODS
    }
    for method in METHODS:
        for experts in EXPERT_COUNTS:
            assert close(result["seed_means_percent"][method][str(experts)], means[method][str(experts)])

    degradation_passes = []
    for method in ["ce", "ova"]:
        clause = result["clauses"]["vanilla_degradation"][method]
        assert len(clause["adjacent"]) == 3
        adjacent_passes = []
        for item, left, right in zip(clause["adjacent"], EXPERT_COUNTS, EXPERT_COUNTS[1:]):
            decrease = means[method][str(left)] - means[method][str(right)]
            passed = means[method][str(left)] > means[method][str(right)]
            assert (item["from_experts"], item["to_experts"]) == (left, right)
            assert close(item["decrease_percentage_points"], decrease)
            assert item["passed"] is passed
            adjacent_passes.append(passed)
        endpoint = means[method]["2"] - means[method]["8"]
        endpoint_passed = endpoint >= 2.0
        passed = all(adjacent_passes) and endpoint_passed
        assert close(clause["endpoint_drop_percentage_points"], endpoint)
        assert clause["endpoint_drop_at_least_2pp"] is endpoint_passed
        assert clause["passed"] is passed
        degradation_passes.append(passed)

    stability_passes = []
    for method in ["picce_ce", "picce_ova"]:
        clause = result["clauses"]["picce_stability"][method]
        spread = max(means[method].values()) - min(means[method].values())
        passed = spread <= 2.0
        assert close(clause["range_percentage_points"], spread)
        assert close(clause["threshold_percentage_points"], 2.0)
        assert clause["passed"] is passed
        stability_passes.append(passed)

    paired_passes = []
    for vanilla, picce in [("ce", "picce_ce"), ("ova", "picce_ova")]:
        clause = result["clauses"]["j8_paired_formulation_comparison"][f"{picce}_minus_{vanilla}"]
        differences = [values[picce, 8, seed] - values[vanilla, 8, seed] for seed in SEEDS]
        mean_difference = statistics.mean(differences)
        deviation = statistics.stdev(differences)
        margin = T_CRITICAL_95_DF2 * deviation / math.sqrt(3)
        passed = means[picce]["8"] > means[vanilla]["8"]
        assert clause["seeds"] == SEEDS
        assert all(close(a, b) for a, b in zip(clause["differences_percentage_points"], differences))
        assert close(clause["mean_difference_percentage_points"], mean_difference)
        assert close(clause["sample_standard_deviation"], deviation)
        assert close(clause["t_critical_95_df2"], T_CRITICAL_95_DF2)
        assert all(close(a, b) for a, b in zip(clause["ci95_percentage_points"], [mean_difference - margin, mean_difference + margin]))
        assert clause["passed"] is passed
        paired_passes.append(passed)

    expected_verdict = "VERIFIED" if all(degradation_passes + stability_passes + paired_passes) else "FALSIFIED"
    assert result["verdict"] == expected_verdict
    print(f"Claim 6 aggregate verified: {expected_verdict}; exact 48-shard grid")


if __name__ == "__main__":
    main()

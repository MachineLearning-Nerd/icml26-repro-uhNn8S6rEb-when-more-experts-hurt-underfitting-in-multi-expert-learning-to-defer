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
    inventory_path = artifacts / "micebone_inventory.json"
    annotations_path = artifacts / "micebone_annotations.json"
    targets_path = artifacts / "micebone_targets.json"
    inventory = json.loads(inventory_path.read_text())
    annotations = json.loads(annotations_path.read_text())
    targets = json.loads(targets_path.read_text())
    dataset_audit = result["dataset_audit"]
    assert inventory["record_id"] == 8115942
    assert inventory["archive_bytes"] == dataset_audit["archive_bytes"] == 680_507_926
    assert inventory["archive_md5"] == dataset_audit["archive_md5"] == "8a4026c22f07373f022d9ab4818089ec"
    assert inventory["zip_crc_all_members_pass"] is dataset_audit["zip_crc_all_members_pass"] is True
    assert inventory["image_count"] == annotations["unique_image_count"] == dataset_audit["images"] == 7240
    assert annotations["fold_counts"] == dataset_audit["fold_counts"]
    assert sum(value for key, value in annotations["fold_counts"].items() if key != "fold5") == 5697
    assert annotations["fold_counts"]["fold5"] == 1543
    assert annotations["complete_annotator_count"] == 8
    assert dataset_audit["expert_ids"] == [expert["expert_id"] for expert in targets["experts"]]
    assert dataset_audit["expert_ids"] == ["047", "290", "533", "534", "580", "581", "966", "745"]
    best = targets["global_priority_tie_rules_ranked_by_table_3_mae"][0]
    assert dataset_audit["target_vote_pool"] == best["vote_pool"] == "complete_annotators"
    assert dataset_audit["target_priority"] == best["priority"] == ["g", "ug", "nr"]
    assert dataset_audit["table3_exact_rounded_matches_out_of_16"] == best["exact_rounded_matches_out_of_16"] == 14
    assert close(dataset_audit["table3_mae_percentage_points"], best["mean_absolute_error_percentage_points"])
    assert close(dataset_audit["table3_max_error_percentage_points"], best["maximum_absolute_error_percentage_points"])
    for path in [inventory_path, annotations_path, targets_path]:
        assert dataset_audit["files"][path.name] == hashlib.sha256(path.read_bytes()).hexdigest()
    accounting_summary = result["job_accounting"]
    accounting_path = artifacts / accounting_summary["raw_file"]
    accounting = json.loads(accounting_path.read_text())
    assert accounting_summary["raw_sha256"] == hashlib.sha256(accounting_path.read_bytes()).hexdigest()
    assert accounting["pricing_source"] == accounting_summary["pricing_source"] == "https://huggingface.co/docs/hub/jobs-pricing"
    assert accounting["cpu_upgrade_hourly_usd"] == accounting_summary["cpu_upgrade_hourly_usd"] == 0.03
    assert accounting["cpu_upgrade_per_minute_usd"] == 0.0005
    expected_jobs = {shard["job_id"]: shard for shard in manifest["shards"]}
    observed_jobs = {job["job_id"]: job for job in accounting["jobs"]}
    assert set(observed_jobs) == set(expected_jobs)
    for job_id, job in observed_jobs.items():
        shard = expected_jobs[job_id]
        assert job["run_id"] == shard["run_id"]
        assert (job["j"], job["method"], job["seed"]) == (shard["j"], shard["method"], shard["seed"])
        assert job["status"] == "COMPLETED"
        assert job["flavor"] == "cpu-upgrade"
        assert job["running_seconds"] > 0
        assert job["billed_minutes"] == math.ceil(job["running_seconds"] / 60)
        assert close(job["cost_usd"], job["billed_minutes"] * 0.0005)
    running_seconds = sum(job["running_seconds"] for job in observed_jobs.values())
    billed_minutes = sum(job["billed_minutes"] for job in observed_jobs.values())
    cost_usd = sum(job["cost_usd"] for job in observed_jobs.values())
    assert accounting["job_count"] == accounting_summary["job_count"] == 48
    assert accounting["total_running_seconds"] == accounting_summary["total_running_seconds"] == running_seconds
    assert accounting["total_billed_minutes"] == accounting_summary["total_billed_minutes"] == billed_minutes
    assert close(accounting["total_cost_usd"], accounting_summary["total_cost_usd"])
    assert close(accounting["total_cost_usd"], cost_usd)
    assert close(accounting_summary["total_running_hours"], running_seconds / 3600)
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
    expected_suffixes = {
        f"j{experts}_{method}_seed{seed}"
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
    assert {path.name for path in artifacts.glob("environment_j*_seed*.json")} == {
        f"environment_{suffix}.json" for suffix in expected_suffixes
    }
    assert {path.name for path in artifacts.glob("shard_verifier_j*_seed*.json")} == {
        f"shard_verifier_{suffix}.json" for suffix in expected_suffixes
    }
    assert {path.name for path in artifacts.glob("shard_negative_j*_seed*.json")} == {
        f"shard_negative_{suffix}.json" for suffix in expected_suffixes
    }
    assert {path.name for path in artifacts.glob("shard_negative_output_j*_seed*.json")} == {
        f"shard_negative_output_{suffix}.json" for suffix in expected_suffixes
    }
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
        suffix = f"j{experts}_{method}_seed{seed}"
        environment_path = artifacts / f"environment_{suffix}.json"
        verifier_path = artifacts / f"shard_verifier_{suffix}.json"
        negative_path = artifacts / f"shard_negative_{suffix}.json"
        negative_output_path = artifacts / f"shard_negative_output_{suffix}.json"
        raw = json.loads(path.read_text())
        environment = json.loads(environment_path.read_text())
        verifier = json.loads(verifier_path.read_text())
        negative_output = json.loads(negative_output_path.read_text())
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
        assert all(
            math.isfinite(epoch[key])
            for epoch in run["history"]
            for key in ["train_loss", "classifier_accuracy_percent", "system_error_percent", "coverage_percent"]
        )
        value = run["history"][-1]["classifier_accuracy_percent"]
        assert math.isfinite(value)
        assert run["runtime_seconds"] > 0
        row = reported[experts, method, seed]
        assert row["raw_file"] == name
        assert row["raw_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
        assert row["final_epoch"] == 100
        assert row["test_samples"] == 1543
        assert close(row["classifier_accuracy_percent"], value)
        assert close(row["training_runtime_seconds"], run["runtime_seconds"])
        assert row["environment_file"] == environment_path.name
        assert row["environment_sha256"] == hashlib.sha256(environment_path.read_bytes()).hexdigest()
        assert row["git_sha"] == environment["git_sha"]
        assert environment["fixed_command"] == "uv run --frozen python run.py"
        assert environment["seed"] == seed
        assert environment["estimated_cores"] == 8
        assert row["selected_flavor"] == environment["selected_flavor"] == "cpu-upgrade"
        assert environment["container_image"] == "ghcr.io/astral-sh/uv:python3.12-bookworm-slim"
        assert row["actual_logical_cpus"] == environment["actual_logical_cpus"]
        assert row["actual_cpu_affinity"] == environment["actual_cpu_affinity"]
        assert row["effective_cpu_quota"] == environment["effective_cpu_quota"] == 8
        assert row["cuda_available"] is environment["cuda_available"] is False
        assert close(row["environment_runtime_seconds"], environment["runtime_seconds"])
        assert environment["runtime_seconds"] >= run["runtime_seconds"]
        assert row["shard_verifier_file"] == verifier_path.name
        assert row["shard_verifier_sha256"] == hashlib.sha256(verifier_path.read_bytes()).hexdigest()
        assert row["shard_verifier_exit"] == verifier["exit_code"] == 0
        assert row["negative_control_file"] == negative_path.name
        assert row["negative_control_sha256"] == hashlib.sha256(negative_path.read_bytes()).hexdigest()
        assert row["negative_control_output_file"] == negative_output_path.name
        assert row["negative_control_output_sha256"] == hashlib.sha256(negative_output_path.read_bytes()).hexdigest()
        assert row["negative_control_exit"] == negative_output["exit_code"]
        assert row["negative_control_exit"] != 0
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

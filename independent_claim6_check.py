import json
import math
import re
import sys
from pathlib import Path


EXPERT_COUNTS = (2, 4, 6, 8)
METHODS = ("ce", "picce_ce", "ova", "picce_ova")
SEEDS = (260217144, 260217145, 260217146)
TARGET = "complete_annotator_majority_priority_g_ug_nr"
NAME = re.compile(r"micebone_training_j(2|4|6|8)_(ce|picce_ce|ova|picce_ova)_seed(260217144|260217145|260217146)\.json")


def near(left: float, right: float) -> bool:
    return abs(left - right) <= 1e-10


def main() -> None:
    result_path = Path(sys.argv[1])
    evidence = json.loads(result_path.read_text())
    inventory = json.loads((result_path.parent / "micebone_inventory.json").read_text())
    annotations = json.loads((result_path.parent / "micebone_annotations.json").read_text())
    targets = json.loads((result_path.parent / "micebone_targets.json").read_text())
    assert inventory["record_id"] == 8115942
    assert inventory["archive_md5"] == "8a4026c22f07373f022d9ab4818089ec"
    assert inventory["archive_bytes"] == 680_507_926
    assert inventory["zip_crc_all_members_pass"] is True
    assert inventory["image_count"] == annotations["unique_image_count"] == 7240
    assert sum(count for fold, count in annotations["fold_counts"].items() if fold != "fold5") == 5697
    assert annotations["fold_counts"]["fold5"] == 1543
    assert [expert["expert_id"] for expert in targets["experts"]] == [
        "047", "290", "533", "534", "580", "581", "966", "745"
    ]
    best_target = targets["global_priority_tie_rules_ranked_by_table_3_mae"][0]
    assert best_target["vote_pool"] == "complete_annotators"
    assert best_target["priority"] == ["g", "ug", "nr"]
    assert best_target["exact_rounded_matches_out_of_16"] == 14
    accounting = json.loads((result_path.parent / "job_accounting.json").read_text())
    assert len(accounting["jobs"]) == 48
    assert len({job["job_id"] for job in accounting["jobs"]}) == 48
    assert all(job["status"] == "COMPLETED" and job["flavor"] == "cpu-upgrade" for job in accounting["jobs"])
    independent_billed_minutes = sum(math.ceil(job["running_seconds"] / 60) for job in accounting["jobs"])
    independent_cost = independent_billed_minutes * 0.0005
    assert accounting["total_billed_minutes"] == independent_billed_minutes
    assert near(accounting["total_cost_usd"], independent_cost)
    assert near(evidence["job_accounting"]["total_cost_usd"], independent_cost)
    observed = {}
    for path in result_path.parent.glob("micebone_training_j*_seed*.json"):
        match = NAME.fullmatch(path.name)
        assert match is not None
        experts, method, seed = int(match.group(1)), match.group(2), int(match.group(3))
        raw = json.loads(path.read_text())
        contract = raw["training_contract"]
        assert raw["accepted_scientific_result"] is True
        assert contract["accepted_scientific_result"] is True
        assert contract["target"] == TARGET
        assert contract["epochs"] == 100
        assert contract["expert_counts"] == [experts]
        assert contract["methods"] == [method]
        assert contract["seeds"] == [seed]
        assert contract["cpu_memory_format"] == "channels_last"
        assert len(raw["runs"]) == 1
        run = raw["runs"][0]
        assert len(run["history"]) == 100
        assert run["history"][-1]["epoch"] == 100
        assert run["history"][-1]["samples"] == 1543
        observed[experts, method, seed] = run["history"][-1]["classifier_accuracy_percent"]

    expected = {
        (experts, method, seed)
        for experts in EXPERT_COUNTS
        for method in METHODS
        for seed in SEEDS
    }
    assert set(observed) == expected
    means = {}
    for method in METHODS:
        means[method] = {}
        for experts in EXPERT_COUNTS:
            mean = sum(observed[experts, method, seed] for seed in SEEDS) / 3
            means[method][experts] = mean
            assert near(evidence["seed_means_percent"][method][str(experts)], mean)

    degradation = {}
    for method in ("ce", "ova"):
        adjacent = all(means[method][left] > means[method][right] for left, right in zip(EXPERT_COUNTS, EXPERT_COUNTS[1:]))
        endpoint_drop = means[method][2] - means[method][8]
        degradation[method] = adjacent and endpoint_drop >= 2.0

    stability = {}
    for method in ("picce_ce", "picce_ova"):
        stability[method] = max(means[method].values()) - min(means[method].values()) <= 2.0

    paired = {}
    intervals = {}
    for vanilla, picce in (("ce", "picce_ce"), ("ova", "picce_ova")):
        key = f"{picce}_minus_{vanilla}"
        differences = [observed[8, picce, seed] - observed[8, vanilla, seed] for seed in SEEDS]
        mean = sum(differences) / 3
        sample_variance = sum((value - mean) ** 2 for value in differences) / 2
        margin = 4.302652729911275 * math.sqrt(sample_variance) / math.sqrt(3)
        intervals[key] = [mean - margin, mean + margin]
        paired[key] = means[picce][8] > means[vanilla][8]
        reported = evidence["clauses"]["j8_paired_formulation_comparison"][key]
        assert all(near(a, b) for a, b in zip(reported["ci95_percentage_points"], intervals[key]))

    passes = list(degradation.values()) + list(stability.values()) + list(paired.values())
    verdict = "VERIFIED" if all(passes) else "FALSIFIED"
    assert evidence["verdict"] == verdict
    print(
        json.dumps(
            {
                "independent_verdict": verdict,
                "dataset_audit": True,
                "job_accounting": {
                    "billed_minutes": independent_billed_minutes,
                    "cost_usd": independent_cost,
                },
                "exact_grid_cells": len(observed),
                "degradation": degradation,
                "stability": stability,
                "j8_paired": paired,
                "paired_ci95_percentage_points": intervals,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

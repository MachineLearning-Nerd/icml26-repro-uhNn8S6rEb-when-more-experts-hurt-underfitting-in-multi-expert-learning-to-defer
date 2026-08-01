import json
import math
import sys
from pathlib import Path


def main() -> None:
    result = json.loads(Path(sys.argv[1]).read_text())
    contract = result["training_contract"]
    assert len(contract["expert_counts"]) == 1
    assert len(contract["methods"]) == 1
    assert len(contract["seeds"]) == 1
    assert contract["target"] == "complete_annotator_majority_priority_g_ug_nr"
    assert contract["epochs"] == (100 if result["accepted_scientific_result"] else 1)
    assert len(result["runs"]) == 1
    run = result["runs"][0]
    assert run["experts"] == contract["expert_counts"][0]
    assert run["method"] == contract["methods"][0]
    assert run["seed"] == contract["seeds"][0]
    assert run["epochs"] == contract["epochs"]
    assert [row["epoch"] for row in run["history"]] == list(range(1, contract["epochs"] + 1))
    for row in run["history"]:
        assert row["samples"] == 1543
        for key in ["train_loss", "classifier_accuracy_percent", "system_error_percent", "coverage_percent"]:
            assert math.isfinite(row[key])
    print("training shard integrity verified")


if __name__ == "__main__":
    main()

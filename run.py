import copy
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import torch

from theory import evaluate_theory


ROOT = Path(__file__).parent
ARTIFACTS = ROOT / ".openresearch" / "artifacts"


def run_checker(script: str, results: Path) -> dict:
    process = subprocess.run(
        [sys.executable, str(ROOT / script), str(results)],
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "command": f"python {script} {results.relative_to(ROOT)}",
        "exit_code": process.returncode,
        "stdout": process.stdout,
        "stderr": process.stderr,
    }


def git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def main() -> None:
    started = time.monotonic()
    config = json.loads((ROOT / "experiment.json").read_text())
    if config["fixed_command"] != "uv run --frozen python run.py":
        raise RuntimeError("fixed command changed")
    if config["selected_flavor"] != "cpu-upgrade":
        raise RuntimeError("unauthorized compute flavor")

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    results = evaluate_theory()
    results_path = ARTIFACTS / "theory_results.json"
    results_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")

    verifier = run_checker("verify.py", results_path)
    independent = run_checker("independent_check.py", results_path)
    (ARTIFACTS / "verifier_output.json").write_text(json.dumps(verifier, indent=2) + "\n")
    (ARTIFACTS / "independent_checker_output.json").write_text(json.dumps(independent, indent=2) + "\n")
    if verifier["exit_code"] != 0 or independent["exit_code"] != 0:
        raise RuntimeError("positive evidence failed verification")

    tampered = copy.deepcopy(results)
    tampered["claims"]["4"]["ce_risk_minimizer_u_j_star"] = {"numerator": 7, "denominator": 20}
    tampered_path = ARTIFACTS / "negative_control_tampered.json"
    tampered_path.write_text(json.dumps(tampered, indent=2, sort_keys=True) + "\n")
    negative = run_checker("verify.py", tampered_path)
    (ARTIFACTS / "negative_control_output.json").write_text(json.dumps(negative, indent=2) + "\n")
    if negative["exit_code"] == 0:
        raise RuntimeError("negative control incorrectly passed")

    elapsed = time.monotonic() - started
    environment = {
        "fixed_command": config["fixed_command"],
        "git_sha": git_sha(),
        "seed": config["seed"],
        "estimated_cores": config["estimated_cores"],
        "selected_flavor": config["selected_flavor"],
        "container_image": config["container_image"],
        "actual_logical_cpus": os.cpu_count(),
        "actual_cpu_affinity": len(os.sched_getaffinity(0)),
        "cuda_available": torch.cuda.is_available(),
        "cuda_device_count": torch.cuda.device_count(),
        "runtime_seconds": elapsed,
        "python": sys.version,
        "platform": platform.platform(),
        "stage": config["stage"],
    }
    (ARTIFACTS / "environment.json").write_text(json.dumps(environment, indent=2) + "\n")

    contracts = {
        "1": {"statement": "Eq. 6 aggregation can scale linearly in J and flatten classifier-label margins", "quantifier": "constructive family for every positive integer J", "result": "VERIFIED"},
        "2": {"statement": "Lemma 4 partition sum equals union coverage for any permutation and x", "quantifier": "universal probability identity", "result": "VERIFIED"},
        "3": {"statement": "Theorem 2 continuity and Lemma 5 CE/OvA classifier consistency", "quantifier": "universal under the stated continuity/symmetry assumptions", "result": "VERIFIED"},
        "4": {"statement": "Theorem 6(A) CE score equals Acc_j* times V_tilde under Condition 1", "quantifier": "any x and minimizer satisfying Condition 1", "result": "FALSIFIED"},
    }
    (ARTIFACTS / "claim_contract.json").write_text(json.dumps(contracts, indent=2) + "\n")

    (ARTIFACTS / "EVAL.md").write_text(
        "# Baseline evaluation\n\n"
        "Claims 1–3: **VERIFIED** by algebraic/probability certificates.\n\n"
        "Claim 4 / Theorem 6(A): **FALSIFIED**. A Condition-1 distribution gives the CE optimum "
        "`u*_{j*}=2/5`, while the printed theorem gives `7/20`; exact gap `1/20`.\n\n"
        "The verifier and independent checker exit 0. The tampered-evidence control exits nonzero. "
        "This baseline does not address Claims 5–6 or claim dataset-level empirical performance.\n"
    )
    print(json.dumps({"verifier": verifier["stdout"].strip(), "independent": independent["stdout"].strip(), "negative_control_exit": negative["exit_code"], "runtime_seconds": elapsed}, indent=2))
    bundle = {path.name: path.read_text() for path in sorted(ARTIFACTS.iterdir())}
    print("ORX_ARTIFACT_BUNDLE_BEGIN")
    print(json.dumps(bundle, sort_keys=True))
    print("ORX_ARTIFACT_BUNDLE_END")


if __name__ == "__main__":
    main()

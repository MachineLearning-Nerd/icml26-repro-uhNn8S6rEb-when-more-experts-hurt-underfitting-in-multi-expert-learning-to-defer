import copy
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import torch

from micebone import audit_micebone, inspect_annotations, resolve_targets
from micebone_train import effective_cpu_count, run_micebone_training
from proof_certificates import build_proof_certificates
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

    controls = {}
    mutations = {}
    mutations["claim_1"] = copy.deepcopy(results)
    mutations["claim_1"]["claims"]["1"]["sweep"][0]["aggregation"] = {"numerator": 0, "denominator": 1}
    mutations["claim_2"] = copy.deepcopy(results)
    mutations["claim_2"]["claims"]["2"]["exhaustive_correlated_checks"] = 872
    mutations["claim_3"] = copy.deepcopy(results)
    mutations["claim_3"]["claims"]["3"]["rational_instance"]["ce_recovered_eta"][0] = {"numerator": 0, "denominator": 1}
    mutations["claim_4"] = copy.deepcopy(results)
    mutations["claim_4"]["claims"]["4"]["ce_risk_minimizer_u_j_star"] = {"numerator": 7, "denominator": 20}
    mutations["claim_5"] = copy.deepcopy(results)
    mutations["claim_5"]["claims"]["5"]["reported_values"]["picce_ce_error"] = {"numerator": 1517, "denominator": 100}
    for name, tampered in mutations.items():
        tampered_path = ARTIFACTS / f"negative_control_{name}.json"
        tampered_path.write_text(json.dumps(tampered, indent=2, sort_keys=True) + "\n")
        controls[name] = run_checker("verify.py", tampered_path)
    (ARTIFACTS / "negative_control_output.json").write_text(json.dumps(controls, indent=2) + "\n")
    if any(control["exit_code"] == 0 for control in controls.values()):
        raise RuntimeError("a negative control incorrectly passed")

    proof_verifier = None
    proof_independent = None
    proof_control = None
    if config["stage"] == "universal-theory-certificates":
        proof = build_proof_certificates()
        proof_path = ARTIFACTS / "universal_proof_certificates.json"
        proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n")
        proof_verifier = run_checker("verify_proof_certificates.py", proof_path)
        proof_independent = run_checker("independent_proof_check.py", proof_path)
        (ARTIFACTS / "proof_verifier_output.json").write_text(json.dumps(proof_verifier, indent=2) + "\n")
        (ARTIFACTS / "proof_independent_output.json").write_text(json.dumps(proof_independent, indent=2) + "\n")
        if proof_verifier["exit_code"] != 0 or proof_independent["exit_code"] != 0:
            raise RuntimeError("universal proof certificate failed verification")
        tampered_proof = copy.deepcopy(proof)
        tampered_proof["claim_3"]["theorem_2"]["overlap_agreement"] = False
        tampered_proof_path = ARTIFACTS / "proof_negative_control.json"
        tampered_proof_path.write_text(json.dumps(tampered_proof, indent=2, sort_keys=True) + "\n")
        proof_control = run_checker("verify_proof_certificates.py", tampered_proof_path)
        (ARTIFACTS / "proof_negative_control_output.json").write_text(json.dumps(proof_control, indent=2) + "\n")
        if proof_control["exit_code"] == 0:
            raise RuntimeError("universal proof negative control incorrectly passed")

    if config["stage"].startswith("micebone-"):
        inventory = audit_micebone(ROOT)
        (ARTIFACTS / "micebone_inventory.json").write_text(json.dumps(inventory, indent=2) + "\n")
    if config["stage"] == "micebone-annotation-audit":
        annotations = inspect_annotations(ROOT)
        (ARTIFACTS / "micebone_annotations.json").write_text(json.dumps(annotations, indent=2) + "\n")
    if config["stage"] == "micebone-target-audit":
        targets = resolve_targets(ROOT)
        (ARTIFACTS / "micebone_targets.json").write_text(json.dumps(targets, indent=2) + "\n")
    shard_name = None
    if config["stage"] == "micebone-training-calibration":
        calibration = run_micebone_training(ROOT, config)
        (ARTIFACTS / "micebone_calibration.json").write_text(json.dumps(calibration, indent=2) + "\n")
    if config["stage"] == "micebone-training-shard":
        training = config["micebone_training"]
        if any(len(training[key]) != 1 for key in ["expert_counts", "methods", "seeds"]):
            raise RuntimeError("a training shard must contain one J, method, and seed")
        shard_name = f"j{training['expert_counts'][0]}_{training['methods'][0]}_seed{training['seeds'][0]}"
        shard = run_micebone_training(ROOT, config)
        shard_path = ARTIFACTS / f"micebone_training_{shard_name}.json"
        shard_path.write_text(json.dumps(shard, indent=2) + "\n")
        shard_verifier = run_checker("verify_shard.py", shard_path)
        (ARTIFACTS / f"shard_verifier_{shard_name}.json").write_text(json.dumps(shard_verifier, indent=2) + "\n")
        if shard_verifier["exit_code"] != 0:
            raise RuntimeError("training shard failed integrity verification")
        tampered = copy.deepcopy(shard)
        tampered["runs"][0]["history"][-1]["samples"] = 1542
        tampered_path = ARTIFACTS / f"shard_negative_{shard_name}.json"
        tampered_path.write_text(json.dumps(tampered, indent=2) + "\n")
        shard_control = run_checker("verify_shard.py", tampered_path)
        (ARTIFACTS / f"shard_negative_output_{shard_name}.json").write_text(json.dumps(shard_control, indent=2) + "\n")
        if shard_control["exit_code"] == 0:
            raise RuntimeError("training shard negative control incorrectly passed")
    if "claim6_contract" in config:
        (ARTIFACTS / "claim6_contract.json").write_text(json.dumps(config["claim6_contract"], indent=2) + "\n")
    for name in ["method.md", "source_audit.md"]:
        (ARTIFACTS / name).write_text((ROOT / name).read_text())

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
        "effective_cpu_quota": effective_cpu_count(),
        "cuda_available": torch.cuda.is_available(),
        "cuda_device_count": torch.cuda.device_count(),
        "runtime_seconds": elapsed,
        "python": sys.version,
        "platform": platform.platform(),
        "stage": config["stage"],
    }
    (ARTIFACTS / "environment.json").write_text(json.dumps(environment, indent=2) + "\n")
    if shard_name is not None:
        (ARTIFACTS / f"environment_{shard_name}.json").write_text(json.dumps(environment, indent=2) + "\n")

    contracts = {
        "1": {"statement": "Eq. 6 aggregation can scale linearly in J and flatten classifier-label margins", "quantifier": "constructive family for every positive integer J", "result": "VERIFIED"},
        "2": {"statement": "Lemma 4 partition sum equals union coverage for any permutation and x", "quantifier": "universal probability identity", "result": "VERIFIED"},
        "3": {"statement": "Theorem 2 continuity and Lemma 5 CE/OvA classifier consistency", "quantifier": "universal under the stated continuity/symmetry assumptions", "result": "VERIFIED"},
        "4": {"statement": "Theorem 6(A) CE score equals Acc_j* times V_tilde under Condition 1", "quantifier": "any x and minimizer satisfying Condition 1", "result": "FALSIFIED"},
        "5": {"statement": "PiCCE has improved system error and higher coverage across expert counts on both real-world datasets", "quantifier": "every reported dataset, method family, and expert count", "result": "FALSIFIED"},
        "6": {"statement": "On MiceBone, vanilla classifier accuracy drops as J increases while PiCCE remains stable", "quantifier": "CE and OvA families at J in {2,4,6,8}, averaged over three trials", "result": "BLOCKED"},
    }
    (ARTIFACTS / "claim_contract.json").write_text(json.dumps(contracts, indent=2) + "\n")

    (ARTIFACTS / "EVAL.md").write_text(
        "# Baseline evaluation\n\n"
        "Claims 1–3: **VERIFIED** by algebraic/probability certificates.\n\n"
        "Claim 4 / Theorem 6(A): **FALSIFIED**. A Condition-1 distribution gives the CE optimum "
        "`u*_{j*}=2/5`, while the printed theorem gives `7/20`; exact gap `1/20`.\n\n"
        "Claim 5: **FALSIFIED AS PRINTED**. Table 2 reports MiceBone/two-expert CE error "
        "`15.17` versus PiCCE-CE `15.23`, contradicting improved error at every count.\n\n"
        "The verifier and independent checker exit 0. All five claim-specific tampered controls exit nonzero. "
        "The universal proof schema has a separate verifier, independent reconstruction, and tampered-overlap control. "
        "Claim 6's full-data decision rule is preregistered; no training result is accepted at this stage.\n"
    )
    summary = {
        "verifier": verifier["stdout"].strip(),
        "independent": independent["stdout"].strip(),
        "negative_control_exits": {name: result["exit_code"] for name, result in controls.items()},
        "runtime_seconds": elapsed,
    }
    if proof_verifier is not None:
        summary["proof_verifier"] = proof_verifier["stdout"].strip()
        summary["proof_independent"] = proof_independent["stdout"].strip()
        summary["proof_negative_control_exit"] = proof_control["exit_code"]
    print(json.dumps(summary, indent=2))
    bundle = {path.name: path.read_text() for path in sorted(ARTIFACTS.iterdir())}
    print("ORX_ARTIFACT_BUNDLE_BEGIN")
    print(json.dumps(bundle, sort_keys=True))
    print("ORX_ARTIFACT_BUNDLE_END")


if __name__ == "__main__":
    main()

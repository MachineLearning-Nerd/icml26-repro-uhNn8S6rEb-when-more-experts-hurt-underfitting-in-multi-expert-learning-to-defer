# Current verification

This page supersedes the historical toy verifier in the judged Space revision
`6d7a28419633108958c5dccc2380e9232971cad3`. It is the canonical entrypoint for
the exact source and theorem audit. The paper source and assumptions are
recorded in [source_audit.md](../source_audit.md).

## Fixed reproduction contract

- Command: `uv run --frozen python run.py`
- Environment: Python 3.12 and [uv.lock](../uv.lock)
- Compute: Hugging Face `cpu-upgrade`; no GPU
- Seed: `260217144`
- Exact run SHA, CPU affinity, runtime, and CUDA visibility:
  [environment.json](../.openresearch/artifacts/environment.json)

## Results visible without running code

| Claim | Exact result | Reviewer verdict |
|---|---|---|
| 1 | For the all-`3/4`-accurate family, vanilla aggregation is exactly `3J/4`; the dummy-label margin is `(1/5)/(1+3J/4)=Theta(1/J)`. | VERIFIED for the exact Eq. 6 scaling mechanism |
| 2 | The first-correct events partition the at-least-one-correct event for every permutation, so their sum is at most one. All correlated Boolean domains and permutations through `J=6` were also exhausted (`873` order checks). | VERIFIED |
| 3 | Symmetry glues the continuous expert-order regions at ties; CE normalization and OvA sigmoid scores recover `eta` exactly. | VERIFIED by reconstructed derivation |
| 4 | Condition 1 holds for accuracies `(3/4,1/2)`, yet CE gives `u*_{j*}=2/5` and printed Theorem 6(A) gives `7/20` (gap `1/20`). | FALSIFIED as printed |
| 5 | Table 2, MiceBone, two experts: vanilla CE error `15.17`; PiCCE-CE error `15.23`. | FALSIFIED as printed (`+0.06` percentage-point error) |
| 6 | No faithful dataset run is accepted yet. | BLOCKED pending dataset evidence |

Claim 4's complete J=2 Condition 1 audit has one permitted subset, the empty
set: adding expert 1 covers `3/4`, strictly more than expert 2's `1/2`. The
joint correctness masses `(00,01,10,11)=(1,1,3,3)/8` are positive and sum to
one. Thus the counterexample is not vacuous and satisfies every theorem
quantifier. Claim 5 is bound to the audited ar5iv HTML SHA-256 and contradicts
the paper's conjunctive statement that system error improves at every expert
count; it does not claim PiCCE is generally worse.

## Code, raw evidence, and failure controls

- Executable sources: [theory.py](../theory.py), [verify.py](../verify.py),
  [independent_check.py](../independent_check.py), [run.py](../run.py)
- Exact contracts: [claim_contract.json](../.openresearch/artifacts/claim_contract.json)
- Raw fractions and audits: [theory_results.json](../.openresearch/artifacts/theory_results.json)
- Primary verifier: [verifier_output.json](../.openresearch/artifacts/verifier_output.json)
- Separately implemented reconstruction:
  [independent_checker_output.json](../.openresearch/artifacts/independent_checker_output.json)
- One tampered-evidence run per claim, each required to exit nonzero:
  [negative_control_output.json](../.openresearch/artifacts/negative_control_output.json)
- Concise limitations: [EVAL.md](../.openresearch/artifacts/EVAL.md)

## Limitations

Claims 1–4 are proof/source claims and do not substitute a trained image model.
Claim 5 is falsified only as broadly printed, using the paper's own reported
mean; the underlying MiceBone run has not yet been independently repeated.
Claim 6 remains blocked here. No score increase is asserted before live judge
evaluation of a later released Hugging Face revision.

# Claim-to-evidence audit

This dossier separates exact mathematical checks, source-table checks, and
empirical training. A status of **VERIFIED (SCOPED)** means the stated
finite or algebraic contract passed. It does not prove a broader theorem than
the contract covers. **FALSIFIED AS PRINTED** is deliberately narrower than a
claim that the method is always wrong. **BLOCKED** means that the evidence
needed for the declared empirical contract is not accepted.

## Claim ledger

| Claim | Paper statement | Production path | Result |
| --- | --- | --- | --- |
| C1 | Vanilla aggregation can scale with the number of experts and flatten the classifier-label margin. | <code>release/universal-theory-certificates:theory.py</code>, <code>verify.py</code>, and <code>.openresearch/artifacts/theory_results.json</code>; reader summary at <code>pages/current-verification.md</code>. | VERIFIED (SCOPED) |
| C2 | PiCCE first-correct terms form a probability partition whose sum is the union coverage. | <code>release/universal-theory-certificates:proof_certificates.py</code>, <code>independent_proof_check.py</code>, and <code>verify_proof_certificates.py</code>; exact contract in <code>.openresearch/artifacts/claim_contract.json</code>. | VERIFIED (SCOPED) |
| C3 | The continuity and CE/OvA consistency results hold under the paper's assumptions. | <code>release/universal-theory-certificates:theory.py</code>, <code>verify.py</code>, <code>independent_check.py</code>, and <code>pages/current-verification.md</code>. | VERIFIED (SCOPED) |
| C4 | Theorem 6(A) gives the CE score <code>u*_{j*} = Acc_{j*} V_tilde</code> under Condition 1. | <code>release/universal-theory-certificates:source_audit.md</code>, <code>.openresearch/artifacts/theory_results.json</code>, <code>verifier_output.json</code>, and <code>independent_checker_output.json</code>. | FALSIFIED AS PRINTED |
| C5 | PiCCE has improved system error and higher coverage across the reported expert counts and real-world datasets. | <code>release/universal-theory-certificates:source_audit.md</code> and the paper's Table 2 values encoded in <code>.openresearch/artifacts/theory_results.json</code>. | FALSIFIED AS PRINTED |
| C6 | On MiceBone, vanilla classifier accuracy falls as J grows while PiCCE remains stable. | <code>release/claim-6-aggregate-preregistered:.openresearch/artifacts/claim6_contract.json</code>, target and environment artifacts, and the named experiment branches. | BLOCKED |

## C1 — aggregation scaling

The exact constructive family gives J experts with conditional accuracy 3/4.
Its aggregation is exactly <code>A_J = 3J/4</code>, and with label gap 1/5 the
dummy-label margin is:

    (1/5) / (1 + 3J/4) = Theta(1/J)

The committed sweep covers J = 1, 2, 4, 8, 16, 32, and 64. The result
verifies the Eq. 6 scaling mechanism under the constructed family. It does
not verify every empirical consequence of increasing the expert set.

## C2 — first-correct partition

For any expert permutation, the event that expert j is the first correct
expert is disjoint from the corresponding event for every other expert. The
events partition the event that at least one expert is correct, so their
probabilities sum to the union coverage, which is at most one. The committed
exact checks cover all Boolean correctness vectors and permutations through
J = 6, with 873 order checks. The proof scripts are preserved on the
universal-theory branch; the finite count is evidence for the declared
certificate, not a substitute for reading the universal argument.

## C3 — continuity and consistency

The continuity check splits the expert scores into strict-order regions,
then checks that symmetry gives the same loss value on shared tie
boundaries. The population minimizer reconstruction gives:

    CE: q_y = eta_y / (1 + V), with normalization recovering eta
    OvA: sigmoid(theta_y) = eta_y

The rational instance uses eta = (1/2, 3/10, 1/5), with union probability
9/10. The result is scoped to the continuity, symmetry, and minimizer
assumptions stated in the source.

## C4 — Theorem 6(A) contradiction

The source prints:

    u*_{j*} = Acc_{j*} V_tilde

but its proof derives:

    u*_{j*} = Acc_{j*}/(1 + V)
            = Acc_{j*}(1 - V_tilde)

The exact binary singleton-X counterexample has accuracies 3/4 and 1/2,
label distribution eta = (3/5, 2/5), positive CE weights, and joint
correctness masses (1, 1, 3, 3)/8. It satisfies the unique-best-expert and
all-subsets Condition 1 checks. The CE risk gives 2/5; the printed formula
gives 7/20; the absolute gap is 1/20.

This falsifies the printed CE equality, not the ranking or OvA statements
and not the entire paper.

## C5 — Table 2 contradiction

The source's Section 6.2 wording makes a conjunction about improved system
error and higher coverage. In Table 2, MiceBone, CE, and two experts, the
reported means are:

| Method | Error | Coverage |
| --- | ---: | ---: |
| Vanilla CE | 15.17 | 60.92 |
| PiCCE-CE | 15.23 | 69.28 |

PiCCE improves coverage by 8.36 percentage points but worsens error by 0.06
percentage points. This is a falsification from the paper's own reported
table. It is not an independent rerun and does not establish that PiCCE is
generally worse.

## C6 — MiceBone empirical contract

The preregistered contract requires all of the following:

- CE and OvA vanilla seed means decrease at every adjacent J step from 2 to 4 to 6 to 8, with a J=2-to-J=8 drop of at least two percentage points.
- PiCCE-CE and PiCCE-OvA have a cross-J range of at most two percentage points.
- At J=8, each PiCCE seed mean exceeds its paired vanilla mean.
- Paired differences and descriptive two-sided 95% t intervals are reported.

The complete 48-cell campaign was not accepted. The only full-data calibration
artifact is one epoch, J=2, CE, seed 260217144; it is explicitly marked
<code>accepted_scientific_result: false</code>. Therefore no Claim 6 verdict is inferred
from its 61.3091% classifier accuracy, 18.4705% system error, or 30.2657%
coverage.

## Evidence boundary

The decisive evidence is committed on the normalized release and experiment
branches. Main is a documentation entrypoint. A branch containing a model
configuration or a partial run is not treated as a successful reproduction.
No current judge score, author endorsement, or source-faithful Claim 6 result
is asserted.

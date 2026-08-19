# Scoped reproduction report

## Final verdict

| Claim | Verdict | Evidence boundary |
| --- | --- | --- |
| C1 | VERIFIED (SCOPED) | Exact constructive aggregation family and margin scaling. |
| C2 | VERIFIED (SCOPED) | First-correct probability partition and finite exhaustive checks through J=6. |
| C3 | VERIFIED (SCOPED) | Continuity, symmetry, and CE/OvA minimizer reconstruction under stated assumptions. |
| C4 | FALSIFIED AS PRINTED | Exact Condition 1 counterexample: 2/5 versus printed 7/20. |
| C5 | FALSIFIED AS PRINTED | Paper Table 2 MiceBone CE row: error 15.17 versus 15.23. |
| C6 | BLOCKED | No accepted source-faithful 48-cell MiceBone campaign. |

The collection-level status is therefore a **partial scoped audit**, not a
claim that the paper has been fully reproduced.

Machine-readable overall verdict: `PARTIAL_CLAIMS_1_TO_3_VERIFIED_SCOPED_CLAIM_4_LITERAL_THEOREM_FALSIFIED_CLAIM_5_SOURCE_TABLE_FALSIFIED_CLAIM_6_BLOCKED`.

Publication boundary: `HISTORICAL_5_OF_12_NO_CURRENT_SCORE_CLAIM_6_BLOCKED_NO_FULL_REPRODUCTION`; `publication_allowed=false`, `score_claim=false`, and `official_author_endorsement=false`.

## What this repository establishes

The exact release branch supports the stated finite algebraic certificates for
the aggregation mechanism, the first-correct partition, and the
continuity/consistency reconstruction. It also records two narrow
source-grounded contradictions: the printed CE equality in Theorem 6(A) and
the broad improvement conjunction against the paper's own Table 2 row.

The experiment branches preserve the intended MiceBone configurations and
calibration checkpoints. The stopped campaign, target ambiguity, and runtime
record are part of the result: they explain why Claim 6 is not promoted to a
scientific verdict.

## Historical external record

The prior judged Space record is preserved as historical evidence:

- Space: <code>DineshAI/uhNn8S6rEb</code>
- Revision: <code>6d7a28419633108958c5dccc2380e9232971cad3</code>
- Recorded score: <code>5/12</code>

This repository does not assert that score as a current judge result, and it
does not claim author endorsement.

## Publication policy

The normalized GitHub dossier is published for transparent review. The local
release policy keeps <code>publication_allowed</code> false for a new
scientific conclusion because Claim 6 remains blocked. Any future empirical
release must include the complete source-faithful contract, accepted artifacts
for all cells, aggregate statistics, and an independently readable manifest.

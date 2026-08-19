# Status

- Paper: When More Experts Hurt: Underfitting in Multi-Expert Learning to Defer
- Repository: `MachineLearning-Nerd/icml26-when-more-experts-hurt-underfitting-in-multi-expert-learning-to-defer`
- Overall verdict: `PARTIAL_CLAIMS_1_TO_3_VERIFIED_SCOPED_CLAIM_4_LITERAL_THEOREM_FALSIFIED_CLAIM_5_SOURCE_TABLE_FALSIFIED_CLAIM_6_BLOCKED`
- Publication boundary: `HISTORICAL_5_OF_12_NO_CURRENT_SCORE_CLAIM_6_BLOCKED_NO_FULL_REPRODUCTION`; `publication_allowed=false`, `score_claim=false`, `official_author_endorsement=false`.
- Current phase: published scoped audit; Claim 6 remains blocked until a complete source-faithful 48-cell MiceBone campaign is accepted.
- Branches: 64 descriptive branches (`main`, 9 `audit/*`, 3 `release/*`, and 51 `experiment/*`).
- Attribution: all reachable commits use `MachineLearning-Nerd <MachineLearning-Nerd@users.noreply.github.com>`.

## Claim outcomes

| Claim | Outcome | Evidence boundary |
| --- | --- | --- |
| C1 | `verified_scoped` | Exact constructive aggregation family and margin scaling. |
| C2 | `verified_scoped` | First-correct partition with 873 finite correlated/permutation checks. |
| C3 | `verified_scoped` | Continuity and CE/OvA consistency under stated assumptions. |
| C4 | `falsified_literal_theorem_formula` | CE optimum 2/5 versus the printed 7/20. |
| C5 | `falsified_source_table` | Table 2 MiceBone CE error 15.17 versus 15.23. |
| C6 | `blocked_source_faithful_empirical` | No accepted complete J=2/4/6/8, four-method, three-seed campaign. |

The machine-readable record is [reproduction_verdicts.json](reproduction_verdicts.json). The historical external record is 5/12 on the recorded Space revision; no current score or author endorsement is claimed.

# Branch audit

This file is the complete branch inventory for the repository normalization. Every source branch was preserved by tip, then renamed to describe its evidence role. The old names exposed the internal orx namespace; the new names expose whether a branch is an audit, release record, or experiment checkpoint.

Expected live state after publication: 64 branches total, one main branch, 9 audit branches, 3 release branches, and 51 experiment branches. The source repository had main plus 63 orx/* branches; no branch was discarded.

| Old ref | New ref | Purpose |
| --- | --- | --- |
| main | main | Documentation landing page and canonical repository entrypoint. |
| orx/aggregate-preregistered-micebone-claim-6 | release/claim-6-aggregate-preregistered | Stopped/preregistered Claim 6 campaign and release-policy record. |
| orx/audit-micebone-majority-tie-rules | audit/micebone-majority-tie-rules | MiceBone majority vote-pool and tie-rule audit. |
| orx/audit-official-micebone-release | audit/official-micebone-release | Audit of the official MiceBone release and inventory. |
| orx/audit-table-2-consistency-claim | audit/table-2-consistency-claim | Source/Table 2 consistency audit for the broad empirical claim. |
| orx/baseline-exact-theorem-audit | audit/baseline-exact-theorem | Pinned exact theorem-audit baseline and environment. |
| orx/benchmark-channels-last-micebone-shard | audit/channels-last-micebone-shard | CPU channels-last shard benchmark and runtime audit. |
| orx/calibrate-corrected-micebone-cpu-training | experiment/micebone-corrected-cpu-training | Corrected MiceBone CPU calibration. |
| orx/calibrate-micebone-cpu-training | experiment/micebone-cpu-training | Initial full-data CPU training calibration. |
| orx/compare-micebone-target-vote-pools | audit/micebone-target-vote-pools | Comparison of MiceBone target vote pools. |
| orx/expose-exact-theory-evidence | release/exact-theory-evidence | Exact CPU theorem evidence and audit outputs. |
| orx/inspect-micebone-annotations | audit/micebone-annotations | MiceBone annotation inventory and geometry audit. |
| orx/machine-check-universal-theory-certificates | release/universal-theory-certificates | Canonical Claims 1–5 certificates, independent checks, and negative controls. |
| orx/preregister-micebone-figure-2-sweep | experiment/micebone-figure-2-sweep | Preregistered Figure 2 MiceBone sweep and verified shard record. |
| orx/resolve-micebone-target-labels | audit/micebone-target-labels | MiceBone clean-target reconstruction against paper Table 3. |
| orx/validate-micebone-shard-pipeline | audit/micebone-shard-pipeline | MiceBone shard and pipeline validation. |
| orx/micebone-j2-ce-seed-260217144 | experiment/micebone-j2-ce-seed-260217144 | MiceBone J=2, ce, seed 260217144 configuration/training checkpoint. |
| orx/micebone-j2-ce-seed-260217145 | experiment/micebone-j2-ce-seed-260217145 | MiceBone J=2, ce, seed 260217145 configuration/training checkpoint. |
| orx/micebone-j2-ce-seed-260217146 | experiment/micebone-j2-ce-seed-260217146 | MiceBone J=2, ce, seed 260217146 configuration/training checkpoint. |
| orx/micebone-j2-ova-seed-260217144 | experiment/micebone-j2-ova-seed-260217144 | MiceBone J=2, ova, seed 260217144 configuration/training checkpoint. |
| orx/micebone-j2-ova-seed-260217145 | experiment/micebone-j2-ova-seed-260217145 | MiceBone J=2, ova, seed 260217145 configuration/training checkpoint. |
| orx/micebone-j2-ova-seed-260217146 | experiment/micebone-j2-ova-seed-260217146 | MiceBone J=2, ova, seed 260217146 configuration/training checkpoint. |
| orx/micebone-j2-picce-ce-seed-260217144 | experiment/micebone-j2-picce-ce-seed-260217144 | MiceBone J=2, picce-ce, seed 260217144 configuration/training checkpoint. |
| orx/micebone-j2-picce-ce-seed-260217145 | experiment/micebone-j2-picce-ce-seed-260217145 | MiceBone J=2, picce-ce, seed 260217145 configuration/training checkpoint. |
| orx/micebone-j2-picce-ce-seed-260217146 | experiment/micebone-j2-picce-ce-seed-260217146 | MiceBone J=2, picce-ce, seed 260217146 configuration/training checkpoint. |
| orx/micebone-j2-picce-ova-seed-260217144 | experiment/micebone-j2-picce-ova-seed-260217144 | MiceBone J=2, picce-ova, seed 260217144 configuration/training checkpoint. |
| orx/micebone-j2-picce-ova-seed-260217145 | experiment/micebone-j2-picce-ova-seed-260217145 | MiceBone J=2, picce-ova, seed 260217145 configuration/training checkpoint. |
| orx/micebone-j2-picce-ova-seed-260217146 | experiment/micebone-j2-picce-ova-seed-260217146 | MiceBone J=2, picce-ova, seed 260217146 configuration/training checkpoint. |
| orx/micebone-j4-ce-seed-260217144 | experiment/micebone-j4-ce-seed-260217144 | MiceBone J=4, ce, seed 260217144 configuration/training checkpoint. |
| orx/micebone-j4-ce-seed-260217145 | experiment/micebone-j4-ce-seed-260217145 | MiceBone J=4, ce, seed 260217145 configuration/training checkpoint. |
| orx/micebone-j4-ce-seed-260217146 | experiment/micebone-j4-ce-seed-260217146 | MiceBone J=4, ce, seed 260217146 configuration/training checkpoint. |
| orx/micebone-j4-ova-seed-260217144 | experiment/micebone-j4-ova-seed-260217144 | MiceBone J=4, ova, seed 260217144 configuration/training checkpoint. |
| orx/micebone-j4-ova-seed-260217145 | experiment/micebone-j4-ova-seed-260217145 | MiceBone J=4, ova, seed 260217145 configuration/training checkpoint. |
| orx/micebone-j4-ova-seed-260217146 | experiment/micebone-j4-ova-seed-260217146 | MiceBone J=4, ova, seed 260217146 configuration/training checkpoint. |
| orx/micebone-j4-picce-ce-seed-260217144 | experiment/micebone-j4-picce-ce-seed-260217144 | MiceBone J=4, picce-ce, seed 260217144 configuration/training checkpoint. |
| orx/micebone-j4-picce-ce-seed-260217145 | experiment/micebone-j4-picce-ce-seed-260217145 | MiceBone J=4, picce-ce, seed 260217145 configuration/training checkpoint. |
| orx/micebone-j4-picce-ce-seed-260217146 | experiment/micebone-j4-picce-ce-seed-260217146 | MiceBone J=4, picce-ce, seed 260217146 configuration/training checkpoint. |
| orx/micebone-j4-picce-ova-seed-260217144 | experiment/micebone-j4-picce-ova-seed-260217144 | MiceBone J=4, picce-ova, seed 260217144 configuration/training checkpoint. |
| orx/micebone-j4-picce-ova-seed-260217145 | experiment/micebone-j4-picce-ova-seed-260217145 | MiceBone J=4, picce-ova, seed 260217145 configuration/training checkpoint. |
| orx/micebone-j4-picce-ova-seed-260217146 | experiment/micebone-j4-picce-ova-seed-260217146 | MiceBone J=4, picce-ova, seed 260217146 configuration/training checkpoint. |
| orx/micebone-j6-ce-seed-260217144 | experiment/micebone-j6-ce-seed-260217144 | MiceBone J=6, ce, seed 260217144 configuration/training checkpoint. |
| orx/micebone-j6-ce-seed-260217145 | experiment/micebone-j6-ce-seed-260217145 | MiceBone J=6, ce, seed 260217145 configuration/training checkpoint. |
| orx/micebone-j6-ce-seed-260217146 | experiment/micebone-j6-ce-seed-260217146 | MiceBone J=6, ce, seed 260217146 configuration/training checkpoint. |
| orx/micebone-j6-ova-seed-260217144 | experiment/micebone-j6-ova-seed-260217144 | MiceBone J=6, ova, seed 260217144 configuration/training checkpoint. |
| orx/micebone-j6-ova-seed-260217145 | experiment/micebone-j6-ova-seed-260217145 | MiceBone J=6, ova, seed 260217145 configuration/training checkpoint. |
| orx/micebone-j6-ova-seed-260217146 | experiment/micebone-j6-ova-seed-260217146 | MiceBone J=6, ova, seed 260217146 configuration/training checkpoint. |
| orx/micebone-j6-picce-ce-seed-260217144 | experiment/micebone-j6-picce-ce-seed-260217144 | MiceBone J=6, picce-ce, seed 260217144 configuration/training checkpoint. |
| orx/micebone-j6-picce-ce-seed-260217145 | experiment/micebone-j6-picce-ce-seed-260217145 | MiceBone J=6, picce-ce, seed 260217145 configuration/training checkpoint. |
| orx/micebone-j6-picce-ce-seed-260217146 | experiment/micebone-j6-picce-ce-seed-260217146 | MiceBone J=6, picce-ce, seed 260217146 configuration/training checkpoint. |
| orx/micebone-j6-picce-ova-seed-260217144 | experiment/micebone-j6-picce-ova-seed-260217144 | MiceBone J=6, picce-ova, seed 260217144 configuration/training checkpoint. |
| orx/micebone-j6-picce-ova-seed-260217145 | experiment/micebone-j6-picce-ova-seed-260217145 | MiceBone J=6, picce-ova, seed 260217145 configuration/training checkpoint. |
| orx/micebone-j6-picce-ova-seed-260217146 | experiment/micebone-j6-picce-ova-seed-260217146 | MiceBone J=6, picce-ova, seed 260217146 configuration/training checkpoint. |
| orx/micebone-j8-ce-seed-260217144 | experiment/micebone-j8-ce-seed-260217144 | MiceBone J=8, ce, seed 260217144 configuration/training checkpoint. |
| orx/micebone-j8-ce-seed-260217145 | experiment/micebone-j8-ce-seed-260217145 | MiceBone J=8, ce, seed 260217145 configuration/training checkpoint. |
| orx/micebone-j8-ce-seed-260217146 | experiment/micebone-j8-ce-seed-260217146 | MiceBone J=8, ce, seed 260217146 configuration/training checkpoint. |
| orx/micebone-j8-ova-seed-260217144 | experiment/micebone-j8-ova-seed-260217144 | MiceBone J=8, ova, seed 260217144 configuration/training checkpoint. |
| orx/micebone-j8-ova-seed-260217145 | experiment/micebone-j8-ova-seed-260217145 | MiceBone J=8, ova, seed 260217145 configuration/training checkpoint. |
| orx/micebone-j8-ova-seed-260217146 | experiment/micebone-j8-ova-seed-260217146 | MiceBone J=8, ova, seed 260217146 configuration/training checkpoint. |
| orx/micebone-j8-picce-ce-seed-260217144 | experiment/micebone-j8-picce-ce-seed-260217144 | MiceBone J=8, picce-ce, seed 260217144 configuration/training checkpoint. |
| orx/micebone-j8-picce-ce-seed-260217145 | experiment/micebone-j8-picce-ce-seed-260217145 | MiceBone J=8, picce-ce, seed 260217145 configuration/training checkpoint. |
| orx/micebone-j8-picce-ce-seed-260217146 | experiment/micebone-j8-picce-ce-seed-260217146 | MiceBone J=8, picce-ce, seed 260217146 configuration/training checkpoint. |
| orx/micebone-j8-picce-ova-seed-260217144 | experiment/micebone-j8-picce-ova-seed-260217144 | MiceBone J=8, picce-ova, seed 260217144 configuration/training checkpoint. |
| orx/micebone-j8-picce-ova-seed-260217145 | experiment/micebone-j8-picce-ova-seed-260217145 | MiceBone J=8, picce-ova, seed 260217145 configuration/training checkpoint. |
| orx/micebone-j8-picce-ova-seed-260217146 | experiment/micebone-j8-picce-ova-seed-260217146 | MiceBone J=8, picce-ova, seed 260217146 configuration/training checkpoint. |

## Interpretation rules

- main is the public documentation entrypoint; the original main branch was only a placeholder README.
- audit/* branches preserve source, theorem, data-inventory, target, tie-rule, pipeline, and table audits.
- release/* branches preserve curated evidence snapshots and campaign/release records. A release branch is not a claim of paper acceptance.
- experiment/* branches preserve configurations, calibrations, shards, and seed-specific training checkpoints. A configuration branch is not an accepted result.
- Branch tips were retained even where the underlying experiment stopped or was explicitly rejected by the evidence policy.

## Verification checklist

- [ ] Every old orx/* branch has exactly one descriptive new branch.
- [ ] No old orx/* branch remains on GitHub after publication.
- [ ] All reachable commits use the MachineLearning-Nerd author and committer identity.
- [ ] main is the default branch and contains the current README and this inventory.
- [ ] Claim 6 remains BLOCKED until a complete, source-faithful, three-seed J=2/4/6/8 campaign is independently accepted.


# Normalized branch summary

The live repository contains 64 public branches:

| Group | Count | Purpose |
| --- | ---: | --- |
| main | 1 | Documentation landing page and final-state verifier. |
| audit/* | 9 | Source, theorem baseline, MiceBone provenance, labels, ties, vote pools, pipeline, and Table 2 audits. |
| release/* | 3 | Exact theory evidence, universal certificates, and the stopped Claim 6 preregistration. |
| experiment/* | 51 | MiceBone calibration, Figure 2 sweep, and explicit J/method/seed checkpoints. |

The complete old-to-new inventory is in
[branch-audit.md](branch-audit.md). It records all 63 former orx/* tips,
their normalized names, and their purpose. The normalized live state has no
orx/*, work/*, or unnamed legacy branches, and no source tip was discarded.

The 48 seed branches are the Cartesian product of:

- J in 2, 4, 6, and 8;
- CE, OvA, PiCCE-CE, and PiCCE-OvA;
- seeds 260217144, 260217145, and 260217146.

The three additional experiment branches are
experiment/micebone-corrected-cpu-training,
experiment/micebone-cpu-training, and
experiment/micebone-figure-2-sweep.

All reachable commits are attributed to:

    MachineLearning-Nerd <37579156+MachineLearning-Nerd@users.noreply.github.com>

Branch names describe evidence roles. Their existence does not imply that
every experiment completed or that a branch's result was accepted.

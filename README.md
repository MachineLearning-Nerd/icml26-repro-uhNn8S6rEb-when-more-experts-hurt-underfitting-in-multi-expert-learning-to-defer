# When More Experts Hurt: Underfitting in Multi-Expert Learning to Defer

This repository is a clean-room audit and reproduction workspace for the ICML 2026 paper “When More Experts Hurt: Underfitting in Multi-Expert Learning to Defer.” It records which claims are supported by exact checks, which are contradicted by the paper’s own formulas or tables, and which still require a faithful dataset experiment.

The current scientific status is deliberately conservative:

- Claims 1–3 are verified at the theorem or probability-identity level.
- Claim 4 is falsified as printed: the exact CE optimum is 2/5, while Theorem 6(A) prints 7/20, a gap of 1/20.
- Claim 5 is falsified as printed by the paper’s own Table 2 MiceBone row: vanilla CE error is 15.17 and PiCCE-CE error is 15.23.
- Claim 6 is blocked: no full, source-faithful MiceBone training grid is accepted as evidence.

This is an audit record, not a claim that the paper’s complete empirical story has been reproduced.

Machine-readable overall verdict: `PARTIAL_CLAIMS_1_TO_3_VERIFIED_SCOPED_CLAIM_4_LITERAL_THEOREM_FALSIFIED_CLAIM_5_SOURCE_TABLE_FALSIFIED_CLAIM_6_BLOCKED`.

Publication boundary: `HISTORICAL_5_OF_12_NO_CURRENT_SCORE_CLAIM_6_BLOCKED_NO_FULL_REPRODUCTION`; `publication_allowed=false`, `score_claim=false`, and `official_author_endorsement=false`.

## Paper

- Title: When More Experts Hurt: Underfitting in Multi-Expert Learning to Defer
- Authors: Shuqi Liu, Yuzhou Cao, Lei Feng, Bo An, and Luke Ong
- arXiv: [2602.17144](https://arxiv.org/abs/2602.17144)
- HTML paper: [arxiv.org/html/2602.17144](https://arxiv.org/html/2602.17144)
- OpenReview: [uhNn8S6rEb](https://openreview.net/forum?id=uhNn8S6rEb)

## What the paper is doing

The paper studies learning to defer with multiple human or machine experts. Its central argument is that vanilla expert aggregation adds expert accuracies into the classifier denominator. As the number of experts J grows, this can flatten the dummy-label probability and make the classifier underfit. The paper proposes PiCCE, or Pick the Confident and Correct Expert, which selects a high-scoring expert among experts that are correct on the current example. It then develops continuity and consistency arguments and evaluates the method on synthetic and image datasets, including MiceBone.

The audit separates the paper’s mathematical statements from its empirical statements. A proof certificate can establish a universal identity; it cannot establish that a neural-network training campaign reproduces the reported dataset results.

## Claim-to-evidence ledger

| Claim | Evidence path | Current result | Scope and limitation |
| --- | --- | --- | --- |
| 1. Vanilla aggregation can cause underfitting as J grows | theory.py, verify.py, theory_results.json, and pages/current-verification.md on release/universal-theory-certificates | VERIFIED | The all-3/4-accurate family gives exact aggregation 3J/4 and dummy-label margin (1/5)/(1+3J/4) = Theta(1/J). This verifies the stated scaling mechanism, not every empirical consequence. |
| 2. PiCCE first-correct terms form a partition | proof_certificates.py, independent_proof_check.py, and proof verifier artifacts | VERIFIED | The first-correct events partition the at-least-one-correct event for every expert permutation. Correlated Boolean domains and permutations through J=6 were exhaustively checked with 873 order checks. |
| 3. Continuity and CE/OvA consistency | theory.py, verify_proof_certificates.py, and the reconstructed derivation in pages/current-verification.md | VERIFIED | The symmetry and normalization argument was reconstructed under the assumptions stated in the paper. |
| 4. Theorem 6(A) CE score formula | source_audit.md, theory.py, verifier_output.json, and independent_checker_output.json | FALSIFIED AS PRINTED | A Condition-1 distribution gives CE optimum 2/5; the printed formula gives 7/20. The counterexample satisfies the theorem’s quantifiers. |
| 5. PiCCE improves system error and coverage across reported settings | source_audit.md and the paper’s Table 2 audit | FALSIFIED AS PRINTED | For MiceBone with two experts under CE, the paper reports error 15.17 for vanilla and 15.23 for PiCCE. This contradicts the broad improvement conjunction as printed; it does not prove PiCCE is always worse. |
| 6. MiceBone vanilla accuracy degrades with J while PiCCE stays stable | claim6_contract.json, MiceBone training branches, and calibration artifacts | BLOCKED | The full J=2/4/6/8, CE/OvA, PiCCE-CE/PiCCE-OvA, three-seed campaign is not accepted. The one-epoch J=2 CE run is explicitly calibration only. |

## Audit dossier and final-state check

The repository-level audit is split into focused, reviewable records:

- [CLAIM_EVIDENCE.md](CLAIM_EVIDENCE.md) maps every paper claim to its production path, result, scope, and limitation.
- [SOURCE_AUDIT.md](SOURCE_AUDIT.md) freezes the paper source, reported table values, theorem contradiction, and MiceBone target assumptions.
- [ENVIRONMENT.md](ENVIRONMENT.md) records the exact theory and training environments, including the stopped 48-cell campaign.
- [REPORT.md](REPORT.md) gives the conservative reproduction verdict and publication policy.
- [STATUS.md](STATUS.md) and [reproduction_verdicts.json](reproduction_verdicts.json) record the current state in human- and machine-readable form.
- [BRANCH_AUDIT.md](BRANCH_AUDIT.md) summarizes the normalized branch groups; [branch-audit.md](branch-audit.md) is the complete old-to-new map.
- [CITATION.cff](CITATION.cff) and [AUTHOR_THANK_YOU.md](AUTHOR_THANK_YOU.md) provide the citation and author acknowledgment.

From a fresh clone, run:

~~~sh
python3 verify_final.py
~~~

The verifier checks the live origin branch set, canonical MachineLearning-Nerd commit attribution, required dossier files, claim contracts, selected branch evidence hashes, and the explicit Claim 6 publication block. It does not convert a source-table audit or a calibration run into an accepted empirical reproduction.

## How each claim is produced

1. Source contract: source_audit.md freezes the relevant equations, assumptions, table values, and the MiceBone target ambiguity against the paper source.
2. Exact theory checks: theory.py and verify.py construct rational distributions and calculate the aggregation, CE, and theorem quantities. The independent checker repeats the central checks separately.
3. Universal proof checks: proof_certificates.py and verify_proof_certificates.py check the permutation and continuity claims, with negative controls that must fail when evidence is tampered with.
4. Empirical-table audit: the Table 2 result is read from the paper itself. It is labeled a source-table falsification, not an independent model-training result.
5. Dataset reconstruction: the MiceBone inventory and annotation artifacts record 7,240 images, eight complete annotators, fold counts, vote-pool alternatives, and tie rules. Complete-annotator majority with priority g > ug > nr matches 14 of 16 Table 3 values after rounding, but two residual discrepancies remain.
6. Training calibration: the MiceBone experiment branches pin model, optimizer, seed, and shard settings. The one-epoch J=2 CE artifact records 489.03 seconds of CPU runtime and is marked accepted_scientific_result=false. It cannot decide Claim 6.

## Repository contents and branch roles

The main branch is the documentation landing page. The executable theory and experiment material is preserved on the descriptive audit, release, and experiment branches. The full old-to-new branch map is in [branch-audit.md](branch-audit.md).

| Branch group | Role |
| --- | --- |
| main | Landing page, claim ledger, citation, thank-you note, and repository policy. |
| audit/* | Source, annotation, target, pipeline, theorem-baseline, and Table 2 audits. |
| release/* | Curated exact-theory evidence, universal proof certificates, and the preregistered Claim 6 campaign record. |
| experiment/* | MiceBone calibration, figure-2 sweep, and explicitly named J/method/seed checkpoints. |

There are 64 preserved branches in total after normalization: main plus 63 descriptive descendants. Branch names no longer expose the internal orx prefix, and each branch name describes the evidence or experiment it contains. No branch is silently treated as a successful reproduction merely because it contains a training configuration.

Representative entry points:

- release/universal-theory-certificates: exact Claims 1–5 audit, proof certificates, independent checks, negative controls, and current-verification.md.
- release/claim-6-aggregate-preregistered: stopped/preregistered Claim 6 campaign record and release-policy artifacts.
- audit/micebone-target-labels and audit/micebone-majority-tie-rules: data-target and tie-rule reconstruction.
- experiment/micebone-j2-ce-seed-260217144: one-epoch CPU calibration, explicitly not accepted scientific evidence.

## Reproduction status and limitations

Run the exact theory/proof checks from a branch containing the code with:

    uv run --frozen python run.py

The historical compute contract uses Python 3.12, uv.lock, and Hugging Face cpu-upgrade. Dataset training requires the MiceBone release and the target reconstruction documented in the artifacts; it is not reproducible from this main branch alone.

Important limitations:

- The paper does not fully specify clean MiceBone targets, majority tie handling, augmentation, normalization, or pretrained initialization.
- The strongest target reconstruction is a documented choice, not a fact supplied by the paper.
- Claims 1–3 are proof-level checks and do not substitute for a trained image model.
- Claim 5 relies on the paper’s reported Table 2 means; the underlying MiceBone run has not been independently repeated here.
- No final judge score or full empirical Claim 6 conclusion is asserted.

## Citation

    @article{liu2026when,
      title = {When More Experts Hurt: Underfitting in Multi-Expert Learning to Defer},
      author = {Liu, Shuqi and Cao, Yuzhou and Feng, Lei and An, Bo and Ong, Luke},
      journal = {arXiv preprint arXiv:2602.17144},
      year = {2026},
      eprint = {2602.17144},
      archivePrefix = {arXiv},
      primaryClass = {cs.LG}
    }

## Thank you

Thank you to Shuqi Liu, Yuzhou Cao, Lei Feng, Bo An, and Luke Ong for the paper, the formal framing, and the empirical details that make independent scrutiny possible. This repository is intended as a respectful, transparent reproduction and audit record: positive checks are credited precisely, discrepancies are reported narrowly, and unresolved experiments remain marked as unresolved.

## Attribution

Approved repository commits and rewritten reachable history use the MachineLearning-Nerd GitHub identity:

    MachineLearning-Nerd <MachineLearning-Nerd@users.noreply.github.com>

The original repository name was icml26-repro-uhNn8S6rEb-when-more-experts-hurt-underfitting-in-multi-expert-learning-to-defer. It is being normalized to icml26-when-more-experts-hurt-underfitting-in-multi-expert-learning-to-defer.

# Source and provenance audit

## Paper identity

- Title: **When More Experts Hurt: Underfitting in Multi-Expert Learning to Defer**
- Authors: Shuqi Liu, Yuzhou Cao, Lei Feng, Bo An, and Luke Ong
- arXiv: [2602.17144](https://arxiv.org/abs/2602.17144)
- HTML source used for the audit: [ar5iv HTML](https://ar5iv.labs.arxiv.org/html/2602.17144)
- OpenReview: [uhNn8S6rEb](https://openreview.net/forum?id=uhNn8S6rEb)
- Former repository: <code>icml26-repro-uhNn8S6rEb-when-more-experts-hurt-underfitting-in-multi-expert-learning-to-defer</code>
- Current repository: <code>icml26-when-more-experts-hurt-underfitting-in-multi-expert-learning-to-defer</code>

The ar5iv HTML was retrieved with a browser User-Agent on 2026-08-01 at
04:32:52 UTC. Its SHA-256 is:

    d381ed2e443e7f2cdb48f51bf0e8cf8d07333bd4ae484fc6a0e4c0922bf67fdc

The audited source scope is Definition 1 / Eq. 9, Theorem 2, Lemmas 3–5,
Condition 1, Theorem 6, Section 6, Tables 1–2, Figure 2, and Appendix D.

## What is being audited

The paper studies learning to defer with multiple human or machine experts.
Vanilla aggregation adds expert accuracies to the classifier denominator,
which can flatten the dummy-label probability as J grows. PiCCE selects a
high-scoring expert among experts that are correct on the current example.
The paper then gives continuity and consistency arguments and reports
synthetic and image experiments, including MiceBone.

The audit treats formulas and reported tables as source claims, while model
training is a separate empirical claim. This distinction is important because
the source does not release a complete, unambiguous MiceBone target and
training specification in the material audited here.

## Frozen source facts

1. Eq. 6 uses vanilla aggregation <code>A(x) = sum_j Acc_j(x)</code> and the
   dummy-label probability <code>eta_y(x)/(1 + A(x))</code>.
2. Definition 1 / Eq. 9 selects the highest-scored correct expert.
3. Lemma 4 quantifies over every permutation and x and identifies the
   first-correct sum with union coverage.
4. Theorem 2 uses continuity and symmetry in the last J inputs; Lemma 5
   gives CE and OvA consistency statements.
5. Section 6.2 says PiCCE has improved system error and higher coverage across
   different expert counts on MiceBone and Chaoyang.
6. Table 2, MiceBone, CE, two experts reports vanilla (Err,Cov) =
   (15.17, 60.92) and PiCCE (15.23, 69.28).
7. Figure 2 and Section 6.2 state the accuracy-degradation/stability story
   for increasing expert counts; Appendix D.2 specifies ResNet-18, AdamW,
   learning rate 3e-4, weight decay 5e-4, batch size 128, 100 epochs, the
   first 2/4/6/8 experts in Table 3 order, folds 1–4 for training, and fold 5
   for testing.

## Theorem 6(A) audit

Theorem 6(A) prints <code>u*_{j*} = Acc_{j*} V_tilde</code>, while the proof derives
<code>u*_{j*} = Acc_{j*}/(1 + V) = Acc_{j*}(1 - V_tilde)</code>. The exact rational
counterexample preserved on <code>release/universal-theory-certificates</code> has:

- accuracies 3/4 and 1/2;
- eta = (3/5, 2/5);
- joint correctness masses (1, 1, 3, 3)/8;
- CE optimum 2/5;
- printed formula 7/20;
- absolute discrepancy 1/20.

The condition audit confirms positive weights, a unique most-accurate expert,
and every required strict subset inequality. No extra assumption in the
proof makes the two formulas equal for 0 < V < 1.

## MiceBone provenance and target ambiguity

- Official source: [Zenodo record 8115942](https://zenodo.org/records/8115942)
- Archive: <code>MiceBone.zip</code>
- Recorded MD5: <code>8a4026c22f07373f022d9ab4818089ec</code>
- Figure asset: [MiceBone.png](https://ar5iv.labs.arxiv.org/html/2602.17144/assets/Figure/MiceBone.png)
- Figure asset SHA-256:
  <code>b8943f6e1f1eec14629dd75d194d5b38fbcb9393d0256b958b99827006829d9d</code>

The source does not fully specify clean targets, majority tie handling,
augmentation, normalization, or pretrained initialization. The audit
compares defensible vote pools and six class-priority rules against the 16
Table 3 values. Majority over the eight complete annotators with priority
<code>g &gt; ug &gt; nr</code> is the strongest documented reconstruction: it
recovers 14/16 values after rounding, with mean absolute error 0.009665 and
maximum error 0.106358 percentage points. The two residual discrepancies
remain open limitations, not silently corrected values.

## Provenance limits

The source audit is based on the pinned HTML and the recorded official
MiceBone archive identifier. The Table 2 contradiction uses the paper's own
reported means; it is not a fresh training result. The exact theory branch
contains the executable checker and its recorded PASS outputs. The Claim 6
branch contains a stopped preregistration and calibration evidence, not a
complete accepted training bundle.

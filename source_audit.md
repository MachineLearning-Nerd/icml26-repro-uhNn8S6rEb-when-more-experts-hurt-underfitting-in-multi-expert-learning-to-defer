# Source audit

- Source: <https://ar5iv.labs.arxiv.org/html/2602.17144>
- Retrieved with `Mozilla/5.0` User-Agent: 2026-08-01T04:32:52Z
- Retrieved HTML SHA-256: `d381ed2e443e7f2cdb48f51bf0e8cf8d07333bd4ae484fc6a0e4c0922bf67fdc`
- Scope: Definition 1 / Eq. 9, Theorem 2, Lemmas 3–5, Condition 1,
  Theorem 6, Section 6, Tables 1–2, Figure 2, and Appendix D.

## Exact contracts and assumptions

1. Section 3.1 / Eq. 6 defines the vanilla expert aggregation
   `A(x)=sum_j Acc_j(x)` and the dummy label probability
   `eta_y(x)/(1+A(x))`; the paper says `A(x)=O(J)` and this flattening
   causes multi-expert classifier underfitting.
2. Definition 1 / Eq. 9 selects the highest-scored correct expert. Lemma 4
   quantifies over **any** permutation and any `x` and states
   `sum_j A_sigma^j(x) = Pr(union_j M_j=Y | X=x)`. The latter is at most one.
3. Theorem 2 assumes only continuity of the base loss and symmetry in its
   last `J` inputs. Lemma 5 quantifies over any `x` and any population-risk
   minimizer for the CE and OvA-log losses.
4. Condition 1 requires a unique most accurate expert `j*` and, for every
   other expert `j` and every subset excluding `j,j*`, strictly greater union
   coverage after adding `j*` than after adding `j`. Theorem 6 quantifies over
   any `x` satisfying that condition and any risk minimizer.
5. Section 6.2 says PiCCE has "improved system error and higher coverage
   across different numbers of experts" on MiceBone and Chaoyang. Table 2's
   MiceBone/two-expert CE row reports `(Err,Cov)=(15.17,60.92)` for vanilla
   and `(15.23,69.28)` for PiCCE. The error component is worse, so the
   printed conjunction and the imported "consistently outperforms" claim
   have an explicit counterexample in the paper's own table.

## Theorem 6(A) source contradiction

Theorem 6(A) states, for cross-entropy,

`u*_{j*} = Acc_{j*}(x) * V_tilde(x)`,

where Lemma 5 defines `V_tilde=V/(1+V)`. The paper's own proof instead derives

`u*_{j*} = Acc_{j*}(x)/(1+V(x)) = Acc_{j*}(x)*(1-V_tilde(x))`.

These formulas disagree whenever `0<V<1`; the baseline
constructs an exact rational distribution satisfying every Condition 1
quantifier and obtains `2/5` from the CE risk but `7/20` from the theorem's
printed formula.

The ar5iv wording was cross-checked against the arXiv source archive:
`preprint.tex` states the first formula near line 786 and derives the second
near lines 1414–1447. No assumption added in the proof makes them equal.

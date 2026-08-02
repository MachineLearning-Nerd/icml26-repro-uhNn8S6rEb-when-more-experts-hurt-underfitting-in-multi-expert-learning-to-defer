def build_proof_certificates() -> dict:
    return {
        "schema_version": 1,
        "source": {
            "paper": "arXiv:2602.17144v1",
            "ar5iv_sha256": "d381ed2e443e7f2cdb48f51bf0e8cf8d07333bd4ae484fc6a0e4c0922bf67fdc",
            "anchors": ["Equation 6", "Definition 1 / Equation 9", "Theorem 2", "Lemma 4", "Lemma 5"],
        },
        "claim_1": {
            "quantifiers": "For every J>=1 and every family alpha<=Acc_j<=beta with 0<alpha<=beta<=1.",
            "assumptions": ["J>=1", "0<alpha<=Acc_j<=beta<=1", "eta_top-eta_runner_up=delta>0"],
            "aggregation_bounds": ["alpha*J <= A_J", "A_J <= beta*J"],
            "margin_identity": "m_J=delta/(1+A_J)",
            "margin_bounds": ["delta/((1+beta)*J) <= m_J", "m_J <= delta/(alpha*J)"],
            "conclusion": "A_J=Theta(J) and m_J=Theta(1/J)",
        },
        "claim_2": {
            "quantifiers": "For every finite J, every permutation sigma, every x, and every joint expert-correctness law.",
            "event_definition": "E_k=C_sigma(k) AND all_{r<k} NOT C_sigma(r)",
            "pairwise_disjoint": "For k<l, E_k requires C_sigma(k) while E_l requires NOT C_sigma(k).",
            "union_equality": "union_k E_k equals union_j C_j by choosing the first correct expert in sigma.",
            "probability_identity": "sum_k Pr(E_k|x)=Pr(union_j C_j|x)<=1",
            "contrast": "sum_j Pr(C_j|x) can equal J",
        },
        "claim_3": {
            "theorem_2": {
                "quantifiers": "Every continuous base loss symmetric in its last J coordinates.",
                "region_continuity": "On each expert-score ordering cone, PiCCE is a continuous composition.",
                "overlap_agreement": True,
                "overlap_reason": "Orderings differ on a shared boundary only by permutations of tied equal coordinates; symmetry gives the same value.",
                "gluing_rule": "A finite closed cover of continuous restrictions agreeing on overlaps is continuous.",
                "ce_rewrite": "logsumexp(all_scores)-max(correct_expert_scores)",
                "ova_rewrite": "-max(correct_expert_scores)",
                "no_correct_case": "constant zero",
            },
            "lemma_5": {
                "quantifiers": "Every x and every population minimizer; finite CE/OvA coordinates for interior class probabilities.",
                "partition_mass": "V=sum_j A_sigma^j=Pr(any expert correct|x)",
                "ce_risk": "-sum_y eta_y log(q_y)-sum_j A_sigma^j log(q_K+j)",
                "ce_minimizer": "q_y=eta_y/(1+V)",
                "ce_recovery": "q_y/sum_c q_c=eta_y",
                "ova_coordinate_risk": "eta_y*softplus(-u_y)+(1-eta_y)*softplus(u_y)",
                "ova_derivative": "sigmoid(u_y)-eta_y",
                "ova_recovery": "sigmoid(u_y)=eta_y",
                "boundary_rule": "eta_y in {0,1} follows by the corresponding extended-real limit",
                "decision": "argmax_y score_y is contained in argmax_y eta_y",
            },
        },
    }

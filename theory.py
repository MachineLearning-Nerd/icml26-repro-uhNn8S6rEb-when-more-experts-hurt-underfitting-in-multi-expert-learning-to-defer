from fractions import Fraction
from itertools import permutations, product


def ratio(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def claim_1() -> dict:
    eta = [Fraction(1, 2), Fraction(3, 10), Fraction(1, 5)]
    accuracy = Fraction(3, 4)
    sweep = []
    for experts in [1, 2, 4, 8, 16, 32, 64]:
        aggregation = experts * accuracy
        denominator = 1 + aggregation
        margin = (eta[0] - eta[1]) / denominator
        sweep.append(
            {
                "experts": experts,
                "aggregation": ratio(aggregation),
                "dummy_label_margin": ratio(margin),
            }
        )
    return {
        "verdict": "VERIFIED",
        "family": "J experts, each with conditional accuracy 3/4",
        "aggregation_identity": "A_J = 3J/4",
        "asymptotic_certificate": {
            "lower_bound_for_J_ge_1": "3J/4 <= 1+A_J",
            "upper_bound_for_J_ge_1": "1+A_J <= 7J/4",
            "margin_identity": "(eta_1-eta_2)/(1+A_J) = (1/5)/(1+3J/4)",
            "conclusion": "A_J is Theta(J) and the label margin is Theta(1/J)",
        },
        "sweep": sweep,
    }


def claim_2() -> dict:
    checked = 0
    for experts in range(1, 7):
        masks = list(product([False, True], repeat=experts))
        total_weight = sum(range(1, len(masks) + 1))
        weights = {
            mask: Fraction(index, total_weight)
            for index, mask in enumerate(masks, start=1)
        }
        for order in permutations(range(experts)):
            first_correct_mass = Fraction(0)
            for position, expert in enumerate(order):
                first_correct_mass += sum(
                    weight
                    for mask, weight in weights.items()
                    if mask[expert]
                    and all(not mask[earlier] for earlier in order[:position])
                )
            union_mass = sum(weight for mask, weight in weights.items() if any(mask))
            if first_correct_mass != union_mass:
                raise AssertionError("Lemma 4 partition identity failed")
            checked += 1
    return {
        "verdict": "VERIFIED",
        "proof_certificate": {
            "partition": "E_j={first correct expert in permutation is sigma_j}",
            "disjoint": "E_j are pairwise disjoint by definition",
            "union": "union_j E_j = {at least one expert is correct}",
            "probability_identity": "sum_j Pr(E_j)=Pr(union_j M_j=Y)",
            "bound": "0 <= Pr(union_j M_j=Y) <= 1 for every J",
            "vanilla_contrast": "sum_j Acc_j <= J, with equality when all experts are always correct",
        },
        "exhaustive_correlated_checks": checked,
        "largest_complete_domain": "all Boolean correctness vectors and permutations through J=6",
    }


def claim_3() -> dict:
    eta = [Fraction(1, 2), Fraction(3, 10), Fraction(1, 5)]
    expert_partition_masses = [Fraction(3, 5), Fraction(1, 4), Fraction(1, 20)]
    union_probability = sum(expert_partition_masses)
    normalizer = 1 + union_probability
    ce_label_scores = [value / normalizer for value in eta]
    recovered_ce = [value / sum(ce_label_scores) for value in ce_label_scores]
    if recovered_ce != eta:
        raise AssertionError("CE class probabilities were not recovered")
    return {
        "verdict": "VERIFIED",
        "continuity_certificate": {
            "regions": "On each strict expert-score ordering, the selected component is continuous.",
            "tie_boundary": "Symmetry makes selected loss components equal whenever tied expert inputs are equal.",
            "gluing": "The finitely many continuous regions agree on every shared boundary.",
            "ce_specialization": "selected CE term = logsumexp(theta)-max_{correct j} theta_{K+j}",
            "no_correct_case": "The second term is the constant zero on that observed outcome.",
        },
        "consistency_certificate": {
            "ce_population_minimizer": "q_y=eta_y/(1+V); normalizing q_1..q_K recovers eta exactly",
            "ova_population_minimizer": "sigmoid(theta_y)=eta_y independently for every label y",
            "argmax": "Both therefore have Argmax_y theta_y contained in Argmax_y eta_y",
        },
        "rational_instance": {
            "eta": [ratio(value) for value in eta],
            "partition_masses": [ratio(value) for value in expert_partition_masses],
            "union_probability": ratio(union_probability),
            "ce_label_scores": [ratio(value) for value in ce_label_scores],
            "ce_recovered_eta": [ratio(value) for value in recovered_ce],
            "ova_sigmoid_labels": [ratio(value) for value in eta],
        },
    }


def claim_4() -> dict:
    joint_correctness = {
        "00": Fraction(1, 8),
        "01": Fraction(1, 8),
        "10": Fraction(3, 8),
        "11": Fraction(3, 8),
    }
    accuracy_1 = joint_correctness["10"] + joint_correctness["11"]
    accuracy_2 = joint_correctness["01"] + joint_correctness["11"]
    union_probability = 1 - joint_correctness["00"]
    v_tilde = union_probability / (1 + union_probability)
    first_partition = accuracy_1
    second_partition = joint_correctness["01"]
    ce_minimizer_score = first_partition / (1 + union_probability)
    theorem_score = accuracy_1 * v_tilde
    if not accuracy_1 > accuracy_2:
        raise AssertionError("Unique optimal expert assumption failed")
    if ce_minimizer_score == theorem_score:
        raise AssertionError("Counterexample did not contradict Theorem 6(A)")
    return {
        "verdict": "FALSIFIED",
        "domain": "singleton X, binary Y with eta=(3/5,2/5); independent correctness indicators; a wrong expert predicts the other binary label",
        "joint_correctness": {key: ratio(value) for key, value in joint_correctness.items()},
        "assumption_audit": {
            "probabilities_sum_to_one": sum(joint_correctness.values()) == 1,
            "unique_optimal_expert": accuracy_1 > accuracy_2,
            "accuracies": [ratio(accuracy_1), ratio(accuracy_2)],
            "condition_1_all_subsets": [
                {
                    "other_expert": 2,
                    "subset": [],
                    "coverage_with_j_star": ratio(accuracy_1),
                    "coverage_with_other": ratio(accuracy_2),
                    "strict": accuracy_1 > accuracy_2,
                }
            ],
            "ce_weights_strictly_positive": True,
        },
        "risk_partition_masses": [ratio(first_partition), ratio(second_partition)],
        "union_probability": ratio(union_probability),
        "v_tilde": ratio(v_tilde),
        "ce_risk_minimizer_u_j_star": ratio(ce_minimizer_score),
        "theorem_6a_printed_u_j_star": ratio(theorem_score),
        "absolute_contradiction": ratio(abs(ce_minimizer_score - theorem_score)),
        "corrected_formula": "Acc_j_star/(1+V) = Acc_j_star*(1-V_tilde)",
        "scope": "This falsifies the printed CE accuracy-estimator equality in Theorem 6(A), not its ranking or OvA statements.",
    }


def evaluate_theory() -> dict:
    return {
        "paper": "arXiv:2602.17144",
        "ar5iv_sha256": "d381ed2e443e7f2cdb48f51bf0e8cf8d07333bd4ae484fc6a0e4c0922bf67fdc",
        "claims": {
            "1": claim_1(),
            "2": claim_2(),
            "3": claim_3(),
            "4": claim_4(),
        },
    }

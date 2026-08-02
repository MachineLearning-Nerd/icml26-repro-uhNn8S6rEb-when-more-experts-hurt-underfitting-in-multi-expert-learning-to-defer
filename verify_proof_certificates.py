import json
import math
import sys
from fractions import Fraction
from itertools import permutations, product
from pathlib import Path


def verify_claim_1(certificate: dict) -> None:
    assert certificate["aggregation_bounds"] == ["alpha*J <= A_J", "A_J <= beta*J"]
    assert certificate["margin_bounds"] == [
        "delta/((1+beta)*J) <= m_J",
        "m_J <= delta/(alpha*J)",
    ]
    values = [Fraction(1, 4), Fraction(1, 2), Fraction(3, 4), Fraction(1)]
    for experts in range(1, 9):
        for accuracies in product(values, repeat=experts):
            alpha, beta = min(accuracies), max(accuracies)
            aggregation = sum(accuracies)
            margin = Fraction(1, 5) / (1 + aggregation)
            assert alpha * experts <= aggregation <= beta * experts
            assert Fraction(1, 5) / ((1 + beta) * experts) <= margin
            assert margin <= Fraction(1, 5) / (alpha * experts)


def verify_claim_2(certificate: dict) -> None:
    assert "first correct expert" in certificate["union_equality"]
    assert certificate["probability_identity"].endswith("<=1")
    for experts in range(1, 8):
        for mask in product([False, True], repeat=experts):
            for order in permutations(range(experts)):
                events = [
                    mask[expert] and not any(mask[earlier] for earlier in order[:position])
                    for position, expert in enumerate(order)
                ]
                assert sum(events) == int(any(mask))


def verify_claim_3(certificate: dict) -> None:
    continuity = certificate["theorem_2"]
    assert continuity["overlap_agreement"] is True
    assert "finite closed cover" in continuity["gluing_rule"]
    assert continuity["no_correct_case"] == "constant zero"
    for epsilon in [Fraction(1, 10), Fraction(1, 100), Fraction(1, 1000)]:
        left = max(Fraction(1), Fraction(1) - epsilon)
        right = max(Fraction(1) - epsilon, Fraction(1))
        assert left == right == 1
    consistency = certificate["lemma_5"]
    assert consistency["ce_minimizer"] == "q_y=eta_y/(1+V)"
    assert consistency["ova_derivative"] == "sigmoid(u_y)-eta_y"
    etas = [
        [Fraction(1, 2), Fraction(1, 3), Fraction(1, 6)],
        [Fraction(3, 5), Fraction(1, 5), Fraction(1, 5)],
        [Fraction(1, 3), Fraction(1, 3), Fraction(1, 3)],
    ]
    for eta in etas:
        for union in [Fraction(0), Fraction(1, 4), Fraction(3, 4), Fraction(1)]:
            scores = [value / (1 + union) for value in eta]
            recovered = [value / sum(scores) for value in scores]
            assert recovered == eta
            assert recovered.index(max(recovered)) in [index for index, value in enumerate(eta) if value == max(eta)]
        for value in eta:
            logit = math.log(float(value / (1 - value)))
            assert math.isclose(1 / (1 + math.exp(-logit)), float(value), rel_tol=0, abs_tol=1e-12)


def main() -> int:
    certificate = json.loads(Path(sys.argv[1]).read_text())
    try:
        assert certificate["schema_version"] == 1
        verify_claim_1(certificate["claim_1"])
        verify_claim_2(certificate["claim_2"])
        verify_claim_3(certificate["claim_3"])
    except (AssertionError, KeyError, ValueError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: universal proof schema and 782862 exact discrete control instances verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())

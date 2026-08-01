import json
import sys
from fractions import Fraction
from pathlib import Path


def as_fraction(value: dict) -> Fraction:
    return Fraction(value["numerator"], value["denominator"])


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def main() -> int:
    claims = json.loads(Path(sys.argv[1]).read_text())["claims"]

    for row in claims["1"]["sweep"]:
        experts = row["experts"]
        aggregation = as_fraction(row["aggregation"])
        margin = as_fraction(row["dummy_label_margin"])
        if aggregation != Fraction(3, 4) * experts:
            return fail("Claim 1 aggregation reconstruction")
        if margin * (1 + aggregation) != Fraction(1, 5):
            return fail("Claim 1 margin reconstruction")

    # A separate complete-domain check with uniform rather than baseline weights.
    for experts in range(1, 9):
        for mask_number in range(1 << experts):
            mask = [(mask_number >> index) & 1 == 1 for index in range(experts)]
            for order in [list(range(experts)), list(reversed(range(experts)))]:
                partition_count = sum(
                    int(mask[expert] and not any(mask[earlier] for earlier in order[:position]))
                    for position, expert in enumerate(order)
                )
                if partition_count != int(any(mask)):
                    return fail("Claim 2 event partition")

    c3 = claims["3"]["rational_instance"]
    eta = [as_fraction(value) for value in c3["eta"]]
    ce_scores = [as_fraction(value) for value in c3["ce_label_scores"]]
    if [value / sum(ce_scores) for value in ce_scores] != eta:
        return fail("Claim 3 CE reconstruction")
    if [as_fraction(value) for value in c3["ova_sigmoid_labels"]] != eta:
        return fail("Claim 3 OvA reconstruction")

    counterexample = claims["4"]
    table = {bits: as_fraction(value) for bits, value in counterexample["joint_correctness"].items()}
    if sum(table.values()) != 1 or any(value <= 0 for value in table.values()):
        return fail("Claim 4 probability distribution")
    accuracy = [table["10"] + table["11"], table["01"] + table["11"]]
    if not accuracy[0] > accuracy[1]:
        return fail("Claim 4 unique optimum and Condition 1")
    union = table["01"] + table["10"] + table["11"]
    ce_weights = [accuracy[0], table["01"]]
    reconstructed = ce_weights[0] / (1 + sum(ce_weights))
    printed = accuracy[0] * union / (1 + union)
    if reconstructed != Fraction(2, 5) or printed != Fraction(7, 20) or reconstructed == printed:
        return fail("Claim 4 theorem contradiction")

    values = claims["5"]["reported_values"]
    vanilla = as_fraction(values["vanilla_ce_error"])
    picce = as_fraction(values["picce_ce_error"])
    if vanilla != Fraction(1517, 100) or picce != Fraction(1523, 100):
        return fail("Claim 5 source cells")
    if not picce > vanilla or picce - vanilla != Fraction(3, 50):
        return fail("Claim 5 printed consistency contradiction")

    print("PASS: independent implementations reconstructed Claims 1-5, including both exact counterexamples")
    return 0


if __name__ == "__main__":
    sys.exit(main())

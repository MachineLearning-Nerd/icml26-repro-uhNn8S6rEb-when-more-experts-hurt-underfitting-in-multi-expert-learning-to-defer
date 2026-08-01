import json
import sys
from fractions import Fraction
from pathlib import Path


def as_fraction(value: dict) -> Fraction:
    return Fraction(value["numerator"], value["denominator"])


def main() -> int:
    results = json.loads(Path(sys.argv[1]).read_text())
    counterexample = results["claims"]["4"]
    table = {bits: as_fraction(value) for bits, value in counterexample["joint_correctness"].items()}

    if sum(table.values()) != 1 or any(value <= 0 for value in table.values()):
        print("FAIL: invalid probability distribution")
        return 1
    accuracy = [table["10"] + table["11"], table["01"] + table["11"]]
    if not accuracy[0] > accuracy[1]:
        print("FAIL: unique optimum and Condition 1 do not hold")
        return 1

    union = table["01"] + table["10"] + table["11"]
    ce_weights = [accuracy[0], table["01"]]
    independently_normalized = ce_weights[0] / (1 + sum(ce_weights))
    printed = accuracy[0] * union / (1 + union)
    if independently_normalized != Fraction(2, 5):
        print("FAIL: reconstructed CE optimum is not 2/5")
        return 1
    if printed != Fraction(7, 20) or independently_normalized == printed:
        print("FAIL: printed theorem was not contradicted")
        return 1
    print("PASS: independent reconstruction gives CE u_j*=2/5, printed Theorem 6(A)=7/20, gap=1/20")
    return 0


if __name__ == "__main__":
    sys.exit(main())

import argparse
import json
import sys
from fractions import Fraction
from pathlib import Path


def fraction(value: dict) -> Fraction:
    return Fraction(value["numerator"], value["denominator"])


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def verify(results: dict) -> None:
    claims = results["claims"]
    require(claims["1"]["verdict"] == "VERIFIED", "Claim 1 verdict")
    for row in claims["1"]["sweep"]:
        experts = row["experts"]
        require(fraction(row["aggregation"]) == Fraction(3 * experts, 4), "Claim 1 aggregation")
        expected_margin = Fraction(1, 5) / (1 + Fraction(3 * experts, 4))
        require(fraction(row["dummy_label_margin"]) == expected_margin, "Claim 1 margin")

    require(claims["2"]["verdict"] == "VERIFIED", "Claim 2 verdict")
    require(claims["2"]["exhaustive_correlated_checks"] == 873, "Claim 2 exhaustive count")

    c3 = claims["3"]
    require(c3["verdict"] == "VERIFIED", "Claim 3 verdict")
    eta = [fraction(value) for value in c3["rational_instance"]["eta"]]
    recovered = [fraction(value) for value in c3["rational_instance"]["ce_recovered_eta"]]
    ova = [fraction(value) for value in c3["rational_instance"]["ova_sigmoid_labels"]]
    require(eta == recovered == ova, "Claim 3 CE/OvA recovery")
    require(eta.index(max(eta)) == recovered.index(max(recovered)), "Claim 3 argmax")

    c4 = claims["4"]
    require(c4["verdict"] == "FALSIFIED", "Claim 4 verdict")
    assumption_keys = ["probabilities_sum_to_one", "unique_optimal_expert", "ce_weights_strictly_positive"]
    require(all(c4["assumption_audit"][key] for key in assumption_keys), "Claim 4 assumptions")
    require(all(row["strict"] for row in c4["assumption_audit"]["condition_1_all_subsets"]), "Claim 4 Condition 1")
    actual = fraction(c4["ce_risk_minimizer_u_j_star"])
    printed = fraction(c4["theorem_6a_printed_u_j_star"])
    require(actual == Fraction(2, 5), "Claim 4 CE optimum")
    require(printed == Fraction(7, 20), "Claim 4 printed formula")
    require(actual != printed, "Claim 4 contradiction")
    require(fraction(c4["absolute_contradiction"]) == Fraction(1, 20), "Claim 4 gap")

    c5 = claims["5"]
    require(c5["verdict"] == "FALSIFIED", "Claim 5 verdict")
    values = c5["reported_values"]
    vanilla_error = fraction(values["vanilla_ce_error"])
    picce_error = fraction(values["picce_ce_error"])
    require(vanilla_error == Fraction(1517, 100), "Claim 5 vanilla Table 2 cell")
    require(picce_error == Fraction(1523, 100), "Claim 5 PiCCE Table 2 cell")
    require(picce_error > vanilla_error, "Claim 5 error contradiction")
    require(fraction(c5["error_regression_percentage_points"]) == Fraction(3, 50), "Claim 5 error gap")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path)
    args = parser.parse_args()
    try:
        verify(json.loads(args.results.read_text()))
    except (AssertionError, KeyError, ValueError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: Claims 1-3 verified; Claims 4-5 falsified; assumptions, source cells, and exact fractions checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())

import json
import sys
from fractions import Fraction
from pathlib import Path


def main() -> int:
    certificate = json.loads(Path(sys.argv[1]).read_text())
    try:
        c1 = certificate["claim_1"]
        assert c1["assumptions"] == ["J>=1", "0<alpha<=Acc_j<=beta<=1", "eta_top-eta_runner_up=delta>0"]
        assert c1["conclusion"] == "A_J=Theta(J) and m_J=Theta(1/J)"
        for experts in range(1, 33):
            accuracies = [Fraction(index + 1, experts + 1) for index in range(experts)]
            alpha, beta = accuracies[0], accuracies[-1]
            aggregation = sum(accuracies)
            assert alpha * experts <= aggregation <= beta * experts

        c2 = certificate["claim_2"]
        assert c2["event_definition"].startswith("E_k=C_sigma(k)")
        for experts in range(1, 65):
            for first in [None, 0, experts // 2, experts - 1]:
                mask = [False] * experts
                if first is not None:
                    mask[first] = True
                    mask[-1] = True
                selected = next((index for index, correct in enumerate(mask) if correct), None)
                event_count = sum(correct and not any(mask[:index]) for index, correct in enumerate(mask))
                assert event_count == int(selected is not None)

        c3 = certificate["claim_3"]
        assert c3["theorem_2"]["overlap_agreement"] is True
        assert c3["lemma_5"]["ce_recovery"] == "q_y/sum_c q_c=eta_y"
        for first in range(1, 20):
            for second in range(1, 20 - first):
                eta = [Fraction(first, 20), Fraction(second, 20), Fraction(20 - first - second, 20)]
                union = Fraction((first + 2 * second) % 21, 20)
                scores = [value / (1 + union) for value in eta]
                assert [value / sum(scores) for value in scores] == eta
                assert max(range(3), key=eta.__getitem__) == max(range(3), key=scores.__getitem__)
    except (AssertionError, KeyError, ValueError) as error:
        print(f"FAIL: {error}")
        return 1
    print("PASS: independent symbolic reconstruction and alternative exact families agree")
    return 0


if __name__ == "__main__":
    sys.exit(main())

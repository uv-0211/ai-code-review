from evals.runner import run_eval
from evals.scorer import score_all, CaseScore

def print_report(scores: list[CaseScore]) -> None:
    total_expected = total_found = 0
    for score in scores:
        total_expected += score.expected_count
        total_found += score.found_count
        
    recall = total_found / total_expected if total_expected else 0.0

    print(f"Recall: {total_found}/{total_expected} ({recall:.0%})")
    print()

    for score in scores:
        if score.expected_count:
            status = "✓" if score.found_count == score.expected_count else "✗"
            print(f"{status} {score.case_name}: found {score.found_count}/{score.expected_count}")

    print()
    print("Noise on clean diffs:")
    totals = {"critical": 0, "warning": 0, "suggestion": 0}

    for score in scores:
        if not score.expected_count:
            for severity, count in score.noise_by_severity.items():
                totals[severity] += count

    for severity, count in totals.items():
        print(f"  {severity}: {count}")


if __name__ == "__main__":
    results = run_eval()
    scores = score_all(results)
    print_report(scores)
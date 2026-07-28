from dataclasses import dataclass
from app.config import ReviewConfig
from app.reviewer.ai_reviewer import AIReviewer
from app.models.review import ReviewIssue
from evals.dataset import GOLDEN_DATASET, EvalCase

@dataclass
class EvalResult:
    case: EvalCase
    actual_issues: list[ReviewIssue]


def run_eval() -> list[EvalResult]:
    reviewer = AIReviewer()
    config = ReviewConfig(max_issues=10, max_iterations=1)

    results = []
    for case in GOLDEN_DATASET:
        actual_issues = reviewer.review_pr(case.diff, config)
        results.append(EvalResult(case=case, actual_issues=actual_issues))

    return results


if __name__ == "__main__":
    results = run_eval()
    for result in results:
        print(f"{result.case.name}: found {len(result.actual_issues)} issue(s)")
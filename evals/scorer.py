from dataclasses import dataclass, field
from app.models.review import ReviewIssue
from evals.dataset import ExpectedIssue
from evals.runner import EvalResult

@dataclass
class CaseScore:
    case_name: str
    expected_count: int
    found_count: int
    noise_by_severity: dict[str, int] = field(
        default_factory=lambda: {"critical": 0, "warning": 0, "suggestion": 0}
    )


def do_issues_match(expected: ExpectedIssue, actual: ReviewIssue) -> bool:
    if actual.file != expected.file:
        return False
    if not (expected.line_range[0] <= actual.line <= expected.line_range[1]):
        return False
    
    text = f"{actual.title} {actual.explanation}".lower()
    return any(keyword.lower() in text for keyword in expected.keywords)


def score_case(result: EvalResult) -> CaseScore:
    found_count = sum(
        1
        for expected in result.case.expected_issues
        if any(do_issues_match(expected, actual) for actual in result.actual_issues)
    )

    score = CaseScore(
        case_name=result.case.name,
        expected_count=len(result.case.expected_issues),
        found_count=found_count
    )

    if not result.case.expected_issues:
        for actual in result.actual_issues:
            score.noise_by_severity[actual.severity] += 1

    return score


def score_all(results: list[EvalResult]) -> list[CaseScore]:
    return [score_case(result) for result in results]
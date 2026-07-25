import os
import sys
import anthropic
from github import GithubException
from pydantic import ValidationError
from app.error_mapping import classify_error
from app.models.review import ReviewRequest
from app.services.review_service import build_review_service

CYAN = "\033[36m"
GREEN = "\033[32m"
RESET = "\033[0m"


def main() -> None:
    pr_url = os.environ.get("PR_URL")
    if not pr_url:
        sys.exit("PR_URL environment variable is required")

    overrides = {
        "max_issues": os.environ.get("MAX_ISSUES"),
        "max_iterations": os.environ.get("MAX_ITERATIONS"),
    }
    overrides = {
        key: value 
        for key, value in overrides.items() 
        if value is not None
    }

    try:
        request = ReviewRequest(pr_url=pr_url, should_post_to_pr=True, **overrides)
    except ValidationError as e:
        sys.exit(f"Invalid configuration: {e}")

    service = build_review_service()

    print(f"{CYAN}Running review for {pr_url}...{RESET}")
    try:
        response = service.review(request)
    except (ValidationError, ValueError, anthropic.APIError, GithubException) as exc:
        _, message = classify_error(exc)
        sys.exit(message)

    print(f"{GREEN}Review complete — results below:{RESET}")
    print(f"Found {len(response.issues)} issue(s).")
    for issue in response.issues:
        print(f"- [{issue.severity}] {issue.file}:{issue.line} — {issue.title}")


if __name__ == "__main__":
    main()

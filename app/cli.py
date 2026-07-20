import os
import sys
from pydantic import ValidationError
from app.models.review import ReviewRequest
from app.services.review_service import build_review_service


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
    response = service.review(request)

    print(f"Found {len(response.issues)} issue(s).")
    for issue in response.issues:
        print(f"- [{issue.severity}] {issue.file}:{issue.line} — {issue.title}")


if __name__ == "__main__":
    main()

import os
import sys
from app.models.review import ReviewRequest
from app.services.review_service import build_review_service


def main() -> None:
    pr_url = os.environ.get("PR_URL")
    if not pr_url:
        sys.exit("PR_URL environment variable is required")

    service = build_review_service()
    request = ReviewRequest(pr_url=pr_url, should_post_to_pr=True)
    response = service.review(request)

    print(f"Found {len(response.issues)} issue(s).")
    for issue in response.issues:
        print(f"- [{issue.severity}] {issue.file}:{issue.line} — {issue.title}")


if __name__ == "__main__":
    main()

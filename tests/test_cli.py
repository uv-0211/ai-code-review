import pytest
from app.cli import main
from app.models.review import ReviewResponse

PR_URL = "https://github.com/owner/repo/pull/1"


class FakeReviewService:
    def __init__(self, response):
        self.response = response
        self.received_request = None

    def review(self, request):
        self.received_request = request
        return self.response


def test_main_exits_when_pr_url_missing(monkeypatch):
    monkeypatch.delenv("PR_URL", raising=False)

    with pytest.raises(SystemExit) as error:
        main()

    assert "PR_URL environment variable is required" in str(error.value)


def test_main_uses_default_limits_when_not_set(monkeypatch):
    monkeypatch.setenv("PR_URL", PR_URL)
    monkeypatch.delenv("MAX_ISSUES", raising=False)
    monkeypatch.delenv("MAX_ITERATIONS", raising=False)
    fake_service = FakeReviewService(ReviewResponse(issues=[]))
    monkeypatch.setattr("app.cli.build_review_service", lambda: fake_service)

    main()

    assert fake_service.received_request.max_issues == 10
    assert fake_service.received_request.max_iterations == 1


def test_main_applies_configured_limits(monkeypatch):
    monkeypatch.setenv("PR_URL", PR_URL)
    monkeypatch.setenv("MAX_ISSUES", "5")
    monkeypatch.setenv("MAX_ITERATIONS", "2")
    fake_service = FakeReviewService(ReviewResponse(issues=[]))
    monkeypatch.setattr("app.cli.build_review_service", lambda: fake_service)

    main()

    assert fake_service.received_request.max_issues == 5
    assert fake_service.received_request.max_iterations == 2


def test_main_exits_on_invalid_max_issues(monkeypatch):
    monkeypatch.setenv("PR_URL", PR_URL)
    monkeypatch.setenv("MAX_ISSUES", "banana")

    with pytest.raises(SystemExit) as error:
        main()

    assert "Invalid configuration" in str(error.value)


def test_main_posts_to_pr_and_prints_issues(monkeypatch, capsys, make_review_issue):
    monkeypatch.setenv("PR_URL", PR_URL)
    monkeypatch.delenv("MAX_ISSUES", raising=False)
    monkeypatch.delenv("MAX_ITERATIONS", raising=False)
    issue = make_review_issue()
    fake_service = FakeReviewService(ReviewResponse(issues=[issue]))
    monkeypatch.setattr("app.cli.build_review_service", lambda: fake_service)

    main()

    assert fake_service.received_request.should_post_to_pr is True

    captured = capsys.readouterr()
    assert "Found 1 issue(s)." in captured.out
    assert issue.title in captured.out

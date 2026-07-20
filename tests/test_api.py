import time
from concurrent.futures import ThreadPoolExecutor
import anthropic
import httpx
import pytest
from fastapi.testclient import TestClient
from github import GithubException
from pydantic import ValidationError
from app.api import app
from app.models.review import ReviewIssue, ReviewResponse

PR_URL = "https://github.com/owner/repo/pull/1"
SLEEP_SECONDS = 0.3


def make_validation_error():
    try:
        ReviewIssue()
    except ValidationError as error:
        return error


def make_anthropic_api_error():
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return anthropic.APIError("boom", request, body=None)


class FakeReviewService:
    def __init__(self):
        self.calls = 0

    def review(self, request):
        self.calls += 1
        return ReviewResponse(issues=[])


def test_review_service_is_built_once_and_reused_across_requests(monkeypatch):
    fake_service = FakeReviewService()
    build_calls = []

    def fake_build():
        build_calls.append(1)
        return fake_service

    monkeypatch.setattr("app.api.build_review_service", fake_build)

    with TestClient(app) as client:
        client.post("/review", json={"pr_url": PR_URL})
        client.post("/review", json={"pr_url": PR_URL})

    assert len(build_calls) == 1
    assert fake_service.calls == 2


class SlowFakeReviewService:
    def review(self, request):
        time.sleep(SLEEP_SECONDS)
        return ReviewResponse(issues=[])


def test_review_endpoint_does_not_block_other_requests(monkeypatch):
    monkeypatch.setattr("app.api.build_review_service", lambda: SlowFakeReviewService())

    with TestClient(app) as client:
        start = time.monotonic()
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(client.post, "/review", json={"pr_url": PR_URL})
                for _ in range(2)
            ]
            for future in futures:
                assert future.result().status_code == 200
        elapsed = time.monotonic() - start

    assert elapsed < SLEEP_SECONDS * 1.5


class RaisingFakeReviewService:
    def __init__(self, exc: Exception):
        self._exc = exc

    def review(self, request):
        raise self._exc


@pytest.mark.parametrize(
    "exc, expected_status, expected_detail",
    [
        (ValueError("Repo or PR not found"), 400, "Repo or PR not found"),
        (make_validation_error(), 502, "Invalid AI response"),
        (make_anthropic_api_error(), 503, "Claude API unavailable"),
        (GithubException(500, {"message": "Internal Server Error"}, None), 502, "GitHub API error"),
        (RuntimeError("boom"), 500, "Server error"),
    ],
)
def test_review_endpoint_maps_service_errors_to_http_status(
    monkeypatch, exc, expected_status, expected_detail
):
    monkeypatch.setattr(
        "app.api.build_review_service", lambda: RaisingFakeReviewService(exc)
    )

    with TestClient(app) as client:
        response = client.post("/review", json={"pr_url": PR_URL})

    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_detail


def test_startup_fails_fast_when_review_service_cannot_be_built(monkeypatch):
    def fake_build():
        raise RuntimeError("GITHUB_TOKEN environment variable is not set")

    monkeypatch.setattr("app.api.build_review_service", fake_build)

    with pytest.raises(RuntimeError, match="GITHUB_TOKEN"):
        with TestClient(app):
            pass

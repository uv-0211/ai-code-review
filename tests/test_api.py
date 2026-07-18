import pytest
from fastapi.testclient import TestClient
from app.api import app
from app.models.review import ReviewResponse

PR_URL = "https://github.com/owner/repo/pull/1"


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


def test_startup_fails_fast_when_review_service_cannot_be_built(monkeypatch):
    def fake_build():
        raise RuntimeError("GITHUB_TOKEN environment variable is not set")

    monkeypatch.setattr("app.api.build_review_service", fake_build)

    with pytest.raises(RuntimeError, match="GITHUB_TOKEN"):
        with TestClient(app):
            pass

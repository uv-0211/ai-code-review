from unittest.mock import patch
import httpx
import anthropic
import pytest
from github import GithubException
from pydantic import ValidationError
from app.config import ReviewConfig
from app.models.github import PostResult
from app.models.review import ReviewIssue
from app.services.review_service import build_review_service

PR_URL = "https://github.com/owner/repo/pull/1"


def make_validation_error():
    try:
        ReviewIssue()
    except ValidationError as error:
        return error


def make_anthropic_api_error():
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return anthropic.APIError("boom", request, body=None)


def test_review_returns_response_when_not_posting(
    review_service,
    mock_github_client,
    mock_github_poster,
    mock_ai_reviewer,
    make_review_request,
    make_review_issue,
):
    mock_github_poster.is_reviewed.return_value = False
    mock_github_client.get_pr_diff.return_value = "some diff"
    issues = [make_review_issue()]
    mock_ai_reviewer.review_pr.return_value = issues
    request = make_review_request(should_post_to_pr=False)

    result = review_service.review(request)

    assert result.issues == issues
    assert result.diff_length == len("some diff")
    assert result.is_posted is False
    assert result.post_result is None
    mock_github_poster.post_review.assert_not_called()
    mock_github_client.get_pr_diff.assert_called_once_with(
        mock_github_client.get_pull_request.return_value
    )
    mock_ai_reviewer.review_pr.assert_called_once_with(
        "some diff",
        ReviewConfig(
            max_issues=request.max_issues,
            max_iterations=request.max_iterations,
        ),
    )


def test_review_posts_when_should_post_to_pr_true(
    review_service,
    mock_github_client,
    mock_github_poster,
    mock_ai_reviewer,
    make_review_request,
    make_review_issue,
):
    mock_github_poster.is_reviewed.return_value = False
    mock_github_client.get_pr_diff.return_value = "some diff"
    issues = [make_review_issue()]
    mock_ai_reviewer.review_pr.return_value = issues
    mock_github_poster.post_review.return_value = PostResult(num_comments=1)
    request = make_review_request(should_post_to_pr=True, max_iterations=2)

    result = review_service.review(request)

    mock_github_poster.post_review.assert_called_once_with(
        mock_github_client.get_pull_request.return_value, issues
    )
    assert result.is_posted is True
    assert result.post_result == PostResult(num_comments=1)


def test_review_returns_early_when_iteration_limit_reached(
    review_service,
    mock_github_client,
    mock_github_poster,
    mock_ai_reviewer,
    make_review_request,
):
    mock_github_poster.is_reviewed.return_value = True
    request = make_review_request(max_iterations=3)

    result = review_service.review(request)

    assert result.issues == []
    assert result.diff_length == 0
    assert result.is_posted is False
    assert result.post_result == PostResult(
        num_comments=0,
        reason="Iteration limit reached (max 3)",
    )
    mock_github_client.get_pr_diff.assert_not_called()
    mock_ai_reviewer.review_pr.assert_not_called()


def test_review_propagates_value_error_when_pr_not_found(
    review_service,
    mock_github_client,
    make_review_request,
):
    mock_github_client.get_pull_request.side_effect = ValueError(
        "Repo or PR not found"
    )
    request = make_review_request()

    with pytest.raises(ValueError, match="Repo or PR not found"):
        review_service.review(request)


def test_review_propagates_value_error_when_pr_is_empty(
    review_service,
    mock_github_client,
    mock_github_poster,
    make_review_request,
):
    mock_github_poster.is_reviewed.return_value = False
    mock_github_client.get_pr_diff.side_effect = ValueError("PR is empty")
    request = make_review_request()

    with pytest.raises(ValueError, match="PR is empty"):
        review_service.review(request)


def test_review_propagates_validation_error_on_invalid_ai_response(
    review_service,
    mock_github_client,
    mock_github_poster,
    mock_ai_reviewer,
    make_review_request,
):
    mock_github_poster.is_reviewed.return_value = False
    mock_github_client.get_pr_diff.return_value = "some diff"
    mock_ai_reviewer.review_pr.side_effect = make_validation_error()
    request = make_review_request()

    with pytest.raises(ValidationError):
        review_service.review(request)


def test_review_propagates_anthropic_api_error(
    review_service,
    mock_github_client,
    mock_github_poster,
    mock_ai_reviewer,
    make_review_request,
):
    mock_github_poster.is_reviewed.return_value = False
    mock_github_client.get_pr_diff.return_value = "some diff"
    mock_ai_reviewer.review_pr.side_effect = make_anthropic_api_error()
    request = make_review_request()

    with pytest.raises(anthropic.APIError):
        review_service.review(request)


def test_review_propagates_github_exception(
    review_service,
    mock_github_client,
    make_review_request,
):
    mock_github_client.get_pull_request.side_effect = GithubException(
        500, {"message": "Internal Server Error"}, None
    )
    request = make_review_request()

    with pytest.raises(GithubException):
        review_service.review(request)


def test_build_review_service_wires_dependencies():
    with (
        patch("app.services.review_service.GithubClient") as mock_client_cls,
        patch("app.services.review_service.GithubPoster") as mock_poster_cls,
        patch("app.services.review_service.AIReviewer") as mock_reviewer_cls,
    ):
        mock_client = mock_client_cls.return_value
        mock_poster = mock_poster_cls.return_value
        mock_reviewer = mock_reviewer_cls.return_value

        service = build_review_service()

        mock_poster_cls.assert_called_once_with()
        assert service.github_client is mock_client
        assert service.github_poster is mock_poster
        assert service.ai_reviewer is mock_reviewer

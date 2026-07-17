from unittest.mock import MagicMock
import pytest
from github import GithubException
from app.models.github import PostResult

def make_comments(*bodies) -> list:
    comments = []

    for body in bodies:
        comment = MagicMock()
        comment.body = body
        comments.append(comment)

    return comments


def test_is_reviewed_returns_false_when_no_reviews(github_poster, mock_pull):
    mock_pull.get_issue_comments.return_value = []

    assert github_poster.is_reviewed(mock_pull, 1) is False


def test_is_reviewed_returns_true_when_iteration_reached(github_poster, mock_pull):
    mock_pull.get_issue_comments.return_value = make_comments(github_poster.BOT_MARKER)

    assert github_poster.is_reviewed(mock_pull, 1)


def test_is_reviewed_counts_only_bot_comments(github_poster, mock_pull):
    mock_pull.get_issue_comments.return_value = make_comments(
        "first comment",
        github_poster.BOT_MARKER,
        "second commeny",
        github_poster.BOT_MARKER,
    )

    assert github_poster.is_reviewed(mock_pull, 2)


def test_build_comment_without_issues(github_poster):
    comment = github_poster._build_comment([])

    assert github_poster.BOT_MARKER in comment
    assert "No issues found" in comment


def test_build_comment_with_issues(
    github_poster,
    sample_review_issues,
):
    comment = github_poster._build_comment(sample_review_issues)

    assert "SQL Injection vulnerability" in comment
    assert "Password stored in plaintext" in comment
    assert github_poster.SEVERITY_EMOJI["critical"] in comment


@pytest.mark.parametrize("severity", ["critical", "warning", "suggestion"])
def test_build_comment_uses_emoji_for_each_severity(
    github_poster,
    make_review_issue,
    severity,
):
    issue = make_review_issue(severity=severity)

    comment = github_poster._build_comment([issue])

    assert github_poster.SEVERITY_EMOJI[severity] in comment


def test_post_review_posts_comment(
    github_poster,
    sample_review_issues,
    mock_pull,
):
    result = github_poster.post_review(mock_pull, sample_review_issues)

    assert result == PostResult(num_comments=2)
    mock_pull.create_issue_comment.assert_called_once()


def test_post_review_propagates_comment_error(
    github_poster,
    mock_pull,
):
    mock_pull.create_issue_comment.side_effect = GithubException(
        403, {"message": "Forbidden"}, None
    )

    with pytest.raises(GithubException):
        github_poster.post_review(mock_pull, [])
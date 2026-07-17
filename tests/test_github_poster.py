from unittest.mock import MagicMock
import pytest

PR_URL = "https://github.com/owner/repo/pull/1"

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
    mock_github_client,
    github_poster,
    sample_review_issues,
    mock_pull,
):
    mock_pull.get_issue_comments.return_value = []
    mock_github_client.get_pull_request.return_value = mock_pull

    result = github_poster.post_review(
        PR_URL,
        sample_review_issues,
    )

    assert result == {
        "num_comments": 2,
    }
    mock_pull.create_issue_comment.assert_called_once()


def test_post_review_requests_correct_pr(
    mock_github_client, 
    github_poster, 
    mock_pull
):
    mock_github_client.get_pull_request.return_value = mock_pull
    mock_pull.get_issue_comments.return_value = []

    github_poster.post_review(PR_URL, [])

    mock_github_client.get_pull_request.assert_called_once_with(PR_URL)


def test_post_review_propagates_github_error(
    github_poster,
    mock_github_client,
):
    mock_github_client.get_pull_request.side_effect = ValueError(
        "Repo or PR not found"
    )

    with pytest.raises(ValueError):
        github_poster.post_review(PR_URL, [])
import json
from unittest.mock import MagicMock
import pytest
from pydantic import ValidationError
from app.config import ReviewConfig
from app.models.review import ReviewIssue
from app.reviewer.ai_reviewer import AIReviewer

def mock_claude_response(client, text: str):
    mock_message = MagicMock()
    mock_message.content = [
        MagicMock(text=json.dumps({"issues": text}))
    ]

    client.messages.create.return_value = mock_message


def test_review_pr_returns_issues(
    mock_anthropic_client,
    sample_issues, 
    ai_reviewer, 
    sample_diff, 
    default_config
):
    mock_claude_response(mock_anthropic_client, sample_issues)

    issues = ai_reviewer.review_pr(sample_diff, default_config)

    assert len(issues) == 2
    assert issues[0].title == "SQL Injection vulnerability"
    assert issues[0].severity == 'critical'
    assert issues[0].line == 14
    assert isinstance(issues[0], ReviewIssue)


def test_review_pr_empty_string(ai_reviewer, default_config):
    issues = ai_reviewer.review_pr("", default_config)

    assert len(issues) == 0


@pytest.mark.parametrize("invalid_response", [
    [{ "severity": "critical"}],
    "[",
])
def test_review_pr_invalid_response(
    mock_anthropic_client,
    ai_reviewer, 
    sample_diff, 
    default_config,
    invalid_response
):
    mock_claude_response(
        mock_anthropic_client, 
        invalid_response
    )

    with pytest.raises(ValidationError):
        ai_reviewer.review_pr(sample_diff, default_config)


def test_review_pr_respects_max_issues(
    mock_anthropic_client, 
    ai_reviewer,
    sample_diff
):
    many_issues = [{
         "title": "SQL Injection vulnerability",
            "severity": "critical",
            "file": "src/auth.py",
            "line": 14,
            "explanation": "String interpolation in SQL query allows injection attacks.",
            "fix": "Use parameterized queries: db.execute('UPDATE users SET password=? WHERE id=?', (new_password, user_id))"
    } for i in range(5)]
    config = ReviewConfig(max_issues=3, max_iterations=1)
    mock_claude_response(mock_anthropic_client, many_issues)

    issues = ai_reviewer.review_pr(sample_diff, config)

    assert len(issues) <=3


def test_build_prompt_contains_diff_and_limit():
    prompt = AIReviewer.build_prompt(
        "some diff",
        5,
    )

    assert "some diff" in prompt
    assert "5" in prompt


def test_review_pr_calls_claude_with_expected_params(
    ai_reviewer,
    mock_anthropic_client,
    sample_diff,
    default_config,
    sample_issues
):
    mock_claude_response(
        mock_anthropic_client,
        sample_issues,
    )

    ai_reviewer.review_pr(
        sample_diff,
        default_config,
    )

    mock_anthropic_client.messages.create.assert_called_once()

    call = (
        mock_anthropic_client
        .messages
        .create
        .call_args
    )

    assert call.kwargs["model"] == "claude-sonnet-4-6"
    assert call.kwargs["max_tokens"] == 4096

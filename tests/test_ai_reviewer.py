from unittest.mock import MagicMock
from app.config import ReviewConfig
from app.reviewer.ai_reviewer import AIReviewer

def mock_claude_response(client, text: str):
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=text)]

    client.messages.create.return_value = mock_message


def test_parse_review_returns_issues(sample_claude_response, default_config):
    issues = AIReviewer.parse_review(sample_claude_response, default_config)

    assert len(issues) == 2
    assert issues[0]["title"] == "SQL Injection vulnerability"
    assert issues[0]["severity"] == 'critical'
    assert issues[0]["line"] == 14


def test_parse_review_empty_string(default_config):
    issues = AIReviewer.parse_review("", default_config)
    assert issues == []


def test_parse_review_missing_fields(default_config):
    raw_text = "SEVERITY: critical\nFILE: main.py\n---"

    issues = AIReviewer.parse_review(raw_text, default_config)

    assert issues == []


def test_parse_review_handles_extra_dashes(default_config):
    raw_text = """ISSUE: Test issue
SEVERITY: warning
FILE: main.py
LINE: 5
EXPLANATION: Some explanation with --- dashes inside
FIX: Some fix
---"""
    issues = AIReviewer.parse_review(raw_text, default_config)
    assert len(issues) == 1


def test_parse_review_respects_max_issues():
    many_issues = "\n---\n".join([
        f"ISSUE: Issue {i}\nSEVERITY: warning\nFILE: main.py\nLINE: {i}\nEXPLANATION: Desc\nFIX: Fix"
        for i in range(5)
    ])
    config = ReviewConfig(max_issues=3, max_iterations=1)

    issues = AIReviewer.parse_review(many_issues, config)

    assert len(issues) <=3


def test_parse_review_invalid_line_number(
    default_config,
):
    issue = """
ISSUE: Test
SEVERITY: warning
FILE: main.py
LINE: abc
EXPLANATION: Problem
FIX: Fix
"""

    result = AIReviewer.parse_review(
        issue,
        default_config,
    )

    assert result[0]["line"] == 0


def test_review_pr_handles_no_issues_response(
    ai_reviewer,
    mock_anthropic_client,
    sample_diff,
    default_config,
):
    mock_claude_response(mock_anthropic_client, "NO_ISSUES_FOUND")

    result = ai_reviewer.review_pr(
        sample_diff,
        default_config,
    )

    assert result == []


def test_review_pr_returns_issues(ai_reviewer, mock_anthropic_client, sample_diff, sample_claude_response, default_config):
    mock_claude_response(mock_anthropic_client, sample_claude_response)
   
    issues = ai_reviewer.review_pr(sample_diff, default_config)

    assert len(issues) == 2
    assert issues[0]["severity"] == "critical"


def test_build_prompt_contains_diff_and_limit():
    prompt = AIReviewer.build_prompt(
        "some diff",
        5,
    )

    assert "some diff" in prompt
    assert "5" in prompt
    assert "NO_ISSUES_FOUND" in prompt


def test_review_pr_calls_claude_with_expected_params(
    ai_reviewer,
    mock_anthropic_client,
    sample_diff,
    default_config,
):
    mock_claude_response(
        mock_anthropic_client,
        "NO_ISSUES_FOUND",
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






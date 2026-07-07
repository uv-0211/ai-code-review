from unittest.mock import MagicMock, patch
from ai_reviewer import review_pr, parse_review
from config import ReviewConfig

def test_parse_review_returns_issues(sample_claude_response, default_config):
    issues = parse_review(sample_claude_response, default_config)

    assert len(issues) == 2
    assert issues[0]["title"] == "SQL Injection vulnerability"
    assert issues[0]["severity"] == 'critical'
    assert issues[0]["line"] == 14


def test_parse_review_empty_string(default_config):
    issues = parse_review("", default_config)
    assert issues == []


def test_parse_review_no_issues_marker(default_config):
    issues = parse_review("NO_ISSUES_FOUND", default_config)
    assert all("title" in issue for issue in issues)


def test_parse_review_missing_fields(default_config):
    raw_text = "SEVERITY: critical\nFILE: main.py\n---"
    issues = parse_review(raw_text, default_config)
    assert issues == []


def test_parse_review_handles_extra_dashes(default_config):
    raw_text = """ISSUE: Test issue
SEVERITY: warning
FILE: main.py
LINE: 5
EXPLANATION: Some explanation with --- dashes inside
FIX: Some fix
---"""
    issues = parse_review(raw_text, default_config)
    assert len(issues) == 1


def test_review_pr_returns_issues(sample_diff, sample_claude_response, default_config):
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=sample_claude_response)]

    with patch("ai_reviewer.anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = mock_message
        issues = review_pr(sample_diff, default_config)

    assert len(issues) == 2
    assert issues[0]["severity"] == "critical"


def test_review_pr_no_issues(sample_diff, default_config):
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="NO_ISSUES_FOUND")]

    with patch("ai_reviewer.anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = mock_message
        issues = review_pr(sample_diff, default_config)

    assert issues == []


def test_review_pr_respects_max_issues(sample_diff):
    many_issues = "\n---\n".join([
        f"ISSUE: Issue {i}\nSEVERITY: warning\nFILE: main.py\nLINE: {i}\nEXPLANATION: Desc\nFIX: Fix"
        for i in range(5)
    ])

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=many_issues)]

    config = ReviewConfig(max_issues=3, max_iterations=1)

    with patch("ai_reviewer.anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = mock_message
        issues = review_pr(sample_diff, config)

    assert len(issues) <=3

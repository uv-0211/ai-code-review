from unittest.mock import MagicMock, patch
from ai_reviewer import review_pr, parse_review
from config import ReviewConfig

def test_parse_review_returns_issues(sample_claude_response):
    issues = parse_review(sample_claude_response)

    assert len(issues) == 2
    assert issues[0]["title"] == "SQL Injection vulnerability"
    assert issues[0]["severity"] == 'critical'
    assert issues[0]["line"] == 14


def test_parse_review_empty_string():
    issues = parse_review("")
    assert issues == []


def test_parse_review_no_issues_marker():
    issues = parse_review("NO_ISSUES_FOUND")
    assert all("title" in issue for issue in issues)


def test_parse_review_missing_fields():
    raw_text = "SEVERITY: critical\nFILE: main.py\n---"
    issues = parse_review(raw_text)
    assert issues == []


def test_parse_review_handles_extra_dashes():
    raw_text = """ISSUE: Test issue
SEVERITY: warning
FILE: main.py
LINE: 5
EXPLANATION: Some explanation with --- dashes inside
FIX: Some fix
---"""
    issues = parse_review(raw_text)
    assert len(issues) == 1



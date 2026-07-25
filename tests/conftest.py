from unittest.mock import MagicMock, patch
import pytest
from app.github.client import GithubClient
from app.github.poster import GithubPoster
from app.config import ReviewConfig
from app.reviewer.ai_reviewer import AIReviewer
from app.services.review_service import ReviewService
from app.models.review import ReviewIssue, ReviewRequest

@pytest.fixture
def default_config():
    return ReviewConfig(max_issues=10, max_iterations=1)

@pytest.fixture
def sample_diff():
    return """### src/auth.py

@@ -10,6 +10,15 @@ def login(username, password):
+def reset_password(user_id, new_password):
+    db.execute(
+        f"UPDATE users SET password='{new_password}' WHERE id={user_id}"
+    )
+    return True"""

@pytest.fixture
def sample_issues():
    return [
        {
            "title": "SQL Injection vulnerability",
            "severity": "critical",
            "file": "src/auth.py",
            "line": 14,
            "explanation": "String interpolation in SQL query allows injection attacks.",
            "fix": "Use parameterized queries: db.execute('UPDATE users SET password=? WHERE id=?', (new_password, user_id))"
        },
        {
            "title": "Password stored in plaintext",
            "severity": "critical",
            "file": "src/auth.py",
            "line": 10,
            "explanation": "Password is stored without hashing.",
            "fix": "Hash the password before storing: bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())"
        }
    ]

@pytest.fixture
def sample_review_issues(sample_issues):
    return [ReviewIssue(**issue) for issue in sample_issues]

@pytest.fixture
def make_review_issue():
    def _make(**overrides):
        defaults = dict(
            title="SQL Injection vulnerability",
            severity="critical",
            file="src/auth.py",
            line=14,
            explanation="String interpolation in SQL query allows injection attacks.",
            fix="Use parameterized queries.",
        )
        defaults.update(overrides)
        return ReviewIssue(**defaults)
    return _make


@pytest.fixture
def mock_github():
    with patch("app.github.client.Github") as MockGithub:
        yield MockGithub

@pytest.fixture
def github_client(mock_github):
    return GithubClient()

@pytest.fixture
def mock_github_client():
    return MagicMock()

@pytest.fixture
def github_poster():
    return GithubPoster()

@pytest.fixture
def mock_pull():
    return MagicMock()

@pytest.fixture
def mock_anthropic_client():
    return MagicMock()

@pytest.fixture
def ai_reviewer(mock_anthropic_client):
    return AIReviewer(mock_anthropic_client)

@pytest.fixture
def mock_github_poster():
    return MagicMock()

@pytest.fixture
def mock_ai_reviewer():
    return MagicMock()

@pytest.fixture
def review_service(mock_github_client, mock_github_poster, mock_ai_reviewer):
    return ReviewService(
        github_client=mock_github_client,
        github_poster=mock_github_poster,
        ai_reviewer=mock_ai_reviewer,
    )

@pytest.fixture
def make_review_request():
    def _make(**overrides):
        defaults = {"pr_url": "https://github.com/owner/repo/pull/1"}
        defaults.update(overrides)
        return ReviewRequest(**defaults)
    return _make
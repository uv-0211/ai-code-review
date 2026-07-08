from unittest.mock import patch
import pytest
from app.github.client import GithubClient
from config import ReviewConfig

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
            "line": 14,
            "explanation": "Password is stored without hashing.",
            "fix": "Hash the password before storing: bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())"
        }
    ]

@pytest.fixture
def sample_claude_response():
    return """ISSUE: SQL Injection vulnerability
SEVERITY: critical
FILE: src/auth.py
LINE: 14
EXPLANATION: String interpolation in SQL query allows injection attacks.
FIX: Use parameterized queries.
---
ISSUE: Password stored in plaintext
SEVERITY: critical
FILE: src/auth.py
LINE: 14
EXPLANATION: Password is stored without hashing.
FIX: Hash the password before storing.
---"""

@pytest.fixture
def mock_client():
    with patch("ai_reviewer.anthropic.Anthropic") as MockClient:
        yield MockClient

@pytest.fixture
def mock_github():
    with patch("app.github.client.Github") as MockGithub:
        yield MockGithub

@pytest.fixture
def github_client(mock_github):
    return GithubClient()

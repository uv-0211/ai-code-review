import pytest
from unittest.mock import MagicMock, patch
from github import GithubException
from dataclasses import dataclass
from app.github.client import GithubClient

PR_URL = "https://github.com/owner/repo/pull/1"

@dataclass
class MockFile:
    filename: str
    patch: str | None

def setup_mock_pr(mock_github, files):
    mock_pull = MagicMock()
    mock_pull.get_files.return_value = files

    mock_github.return_value.get_repo.return_value.get_pull.return_value = mock_pull


def test_parse_pr_url_valid():
    owner, repo, pr_number = GithubClient.parse_pr_url("https://github.com/facebook/react/pull/42")

    assert (owner, repo, pr_number) == ("facebook", "react", 42)


@pytest.mark.parametrize("bad_url", [
    "not-a-url",
    "https://gitlab.com/owner/repo/merge_requests/1",
    "https://github.com/owner/repo/issues/1",
    "https://github.com/owner/repo/pull/",
    "",
])


def test_parse_pr_url_invalid(bad_url):
    with pytest.raises(ValueError):
        GithubClient.parse_pr_url(bad_url)


def test_get_pr_diff_normal(mock_github, github_client):
    mock_file = MockFile("src/auth.py", "@@ -1,3 +1,4 @@\n+new line")
    setup_mock_pr(mock_github, [mock_file])

    diff = github_client.get_pr_diff(PR_URL)

    assert "src/auth.py" in diff
    assert "@@ -1,3 +1,4 @@" in diff


def test_get_pr_diff_skips_binary_files(mock_github, github_client):
    binary_file = MockFile("assets/logo.png", None)
    text_file = MockFile("src/main.py", "@@ -1 +1 @@\n+code")
    setup_mock_pr(mock_github, [binary_file, text_file])

    diff = github_client.get_pr_diff(PR_URL)

    assert "logo.png" not in diff
    assert "src/main.py" in diff


def test_get_pr_diff_empty_pr(mock_github, github_client):
    setup_mock_pr(mock_github, [])

    with pytest.raises(ValueError, match="PR is empty"):
        github_client.get_pr_diff(PR_URL)


def test_get_pr_diff_repo_not_found(mock_github, github_client):
    mock_github.return_value.get_repo.side_effect = GithubException(
        404, {"message": "Not Found"}, None
    )
    with pytest.raises(ValueError, match="Repo or PR not found"):
        github_client.get_pr_diff(PR_URL)


def test_get_pr_diff_filters_generated_files(mock_github, github_client):
    lock_file = MockFile("package-lock.json", "@@ -1 +1 @@\n+something")
    real_file = MockFile("src/app.py", "@@ -1 +1 @@\n+code")
    setup_mock_pr(mock_github, [lock_file, real_file])

    diff = github_client.get_pr_diff(PR_URL)
    
    assert "package-lock.json" not in diff
    assert "src/app.py" in diff


def test_get_pr_diff_all_files_ignored(mock_github, github_client):
    setup_mock_pr(mock_github, [
        MockFile("assets/logo.png", None),
        MockFile("package-lock.json", "@@ -1 +1 @@\n+something"),
    ])

    with pytest.raises(ValueError, match="PR is empty"):
        github_client.get_pr_diff(PR_URL)
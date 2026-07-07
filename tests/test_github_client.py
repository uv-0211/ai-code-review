import pytest
from unittest.mock import MagicMock, patch
from github import GithubException
from dataclasses import dataclass
from github_client import parse_pr_url, get_pr_diff

PR_URL = "https://github.com/owner/repo/pull/1"

@dataclass
class MockFile:
    filename: str
    patch: str | None

def setup_mock_pr(MockGithub, files):
    mock_pull = MagicMock()
    mock_pull.get_files.return_value = files

    MockGithub.return_value.get_repo.return_value.get_pull.return_value = mock_pull

def test_parse_pr_url_valid():
    owner, repo, pr_number = parse_pr_url("https://github.com/facebook/react/pull/42")
    assert owner == "facebook"
    assert repo == "react"
    assert pr_number == 42


@pytest.mark.parametrize("bad_url", [
    "not-a-url",
    "https://gitlab.com/owner/repo/merge_requests/1",
    "https://github.com/owner/repo/issues/1",
    "https://github.com/owner/repo/pull/",
    "",
])

def test_parse_pr_url_invalid(bad_url):
    with pytest.raises(ValueError):
        parse_pr_url(bad_url)


def test_get_pr_diff_normal(mock_github):
    mock_file = MockFile("src/auth.py", "@@ -1,3 +1,4 @@\n+new line")
    setup_mock_pr(mock_github, [mock_file])

    diff = get_pr_diff(PR_URL)

    assert "src/auth.py" in diff
    assert "@@ -1,3 +1,4 @@" in diff


def test_get_pr_diff_skips_binary_files(mock_github):
    binary_file = MockFile("assets/logo.png", None)
    text_file = MockFile("src/main.py", "@@ -1 +1 @@\n+code")
    setup_mock_pr(mock_github, [binary_file, text_file])

    diff = get_pr_diff(PR_URL)

    assert "logo.png" not in diff
    assert "src/main.py" in diff


def test_get_pr_diff_empty_pr():
    with patch("github_client.Github") as MockGithub:
        mock_pull = MagicMock()
        mock_pull.get_files.return_value = []
        MockGithub.return_value.get_repo.return_value.get_pull.return_value = mock_pull

        with pytest.raises(ValueError, match="PR is empty"):
            get_pr_diff(PR_URL)


def test_get_pr_diff_repo_not_found():
    with patch("github_client.Github") as MockGithub:
        MockGithub.return_value.get_repo.side_effect = GithubException(
            404, {"message": "Not Found"}, None
        )
        with pytest.raises(ValueError, match="Repo or PR not found"):
            get_pr_diff(PR_URL)


def test_get_pr_diff_filters_generated_files(mock_github):
    lock_file = MockFile("package-lock.json", "@@ -1 +1 @@\n+something")
    real_file = MockFile("src/app.py", "@@ -1 +1 @@\n+code")
    setup_mock_pr(mock_github, [lock_file, real_file])

    diff = get_pr_diff(PR_URL)
    
    assert "package-lock.json" not in diff
    assert "src/app.py" in diff
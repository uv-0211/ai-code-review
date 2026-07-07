import os
import re
from dotenv import load_dotenv
from github import Github, GithubException

load_dotenv()

PR_URL_PATTERN = re.compile(
    r"^https://github\.com/[\w.-]+/[\w.-]+/pull/\d+$"
)
IGNORED_FILES = {
    "package-lock.json",
    "yarn.lock"
}

def get_github_client():
    return Github(os.getenv("GITHUB_TOKEN"))


def parse_pr_url(pr_url: str) -> tuple[str, str, int]:
    if not PR_URL_PATTERN.match(pr_url):
        raise ValueError(f"Invalid link to PR: '{pr_url}'. Expected format: https://github.com/owner/repo/pull/123")

    parts = pr_url.rstrip("/").split("/")
    owner = parts[-4]
    repo  = parts[-3]
    pr_number = int(parts[-1])

    return owner, repo, pr_number


def get_pull_request(pr_url: str) -> str:
    github = get_github_client()
    owner, repo, pr_number = parse_pr_url(pr_url)

    try: 
        repository = github.get_repo(f'{owner}/{repo}')
        pull = repository.get_pull(pr_number)

        return pull
    except GithubException as e:
        if e.status == 404:
            raise ValueError(f"Repo or PR not found: {owner}/{repo}/{pr_number}")
        raise ValueError(f"GitHub API error: {e.data.get('message', str(e))}")


def get_pr_diff(pr_url: str) -> str:
    pull = get_pull_request(pr_url)
    files = pull.get_files()
    diff_parts = []

    for file in files:
        if file.filename in IGNORED_FILES:
            continue

        if not file.patch:
            continue

        diff_parts.append(f'### {file.filename}')
        diff_parts.append(file.patch)

    if not diff_parts:
        raise ValueError("PR is empty")

    return '\n\n'.join(diff_parts)


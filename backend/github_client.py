import os
from dotenv import load_dotenv
from github import Github

load_dotenv()

def get_pr_diff(pr_url: str) -> str:
    token = os.getenv("GITHUB_TOKEN")
    github = Github(token)

    parts = pr_url.rstrip('/').split('/')

    owner = parts[-4]
    repo = parts[-3]
    pr_number = int(parts[-1])

    repository = github.get_repo(f'{owner}/{repo}')
    pull = repository.get_pull(pr_number)
    files = pull.get_files()

    diff_parts = []

    for file in files:
        diff_parts.append(f'### {file.filename}')
        if file.patch:
            diff_parts.append(file.patch)

    return '\n\n'.join(diff_parts)


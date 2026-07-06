import os
from dotenv import load_dotenv
from github import Github

load_dotenv()

BOT_MARKER = "<!-- ai-code-reviewer -->"

SEVERITY_EMOJI = {
    "critical": "🚨",
    "warning": "⚠️",
    "suggestion": "💡",
}

def _already_reviewed(pull, iteration: int) -> bool:
    count = 0

    for comment in pull.get_issue_comments():
        if BOT_MARKER in comment.body:
            count += 1
    return count >= iteration

def post_review(pr_url: str, issues: list[dict], iteration: int = 1) -> dict:
    token = os.getenv("GITHUB_TOKEN")
    g = Github(token)

    parts = pr_url.rstrip("/").split("/")
    owner, repo_name, pr_number = parts[-4], parts[-3], int(parts[-1])

    repository = g.get_repo(f"{owner}/{repo_name}")
    pull = repository.get_pull(pr_number)

    if _already_reviewed(pull, iteration):
        return { 
            "posted": False,
            "reason": f"Iteration limit reached (max {iteration})"
        }
    
    if not issues:
        body = f"{BOT_MARKER}\n✅ **AI Code Review** - No issues found during this iteration."
        pull.create_issue_comment(body)
        return {"posted": True, "num_comments": 0}

    lines = [f"{BOT_MARKER}", "## 🤖 AI Code Review\n"]

    for i, issue in enumerate(issues, 1):
        emoji = SEVERITY_EMOJI.get(issue.get("severity", "suggestion"), '💡')
        lines.append(f"### {emoji} [{i}] {issue.get('title', '?')}")
        lines.append(f"**File:** `{issue.get('file', '?')}`")
        lines.append(f"\n**Issue:** {issue.get('explanation', '?')}")
        lines.append(f"\n**Fix:** {issue.get('fix', '?')}\n")
        lines.append("---")

    pull.create_issue_comment("\n".join(lines))

    return {"posted": True, "num_comments": len(issues)}

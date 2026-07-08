from github.PullRequest import PullRequest
from app.github.client import GithubClient

class GithubPoster:
    BOT_MARKER = "<!-- ai-code-reviewer -->"
    SEVERITY_EMOJI = {
        "critical": "🚨",
        "warning": "⚠️",
        "suggestion": "💡",
    }

    def __init__(self, github: GithubClient):
        self.github = github


    def _is_reviewed(self, pull_request: PullRequest, iteration: int) -> bool:
        count = sum(
            1 for comment in pull_request.get_issue_comments()
            if self.BOT_MARKER in comment.body
        )
        return count >= iteration


    def _build_comment(self, issues: list[dict]) -> str:
        if not issues:
            return f"{self.BOT_MARKER}\n✅ **AI Code Review** - No issues found during this iteration."

        lines = [f"{self.BOT_MARKER}", "## 🤖 AI Code Review\n"]

        for i, issue in enumerate(issues, 1):
            emoji = self.SEVERITY_EMOJI.get(issue.get("severity", "suggestion"), '💡')
            lines.append(f"### {emoji} [{i}] {issue.get('title', '?')}")
            lines.append(f"**File:** `{issue.get('file', '?')}`")
            lines.append(f"\n**Issue:** {issue.get('explanation', '?')}")
            lines.append(f"\n**Fix:** {issue.get('fix', '?')}\n")
            lines.append("---")

        return "\n".join(lines)


    def post_review(self, pr_url: str, issues: list[dict], iteration: int = 1) -> dict:
        pull_request: PullRequest = self.github.get_pull_request(pr_url)

        if self._is_reviewed(pull_request, iteration):
            return { 
                "posted": False,
                "reason": f"Iteration limit reached (max {iteration})"
            }

        pull_request.create_issue_comment(self._build_comment(issues))
        return {"posted": True, "num_comments": len(issues)}
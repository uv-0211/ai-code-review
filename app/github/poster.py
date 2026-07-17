from github.PullRequest import PullRequest
from app.github.client import GithubClient
from app.models.review import ReviewIssue

class GithubPoster:
    BOT_MARKER = "<!-- ai-code-reviewer -->"
    SEVERITY_EMOJI = {
        "critical": "🚨",
        "warning": "⚠️",
        "suggestion": "💡",
    }

    def __init__(self, github: GithubClient):
        self.github = github


    def is_reviewed(self, pull_request: PullRequest, max_iterations: int) -> bool:
        count = sum(
            1 for comment in pull_request.get_issue_comments()
            if self.BOT_MARKER in comment.body
        )
        return count >= max_iterations


    def _build_comment(self, issues: list[ReviewIssue]) -> str:
        if not issues:
            return f"{self.BOT_MARKER}\n✅ **AI Code Review** - No issues found during this iteration."

        lines = [f"{self.BOT_MARKER}", "## 🤖 AI Code Review\n"]

        for i, issue in enumerate(issues, 1):
            emoji = self.SEVERITY_EMOJI[issue.severity]
            lines.append(f"### {emoji} [{i}] {issue.title}")
            lines.append(f"**File:** `{issue.file}`")
            lines.append(f"\n**Issue:** {issue.explanation}")
            lines.append(f"\n**Fix:** {issue.fix}\n")
            lines.append("---")

        return "\n".join(lines)


    def post_review(self, pr_url: str, issues: list[ReviewIssue]) -> dict:
        pull_request: PullRequest = self.github.get_pull_request(pr_url)
        pull_request.create_issue_comment(self._build_comment(issues))

        return {"num_comments": len(issues)}
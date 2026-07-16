import os
from dotenv import load_dotenv
import anthropic
from pydantic import ValidationError
from app.config import ReviewConfig
from app.models.review import ReviewIssue, AIReviewResponse

load_dotenv()

class AIReviewer:    
    def __init__(self, client: anthropic.Anthropic | None = None):
        self._client = client or anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )

    def review_pr(self, diff: str, config: ReviewConfig) -> list[ReviewIssue]:
        if not diff:
            return []

        message = self._client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": self.build_prompt(diff, config.max_issues)
                }
            ]
        )

        raw_text = message.content[0].text
        
        try:
            review = AIReviewResponse.model_validate_json(raw_text)
            review.issues = review.issues[:config.max_issues]
        except ValidationError as error:
            raise RuntimeError(f"Claude returned invalid JSON or some fields are missing") from error
        return review.issues


    @staticmethod
    def build_prompt(diff: str, max_issues: int) -> str:
        return f"""You are an expert code reviewer. Analyze the following pull request diff.

        Return no more than {max_issues} most important issues found.
        Prioritize by severity: critical bugs first, then warnings, then suggestions.

        Return ONLY valid JSON.
        Do not use markdown.
        Do not wrap the response in ```json blocks.

        Use this structure:

        {{
        "issues": [
            {{
            "title": "brief issue title",
            "severity": "critical | warning | suggestion",
            "file": "filename",
            "line": 0,
            "explanation": "what the problem is and why it matters",
            "fix": "how to fix it"
            }}
        ]
        }}

        If there are no issues, return:

        {{
        "issues": []
        }}

        Diff:

        {diff}
        """

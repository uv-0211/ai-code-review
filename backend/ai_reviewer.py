import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

PROMPT_TEMPLATE = """You are an expert code reviewer. Analyze the following pull request diff and provide a structured review.

For each issue found, respond in this exact format:

ISSUE: <brief title>
SEVERITY: <critical | warning | suggestion>
FILE: <filename>
EXPLANATION: <what the problem is and why it matters>
FIX: <concrete suggestion how to fix it>
---

Focus on:
- Bugs and logic errors (critical)
- Security vulnerabilities (critical)
- Performance problems (warning)
- Code style and readability (suggestion)

If the code looks good, write: NO_ISSUES_FOUND

Here is the diff:

{diff}
"""

def review_pr(diff: str) -> list[dict]:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": PROMPT_TEMPLATE.format(diff=diff)
            }
        ]
    )

    raw_text = message.content[0].text

    if "NO_ISSUES_FOUND" in raw_text:
        return []

    return parse_review(raw_text)


def parse_review(raw_text: str) -> list[dict]:
    issues = []
    blocks = raw_text.strip().split('---')

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        issue = {}
        for line in block.splitlines():
            if line.startswith('ISSUE:'):
                issue['title'] = line.replace('ISSUE:', ''.strip())
            elif line.startswith("SEVERITY:"):
                issue["severity"] = line.replace("SEVERITY:", "").strip()
            elif line.startswith("FILE:"):
                issue["file"] = line.replace("FILE:", "").strip()
            elif line.startswith("EXPLANATION:"):
                issue["explanation"] = line.replace("EXPLANATION:", "").strip()
            elif line.startswith("FIX:"):
                issue["fix"] = line.replace("FIX:", "").strip()

        if 'title' in issue:
            issues.append(issue)

    return issues


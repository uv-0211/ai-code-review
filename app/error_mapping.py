import anthropic
from github import GithubException
from pydantic import ValidationError


def classify_error(exc: Exception) -> tuple[int, str]:
    if isinstance(exc, ValidationError):
        return 502, "Invalid AI response"
    if isinstance(exc, ValueError):
        return 400, str(exc)
    if isinstance(exc, anthropic.APIError):
        return 503, "Claude API unavailable"
    if isinstance(exc, GithubException):
        status = exc.status if exc.status < 500 else 502
        return status, "GitHub API error"
    return 500, "Server error"

import httpx
import anthropic
from pydantic import ValidationError
from app.models.review import ReviewIssue


def make_validation_error() -> ValidationError:
    try:
        ReviewIssue()
    except ValidationError as error:
        return error
    raise AssertionError("ReviewIssue() did not raise ValidationError")


def make_anthropic_api_error() -> anthropic.APIError:
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return anthropic.APIError("boom", request, body=None)

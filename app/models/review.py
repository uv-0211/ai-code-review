from typing import Literal
from pydantic import BaseModel

class ReviewIssue(BaseModel):
    title: str
    severity: Literal["critical", "warning", "suggestion" ]
    file: str
    line: int
    explanation: str
    fix: str


class ReviewResponse(BaseModel):
    issues: list[ReviewIssue]

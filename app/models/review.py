from typing import Literal
from pydantic import BaseModel, Field
from app.models.github import PostResult

class ReviewIssue(BaseModel):
    title: str
    severity: Literal["critical", "warning", "suggestion" ]
    file: str
    line: int
    explanation: str
    fix: str


class AIReviewResponse(BaseModel):
    issues: list[ReviewIssue]


class ReviewResponse(BaseModel):
    issues: list[ReviewIssue]
    diff_length: int = 0
    is_posted: bool = False
    post_result: PostResult | None = None

class ReviewRequest(BaseModel):
    pr_url: str
    max_issues: int = Field(default=10, ge=1, le=50)
    max_iterations: int = Field(default=1, ge=1, le=3)
    should_post_to_pr: bool = False
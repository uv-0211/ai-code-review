from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from github_client import get_pr_diff
from ai_reviewer import review_pr
from github_poster import post_review
from config import ReviewConfig

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ReviewRequest(BaseModel):
    pr_url: str
    max_issues: int = Field(default=10, ge=1, le=50)
    max_iterations: int = Field(default=1, ge=1, le=3)
    should_post_to_pr: bool = False

class ReviewResponse(BaseModel):
    issues: list[dict]
    diff_length: int
    is_posted: bool = False
    post_result: dict = {}

@app.post("/review", response_model=ReviewResponse)
async def review(request: ReviewRequest):
    try:
        config = ReviewConfig(
            max_issues=request.max_issues,
            max_iterations=request.max_iterations,
        )

        diff = get_pr_diff(request.pr_url)
        issues = review_pr(diff, config)

        if request.should_post_to_pr:
            post_result = post_review(request.pr_url, issues, request.max_iterations)

        return ReviewResponse(
            issues=issues, 
            diff_length=len(diff),
            is_posted=request.should_post_to_pr,
            post_result=post_result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
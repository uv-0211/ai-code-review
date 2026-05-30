from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from github_client import get_pr_diff
from ai_reviewer import review_pr

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ReviewRequest(BaseModel):
    pr_url: str

class ReviewResponse(BaseModel):
    issues: list[dict]
    diff_length: int

@app.post("/review", response_model=ReviewResponse)
async def review(request: ReviewRequest):
    try:
        diff = get_pr_diff(request.pr_url)
        issues = review_pr(diff)
        return ReviewResponse(issues=issues, diff_length=len(diff))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
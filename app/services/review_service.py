import anthropic
from fastapi import HTTPException
from github import GithubException
from pydantic import ValidationError
from app.config import ReviewConfig
from app.models.github import PostResult
from app.models.review import ReviewRequest, ReviewResponse
from app.github.client import GithubClient
from app.github.poster import GithubPoster
from app.reviewer.ai_reviewer import AIReviewer


def build_review_service() -> "ReviewService":
    github_client = GithubClient()
    github_poster = GithubPoster()
    ai_reviewer = AIReviewer()

    return ReviewService(
        github_client=github_client,
        github_poster=github_poster,
        ai_reviewer=ai_reviewer,
    )


class ReviewService:
    def __init__(
        self,
        github_client: GithubClient,
        github_poster: GithubPoster,
        ai_reviewer: AIReviewer,
    ):
        self.github_client = github_client
        self.github_poster = github_poster
        self.ai_reviewer = ai_reviewer


    def review(self, request: ReviewRequest):
        try:
            pull_request = self.github_client.get_pull_request(request.pr_url)

            if self.github_poster.is_reviewed(pull_request, request.max_iterations):
                return ReviewResponse(
                    issues=[],
                    diff_length=0,
                    is_posted=False,
                    post_result=PostResult(
                        num_comments=0,
                        reason=f"Iteration limit reached (max {request.max_iterations})",
                    ),
                )

            diff = self.github_client.get_pr_diff(pull_request)
            config = ReviewConfig(
                max_issues=request.max_issues,
                max_iterations=request.max_iterations,
            )
            issues = self.ai_reviewer.review_pr(diff, config)

            post_result: PostResult | None = (
                self.github_poster.post_review(pull_request, issues)
                if request.should_post_to_pr
                else None
            )

            return ReviewResponse(
                issues=issues, 
                diff_length=len(diff),
                is_posted=request.should_post_to_pr,
                post_result=post_result
            )
            
        except ValidationError:
            raise HTTPException(
                502,
                detail="Invalid AI response",
            )
        except ValueError as e:
            raise HTTPException(
                400,
                detail=str(e)
            )
        except anthropic.APIError:
            raise HTTPException(
                503,
                detail="Claude API unavailable",
            )
        except GithubException:
            raise HTTPException(
                502,
                detail="GitHub API error",
            )
        except Exception as e:
            raise HTTPException(
                500, 
                detail=f"Server error"
            )

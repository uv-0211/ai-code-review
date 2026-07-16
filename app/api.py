from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models.review import ReviewRequest, ReviewResponse
from app.services.review_service import ReviewService, get_review_service

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/review", response_model=ReviewResponse)
async def review(
    request: ReviewRequest,
    service: ReviewService = Depends(get_review_service)
):
    return service.review(request)
    
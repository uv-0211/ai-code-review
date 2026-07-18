import os
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.models.review import ReviewRequest, ReviewResponse
from app.services.review_service import ReviewService, build_review_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.review_service = build_review_service()
    yield


app = FastAPI(lifespan=lifespan)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


def get_review_service(request: Request) -> ReviewService:
    return request.app.state.review_service


@app.post("/review", response_model=ReviewResponse)
async def review(
    request: ReviewRequest,
    service: ReviewService = Depends(get_review_service)
):
    return service.review(request)

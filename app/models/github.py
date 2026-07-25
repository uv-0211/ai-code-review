from pydantic import BaseModel

class PostResult(BaseModel):
    num_comments: int
    reason: str | None = None
from pydantic import BaseModel, Field

class ReviewConfig(BaseModel):
    max_issues: int = Field(default=10, ge=1, le=50)
    max_iterations: int = Field(default=1, ge=1, le=3)

    model_config = { "frozen": True }
from pydantic import BaseModel, Field
from typing import Optional


class IdeaUpdateRequest(BaseModel):
    title: Optional[str] = Field(
        None,
        description="Updated title for the idea",
        max_length=100
    )
    description: Optional[str] = Field(
        None,
        description="Updated description for the idea",
        max_length=500
    )
    problem_statement: Optional[str] = Field(
        None,
        description="Updated problem statement for the idea",
        max_length=300
    )
    ideal_customer_profile: Optional[str] = Field(
        None,
        description="Updated ideal customer profile",
        max_length=400
    )

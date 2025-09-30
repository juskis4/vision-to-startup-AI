from pydantic import BaseModel, Field
from typing import Optional, List


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


class UpdateListRequest(BaseModel):
    key_features: Optional[List[str]] = Field(
        None,
        description="Updated list of key features",
        min_length=1,
        max_length=12
    )
    pain_points: Optional[List[str]] = Field(
        None,
        description="Updated list of pain points",
        min_length=1,
        max_length=12
    )
    target_demographics: Optional[List[str]] = Field(
        None,
        description="Updated list of target demographics",
        min_length=1,
        max_length=12
    )
    user_motivations: Optional[List[str]] = Field(
        None,
        description="Updated list of user motivations",
        min_length=1,
        max_length=12
    )

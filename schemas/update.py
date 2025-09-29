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


class UpdateKeyFeaturesRequest(BaseModel):
    features: List[str] = Field(
        description="Complete list of key features to replace existing ones",
        min_length=1,
        max_length=12
    )

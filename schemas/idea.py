from pydantic import BaseModel, Field
from typing import List


class IdeaSchema(BaseModel):
    title: str = Field(
        description="A short, catchy title for the idea."
    )
    description: str = Field(
        description="1-3 sentence canonical description of the idea."
    )
    functionality: List[str] = Field(
        description="Prioritized bullet list of core features / flows"
    )
    pros: List[str] = Field(
        description="Positive aspects and advantages"
    )
    cons: List[str] = Field(
        description="Risks, pitfalls, or costs"
    )
    suggested_next_steps: List[str] = Field(
        description="Practical next steps (technical & business)"
    )
    confidence: float = Field(
        description="How confident the model is in the evaluation",
        ge=0.0,
        le=1.0
    )

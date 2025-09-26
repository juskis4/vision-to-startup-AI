from pydantic import BaseModel, Field
from typing import List


class IdeaSchema(BaseModel):
    title: str = Field(
        description="A short, catchy title for the idea."
    )
    description: str = Field(
        description="1-3 sentence canonical description of the idea."
    )
    core_problem: str = Field(
        description="Backwards deconstructed idea to identify the core problem it solves."
    )
    functionality: List[str] = Field(
        description="Prioritized bullet list of core features / flows"
    )
    confidence: float = Field(
        description="How confident the model is in the evaluation",
        ge=0.0,
        le=1.0
    )


class IcpSchema(BaseModel):
    demographics: str = Field(
        description="Age, location, occupation."
    )
    psychographics: str = Field(
        description="Values, beliefs, goals."
    )
    pain_points: str = Field(
        description="Customers pain points that relate to the core problem."
    )
    motivation: List[str] = Field(
        description="Key motivation for using the product."
    )
    confidence: float = Field(
        description="How confident the model is in the evaluation",
        ge=0.0,
        le=1.0
    )


class RedditObservation(BaseModel):
    frustration: str = Field(
        description="The key frustration or pain point expressed"
    )
    quote: str = Field(
        description="The exact quote from the Reddit post/comment"
    )
    quote_link: str = Field(
        description="Direct link to the Reddit post/comment"
    )
    implication: str = Field(
        description="What this observation implies about user needs or product opportunities"
    )


class RedditSchema(BaseModel):
    subreddits: List[str] = Field(
        description="List of subreddit names relevant to the idea and ICP"
    )
    observations: List[RedditObservation] = Field(
        description="List of Reddit observations with frustrations, quotes, links, and implications"
    )
    confidence: float = Field(
        description="How confident the model is in the evaluation",
        ge=0.0,
        le=1.0
    )


class ResponseSchema(BaseModel):
    idea: IdeaSchema = Field()
    icp: IcpSchema = Field()
    reddit_analysis: RedditSchema = Field()

from pydantic import BaseModel, Field
from typing import List, Optional


class IdeaSchema(BaseModel):
    title: str = Field(
        description="A short, catchy title for the idea.",
        max_length=100
    )
    description: str = Field(
        description="1-3 sentence canonical description of the idea.",
        max_length=500
    )
    problem_statement: str = Field(
        description="Clear statement of the core problem this idea solves.",
        max_length=300
    )
    key_features: List[str] = Field(
        description="List of key features or capabilities of the solution",
        min_length=3,
        max_length=7
    )
    confidence: float = Field(
        description="Confidence score (0.0-1.0) indicating quality and relevance of the idea analysis. Used as a guard to filter low-quality responses.",
        ge=0.0,
        le=1.0
    )


class IcpSchema(BaseModel):
    target_demographics: List[str] = Field(
        description="List of demographic tags describing the target audience (e.g., 'Busy professionals aged 25-45', 'Health-conscious individuals. Up to 4 words per tag.')",
        min_length=3,
        max_length=6
    )
    ideal_customer_profile: str = Field(
        description="Detailed description of the ideal customer including demographics, income, location, and characteristics",
        max_length=400
    )
    pain_points: List[str] = Field(
        description="List of specific pain points the target customers face",
        min_length=3,
        max_length=7
    )
    user_motivations: List[str] = Field(
        description="List of key motivations that drive users to seek this solution",
        min_length=3,
        max_length=7
    )
    confidence: float = Field(
        description="Confidence score (0.0-1.0) indicating quality and relevance of the ICP analysis. Used as a guard to filter low-quality responses.",
        ge=0.0,
        le=1.0
    )


class RedditFeedback(BaseModel):
    comment: str = Field(
        description="The Reddit comment or feedback text",
        max_length=300
    )
    username: str = Field(
        description="Reddit username (e.g., 'u/busymom2024')",
        pattern=r"^u/[a-zA-Z0-9_-]+$"
    )
    subreddit: str = Field(
        description="Subreddit where the comment was found (e.g., 'r/MealPrepSunday')",
        pattern=r"^r/[a-zA-Z0-9_]+$"
    )
    link: str = Field(
        description="Direct URL link to the Reddit comment or post"
    )


class RedditSchema(BaseModel):
    supportive_feedback: List[RedditFeedback] = Field(
        description="List of supportive feedback from Reddit comments",
        min_length=1,
        max_length=5
    )
    challenging_feedback: List[RedditFeedback] = Field(
        description="List of challenging or critical feedback from Reddit comments",
        min_length=1,
        max_length=3
    )
    relevant_subreddits: List[str] = Field(
        description="List of relevant subreddit names for research (e.g., 'r/MealPrepSunday', 'r/Cooking')",
        min_length=4,
        max_length=8
    )
    confidence: float = Field(
        description="Confidence score (0.0-1.0) indicating quality and relevance of the Reddit analysis. Used as a guard to filter low-quality responses.",
        ge=0.0,
        le=1.0
    )


class ResponseSchema(BaseModel):
    idea: IdeaSchema = Field()
    icp: IcpSchema = Field()
    reddit_analysis: RedditSchema = Field()
    idea_id: Optional[str] = Field(
        default=None, description="Generated idea ID from database")

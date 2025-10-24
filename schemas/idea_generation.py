from pydantic import BaseModel, Field
from typing import Optional


class IdeaGenerateResponse(BaseModel):
    """Response schema for starting idea generation"""
    job_id: str = Field(description="Job ID for tracking generation progress")
    status: str = Field(description="Current job status")
    poll_url: str = Field(description="URL to poll for job status updates")


class IdeaJobStatusResponse(BaseModel):
    """Response schema for idea generation job status"""
    job_id: str = Field(description="Job ID")
    status: str = Field(
        description="Job status: queued, running, succeeded, failed")
    progress: float = Field(description="Progress percentage (0.0 to 1.0)")
    error: Optional[str] = Field(description="Error message if job failed")
    user_id: str = Field(description="User ID who initiated the job")
    retry_after: Optional[int] = Field(
        description="Seconds to wait before next poll")
    idea_url: Optional[str] = Field(
        description="URL to retrieve the generated idea (available after success)")

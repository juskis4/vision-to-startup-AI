from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PromptGenerateRequest(BaseModel):
    """Request schema for starting prompt generation"""
    idea_id: str = Field(description="UUID of the idea to generate prompt for")
    service_type: str = Field(
        description="Service type: lovable, chatgpt, claude, cursor, bolt")


class PromptGenerateResponse(BaseModel):
    """Response schema for starting prompt generation"""
    job_id: str = Field(description="Job ID for tracking generation progress")
    status: str = Field(description="Current job status")
    poll_url: str = Field(description="URL to poll job status")
    result_url: str = Field(
        description="URL to get latest prompt for this service")
    by_id_url: Optional[str] = Field(
        None, description="URL to get prompt by ID (available after success)")


class JobStatusResponse(BaseModel):
    """Response schema for job status polling"""
    job_id: str = Field(description="Job ID")
    status: str = Field(
        description="Job status: queued, running, succeeded, failed")
    progress: float = Field(description="Progress from 0.0 to 1.0")
    error: Optional[str] = Field(None, description="Error message if failed")
    idea_id: str = Field(description="Idea ID this job is for")
    service_type: str = Field(description="Service type")
    result_url: str = Field(
        description="URL to get latest prompt for this service")
    by_id_url: Optional[str] = Field(
        None, description="URL to get prompt by ID (available after success)")
    retry_after: Optional[int] = Field(
        None, description="Recommended polling interval in seconds")


class PromptData(BaseModel):
    """Schema for prompt data"""
    id: str = Field(description="Prompt ID")
    idea_id: str = Field(description="Idea ID")
    service_type: str = Field(description="Service type")
    prompt: str = Field(description="Generated prompt content")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class PromptResponse(BaseModel):
    """Response schema for prompt retrieval"""
    success: bool = Field(description="Whether the request was successful")
    data: Optional[PromptData] = Field(
        None, description="Prompt data if found")
    message: Optional[str] = Field(None, description="Status message")

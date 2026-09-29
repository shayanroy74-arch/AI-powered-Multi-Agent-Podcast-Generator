from pydantic import BaseModel
from typing import Optional


class PodcastCreate(BaseModel):
    user_id: int
    title: str
    topic: str
    duration: Optional[int] = None
    language: Optional[str] = None
    speakers: Optional[int] = None
    status: Optional[str] = "draft"

class ResearchCreate(BaseModel):
    podcast_id: int
    content: str

class ScriptCreate(BaseModel):
    podcast_id: int
    content: str

class AudioFileCreate(BaseModel):
    podcast_id: int
    speaker: Optional[str] = None
    file_url: str

class PodcastGenerationRequest(BaseModel):
    podcast_id: int
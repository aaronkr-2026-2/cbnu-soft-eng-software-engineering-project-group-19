import re
import uuid
from typing import Literal
from pydantic import field_validator, model_validator
from urllib.parse import parse_qs, urlparse

from pydantic import BaseModel, Field


def validate_youtube_url(value: str | None) -> str | None:
    if value is None:
        return None
    parsed = urlparse(value.strip())
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host not in {
        "youtu.be",
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "www.youtube-nocookie.com",
    }:
        raise ValueError("Use a secure YouTube or youtu.be link")

    parts = [part for part in parsed.path.split("/") if part]
    query = parse_qs(parsed.query)
    video_id = query.get("v", [""])[0]
    playlist_id = query.get("list", [""])[0]
    if host == "youtu.be" and len(parts) == 1:
        video_id = parts[0]
    elif not video_id and len(parts) == 2 and parts[0] in {"embed", "shorts", "live"}:
        video_id = parts[1] if parts[1] != "videoseries" else ""
    if video_id and not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError("Use a YouTube video or playlist link")
    if playlist_id and not re.fullmatch(r"[A-Za-z0-9_-]{10,100}", playlist_id):
        raise ValueError("Use a YouTube video or playlist link")
    if not video_id and not (playlist_id and parts in (["playlist"], ["embed", "videoseries"])):
        raise ValueError("Use a YouTube video or playlist link")
    if host == "youtu.be":
        return parsed._replace(path=f"/{video_id}").geturl()
    return parsed.geturl()


class LessonCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    content: str = Field(min_length=1)
    resource_type: Literal["text", "pdf", "video", "audio"] = "text"
    external_video_url: str | None = Field(default=None, max_length=500)
    position: int = Field(ge=1)
    module_id: uuid.UUID | None = None

    @field_validator("external_video_url")
    @classmethod
    def validate_video_url(cls, value):
        return validate_youtube_url(value)

    @model_validator(mode="after")
    def video_url_requires_video_lesson(self):
        if self.external_video_url and self.resource_type != "video":
            raise ValueError("External video links can only be used for video lessons")
        return self


class LessonUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    content: str | None = Field(default=None, min_length=1)
    resource_type: Literal["text", "pdf", "video", "audio"] | None = None
    position: int | None = Field(default=None, ge=1)
    external_video_url: str | None = Field(default=None, max_length=500)
    module_id: uuid.UUID | None = None

    @field_validator("external_video_url")
    @classmethod
    def validate_video_url(cls, value):
        return validate_youtube_url(value)

    @model_validator(mode="after")
    def video_url_requires_video_lesson(self):
        if self.external_video_url and self.resource_type not in (None, "video"):
            raise ValueError("External video links can only be used for video lessons")
        return self


class LessonMaterialResponse(BaseModel):
    id: str
    title: str
    resource_type: Literal["pdf", "audio"]
    resource_url: str
    resource_mime_type: str
    position: int


class LessonResponse(BaseModel):
    id: str
    course_id: str
    title: str
    content: str
    resource_type: str = "text"
    resource_url: str | None = None
    resource_mime_type: str | None = None
    external_video_url: str | None = None
    banner_url: str | None = None
    content_language: str = "uz"
    translated: bool = False
    position: int
    module_id: str | None = None
    materials: list[LessonMaterialResponse] = Field(default_factory=list)

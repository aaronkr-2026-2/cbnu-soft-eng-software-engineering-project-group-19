from typing import Literal
from pydantic import field_validator, model_validator
from urllib.parse import urlparse

from pydantic import BaseModel, Field


class LessonCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    content: str = Field(min_length=1)
    resource_type: Literal["text", "pdf", "video", "audio"] = "text"
    external_video_url: str | None = Field(default=None, max_length=500)
    position: int = Field(ge=1)

    @field_validator("external_video_url")
    @classmethod
    def validate_video_url(cls, value):
        if value is None:
            return value
        parsed = urlparse(value)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or not (host == "youtu.be" or host == "youtube.com" or host.endswith(".youtube.com")):
            raise ValueError("Use a secure YouTube or youtu.be link")
        path_parts = [part for part in parsed.path.split("/") if part]
        has_video = bool(parsed.hostname == "youtu.be" and path_parts)
        has_video = has_video or bool(parsed.hostname != "youtu.be" and (
            parsed.query and any(part.partition("=")[0] == "v" and part.partition("=")[2] for part in parsed.query.split("&"))
            or len(path_parts) >= 2 and path_parts[0] in {"embed", "shorts", "live"}
        ))
        has_playlist = bool(parsed.path.startswith("/playlist") and any(
            part.partition("=")[0] == "list" and part.partition("=")[2] for part in parsed.query.split("&")
        ))
        if not (has_video or has_playlist):
            raise ValueError("Use a YouTube video or playlist link")
        return value

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

    @field_validator("external_video_url")
    @classmethod
    def validate_video_url(cls, value):
        if value is None:
            return value
        parsed = urlparse(value)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or not (host == "youtu.be" or host == "youtube.com" or host.endswith(".youtube.com")):
            raise ValueError("Use a secure YouTube or youtu.be link")
        path_parts = [part for part in parsed.path.split("/") if part]
        has_video = bool(parsed.hostname == "youtu.be" and path_parts)
        has_video = has_video or bool(parsed.hostname != "youtu.be" and (
            parsed.query and any(part.partition("=")[0] == "v" and part.partition("=")[2] for part in parsed.query.split("&"))
            or len(path_parts) >= 2 and path_parts[0] in {"embed", "shorts", "live"}
        ))
        has_playlist = bool(parsed.path.startswith("/playlist") and any(
            part.partition("=")[0] == "list" and part.partition("=")[2] for part in parsed.query.split("&")
        ))
        if not (has_video or has_playlist):
            raise ValueError("Use a YouTube video or playlist link")
        return value

    @model_validator(mode="after")
    def video_url_requires_video_lesson(self):
        if self.external_video_url and self.resource_type not in (None, "video"):
            raise ValueError("External video links can only be used for video lessons")
        return self


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

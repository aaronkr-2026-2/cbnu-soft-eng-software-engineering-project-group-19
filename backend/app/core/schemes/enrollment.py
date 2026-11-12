from datetime import datetime

from pydantic import BaseModel


class EnrollmentResponse(BaseModel):
    id: str
    course_id: str
    course_title: str
    enrolled_at: datetime

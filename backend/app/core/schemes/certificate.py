from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CertificateResponse(BaseModel):
    id: UUID
    certificate_code: str
    recipient_name: str
    course_title: str
    issued_at: datetime


class CertificateVerificationResponse(BaseModel):
    valid: bool
    certificate_code: str
    recipient_name: str
    course_title: str
    issued_at: datetime

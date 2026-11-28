from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import AuthorInvitation

INVITATION_TTL = timedelta(hours=24)


def token_digest(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def create_author_invitation(db: Session, email: str) -> str:
    token = token_urlsafe(32)
    db.add(
        AuthorInvitation(
            token_digest=token_digest(token),
            email=email.casefold(),
            expires_at=datetime.now(UTC) + INVITATION_TTL,
        )
    )
    return token


def consume_author_invitation(db: Session, email: str, token: str) -> bool:
    now = datetime.now(UTC)
    return (
        db.scalar(
            update(AuthorInvitation)
            .where(
                AuthorInvitation.token_digest == token_digest(token),
                AuthorInvitation.email == email.casefold(),
                AuthorInvitation.expires_at > now,
                AuthorInvitation.used_at.is_(None),
            )
            .values(used_at=now)
            .returning(AuthorInvitation.token_digest)
        )
        is not None
    )

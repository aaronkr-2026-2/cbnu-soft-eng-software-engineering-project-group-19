import hashlib
import os
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import PasskeyProof

WEBAUTHN_RP_ID = os.getenv("WEBAUTHN_RP_ID") or os.getenv("RENDER_EXTERNAL_HOSTNAME", "localhost")
WEBAUTHN_RP_NAME = os.getenv("WEBAUTHN_RP_NAME", "StudyFlow AI")
WEBAUTHN_ORIGIN = os.getenv("WEBAUTHN_ORIGIN") or os.getenv("RENDER_EXTERNAL_URL", "http://localhost:8000")


def consume_passkey_proof(token: str | None, user_id, purpose: str, db: Session) -> None:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail="Verify your passkey before continuing",
        )
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    now = datetime.now(timezone.utc)
    proof = (
        db.query(PasskeyProof)
        .filter(
            PasskeyProof.user_id == user_id,
            PasskeyProof.token_hash == token_hash,
            PasskeyProof.purpose == purpose,
            PasskeyProof.consumed_at.is_(None),
            PasskeyProof.expires_at > now,
        )
        .with_for_update()
        .first()
    )
    if proof is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A valid, recent passkey verification is required",
        )
    proof.consumed_at = now
    db.flush()


def proof_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=5)

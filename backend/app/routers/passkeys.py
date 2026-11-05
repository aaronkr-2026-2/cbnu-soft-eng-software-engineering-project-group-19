import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from webauthn import (
    base64url_to_bytes,
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import bytes_to_base64url
from webauthn.helpers.structs import (
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from app.core.dependencies import get_current_user
from app.core.passkeys import (
    WEBAUTHN_ORIGIN,
    WEBAUTHN_RP_ID,
    WEBAUTHN_RP_NAME,
    proof_expiry,
)
from app.database import get_db
from app.models import PasskeyChallenge, PasskeyCredential, PasskeyProof, User

router = APIRouter(prefix="/auth/passkeys", tags=["Passkeys"])


class RegistrationVerify(BaseModel):
    challenge_id: uuid.UUID
    credential: dict[str, Any]
    label: str = Field(default="This device", min_length=1, max_length=120)


class AuthenticationOptionsRequest(BaseModel):
    purpose: Literal["final_exam", "certificate"]


class AuthenticationVerify(BaseModel):
    challenge_id: uuid.UUID
    credential: dict[str, Any]


def _challenge_or_404(challenge_id: uuid.UUID, user_id: uuid.UUID, purpose: str, db: Session) -> PasskeyChallenge:
    now = datetime.now(timezone.utc)
    challenge = (
        db.query(PasskeyChallenge)
        .filter(
            PasskeyChallenge.id == challenge_id,
            PasskeyChallenge.user_id == user_id,
            PasskeyChallenge.purpose == purpose,
            PasskeyChallenge.consumed_at.is_(None),
            PasskeyChallenge.expires_at > now,
        )
        .with_for_update()
        .first()
    )
    if challenge is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passkey challenge expired or already used")
    return challenge


@router.get("/me")
def passkey_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    credentials = (
        db.query(PasskeyCredential)
        .filter(PasskeyCredential.user_id == current_user.id)
        .order_by(PasskeyCredential.created_at)
        .all()
    )
    return {
        "enabled": bool(credentials),
        "credentials": [
            {"id": str(item.id), "label": item.label, "created_at": item.created_at}
            for item in credentials
        ],
    }


@router.post("/registration/options")
def registration_options(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    existing = db.query(PasskeyCredential).filter(PasskeyCredential.user_id == current_user.id).all()
    options = generate_registration_options(
        rp_id=WEBAUTHN_RP_ID,
        rp_name=WEBAUTHN_RP_NAME,
        user_id=current_user.id.bytes,
        user_name=current_user.email,
        user_display_name=current_user.full_name,
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        exclude_credentials=[
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(item.credential_id))
            for item in existing
        ],
    )
    db.query(PasskeyChallenge).filter(
        PasskeyChallenge.user_id == current_user.id,
        PasskeyChallenge.purpose == "registration",
        PasskeyChallenge.consumed_at.is_(None),
    ).delete(synchronize_session=False)
    challenge = PasskeyChallenge(
        user_id=current_user.id,
        challenge=bytes_to_base64url(options.challenge),
        purpose="registration",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    db.add(challenge)
    db.commit()
    return {"challenge_id": str(challenge.id), "publicKey": options_to_json(options)}


@router.post("/registration/verify")
def verify_registration(
    payload: RegistrationVerify,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    challenge = _challenge_or_404(payload.challenge_id, current_user.id, "registration", db)
    try:
        verification = verify_registration_response(
            credential=payload.credential,
            expected_challenge=base64url_to_bytes(challenge.challenge),
            expected_rp_id=WEBAUTHN_RP_ID,
            expected_origin=WEBAUTHN_ORIGIN,
            require_user_verification=True,
        )
    except Exception as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passkey registration could not be verified") from error

    credential_id = bytes_to_base64url(verification.credential_id)
    response = payload.credential.get("response", {})
    transports = response.get("transports") if isinstance(response, dict) else None
    db.add(
        PasskeyCredential(
            user_id=current_user.id,
            credential_id=credential_id,
            public_key=verification.credential_public_key,
            sign_count=verification.sign_count,
            transports=transports if isinstance(transports, list) else None,
            label=payload.label.strip() or "This device",
        )
    )
    challenge.consumed_at = datetime.now(timezone.utc)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This passkey is already registered") from error
    return {"enabled": True}


@router.post("/authentication/options")
def authentication_options(
    payload: AuthenticationOptionsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    credentials = db.query(PasskeyCredential).filter(PasskeyCredential.user_id == current_user.id).all()
    if not credentials:
        raise HTTPException(status_code=status.HTTP_428_PRECONDITION_REQUIRED, detail="Register a passkey before this action")
    options = generate_authentication_options(
        rp_id=WEBAUTHN_RP_ID,
        allow_credentials=[
            PublicKeyCredentialDescriptor(
                id=base64url_to_bytes(item.credential_id),
                transports=item.transports,
            )
            for item in credentials
        ],
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    db.query(PasskeyChallenge).filter(
        PasskeyChallenge.user_id == current_user.id,
        PasskeyChallenge.purpose == payload.purpose,
        PasskeyChallenge.consumed_at.is_(None),
    ).delete(synchronize_session=False)
    challenge = PasskeyChallenge(
        user_id=current_user.id,
        challenge=bytes_to_base64url(options.challenge),
        purpose=payload.purpose,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    db.add(challenge)
    db.commit()
    return {"challenge_id": str(challenge.id), "publicKey": options_to_json(options)}


@router.post("/authentication/verify")
def verify_authentication(
    payload: AuthenticationVerify,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    challenge = (
        db.query(PasskeyChallenge)
        .filter(
            PasskeyChallenge.id == payload.challenge_id,
            PasskeyChallenge.user_id == current_user.id,
            PasskeyChallenge.purpose.in_(["final_exam", "certificate"]),
            PasskeyChallenge.consumed_at.is_(None),
            PasskeyChallenge.expires_at > datetime.now(timezone.utc),
        )
        .with_for_update()
        .first()
    )
    if challenge is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passkey challenge expired or already used")
    raw_id = payload.credential.get("rawId") or payload.credential.get("id")
    credential = db.query(PasskeyCredential).filter(
        PasskeyCredential.user_id == current_user.id,
        PasskeyCredential.credential_id == raw_id,
    ).first()
    if credential is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This passkey is not registered to your account")
    try:
        verification = verify_authentication_response(
            credential=payload.credential,
            expected_challenge=base64url_to_bytes(challenge.challenge),
            expected_rp_id=WEBAUTHN_RP_ID,
            expected_origin=WEBAUTHN_ORIGIN,
            credential_public_key=credential.public_key,
            credential_current_sign_count=credential.sign_count,
            require_user_verification=True,
        )
    except Exception as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passkey verification failed") from error
    if not verification.user_verified:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device user verification is required")

    credential.sign_count = verification.new_sign_count
    challenge.consumed_at = datetime.now(timezone.utc)
    token = uuid.uuid4().hex + uuid.uuid4().hex
    proof = PasskeyProof(
        user_id=current_user.id,
        token_hash=__import__("hashlib").sha256(token.encode()).hexdigest(),
        purpose=challenge.purpose,
        expires_at=proof_expiry(),
    )
    db.add(proof)
    db.commit()
    return {"proof": token, "purpose": challenge.purpose, "expires_in": 300}

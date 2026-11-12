import json
import os
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models import Course, CoursePayment, Enrollment, User

router = APIRouter(prefix="/payments", tags=["Payments"])


class CheckoutResponse(BaseModel):
    payment_id: str
    checkout_url: str
    amount_uzs: int
    status: str


class PaymentStatusResponse(BaseModel):
    payment_id: str
    course_id: str
    status: str
    amount_uzs: int
    enrolled: bool


def _provider_base() -> str:
    environment = os.getenv("GLOBALPAY_ENV", "sandbox").strip().lower()
    if environment == "sandbox":
        return "https://checkout-api-dev.globalpay.uz/checkout"
    if environment == "production":
        return "https://checkout-api.globalpay.uz/checkout"
    raise HTTPException(status_code=503, detail="GLOBALPAY_ENV must be sandbox or production")


def _provider_config() -> tuple[str, str, str]:
    username = os.getenv("GLOBALPAY_USERNAME", "").strip()
    password = os.getenv("GLOBALPAY_PASSWORD", "").strip()
    service_id = os.getenv("GLOBALPAY_SERVICE_ID", "").strip()
    if not username or not password or not service_id:
        raise HTTPException(status_code=503, detail="GlobalPay merchant credentials are not configured")
    return username, password, service_id


def _provider_request(method: str, path: str, *, token: str | None = None, body: dict | None = None) -> dict:
    base = _provider_base()
    headers = {"Accept": "application/json"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"{base}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise HTTPException(status_code=502, detail=f"Payment provider returned HTTP {error.code}") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        raise HTTPException(status_code=502, detail="Could not reach the payment provider") from None
    if not isinstance(payload, dict):
        raise HTTPException(status_code=502, detail="Payment provider returned an invalid response")
    return payload


def _provider_access_token() -> tuple[str, str]:
    username, password, service_id = _provider_config()
    payload = _provider_request("POST", "/v1/merchant/auth", body={"username": username, "password": password})
    token = payload.get("access_token") or payload.get("accessToken")
    if not token:
        raise HTTPException(status_code=502, detail="Payment provider did not return an access token")
    return str(token), service_id


def _to_response(payment: CoursePayment, enrolled: bool) -> PaymentStatusResponse:
    return PaymentStatusResponse(
        payment_id=str(payment.id), course_id=str(payment.course_id), status=payment.status,
        amount_uzs=payment.amount_uzs, enrolled=enrolled,
    )


@router.post("/courses/{course_id}", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
def create_course_checkout(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CheckoutResponse:
    course = db.query(Course).filter(Course.id == course_id, Course.is_published.is_(True)).first()
    if course is None:
        raise HTTPException(status_code=404, detail="Published course not found")
    if course.price_uzs <= 0:
        raise HTTPException(status_code=400, detail="This course is free; enroll directly")
    if db.query(Enrollment.id).filter(Enrollment.user_id == current_user.id, Enrollment.course_id == course.id).first():
        raise HTTPException(status_code=409, detail="Already enrolled in this course")

    app_url = (
        os.getenv("PUBLIC_APP_URL")
        or os.getenv("RENDER_EXTERNAL_URL")
        or "http://localhost:8000"
    ).strip().rstrip("/")
    if not app_url.startswith("https://") and "localhost" not in app_url and "127.0.0.1" not in app_url:
        raise HTTPException(status_code=503, detail="PUBLIC_APP_URL must use HTTPS")
    payment_id = uuid.uuid4()
    external_id = str(payment_id)
    access_token, service_id = _provider_access_token()
    try:
        service_id_value: int | str = int(service_id)
    except ValueError:
        service_id_value = service_id
    response = _provider_request(
        "POST", "/v1/user-service-tokens", token=access_token,
        body={
            "name": f"StudyFlow course {str(course.id)[:8]}",
            "description": course.title[:200],
            "externalId": external_id,
            "externalServiceId": service_id_value,
            "tokenLifespan": 900,
            "requestFields": [
                {"name": "amount", "value": str(course.price_uzs * 100)},
                {"name": "currency", "value": "UZS"},
            ],
            "successRedirectUrl": f"{app_url}/app/?payment_id={payment_id}",
            "failRedirectUrl": f"{app_url}/app/?payment_id={payment_id}",
        },
    )
    provider_token = response.get("id") or response.get("token")
    checkout_url = response.get("userRedirectUrl") or response.get("paymentUrl")
    if not provider_token or not checkout_url or not str(checkout_url).startswith("https://"):
        raise HTTPException(status_code=502, detail="Payment provider did not return a valid checkout link")

    payment = CoursePayment(
        id=payment_id, user_id=current_user.id, course_id=course.id, amount_uzs=course.price_uzs,
        status="pending", external_id=external_id, provider_token=str(provider_token), checkout_url=str(checkout_url),
    )
    db.add(payment)
    db.commit()
    return CheckoutResponse(payment_id=str(payment.id), checkout_url=str(checkout_url), amount_uzs=payment.amount_uzs, status=payment.status)


@router.get("/{payment_id}", response_model=PaymentStatusResponse)
def get_course_payment_status(
    payment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaymentStatusResponse:
    payment = db.query(CoursePayment).filter(CoursePayment.id == payment_id, CoursePayment.user_id == current_user.id).first()
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status not in {"success", "failed", "cancelled", "reverted"}:
        access_token, _ = _provider_access_token()
        remote = _provider_request("GET", f"/v1/payment/servicetoken/{quote(payment.provider_token, safe='')}", token=access_token)
        remote_status = str(remote.get("status", "")).upper()
        if remote_status == "APPROVED":
            remote_external_id = str(remote.get("externalId", ""))
            try:
                remote_amount = int(remote.get("amount"))
            except (TypeError, ValueError):
                remote_amount = -1
            remote_currency = str(remote.get("currency", "")).upper()
            if remote_external_id != payment.external_id or remote_amount != payment.amount_uzs * 100 or remote_currency != "UZS":
                raise HTTPException(status_code=502, detail="Provider payment details did not match this course order")
            payment.status = "success"
            payment.confirmed_at = datetime.now(timezone.utc)
            if not db.query(Enrollment.id).filter(Enrollment.user_id == payment.user_id, Enrollment.course_id == payment.course_id).first():
                db.add(Enrollment(user_id=payment.user_id, course_id=payment.course_id))
        elif remote_status == "FAILED":
            payment.status = "failed"
        db.commit()
        db.refresh(payment)

    enrolled = db.query(Enrollment.id).filter(Enrollment.user_id == payment.user_id, Enrollment.course_id == payment.course_id).first() is not None
    return _to_response(payment, enrolled)

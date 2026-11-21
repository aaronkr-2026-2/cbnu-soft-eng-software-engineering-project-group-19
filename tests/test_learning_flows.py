import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from xml.etree import ElementTree
from urllib.parse import parse_qs, urlparse

import cbor2
import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException
from starlette.requests import Request
from webauthn.helpers import bytes_to_base64url
from webauthn.helpers.structs import AuthenticatorTransport

from app.routers import auth as auth_router
from app.routers import courses as courses_router
from app.routers import lessons as lessons_router
from app.routers import passkeys as passkeys_router
from app.routers import progress as progress_router
from app.routers import quizzes as quizzes_router
from tests.helpers import login, register


_save_course_banner = courses_router.save_course_banner


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("email", "invalid-email", "email address"),
        ("full_name", "   ", "at least 2"),
        ("full_name", "n" * 151, "at most 150"),
        ("password", "short", "at least 8"),
        ("password", "p" * 129, "at most 128"),
    ],
)
def test_registration_validates_inputs(client, field, value, message):
    payload = {
        "email": "student@example.com",
        "full_name": "StudyFlow Student",
        "password": "correct-horse-42",
        field: value,
    }

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422
    error = response.json()["detail"][0]
    assert error["loc"] == ["body", field]
    assert message in error["msg"]


def create_course(client, author_headers, title="Intro to Python", price_uzs=0, language="uz"):
    response = client.post(
        "/courses",
        headers=author_headers,
        json={
            "title": title,
            "description": "Test course description",
            "category": "Programming",
            "price_uzs": price_uzs,
            "language": language,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_local_passkeys_require_localhost_origin(monkeypatch):
    monkeypatch.setattr(passkeys_router, "WEBAUTHN_ORIGIN", "http://localhost:8000")

    def request_for(origin):
        return Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/auth/passkeys/options",
                "scheme": "http",
                "server": ("127.0.0.1", 8000),
                "client": ("127.0.0.1", 12345),
                "headers": [(b"origin", origin.encode("ascii"))],
            }
        )

    assert passkeys_router._request_webauthn_scope(request_for("http://localhost:8000")) == (
        "localhost",
        "http://localhost:8000",
    )
    with pytest.raises(HTTPException) as error:
        passkeys_router._request_webauthn_scope(request_for("http://127.0.0.1:8000"))
    assert error.value.status_code == 400
    assert "http://localhost:8000/app" in error.value.detail

    assert passkeys_router._credential_transports(["internal", "usb", "old-transport"]) == [
        AuthenticatorTransport.INTERNAL,
        AuthenticatorTransport.USB,
    ]
    assert passkeys_router._credential_transports(None) is None


def test_passkey_registration_and_signed_verification(client, monkeypatch):
    host = "studyflow-web-1hab.vercel.app"
    origin = f"https://{host}"
    monkeypatch.setattr(passkeys_router, "WEBAUTHN_ORIGIN", origin)
    email = "passkey-learner@example.com"
    register(client, email)
    headers = {**login(client, email), "Origin": origin}
    endpoint = "/auth/passkeys"
    credential_id = uuid4().bytes
    encoded_id = bytes_to_base64url(credential_id)
    credential = {"id": encoded_id, "rawId": encoded_id, "type": "public-key"}
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key().public_numbers()
    cose_key = cbor2.dumps(
        {
            1: 2,
            3: -7,
            -1: 1,
            -2: public_key.x.to_bytes(32, "big"),
            -3: public_key.y.to_bytes(32, "big"),
        }
    )
    rp_hash = hashlib.sha256(host.encode()).digest()

    def client_data(challenge, operation):
        return json.dumps(
            {
                "type": operation,
                "challenge": json.loads(challenge["publicKey"])["challenge"],
                "origin": origin,
            }
        ).encode()

    upstream = "https://studyflow-backend.example"
    proxy_headers = {key: value for key, value in headers.items() if key != "Origin"}
    status_response = client.get(f"{upstream}{endpoint}/me", headers=proxy_headers)
    assert status_response.status_code == 200, status_response.text
    assert status_response.json() == {"enabled": False, "credentials": []}
    assert (
        client.get(
            f"{upstream}{endpoint}/me", headers={**proxy_headers, "Origin": upstream}
        ).status_code
        == 403
    )
    assert (
        client.post(f"{upstream}{endpoint}/registration/options", headers=proxy_headers).status_code
        == 403
    )

    options = client.post(f"{endpoint}/registration/options", headers=headers)
    assert options.status_code == 200, options.text
    challenge = options.json()
    registration_data = (
        rp_hash
        + b"\x45"
        + bytes(4)
        + bytes(16)
        + len(credential_id).to_bytes(2, "big")
        + credential_id
        + cose_key
    )
    attestation = cbor2.dumps({"fmt": "none", "authData": registration_data, "attStmt": {}})
    registered = client.post(
        f"{endpoint}/registration/verify",
        headers=headers,
        json={
            "challenge_id": challenge["challenge_id"],
            "credential": {
                **credential,
                "response": {
                    "clientDataJSON": bytes_to_base64url(client_data(challenge, "webauthn.create")),
                    "attestationObject": bytes_to_base64url(attestation),
                },
            },
        },
    )
    assert registered.status_code == 200, registered.text

    status_response = client.get(f"{upstream}{endpoint}/me", headers=proxy_headers)
    assert status_response.status_code == 200, status_response.text
    assert status_response.json()["enabled"] is True

    options = client.post(
        f"{endpoint}/authentication/options", headers=headers, json={"purpose": "certificate"}
    )
    assert options.status_code == 200, options.text
    challenge = options.json()
    authenticator_data = rp_hash + b"\x05" + (1).to_bytes(4, "big")
    client_json = client_data(challenge, "webauthn.get")
    signature = private_key.sign(
        authenticator_data + hashlib.sha256(client_json).digest(), ec.ECDSA(hashes.SHA256())
    )
    payload = {
        "challenge_id": challenge["challenge_id"],
        "credential": {
            **credential,
            "response": {
                "clientDataJSON": bytes_to_base64url(client_json),
                "authenticatorData": bytes_to_base64url(authenticator_data),
                "signature": bytes_to_base64url(signature),
            },
        },
    }
    verification = client.post(f"{endpoint}/authentication/verify", headers=headers, json=payload)
    assert verification.status_code == 200, verification.text
    assert verification.json()["proof"]
    assert verification.json()["purpose"] == "certificate"
    assert verification.json()["expires_in"] == 300
    assert (
        client.post(f"{endpoint}/authentication/verify", headers=headers, json=payload).status_code
        == 400
    )


def test_password_change_invalidates_existing_session(client):
    register(client, "author@example.com", "author")
    old_headers = login(client, "author@example.com", "author")

    wrong_role_login = client.post(
        "/auth/login",
        json={
            "email": "author@example.com",
            "password": "correct-horse-42",
            "account_type": "learner",
        },
    )
    assert wrong_role_login.status_code == 403

    change = client.post(
        "/auth/change-password",
        headers=old_headers,
        json={"current_password": "correct-horse-42", "new_password": "new-password-42"},
    )
    assert change.status_code == 200, change.text
    assert client.get("/auth/me", headers=old_headers).status_code == 401

    new_login = client.post(
        "/auth/login",
        json={
            "email": "author@example.com",
            "password": "new-password-42",
            "account_type": "author",
        },
    )
    assert new_login.status_code == 200, new_login.text


def test_course_ownership_enrollment_payment_and_language_filter(client):
    register(client, "owner@example.com", "author")
    register(client, "other-author@example.com", "author")
    register(client, "learner@example.com")
    owner_headers = login(client, "owner@example.com", "author")
    other_author_headers = login(client, "other-author@example.com", "author")
    learner_headers = login(client, "learner@example.com")

    course = create_course(client, owner_headers)
    course_id = course["id"]
    forbidden_edit = client.put(
        f"/courses/{course_id}",
        headers=other_author_headers,
        json={"title": "Taken over course"},
    )
    assert forbidden_edit.status_code == 404
    forbidden_lesson = client.post(
        f"/courses/{course_id}/lessons",
        headers=other_author_headers,
        json={"title": "Unauthorized Lesson", "content": "Not owned", "position": 1},
    )
    assert forbidden_lesson.status_code == 404
    assert (
        client.post(
            "/courses", headers=learner_headers, json={"title": "No author role"}
        ).status_code
        == 403
    )
    assert client.post(f"/courses/{course_id}/enroll", headers=learner_headers).status_code == 404

    assert client.post(f"/courses/{course_id}/publish", headers=owner_headers).status_code == 200
    enrolled = client.post(f"/courses/{course_id}/enroll", headers=learner_headers)
    assert enrolled.status_code == 201, enrolled.text
    assert client.post(f"/courses/{course_id}/enroll", headers=learner_headers).status_code == 409

    paid_course = create_course(client, owner_headers, "Paid Python", price_uzs=1000)
    assert (
        client.post(f"/courses/{paid_course['id']}/publish", headers=owner_headers).status_code
        == 200
    )
    payment_required = client.post(f"/courses/{paid_course['id']}/enroll", headers=learner_headers)
    assert payment_required.status_code == 402

    english_course = create_course(client, owner_headers, "English Python", language="en")
    assert (
        client.post(f"/courses/{english_course['id']}/publish", headers=owner_headers).status_code
        == 200
    )
    english_catalog = client.get("/courses/catalog?language=en").json()
    uzbek_catalog = client.get("/courses/catalog?language=uz").json()
    assert english_course["id"] in {item["id"] for item in english_catalog}
    assert english_course["id"] not in {item["id"] for item in uzbek_catalog}


def test_missing_course_banner_is_regenerated_without_exposing_draft(client, monkeypatch, tmp_path):
    original_save_course_banner = _save_course_banner
    monkeypatch.setattr(courses_router, "save_course_banner", original_save_course_banner)
    monkeypatch.setattr(courses_router, "COURSE_BANNER_DIR", tmp_path)
    email = "banner-author@example.com"
    register(client, email, "author")
    headers = login(client, email, "author")
    response = client.post(
        "/courses",
        headers=headers,
        json={"title": "HTML & CSS", "description": "A course on layout", "category": "R&D"},
    )
    assert response.status_code == 201, response.text
    draft = response.json()
    banner_url = draft["banner_url"]
    assert banner_url
    banner_path = urlparse(banner_url).path
    original = list(tmp_path.iterdir())
    assert len(original) == 1
    original[0].unlink()

    assert client.get(banner_path).status_code == 404
    preview = client.get(banner_url)
    assert preview.status_code == 200
    assert preview.headers["cache-control"] == "private, no-store"
    assert ElementTree.fromstring(preview.content).attrib["aria-label"] == "HTML & CSS"

    published = client.post(f"/courses/{draft['id']}/publish", headers=headers)
    assert published.status_code == 200
    cover = client.get(published.json()["banner_url"])
    assert cover.status_code == 200
    assert cover.headers["content-type"] == "image/svg+xml"
    assert any(node.text == "R&D" for node in ElementTree.fromstring(cover.content))
    assert not list(tmp_path.iterdir())


def test_missing_lesson_banner_uses_topic_art_and_keeps_draft_private(
    client, monkeypatch, tmp_path
):
    monkeypatch.setattr(lessons_router, "BANNER_DIR", tmp_path)
    email = "lesson-banner-author@example.com"
    register(client, email, "author")
    headers = login(client, email, "author")
    course_id = create_course(client, headers)["id"]
    lesson = client.post(
        f"/courses/{course_id}/lessons",
        headers=headers,
        json={"title": "HTML & CSS", "content": "Build a semantic web page", "position": 1},
    )
    assert lesson.status_code == 201, lesson.text
    path = f"/courses/{course_id}/lessons/{lesson.json()['id']}/banner"
    image = b"\x89PNG\r\n\x1a\nexample"
    upload = client.put(path, headers={**headers, "Content-Type": "image/png"}, content=image)
    assert upload.status_code == 200, upload.text
    draft_url = upload.json()["banner_url"]
    assert client.get(draft_url).content == image
    next(tmp_path.iterdir()).unlink()

    assert client.get(path).status_code == 404
    private_cover = client.get(draft_url)
    assert private_cover.status_code == 200
    assert private_cover.headers["cache-control"] == "private, no-store"
    assert ElementTree.fromstring(private_cover.content).attrib["aria-label"] == "HTML & CSS"

    assert client.post(f"/courses/{course_id}/publish", headers=headers).status_code == 200
    public_cover = client.get(path)
    assert public_cover.status_code == 200
    assert public_cover.headers["content-type"] == "image/svg+xml"
    assert public_cover.content == private_cover.content
    assert not list(tmp_path.iterdir())


def test_course_modules_group_lessons_and_keep_old_lessons_compatible(client):
    register(client, "module-author@example.com", "author")
    register(client, "module-outsider@example.com", "author")
    author_headers = login(client, "module-author@example.com", "author")
    outsider_headers = login(client, "module-outsider@example.com", "author")
    course = create_course(client, author_headers, "Modular Course")
    course_id = course["id"]

    first_module = client.post(
        f"/courses/{course_id}/modules",
        headers=author_headers,
        json={"title": "Basics", "position": 1},
    )
    second_module = client.post(
        f"/courses/{course_id}/modules",
        headers=author_headers,
        json={"title": "Practice", "position": 2},
    )
    assert first_module.status_code == 201, first_module.text
    assert second_module.status_code == 201, second_module.text
    module_id = second_module.json()["id"]
    locked_language = client.put(
        f"/courses/{course_id}", headers=author_headers, json={"language": "en"}
    )
    assert locked_language.status_code == 409

    lesson = client.post(
        f"/courses/{course_id}/lessons",
        headers=author_headers,
        json={
            "title": "First Practice",
            "content": "Practice content",
            "position": 1,
            "module_id": module_id,
        },
    )
    assert lesson.status_code == 201, lesson.text
    assert lesson.json()["module_id"] == module_id

    forbidden = client.put(
        f"/courses/{course_id}/modules/{module_id}",
        headers=outsider_headers,
        json={"title": "Changed by outsider"},
    )
    assert forbidden.status_code == 404

    assert client.post(f"/courses/{course_id}/publish", headers=author_headers).status_code == 200
    outline = client.get(f"/courses/catalog/{course_id}/outline?language=uz")
    assert outline.status_code == 200, outline.text
    assert outline.json()["modules"][1]["title"] == "Practice"
    assert outline.json()["modules"][1]["lessons"][0]["title"] == "First Practice"
    assert outline.json()["unassigned_lessons"] == []

    assert (
        client.delete(
            f"/courses/{course_id}/modules/{module_id}", headers=author_headers
        ).status_code
        == 204
    )
    lessons = client.get(f"/courses/{course_id}/lessons?language=uz", headers=author_headers)
    assert lessons.status_code == 200, lessons.text
    assert lessons.json()[0]["module_id"] is None
    outline_after_delete = client.get(f"/courses/catalog/{course_id}/outline?language=uz")
    assert outline_after_delete.json()["modules"][0]["title"] == "Basics"
    assert outline_after_delete.json()["unassigned_lessons"][0]["title"] == "First Practice"


def test_lesson_assignment_submission_and_author_grading(client):
    register(client, "assignment-author@example.com", "author")
    register(client, "assignment-learner@example.com")
    register(client, "assignment-outsider@example.com")
    author_headers = login(client, "assignment-author@example.com", "author")
    learner_headers = login(client, "assignment-learner@example.com")
    outsider_headers = login(client, "assignment-outsider@example.com")
    course = create_course(client, author_headers, "Assignment Course")
    course_id = course["id"]
    lesson = client.post(
        f"/courses/{course_id}/lessons",
        headers=author_headers,
        json={"title": "Build a function", "content": "Write a small function.", "position": 1},
    )
    assert lesson.status_code == 201, lesson.text
    lesson_id = lesson.json()["id"]

    assignment_response = client.put(
        f"/courses/{course_id}/lessons/{lesson_id}/assignment",
        headers=author_headers,
        json={
            "title": "Function task",
            "instructions": "Write a function and explain it.",
            "max_score": 100,
        },
    )
    assert assignment_response.status_code == 200, assignment_response.text
    assert client.post(f"/courses/{course_id}/publish", headers=author_headers).status_code == 200
    assert client.post(f"/courses/{course_id}/enroll", headers=learner_headers).status_code == 201

    hidden = client.get(
        f"/courses/{course_id}/lessons/{lesson_id}/assignment", headers=outsider_headers
    )
    assert hidden.status_code == 404
    assignment = client.get(
        f"/courses/{course_id}/lessons/{lesson_id}/assignment?language=uz", headers=learner_headers
    )
    assert assignment.status_code == 200, assignment.text
    assert assignment.json()["my_submission"] is None

    submission = client.post(
        f"/courses/{course_id}/lessons/{lesson_id}/assignment/submissions",
        headers=learner_headers,
        json={"answer": "def greet(name): return f'Hello {name}'"},
    )
    assert submission.status_code == 200, submission.text
    submission_id = submission.json()["id"]
    assert submission.json()["status"] == "submitted"

    too_high = client.put(
        f"/courses/{course_id}/lessons/{lesson_id}/assignment/submissions/{submission_id}",
        headers=author_headers,
        json={"score": 101, "feedback": "Great"},
    )
    assert too_high.status_code == 422
    graded = client.put(
        f"/courses/{course_id}/lessons/{lesson_id}/assignment/submissions/{submission_id}",
        headers=author_headers,
        json={"score": 90, "feedback": "Good explanation"},
    )
    assert graded.status_code == 200, graded.text
    assert graded.json()["learner_name"] == "Assignment-Learner"

    learner_view = client.get(
        f"/courses/{course_id}/lessons/{lesson_id}/assignment", headers=learner_headers
    ).json()
    assert learner_view["my_submission"]["status"] == "graded"
    assert learner_view["my_submission"]["score"] == 90
    assert learner_view["my_submission"]["feedback"] == "Good explanation"

    resubmitted = client.post(
        f"/courses/{course_id}/lessons/{lesson_id}/assignment/submissions",
        headers=learner_headers,
        json={"answer": "Improved function with a detailed explanation."},
    )
    assert resubmitted.status_code == 200, resubmitted.text
    updated_view = client.get(
        f"/courses/{course_id}/lessons/{lesson_id}/assignment", headers=learner_headers
    ).json()["my_submission"]
    assert updated_view["status"] == "submitted"
    assert updated_view["score"] is None


def test_author_can_open_saved_lesson_quiz_for_editing(client):
    register(client, "quiz-author@example.com", "author")
    headers = login(client, "quiz-author@example.com", "author")
    course = create_course(client, headers)
    lesson = client.post(
        f"/courses/{course['id']}/lessons",
        headers=headers,
        json={"title": "First lesson", "content": "Lesson content", "position": 1},
    )
    assert lesson.status_code == 201, lesson.text
    quiz_url = f"/courses/{course['id']}/lessons/{lesson.json()['id']}/quiz"
    created = client.post(
        quiz_url,
        headers=headers,
        json={
            "title": "Lesson quiz",
            "questions": [
                {"prompt": "What is two plus two?", "choices": ["3", "4"], "correct_index": 1},
            ],
        },
    )
    assert created.status_code == 201, created.text

    editable_quiz = client.get(f"{quiz_url}/manage", headers=headers)

    assert editable_quiz.status_code == 200, editable_quiz.text
    assert editable_quiz.json()["id"] == created.json()["id"]
    assert editable_quiz.json()["questions"][0]["correct_index"] == 1


def test_quiz_locks_after_attempt_and_still_reviews_mistakes(client, monkeypatch):
    now = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)

    class QuizClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return now.astimezone(tz)

    monkeypatch.setattr(quizzes_router, "datetime", QuizClock)
    register(client, "review-author@example.com", "author")
    register(client, "review-learner@example.com")
    author = login(client, "review-author@example.com", "author")
    learner = login(client, "review-learner@example.com")
    course_id = create_course(client, author)["id"]
    course = f"/courses/{course_id}"
    lesson = client.post(
        f"{course}/lessons",
        headers=author,
        json={"title": "Addition", "content": "Add two numbers", "position": 1},
    )
    assert lesson.status_code == 201, lesson.text
    quiz = f"{course}/lessons/{lesson.json()['id']}/quiz"
    questions = [
        {
            "prompt": "Two plus two?",
            "choices": ["3", "4"],
            "correct_index": 1,
            "explanation": "  Count two more after two to reach four.  ",
        },
        {"prompt": "Two plus three?", "choices": ["5", "6"], "correct_index": 0, "points": 2},
    ]
    payload = {"title": "Addition quiz", "passing_score": 70, "questions": questions}
    assert client.post(quiz, headers=author, json=payload).status_code == 201
    assert client.post(f"{course}/publish", headers=author).status_code == 200
    assert client.get(quiz, headers=learner).status_code == 403
    assert client.post(f"{course}/enroll", headers=learner).status_code == 201
    visible_questions = client.get(quiz, headers=learner).json()["questions"]
    assert all(
        "correct_index" not in question and "explanation" not in question
        for question in visible_questions
    )
    first, second = [question["id"] for question in visible_questions]

    def send(first_answer, second_answer):
        return client.post(
            f"{quiz}/attempts",
            headers=learner,
            json={
                "answers": [
                    {"question_id": second, "selected_index": second_answer},
                    {"question_id": first, "selected_index": first_answer},
                ],
            },
        )

    invalid = send(0, 2)
    assert invalid.status_code == 422
    assert "mistakes" not in invalid.json()
    attempt = send(0, 0)
    assert attempt.status_code == 201, attempt.text
    assert attempt.json()["score_percent"] == 66.67
    assert attempt.json()["passed"] is False
    retry_at = datetime.fromisoformat(attempt.json()["attempt_lock"]["retry_at"])
    assert retry_at == now + timedelta(hours=24)
    assert attempt.json()["mistakes"] == [
        {
            "question_id": first,
            "selected_index": 0,
            "correct_index": 1,
            "explanation": "Count two more after two to reach four.",
        }
    ]
    locked = client.get(quiz, headers=learner).json()
    assert locked["attempt_lock"] == attempt.json()["attempt_lock"]
    assert locked["questions"] == []
    rejected = send(1, 0)
    assert rejected.status_code == 429
    assert rejected.headers["Retry-After"] == "86400"

    questions[0]["explanation"] = "Two pairs make four."
    updated = client.put(quiz, headers=author, json=payload)
    assert updated.status_code == 200, updated.text
    assert updated.json()["questions"][0]["id"] == first
    management = client.get(f"{quiz}/manage", headers=author)
    assert management.json()["questions"][0]["explanation"] == "Two pairs make four."
    questions[0]["correct_index"] = 0
    assert client.put(quiz, headers=author, json=payload).status_code == 409
    now = retry_at - timedelta(seconds=1)
    assert send(1, 0).status_code == 429
    now = retry_at
    assert client.get(quiz, headers=learner).json()["attempt_lock"] is None
    wrong_without_explanation = send(1, 1)
    assert wrong_without_explanation.status_code == 201
    assert wrong_without_explanation.json()["mistakes"][0]["explanation"] is None
    assert send(1, 0).status_code == 429
    now += timedelta(hours=24)
    assert send(0, 0).json()["mistakes"][0]["explanation"] == "Two pairs make four."
    now += timedelta(hours=24)
    passed = send(1, 0)
    assert passed.status_code == 201, passed.text
    assert passed.json()["attempt_lock"] == {"reason": "passed", "retry_at": None}
    assert passed.json()["mistakes"] == []
    now += timedelta(days=30)
    locked = client.get(quiz, headers=learner).json()
    assert locked["attempt_lock"] == passed.json()["attempt_lock"]
    assert locked["questions"] == []
    assert send(1, 0).status_code == 409
    history = client.get(f"{quiz}/attempts/me", headers=learner).json()
    assert len(history) == 4 and all("mistakes" not in item for item in history)


def test_course_analytics_counts_completions_and_first_incomplete_lesson(client):
    register(client, "analytics-owner@example.com", "author")
    author = login(client, "analytics-owner@example.com", "author")
    register(client, "analytics-other@example.com", "author")
    other_author = login(client, "analytics-other@example.com", "author")
    course = f"/courses/{create_course(client, author)['id']}"
    analytics_url = f"{course}/analytics"
    empty = client.get(analytics_url, headers=author).json()
    assert empty["lessons"] == []
    assert empty["started_learners"] == 0
    assert client.get(analytics_url, headers=other_author).status_code == 404

    def add_lesson(title, position):
        response = client.post(
            f"{course}/lessons",
            headers=author,
            json={"title": title, "content": "Lesson content", "position": position},
        )
        assert response.status_code == 201, response.text
        return response.json()["id"]

    last = add_lesson("Second lesson", 2)
    first = add_lesson("First lesson", 1)
    quiz_url = f"{course}/lessons/{last}/quiz"
    quiz = client.post(
        quiz_url,
        headers=author,
        json={
            "title": "Demo quiz",
            "questions": [{"prompt": "Choose yes", "choices": ["Yes", "No"], "correct_index": 0}],
        },
    )
    assert quiz.status_code == 201, quiz.text
    assert client.post(f"{course}/publish", headers=author).status_code == 200

    def enroll(name):
        email = f"analytics-{name}@example.com"
        register(client, email)
        learner = login(client, email)
        assert client.post(f"{course}/enroll", headers=learner).status_code == 201
        return learner

    def complete(learner, lesson):
        response = client.post(f"{course}/progress/lessons/{lesson}/complete", headers=learner)
        assert response.status_code == 200, response.text

    finished = enroll("finished")
    complete(finished, first)
    complete(finished, last)
    for name in ["paused", "continuing"]:
        complete(enroll(name), first)
    quiz_only = enroll("quiz")
    question_id = quiz.json()["questions"][0]["id"]
    assert (
        client.post(
            f"{quiz_url}/attempts",
            headers=quiz_only,
            json={"answers": [{"question_id": question_id, "selected_index": 1}]},
        ).status_code
        == 201
    )
    never_started = enroll("inactive")
    assert client.get(analytics_url, headers=never_started).status_code == 403

    response = client.get(analytics_url, headers=author)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["enrollment_count"] == 5
    assert result["started_learners"] == 4
    assert result["completed_learners"] == 1
    assert result["completion_rate"] == 20
    assert result["lessons"] == [
        {
            "lesson_id": first,
            "title": "First lesson",
            "position": 1,
            "completed_learners": 3,
            "next_lesson_learners": 1,
        },
        {
            "lesson_id": last,
            "title": "Second lesson",
            "position": 2,
            "completed_learners": 1,
            "next_lesson_learners": 2,
        },
    ]


def test_final_exam_requires_completed_lessons_and_certificate_is_single(client):
    register(client, "course-author@example.com", "author")
    register(client, "course-learner@example.com")
    author_headers = login(client, "course-author@example.com", "author")
    learner_headers = login(client, "course-learner@example.com")

    course = create_course(client, author_headers, "Final Exam Course")
    course_id = course["id"]
    lesson_response = client.post(
        f"/courses/{course_id}/lessons",
        headers=author_headers,
        json={"title": "First Lesson", "content": "Lesson content", "position": 1},
    )
    assert lesson_response.status_code == 201, lesson_response.text
    lesson_id = lesson_response.json()["id"]

    exam_response = client.put(
        f"/courses/{course_id}/final-exam/manage",
        headers=author_headers,
        json={
            "title": "Final Exam",
            "passing_score": 70,
            "questions": [
                {"prompt": "2 + 2?", "choices": ["3", "4"], "correct_index": 1},
                {"prompt": "Python language?", "choices": ["Yes", "No"], "correct_index": 0},
            ],
        },
    )
    assert exam_response.status_code == 200, exam_response.text
    assert client.post(f"/courses/{course_id}/publish", headers=author_headers).status_code == 200
    assert client.post(f"/courses/{course_id}/enroll", headers=learner_headers).status_code == 201

    blocked_exam = client.get(f"/courses/{course_id}/final-exam", headers=learner_headers)
    assert blocked_exam.status_code == 409
    completed = client.post(
        f"/courses/{course_id}/progress/lessons/{lesson_id}/complete",
        headers=learner_headers,
    )
    assert completed.status_code == 200, completed.text

    exam = client.get(f"/courses/{course_id}/final-exam", headers=learner_headers)
    assert exam.status_code == 200, exam.text
    question_ids = [question["id"] for question in exam.json()["questions"]]
    incomplete_attempt = client.post(
        f"/courses/{course_id}/final-exam/attempts",
        headers=learner_headers,
        json={"answers": [{"question_id": question_ids[0], "selected_index": 1}]},
    )
    assert incomplete_attempt.status_code == 422

    attempt = client.post(
        f"/courses/{course_id}/final-exam/attempts",
        headers=learner_headers,
        json={
            "answers": [
                {"question_id": question_ids[0], "selected_index": 1},
                {"question_id": question_ids[1], "selected_index": 0},
            ]
        },
    )
    assert attempt.status_code == 201, attempt.text
    assert attempt.json()["passed"] is True
    assert attempt.json()["score_percent"] == 100

    incorrect_attempt = client.post(
        f"/courses/{course_id}/final-exam/attempts",
        headers=learner_headers,
        json={
            "answers": [
                {"question_id": question_ids[0], "selected_index": 0},
                {"question_id": question_ids[1], "selected_index": 1},
            ]
        },
    )
    assert incorrect_attempt.status_code == 201, incorrect_attempt.text
    assert incorrect_attempt.json()["correct_count"] == 0
    assert incorrect_attempt.json()["score_percent"] == 0
    assert incorrect_attempt.json()["passed"] is False

    certificate_url = f"/courses/{course_id}/certificate"
    first_certificate = client.post(certificate_url, headers=learner_headers)
    second_certificate = client.post(certificate_url, headers=learner_headers)
    assert first_certificate.status_code == 200, first_certificate.text
    assert second_certificate.status_code == 200, second_certificate.text
    assert first_certificate.json()["id"] == second_certificate.json()["id"]


def test_video_lesson_cannot_be_completed_by_seeking_past_end(client):
    register(client, "video-author@example.com", "author")
    register(client, "video-learner@example.com")
    author_headers = login(client, "video-author@example.com", "author")
    learner_headers = login(client, "video-learner@example.com")
    course = create_course(client, author_headers, "Video Course")
    course_id = course["id"]

    lesson = client.post(
        f"/courses/{course_id}/lessons",
        headers=author_headers,
        json={
            "title": "Video Lesson",
            "content": "Watch the course video",
            "resource_type": "video",
            "external_video_url": "https://www.youtube.com/watch?v=abc123",
            "position": 1,
        },
    )
    assert lesson.status_code == 201, lesson.text
    lesson_id = lesson.json()["id"]
    assert client.post(f"/courses/{course_id}/publish", headers=author_headers).status_code == 200
    assert client.post(f"/courses/{course_id}/enroll", headers=learner_headers).status_code == 201

    incomplete = client.post(
        f"/courses/{course_id}/progress/lessons/{lesson_id}/complete",
        headers=learner_headers,
    )
    assert incomplete.status_code == 409

    seek_past_end = client.post(
        f"/courses/{course_id}/progress/lessons/{lesson_id}/video-watch",
        headers=learner_headers,
        json={"position_seconds": 13, "duration_seconds": 10, "ended": True},
    )
    assert seek_past_end.status_code == 422


def test_video_resume_reports_first_unfinished_item_and_contiguous_position(client, monkeypatch):
    register(client, "resume-author@example.com", "author")
    register(client, "resume-learner@example.com")
    author = login(client, "resume-author@example.com", "author")
    learner = login(client, "resume-learner@example.com")
    course_id = create_course(client, author, "Playlist Course")["id"]
    course_url = f"/courses/{course_id}"
    lesson = client.post(
        f"{course_url}/lessons",
        headers=author,
        json={
            "title": "Playlist lesson",
            "content": "Watch both playlist items",
            "resource_type": "video",
            "external_video_url": "https://www.youtube.com/playlist?list=PL123456789",
            "position": 1,
        },
    )
    assert lesson.status_code == 201, lesson.text
    assert client.post(f"{course_url}/publish", headers=author).status_code == 200
    assert client.post(f"{course_url}/enroll", headers=learner).status_code == 201
    lesson_url = f"{course_url}/progress/lessons/{lesson.json()['id']}"
    video_url = f"{lesson_url}/video-watch"
    timestamp = datetime(2026, 11, 21, tzinfo=timezone.utc)

    class PlaybackClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return timestamp.astimezone(tz) if tz else timestamp.replace(tzinfo=None)

    monkeypatch.setattr(progress_router, "datetime", PlaybackClock)

    def report(index, position, elapsed=0, ended=False):
        nonlocal timestamp
        timestamp += timedelta(seconds=elapsed)
        response = client.post(
            video_url,
            headers=learner,
            json={
                "item_index": index,
                "item_count": 2,
                "position_seconds": position,
                "duration_seconds": 10,
                "ended": ended,
            },
        )
        assert response.status_code == 200, response.text
        return response.json()

    assert report(0, 0)["resume_item_index"] == 0
    before_second_item = report(0, 10, elapsed=10, ended=True)
    assert before_second_item["resume_item_index"] == 1
    assert before_second_item["resume_position_seconds"] == 0
    report(1, 0)
    report(1, 4, elapsed=4)
    skipped = report(1, 10, ended=True)
    assert skipped["can_complete"] is False
    reopened = client.get(video_url, headers=learner).json()
    assert reopened["furthest_position_seconds"] == 10
    assert reopened["resume_item_index"] == 1
    assert reopened["resume_position_seconds"] == 4

    report(1, 4)
    finished = report(1, 10, elapsed=6, ended=True)
    assert finished["resume_item_index"] is None
    assert finished["can_complete"] is True
    assert client.post(f"{lesson_url}/complete", headers=learner).status_code == 200


def test_ordered_lesson_materials_are_private_managed_and_visible_to_enrolled_learners(client):
    register(client, "materials-author@example.com", "author")
    register(client, "materials-outsider@example.com", "author")
    register(client, "materials-learner@example.com")
    author_headers = login(client, "materials-author@example.com", "author")
    outsider_headers = login(client, "materials-outsider@example.com", "author")
    learner_headers = login(client, "materials-learner@example.com")
    course = create_course(client, author_headers, "Materials course")
    course_id = course["id"]
    lesson_response = client.post(
        f"/courses/{course_id}/lessons",
        headers=author_headers,
        json={"title": "Reading lesson", "content": "Read the notes", "position": 1},
    )
    assert lesson_response.status_code == 201, lesson_response.text
    lesson_id = lesson_response.json()["id"]
    first = client.post(
        f"/courses/{course_id}/lessons/{lesson_id}/materials?title=First%20notes",
        headers={**author_headers, "Content-Type": "application/pdf"},
        content=b"%PDF-1.4 first notes",
    )
    second = client.post(
        f"/courses/{course_id}/lessons/{lesson_id}/materials?title=Second%20notes",
        headers={**author_headers, "Content-Type": "application/pdf"},
        content=b"%PDF-1.4 second notes",
    )
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert (
        client.post(
            f"/courses/{course_id}/lessons/{lesson_id}/materials?title=Blocked",
            headers={**outsider_headers, "Content-Type": "application/pdf"},
            content=b"%PDF-1.4 blocked",
        ).status_code
        == 404
    )
    assert client.post(f"/courses/{course_id}/publish", headers=author_headers).status_code == 200
    assert client.post(f"/courses/{course_id}/enroll", headers=learner_headers).status_code == 201
    learner_lessons = client.get(
        f"/courses/{course_id}/lessons?language=uz",
        headers=learner_headers,
    )
    assert learner_lessons.status_code == 200, learner_lessons.text
    materials = learner_lessons.json()[0]["materials"]
    assert [item["title"] for item in materials] == ["First notes", "Second notes"]
    downloaded = client.get(materials[0]["resource_url"])
    assert downloaded.status_code == 200
    assert downloaded.content == b"%PDF-1.4 first notes"

    reordered = client.put(
        f"/courses/{course_id}/lessons/{lesson_id}/materials/{second.json()['id']}/position?position=1",
        headers=author_headers,
    )
    assert reordered.status_code == 200, reordered.text
    assert reordered.json()["position"] == 1
    removed = client.delete(
        f"/courses/{course_id}/lessons/{lesson_id}/materials/{second.json()['id']}",
        headers=author_headers,
    )
    assert removed.status_code == 204
    after_delete = client.get(
        f"/courses/{course_id}/lessons?language=uz", headers=learner_headers
    ).json()[0]["materials"]
    assert [(item["title"], item["position"]) for item in after_delete] == [("First notes", 1)]


def test_email_password_reset_accepts_new_password_and_rejects_reused_link(client, monkeypatch):
    register(client, "reset-user@example.com")
    sent_messages = []

    class FakeSMTP:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def starttls(self):
            return None

        def login(self, *_args):
            return None

        def send_message(self, message):
            sent_messages.append(message)

    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USERNAME", "studyflow@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "test-app-password")
    monkeypatch.setenv("SMTP_FROM", "studyflow@example.com")
    monkeypatch.setattr(auth_router.smtplib, "SMTP", FakeSMTP)

    request = client.post(
        "/auth/password-reset/request",
        json={"email": "reset-user@example.com"},
    )
    assert request.status_code == 200, request.text
    assert len(sent_messages) == 1

    reset_url = re.search(r"https?://\S+", sent_messages[0].get_content()).group(0)
    reset_token = parse_qs(urlparse(reset_url).query)["token"][0]
    reset = client.post(
        "/auth/password-reset/confirm",
        json={"token": reset_token, "new_password": "reset-password-43"},
    )
    assert reset.status_code == 200, reset.text

    old_password = client.post(
        "/auth/login",
        json={"email": "reset-user@example.com", "password": "correct-horse-42"},
    )
    new_password = client.post(
        "/auth/login",
        json={"email": "reset-user@example.com", "password": "reset-password-43"},
    )
    assert old_password.status_code == 401
    assert new_password.status_code == 200

    reused_link = client.post(
        "/auth/password-reset/confirm",
        json={"token": reset_token, "new_password": "another-password-44"},
    )
    assert reused_link.status_code == 400

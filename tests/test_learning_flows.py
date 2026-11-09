import re
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.routers import auth as auth_router
from app.routers import passkeys as passkeys_router
from tests.helpers import login, register


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
        return Request({
            "type": "http", "method": "POST", "path": "/auth/passkeys/options",
            "scheme": "http", "server": ("127.0.0.1", 8000), "client": ("127.0.0.1", 12345),
            "headers": [(b"origin", origin.encode("ascii"))],
        })

    assert passkeys_router._request_webauthn_scope(request_for("http://localhost:8000")) == (
        "localhost", "http://localhost:8000"
    )
    with pytest.raises(HTTPException) as error:
        passkeys_router._request_webauthn_scope(request_for("http://127.0.0.1:8000"))
    assert error.value.status_code == 400
    assert "http://localhost:8000/app" in error.value.detail


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
    assert client.post("/courses", headers=learner_headers, json={"title": "No author role"}).status_code == 403
    assert client.post(f"/courses/{course_id}/enroll", headers=learner_headers).status_code == 404

    assert client.post(f"/courses/{course_id}/publish", headers=owner_headers).status_code == 200
    enrolled = client.post(f"/courses/{course_id}/enroll", headers=learner_headers)
    assert enrolled.status_code == 201, enrolled.text
    assert client.post(f"/courses/{course_id}/enroll", headers=learner_headers).status_code == 409

    paid_course = create_course(client, owner_headers, "Paid Python", price_uzs=1000)
    assert client.post(f"/courses/{paid_course['id']}/publish", headers=owner_headers).status_code == 200
    payment_required = client.post(f"/courses/{paid_course['id']}/enroll", headers=learner_headers)
    assert payment_required.status_code == 402

    english_course = create_course(client, owner_headers, "English Python", language="en")
    assert client.post(f"/courses/{english_course['id']}/publish", headers=owner_headers).status_code == 200
    english_catalog = client.get("/courses/catalog?language=en").json()
    uzbek_catalog = client.get("/courses/catalog?language=uz").json()
    assert english_course["id"] in {item["id"] for item in english_catalog}
    assert english_course["id"] not in {item["id"] for item in uzbek_catalog}


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

    assert client.delete(
        f"/courses/{course_id}/modules/{module_id}", headers=author_headers
    ).status_code == 204
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
        json={"title": "Function task", "instructions": "Write a function and explain it.", "max_score": 100},
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
        f"/courses/{course_id}/lessons", headers=author_headers,
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
    assert client.post(
        f"/courses/{course_id}/lessons/{lesson_id}/materials?title=Blocked",
        headers={**outsider_headers, "Content-Type": "application/pdf"},
        content=b"%PDF-1.4 blocked",
    ).status_code == 404
    assert client.post(f"/courses/{course_id}/publish", headers=author_headers).status_code == 200
    assert client.post(f"/courses/{course_id}/enroll", headers=learner_headers).status_code == 201
    learner_lessons = client.get(
        f"/courses/{course_id}/lessons?language=uz", headers=learner_headers,
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
    after_delete = client.get(f"/courses/{course_id}/lessons?language=uz", headers=learner_headers).json()[0]["materials"]
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

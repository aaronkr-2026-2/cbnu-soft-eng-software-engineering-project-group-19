from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from importlib import import_module
from io import BytesIO
from uuid import UUID

import pytest
from pypdf import PdfReader

from app.core.catalog_art import render_subject_banner
from app.database import get_db
from app.models import Course, Lesson
from app.routers import progress
from migrations.academy_video_content import IT_COURSES, video_key
from migrations.language_starters import COPY, LESSONS, PHRASES, USAGE
from tests.helpers import login, register

seed_language_courses = import_module(
    "migrations.versions.74ac7b2de641_language_starter_catalog"
).seed_language_courses
attach_bundled_videos = import_module(
    "migrations.versions.8cde17f45a20_academy_lesson_videos"
).attach_bundled_videos

LANGUAGE_PAIRS = [(source, target) for source in USAGE for target in USAGE[source]]


@pytest.mark.parametrize(("source", "target"), LANGUAGE_PAIRS)
def test_language_course_can_award_a_localized_certificate(client, source, target, monkeypatch):
    with contextmanager(client.app.dependency_overrides[get_db])() as db:
        seed_language_courses(db.connection())
        seed_language_courses(db.connection())
        attach_bundled_videos(db.connection())
        db.commit()

    category = COPY[source]["category"]
    catalog = client.get("/courses/catalog", params={"language": source, "q": category})
    assert catalog.status_code == 200
    assert {entry["title"] for entry in catalog.json()} == {
        COPY[source]["titles"][language] for language in USAGE[source]
    }
    title = COPY[source]["titles"][target]
    course = next(entry for entry in catalog.json() if entry["title"] == title)
    assert course["display_language"] == source and course["price_uzs"] == 0
    cover = client.get(course["banner_url"])
    assert cover.status_code == 200
    assert {"uz": "Salom!", "en": "Hello!", "ru": "Привет!", "ko": "안녕하세요!"}[
        target
    ] in cover.text
    assert len({client.get(entry["banner_url"]).content for entry in catalog.json()}) == 3

    course_path = f"/courses/{course['id']}"
    outline = client.get(
        f"/courses/catalog/{course['id']}/outline", params={"language": source}
    ).json()
    assert [lesson["title"] for lesson in outline["lessons"]] == [row[source][0] for row in LESSONS]
    email = "language-learner@example.com"
    register(client, email)
    learner = login(client, email)
    assert client.post(f"{course_path}/enroll", headers=learner).status_code == 201
    exam_url = f"{course_path}/final-exam"
    cert_url = f"{course_path}/certificate"
    assert client.get(exam_url, headers=learner).status_code == 409
    assert client.post(cert_url, headers=learner).status_code == 409

    lessons = client.get(f"{course_path}/lessons", headers=learner, params={"lang": source}).json()
    assert len(lessons) == 3
    timestamp = datetime(2026, 11, 27, tzinfo=UTC)

    class PlaybackClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return timestamp.astimezone(tz) if tz else timestamp.replace(tzinfo=None)

    monkeypatch.setattr(progress, "datetime", PlaybackClock)
    for unit, lesson in enumerate(lessons):
        assert PHRASES[unit][target][0] in lesson["content"]
        assert PHRASES[unit][source][0] in lesson["content"]
        assert lesson["resource_type"] == "video"
        media_url = lesson["resource_url"]
        assert client.get(media_url.split("?")[0] + "?token=invalid").status_code == 401
        clip = client.get(media_url, headers={"Range": "bytes=0-31"})
        assert clip.status_code == 206 and clip.headers["content-type"] == "video/mp4"
        assert len(clip.content) == 32 and clip.content[4:8] == b"ftyp"
        progress_url = f"{course_path}/progress/lessons/{lesson['id']}"
        assert client.post(f"{progress_url}/complete", headers=learner).status_code == 409
        watch = f"{progress_url}/video-watch"
        assert (
            client.post(
                watch, headers=learner, json={"position_seconds": 0, "duration_seconds": 40}
            ).status_code
            == 200
        )
        timestamp += timedelta(seconds=40)
        played = client.post(
            watch,
            headers=learner,
            json={"position_seconds": 40, "duration_seconds": 40, "ended": True},
        )
        assert played.status_code == 200 and played.json()["can_complete"]
        quiz_url = f"{course_path}/lessons/{lesson['id']}/quiz"
        quiz = client.get(quiz_url, headers=learner, params={"lang": source}).json()
        questions = quiz["questions"]
        assert len(questions) == 4 and quiz["title"] == COPY[source]["quiz"]
        answers = [
            {
                "question_id": question["id"],
                "selected_index": question["choices"].index(PHRASES[unit][source][index]),
            }
            for index, question in enumerate(questions)
        ]
        attempt = client.post(f"{quiz_url}/attempts", headers=learner, json={"answers": answers})
        assert attempt.status_code == 201
        assert attempt.json()["passed"]
        assert (
            client.post(
                f"{course_path}/progress/lessons/{lesson['id']}/complete", headers=learner
            ).status_code
            == 200
        )

    assert client.post(cert_url, headers=learner).status_code == 409
    exam = client.get(exam_url, headers=learner, params={"lang": source}).json()
    assert exam["title"] == COPY[source]["exam"] and exam["passing_score"] == 75
    assert len(exam["questions"]) == 12
    answers = [
        {
            "question_id": question["id"],
            "selected_index": question["choices"].index(PHRASES[index // 4][target][index % 4 + 2]),
        }
        for index, question in enumerate(exam["questions"])
    ]
    assert client.post(f"{exam_url}/attempts", headers=learner, json={"answers": answers}).json()[
        "passed"
    ]
    certificate = client.post(cert_url, headers=learner, params={"lang": source}).json()
    assert certificate["course_title"] == title
    code = certificate["certificate_code"]
    for language, translation in COPY.items():
        expected_title = translation["titles"][target]
        verification = client.get(f"/certificates/verify/{code}", params={"lang": language})
        assert verification.json()["course_title"] == expected_title
        download = client.get(f"/certificates/verify/{code}/pdf", params={"lang": language})
        assert download.status_code == 200
        page = PdfReader(BytesIO(download.content)).pages[0]
        assert expected_title in " ".join(page.extract_text().split())
        links = {link.get_object()["/A"]["/URI"] for link in page["/Annots"]}
        assert links == {
            f"https://scholward-academy.vercel.app/app/verify.html?code={code}&lang={language}"
        }


def test_preserves_existing_it_video_and_fills_empty_lessons(client):
    author = register(client, "coding-instructor@example.com", "author")
    course_id = UUID(IT_COURSES["ko"]["python"])
    with contextmanager(client.app.dependency_overrides[get_db])() as db:
        course = Course(
            id=course_id, owner_id=UUID(author["id"]), title="파이썬 기초", language="ko"
        )
        db.add(course)
        db.flush()
        external = Lesson(
            course_id=course_id,
            position=1,
            title="기존 동영상",
            content="동영상 강의",
            resource_type="video",
            external_video_url="https://www.youtube.com/watch?v=abc12345678",
        )
        unfilled = Lesson(
            course_id=course_id, position=2, title="조건문", content="수업", resource_type="text"
        )
        db.add_all([external, unfilled])
        db.flush()
        attach_bundled_videos(db.connection())
        db.refresh(external)
        db.refresh(unfilled)
        assert external.external_video_url.endswith("abc12345678") and external.resource_key is None
        assert unfilled.resource_key == video_key("python", "ko", 2)
        assert unfilled.resource_type == "video" and unfilled.resource_mime_type == "video/mp4"
        assert "프로그래밍" in render_subject_banner(course).decode()

from contextlib import contextmanager
from importlib import import_module
from io import BytesIO

import pytest
from pypdf import PdfReader

from app.database import get_db
from migrations.language_starters import COPY, LESSONS, PHRASES, USAGE
from tests.helpers import login, register

seed_language_courses = import_module(
    "migrations.versions.74ac7b2de641_language_starter_catalog"
).seed_language_courses

LANGUAGE_PAIRS = [(source, target) for source in USAGE for target in USAGE[source]]


@pytest.mark.parametrize(("source", "target"), LANGUAGE_PAIRS)
def test_language_course_can_award_a_localized_certificate(client, source, target):
    with contextmanager(client.app.dependency_overrides[get_db])() as db:
        seed_language_courses(db.connection())
        seed_language_courses(db.connection())
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
    assert client.get(course["banner_url"]).status_code == 200

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
    for unit, lesson in enumerate(lessons):
        assert PHRASES[unit][target][0] in lesson["content"]
        assert PHRASES[unit][source][0] in lesson["content"]
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

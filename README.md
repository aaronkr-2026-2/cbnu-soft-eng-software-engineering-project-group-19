# StudyFlow AI

StudyFlow AI is a multilingual learning platform where learners can discover courses, enroll, study lessons, track progress, take lesson quizzes and a course final exam, and receive a verifiable completion certificate. The interface supports Uzbek, English, Russian, and Korean.

## Product vision

For independent learners who need a clear path from choosing a course to proving what they learned, StudyFlow AI provides structured lessons, progress tracking, knowledge checks, and verifiable certificates in four languages. Unlike a static course list, it connects learning activity with a final assessment and a public certificate verification page.

## Current product

- Account registration and login, course catalog, enrollment, lessons, and progress tracking.
- Course recommendations and personal study plans.
- Course authoring, lesson quizzes, final exams, and course analytics.
- Learner profile editing and four-language interface.
- Unique certificate verification codes and public verification page.
- Device passkey verification before final exam submission and first certificate issuance.

This repository is the working course project. No public cloud deployment URL is recorded here yet. The Week 7 cloud deployment milestone must be confirmed and documented separately before claiming it is complete.

## Technology

- Backend: Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL.
- Frontend: plain HTML, CSS, and JavaScript served by FastAPI.
- Authentication: JWT-based account authentication; WebAuthn passkeys for step-up verification.

## Run locally

Requirements: Python 3.11 or newer and a local PostgreSQL server with a database named `studyflow_db`.

```sh
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set a private `SECRET_KEY` in `backend/.env`. Start PostgreSQL and create the `studyflow_db` database, then run the migrations and server:

```sh
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000/app>. API documentation is available at <http://127.0.0.1:8000/docs>.

The current database connection is configured in `backend/app/database.py` for local PostgreSQL. Review and externalize this setting before deploying to a cloud database. For passkeys, set `WEBAUTHN_RP_ID` and `WEBAUTHN_ORIGIN` to the deployed domain and HTTPS origin on the production host.

## Course milestones through Week 9

- Week 2: idea and stack are documented; add the actual team roster/roles before submission.
- Week 3: working MVP and product vision are described; attach a public demo URL when deployed.
- Week 4: retrospective personas and user stories are in `docs/personas-and-user-stories.md`.
- Week 5: the proposed lightweight process is in `docs/agile-process.md`; it is explicitly a retrofit, not a claim of earlier Scrum practice.
- Week 6: architecture and design critique are in `docs/architecture-and-critique.md`.
- Week 7: cloud redeployment is not evidenced by this repository; add host, URL, deployment date, and verification before marking complete.
- Week 8: midterm review checkpoint.
- Week 9: decomposition decision is in `docs/decomposition-review.md`.

## Project documentation

See `docs/` for the milestone artifacts. `AI_LOG.md` records AI assistance and remaining items that need the student's own confirmation. The project should only be submitted after reviewing the code and documentation and filling in personal/team details.

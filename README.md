# StudyFlow AI

<p align="center">
  <a href="https://github.com/aaronkr-2026-2/cbnu-soft-eng-software-engineering-project-group-19">
    <img src="docs/assets/studyflow-logo.svg" alt="StudyFlow AI logo" width="480" />
  </a>
</p>

<p align="center">
  <a href="https://deepwiki.com/aaronkr-2026-2/cbnu-soft-eng-software-engineering-project-group-19"><img alt="Ask DeepWiki" src="https://img.shields.io/badge/DeepWiki-Ask-blue"></a>
  <a href="https://github.com/aaronkr-2026-2/cbnu-soft-eng-software-engineering-project-group-19"><img alt="GitHub repository" src="https://img.shields.io/badge/GitHub-StudyFlow_AI-181717?logo=github&logoColor=white"></a>
</p>

StudyFlow AI is a multilingual learning platform for independent learners, course authors, and organizations that verify course certificates. It brings course discovery, structured lessons, progress tracking, assessments, and certificate verification into one learning flow.

**Local demo:** Follow [requirements and quick start](#requirements-and-quick-start). A public cloud deployment URL is not available yet.

The backend uses FastAPI, SQLAlchemy, Alembic, and PostgreSQL. The frontend is a responsive, dependency-free HTML/CSS/JavaScript app served by FastAPI at `/app`. Learners can use the interface in Uzbek, English, Russian, or Korean.

<p align="center">
  <a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white"></a>
  <a href="https://fastapi.tiangolo.com/"><img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white"></a>
  <a href="https://www.postgresql.org/"><img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white"></a>
  <a href="https://www.sqlalchemy.org/"><img alt="SQLAlchemy" src="https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white"></a>
  <a href="https://developer.mozilla.org/en-US/docs/Web/JavaScript"><img alt="JavaScript" src="https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black"></a>
  <a href="https://developer.mozilla.org/en-US/docs/Web/HTML"><img alt="HTML5" src="https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white"></a>
  <a href="https://developer.mozilla.org/en-US/docs/Web/CSS"><img alt="CSS3" src="https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white"></a>
</p>

## Contents

- [Existing features list](#existing-features-list)
- [Requirements and quick start](#requirements-and-quick-start)
- [Environment configuration](#environment-configuration)
- [API documentation and status](#api-documentation-and-status)
- [Development and testing](#development-and-testing)
- [Architecture](#architecture)
- [Account authentication and passkeys](#account-authentication-and-passkeys)
- [Learner profiles](#learner-profiles)
- [Courses, lessons, and progress](#courses-lessons-and-progress)
- [Quizzes and final exams](#quizzes-and-final-exams)
- [Certificates and public verification](#certificates-and-public-verification)
- [Course reviews and analytics](#course-reviews-and-analytics)
- [Deployment](#deployment)
- [Known limitations](#known-limitations)
- [Project records](#project-records)

## Existing features list

- **Accounts:** Registration, login, JWT bearer tokens, password changes, and authenticated profile endpoints.
- **Four-language UI:** Uzbek, English, Russian, and Korean interface copy.
- **Course catalog:** Browse and preview published courses and their lesson outlines before enrolling.
- **Learning progress:** Enroll in courses, read lessons, mark lessons complete, and view course progress.
- **Personal study tools:** Course recommendations and generated learning plans.
- **Course authoring:** Create, edit, publish, and unpublish courses; manage lessons and lesson quizzes.
- **Assessment:** Take lesson quizzes, review prior attempts, and take a final exam after completing course lessons. A passing final exam requires 70% or higher.
- **Certificates:** Passing the final exam unlocks a uniquely coded certificate that can be printed or saved as a PDF.
- **Public certificate checks:** Anyone can verify a certificate code without an account; the result comes from the certificate record in the database.
- **Step-up security:** Device passkeys are required before final-exam submission and first certificate issuance. The device may use a PIN, fingerprint, or face verification; the site does not receive biometric data or learn which device method was used.
- **Profile:** Edit profile details and upload a profile image.
- **Reviews and analytics:** Learners can rate completed courses; authors can view course enrollment, completion, rating, and final-exam statistics.

## Requirements and quick start

Use Python 3.11 or newer and a local PostgreSQL server. The app currently expects a database named `studyflow_db` at the local PostgreSQL connection configured in `backend/app/database.py`.

From the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set a strong, private `SECRET_KEY` in `backend/.env`. Start PostgreSQL and create the database:

```bash
createdb studyflow_db
```

Run migrations and start the backend from `backend/`:

```bash
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open the [StudyFlow AI web app](http://127.0.0.1:8000/app), [API docs](http://127.0.0.1:8000/docs), or [health check](http://127.0.0.1:8000/health).

## Environment configuration

`backend/app/core/security.py` loads the `.env` file from the backend working directory. Never commit a real `.env` file or production secrets.

| Setting | Purpose | Local default or requirement |
|---|---|---|
| `SECRET_KEY` | Signs JWT access tokens | Required; replace `change-me` with a private random value |
| `WEBAUTHN_RP_ID` | WebAuthn relying-party domain | `127.0.0.1` locally |
| `WEBAUTHN_RP_NAME` | Name shown in the device passkey prompt | `StudyFlow AI` |
| `WEBAUTHN_ORIGIN` | Exact origin accepted for passkey verification | `http://127.0.0.1:8000` locally |
| Database URL | PostgreSQL connection | Currently hard-coded in `backend/app/database.py` as `postgresql+psycopg://localhost/studyflow_db` |

For production, configure the database URL through an environment variable, use HTTPS, and set the WebAuthn relying-party ID and origin to the real domain.

## API documentation and status

With the local server running:

| URL | Purpose |
|---|---|
| [`/docs`](http://127.0.0.1:8000/docs) | Interactive Swagger UI |
| [`/openapi.json`](http://127.0.0.1:8000/openapi.json) | OpenAPI schema |
| [`/health`](http://127.0.0.1:8000/health) | Basic health check |
| [`/app`](http://127.0.0.1:8000/app) | Web application |
| [`/app/verify.html`](http://127.0.0.1:8000/app/verify.html) | Public certificate verification page |

Protected routes require the JWT access token returned by `/auth/login`. Use **Authorize** in Swagger and enter the bearer token.

## Development and testing

Frontend JavaScript syntax can be checked with Node.js:

```bash
node --check apps/web/app.js
node --check apps/web/verify.js
```

Python application and migration modules can be syntax-checked with:

```bash
cd backend
python -m compileall -q app migrations
```

There is not yet a committed automated test suite or continuous-integration workflow. The checks above verify syntax only; they do not replace API or browser acceptance tests.

## Architecture

StudyFlow AI is a modular monolith. One FastAPI process serves the static frontend and API routes. Feature routers share SQLAlchemy models and a PostgreSQL database; Alembic tracks schema changes.

```text
Browser: HTML, CSS, JavaScript
              │ JSON API / WebAuthn
              ▼
        FastAPI application
        ├── Authentication & passkeys
        ├── Courses, lessons & progress
        ├── Quizzes, exams & certificates
        ├── Recommendations & study plans
        └── Reviews & analytics
              │
              ▼
          PostgreSQL
```

See the [architecture diagram and critique](docs/architecture-and-critique.md) for tradeoffs and deployment risks. The project keeps a modular monolith because the current scale and team setup do not justify microservices; see the [Week 9 decomposition review](docs/decomposition-review.md).

## Account authentication and passkeys

The `/auth` REST routes support registration and login with JWT bearer tokens. Authenticated users can view and update their account details, update their profile image, and change their password.

The `/auth/passkeys` routes register a device passkey and perform user verification before a final exam or the first issuance of a certificate. WebAuthn verifies the challenge and user-verification flag; it does not tell StudyFlow AI whether the device used its PIN, fingerprint, or face method.

See Swagger for request and response schemas, or the [passkey implementation](backend/app/routers/passkeys.py).

## Learner profiles

Learners can edit their name and optional profile details and upload a profile photo. The avatar endpoint requires account authentication. Profile fields are documented in [the profile schemas](backend/app/core/schemes/user.py).

## Courses, lessons, and progress

Published courses appear in the public catalog. Learners can preview course descriptions and lesson outlines, enroll, read course lessons, and mark lessons complete. The dashboard shows current course and lesson progress, recommendations, study plans, and course completion status.

Course authors manage their courses and lessons through authenticated endpoints and can publish or unpublish a course. Course and lesson routes are grouped under `/courses`.

## Quizzes and final exams

Authors can attach multi-question quizzes to lessons. Learners can submit quiz attempts and review their own results. After required lessons are completed, the final exam assembles questions from lesson quizzes. A pass mark of 70% is required for certificate eligibility, and the final-exam submission requires a fresh passkey verification proof.

## Certificates and public verification

A learner who passes the final exam can request a course certificate. New issuance requires a fresh passkey verification proof. Existing certificates can be viewed from the learner account.

Each certificate has a unique verification code and a public verification link. The page at `/app/verify.html` works without an account and checks the submitted code against the database. A code is reported valid only when a corresponding certificate record exists.

## Course reviews and analytics

Enrolled learners can submit or update a 1–5 star review after completing a course. Public course previews show the rating summary. Course authors can view enrollment, completion, rating, and final-exam pass statistics for courses they own.

## Deployment

The repository currently documents and supports local development. A public cloud deployment URL and host configuration have not been recorded yet, so this project page does not claim a live production site.

Before deploying, externalize the database URL, configure secrets on the host, apply Alembic migrations, set WebAuthn to the production HTTPS origin, and verify `/health`, authentication, learning flows, and certificate verification. Keep user-uploaded profile images on storage that persists across redeploys.

## Known limitations

- No public cloud deployment is documented yet.
- Database connection configuration is hard-coded for local PostgreSQL and should be externalized before deployment.
- No automated test suite or CI workflow is committed yet.
- Profile image storage and operational monitoring need a persistent production plan.
- The personas are retrospective product assumptions, not findings from completed interviews.
- Team member names and roles were not available in the supplied files and should be added if required for the course submission.

## Project records

| Course milestone | Project record |
|---|---|
| Weeks 2–3: idea, stack, and vision | [Pitch and product vision](docs/vision-and-pitch.md) |
| Week 4: personas and stories | [Personas and user stories](docs/personas-and-user-stories.md) |
| Week 5: Agile/Scrum retrofit | [Lightweight Agile process](docs/agile-process.md) |
| Week 6: architecture | [Architecture and critique](docs/architecture-and-critique.md) |
| Week 7: cloud deployment | Pending; add host, public URL, migration process, and health-check evidence |
| Week 8: midterm | Review checkpoint |
| Week 9: decomposition | [Microservices discussion](docs/decomposition-review.md) |
| AI-assisted project work | [AI collaboration log](AI_LOG.md) |

The AI collaboration log should be reviewed and completed honestly by the student before each submission.

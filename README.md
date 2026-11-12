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

**Local demo:** Follow [requirements and quick start](#requirements-and-quick-start). A public cloud deployment URL is not available yet; see the current [deployment status](docs/deployment.md).

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
- [API route reference](#api-route-reference)
- [Example API calls](#example-api-calls)
- [Learner and author workflows](#learner-and-author-workflows)
- [Data model overview](#data-model-overview)
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

- **Accounts:** Registration, login, JWT bearer tokens, password changes, forgot-password email links, and authenticated profile endpoints.
- **Four-language UI:** Uzbek, English, Russian, and Korean interface copy.
- **Course catalog:** Browse and preview published courses and their lesson outlines before enrolling.
- **Learning progress:** Enroll in courses, read lessons, mark lessons complete, and view course progress.
- **Personal study tools:** Course recommendations and generated learning plans.
- **Course authoring:** Create courses with ordered modules and lessons. Assign lessons to modules, manage the course outline, and add lesson materials, quizzes, and written assignments.
- **Assignments:** Learners submit written work for enrolled courses; authors review submissions, give feedback, and award points.
- **Assessment:** Take lesson quizzes, review prior attempts, and take an author-configured final exam after completing course lessons. The pass mark defaults to 70% and can be changed by the author.
- **Certificates:** Passing the final exam unlocks a uniquely coded certificate that can be printed or saved as a PDF.
- **Public certificate checks:** Anyone can verify a certificate code without an account; the result comes from the certificate record in the database.
- **Step-up security:** Device passkeys are required before final-exam submission and first certificate issuance. The device may use a PIN, fingerprint, or face verification; the site does not receive biometric data or learn which device method was used.
- **Profile:** Edit profile details and upload a profile image.
- **Reviews and analytics:** Learners can rate completed courses; authors can view course enrollment, completion, rating, and final-exam statistics.

## Requirements and quick start

Use Python 3.11 or newer and a local PostgreSQL server. By default, the app connects to the local `studyflow_db` database; set `DATABASE_URL` in `backend/.env` to use a different database.

From the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
test -f .env || cp .env.example .env
```

Keep any existing `backend/.env` so its secret and SMTP settings are not overwritten. Replace the example `SECRET_KEY` with a strong private value. Start the PostgreSQL service first; then create the database once (skip this if it already exists):

```bash
createdb studyflow_db
```

Run the migration from `backend/`:

```bash
alembic upgrade head
```

Start the backend as a separate command, still from `backend/`:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Use `localhost` for local passkeys. If the app is opened through `127.0.0.1`, it redirects to `localhost` because passkey credentials are tied to the site hostname. Open the [StudyFlow AI web app](http://localhost:8000/app), [API docs](http://localhost:8000/docs), or [health check](http://localhost:8000/health).

## Environment configuration

`backend/app/core/security.py` loads the `.env` file from the backend working directory. Never commit a real `.env` file or production secrets.

| Setting | Purpose | Local default or requirement |
|---|---|---|
| `SECRET_KEY` | Signs JWT access tokens | Required; use a private random value of at least 32 bytes |
| `WEBAUTHN_RP_ID` | WebAuthn relying-party domain | `localhost` locally |
| `WEBAUTHN_RP_NAME` | Name shown in the device passkey prompt | `StudyFlow AI` |
| `WEBAUTHN_ORIGIN` | Exact origin accepted for passkey verification | `http://localhost:8000` locally |
| `AI_API_KEY` | Enables AI course recommendations and author-triggered quiz generation | Optional; add a private OpenAI API key in `backend/.env` |
| `AI_MODEL` | Model used for AI recommendations and quiz generation | `gpt-4o-mini` |
| `AI_BASE_URL` | OpenAI-compatible API base URL | Defaults to `https://api.openai.com/v1` |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM` | Sends expiring password-reset links by email | Required for forgot-password requests |
| `FRONTEND_BASE_URL` | Base URL used in password-reset links | `http://localhost:8000/app` locally |
| `DATABASE_URL` | PostgreSQL connection | `postgresql+psycopg://localhost/studyflow_db` locally; set the provider URL in production |

AI quiz generation sends the selected lesson text and extracted text from its PDF to the configured AI API after an author clicks **Generate quiz with AI**. Course recommendations send the learner's search topic, quiz-derived level, and course IDs/titles/subjects/levels after the learner submits a search. Audio/video files and account identifiers are not sent. Add a transcript to lesson text to use video/audio material for quiz generation. API usage may incur provider charges. Keep the key in the untracked `.env` file and never commit it.

Forgot-password requests need working SMTP settings in `backend/.env`. For Gmail, use `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, your Gmail address for both `SMTP_USERNAME` and `SMTP_FROM`, and a Google App Password for `SMTP_PASSWORD`. Google requires 2-Step Verification before an App Password can be created; do not use your normal Google password. Reset links expire after 30 minutes and can be used once. A Gmail mailbox and App Password are not included with this repository.

For production, set `DATABASE_URL` to the provider's PostgreSQL URL, use HTTPS, and set the WebAuthn relying-party ID and origin to the real domain.

## API documentation and status

With the local server running:

| URL | Purpose |
|---|---|
| [`/docs`](http://localhost:8000/docs) | Interactive Swagger UI |
| [`/openapi.json`](http://localhost:8000/openapi.json) | OpenAPI schema |
| [`/health`](http://localhost:8000/health) | Basic health check |
| [`/app`](http://localhost:8000/app) | Web application |
| [`/app/verify.html`](http://localhost:8000/app/verify.html) | Public certificate verification page |

Protected routes require the JWT access token returned by `/auth/login`. Use **Authorize** in Swagger and enter the bearer token.

## API route reference

The API is served by FastAPI. Unless a route is listed as public, send the access token from `/auth/login` in an `Authorization: Bearer <access_token>` header. Request and response schemas are also available in Swagger at `/docs`.

### Service and public routes

| Method | Route | Purpose | Access |
|---|---|---|---|
| `GET` | `/` | Basic service information | Public |
| `GET` | `/health` | Basic health status | Public |
| `GET` | `/courses/catalog` | List published courses | Public |
| `GET` | `/courses/catalog/{course_id}` | Read a published course | Public |
| `GET` | `/courses/catalog/{course_id}/outline` | Read a published course outline and its reviews | Public |
| `GET` | `/certificates/verify/{certificate_code}` | Check a certificate without signing in | Public |

### Account and profile routes

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/auth/register` | Create an account |
| `POST` | `/auth/login` | Get a JWT access token |
| `GET` | `/auth/me` | Read the signed-in user's profile |
| `PUT` | `/auth/me` | Update profile fields |
| `GET` | `/auth/me/avatar` | Read the signed-in user's avatar |
| `PUT` | `/auth/me/avatar` | Upload or replace the avatar |
| `POST` | `/auth/change-password` | Change the account password |
| `GET` | `/auth/passkeys/me` | Check whether a passkey is registered |

### Course author routes

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/courses` | List courses owned by the signed-in author |
| `POST` | `/courses` | Create a course |
| `PUT` | `/courses/{course_id}` | Update an owned course |
| `DELETE` | `/courses/{course_id}` | Delete an owned course and its dependent learning records |
| `POST` | `/courses/{course_id}/publish` | Publish an owned course |
| `POST` | `/courses/{course_id}/unpublish` | Unpublish an owned course |
| `GET` | `/courses/{course_id}/analytics` | Read analytics for an owned course |
| `POST` | `/courses/{course_id}/lessons` | Add a lesson to an owned course |
| `GET` | `/courses/{course_id}/lessons` | List a course's lessons |
| `PUT` | `/courses/{course_id}/lessons/{lesson_id}` | Update an owned lesson |
| `DELETE` | `/courses/{course_id}/lessons/{lesson_id}` | Delete an owned lesson |
| `GET` | `/courses/{course_id}/lessons/{lesson_id}/assignment` | Read a lesson assignment and your submission |
| `PUT` | `/courses/{course_id}/lessons/{lesson_id}/assignment` | Create or update an owned lesson assignment |
| `POST` | `/courses/{course_id}/lessons/{lesson_id}/assignment/submissions` | Submit or resubmit written work |
| `GET` | `/courses/{course_id}/lessons/{lesson_id}/assignment/submissions` | List submissions for an owned course |
| `PUT` | `/courses/{course_id}/lessons/{lesson_id}/assignment/submissions/{submission_id}` | Grade an assignment and leave feedback |
| `GET` | `/courses/{course_id}/modules` | List modules for an owned course |
| `POST` | `/courses/{course_id}/modules` | Add a module to an owned course |
| `PUT` | `/courses/{course_id}/modules/{module_id}` | Rename or reorder a module |
| `DELETE` | `/courses/{course_id}/modules/{module_id}` | Remove a module while keeping its lessons in the course |
| `PUT` | `/courses/{course_id}/lessons/{lesson_id}/resource` | Upload or replace a PDF, video, or audio resource (150 MB maximum) |
| `DELETE` | `/courses/{course_id}/lessons/{lesson_id}/resource` | Remove a lesson's uploaded resource |
| `POST` | `/courses/{course_id}/lessons/{lesson_id}/materials?title=...` | Add an ordered PDF or audio supplement (150 MB maximum) |
| `PUT` | `/courses/{course_id}/lessons/{lesson_id}/materials/{material_id}/position?position=...` | Reorder a supplement |
| `DELETE` | `/courses/{course_id}/lessons/{lesson_id}/materials/{material_id}` | Remove a supplement |

Course language must be `uz`, `en`, `ru`, or `ko`; course level must be `beginner`, `intermediate`, or `advanced`. A lesson has a title, notes/text, content type, and positive position number. See the [course authoring guide](docs/course-authoring.md) for the Coursera-inspired module and lesson workflow. Uploaded material is stored locally under `backend/storage/course-materials`; configure private object storage before a production deployment.

### Learner enrollment and progress routes

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/courses/{course_id}/enroll` | Enroll in a published course |
| `GET` | `/enrollments/me` | List the signed-in learner's enrollments |
| `POST` | `/courses/{course_id}/progress/lessons/{lesson_id}/complete` | Mark an enrolled lesson complete |
| `GET` | `/courses/{course_id}/progress/me` | Read the learner's completion totals and percentage |
| `GET` | `/courses/{course_id}/reviews/me` | Read the learner's own review |
| `PUT` | `/courses/{course_id}/reviews/me` | Create or update a completed-course review |

A review rating is an integer from 1 to 5; an optional comment may contain up to 2,000 characters.

### Quiz and final-exam routes

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/courses/{course_id}/lessons/{lesson_id}/quiz` | Create a quiz for an owned lesson |
| `GET` | `/courses/{course_id}/lessons/{lesson_id}/quiz` | Read a learner-safe quiz |
| `PUT` | `/courses/{course_id}/lessons/{lesson_id}/quiz` | Replace an owned quiz and its questions |
| `DELETE` | `/courses/{course_id}/lessons/{lesson_id}/quiz` | Delete an owned quiz |
| `GET` | `/courses/{course_id}/lessons/{lesson_id}/quiz/manage` | Read the owner's quiz, including correct answers |
| `POST` | `/courses/{course_id}/lessons/{lesson_id}/quiz/attempts` | Submit a lesson-quiz attempt |
| `GET` | `/courses/{course_id}/lessons/{lesson_id}/quiz/attempts/me` | List the learner's attempts for a quiz |
| `GET` | `/courses/{course_id}/final-exam` | Read the course final exam |
| `POST` | `/courses/{course_id}/final-exam/attempts` | Submit a final-exam attempt |

A quiz has one or more questions. Each question has 2–8 answer choices, a zero-based `correct_index`, and a point value. Learner-facing quiz responses omit correct answers; the owner-only management route includes them. Authors configure the final exam's questions and pass mark separately from lesson quizzes. Learners must complete every lesson before opening it; the default pass mark is 70%.

### Certificate, recommendations, and study-plan routes

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/courses/{course_id}/certificate` | Issue a certificate after course and exam requirements are met |
| `GET` | `/courses/{course_id}/certificate/me` | Read the learner's existing certificate |
| `GET` | `/certificates/verify/{certificate_code}` | Return the public verification result |
| `GET` | `/recommendations/me` | Read personalized course recommendations |
| `POST` | `/learning-plans/generate` | Generate a plan for an enrolled course |
| `GET` | `/learning-plans/me` | List the learner's plans |

## Example API calls

These examples use `http://localhost:8000`. Replace the sample values and UUIDs with values returned by your API. Keep real passwords and tokens out of source control.

### Register and sign in

```bash
curl -X POST http://localhost:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"learner@example.com","full_name":"Example Learner","password":"use-a-private-password","preferred_language":"en","account_type":"learner"}'
```

```bash
curl -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"learner@example.com","password":"use-a-private-password","account_type":"learner"}'
```

The login response contains `access_token` and `token_type`. Use the token as a bearer token for protected routes; Swagger's **Authorize** button can set it for interactive API calls.

Learners and authors use separate portals: `/app/learner-login.html` and `/app/author-login.html`. Registration on each portal creates the corresponding account type. Existing course owners are migrated as authors; other existing accounts remain learners. Course creation and management endpoints enforce the author role on the backend.

### Create a course, lesson, and quiz

Create a course as an authenticated course author:

```bash
curl -X POST http://localhost:8000/courses \
  -H 'Authorization: Bearer <access_token>' \
  -H 'Content-Type: application/json' \
  -d '{"title":"Introduction to Python","description":"A beginner course","language":"en","level":"beginner"}'
```

Create a lesson using the returned course ID:

```json
{
  "title": "Variables and values",
  "content": "Lesson content goes here.",
  "position": 1
}
```

Create a lesson quiz using the returned course and lesson IDs:

```json
{
  "title": "Variables quiz",
  "passing_score": 60,
  "questions": [
    {
      "prompt": "Which keyword creates a variable in Python?",
      "choices": ["let", "A name assignment", "var"],
      "correct_index": 1,
      "points": 1
    }
  ]
}
```

The quiz's `correct_index` starts at zero and must refer to an existing choice. Do not expose author-only quiz data in the learner interface.

### Submit a quiz attempt

Read the learner-facing quiz first and use its question IDs:

```json
{
  "answers": [
    {"question_id": "<question-uuid>", "selected_index": 1}
  ]
}
```

The attempt response reports the score, earned points, and whether the quiz pass mark was reached. A learner can fetch their earlier attempts from the `/attempts/me` route.

### Complete the final exam and issue a certificate

1. Enroll in the course and complete all required lessons.
2. Register a device passkey if the account does not already have one.
3. Read `/courses/{course_id}/final-exam` to get the exam questions.
4. Request and verify a fresh passkey assertion with purpose `final_exam`.
5. Submit answers to `/courses/{course_id}/final-exam/attempts` with the returned proof in the `X-Passkey-Proof` header.
6. If the score meets the course's configured passing score, request a fresh passkey proof with purpose `certificate` and send it to `POST /courses/{course_id}/certificate`.
7. Print or save the certificate; share the verification code or public link with an organization.

Passkey proof values are short-lived and single-use. Do not log them or store them in the repository.

## Learner and author workflows

### Learner path

1. Register and sign in; choose the preferred interface language.
2. Browse public courses and preview a course outline.
3. Enroll in a course and open its lessons.
4. Mark each lesson complete and take its lesson quiz.
5. Use the learner dashboard to see completed lessons, recommendations, and study plans.
6. After all course lessons are complete, take the final exam with passkey verification.
7. After passing, issue a certificate and share its verification link.

### Course-author path

1. Create a course with its language and level.
2. Add lessons in order; each lesson can be text, a PDF reading, a video, or an audio recording.
3. Add at least one quiz to every lesson used for the final exam.
4. Preview and publish the course when ready.
5. Review enrollment, progress, learner ratings, and exam pass statistics.
6. Update or unpublish course content when necessary.

### Certificate-verifier path

1. Open `/app/verify.html` or the link printed on the certificate.
2. Enter the certificate's verification code.
3. Compare the returned recipient, course, and issue date with the certificate presented.
4. Treat a code as valid only when the API finds its certificate record.

## Data model overview

The PostgreSQL schema stores the main course and learning records as related tables:

| Model | Role |
|---|---|
| `User` | Account, preferred language, profile fields, and avatar data |
| `Course` | Course content metadata, level, language, publication state, and owner |
| `Lesson` | Ordered lesson content for a course |
| `Enrollment` | Learner's course enrollment |
| `LessonProgress` | Completion state and timestamp for a learner's lesson |
| `Quiz`, `QuizQuestion`, `QuizAttempt` | Lesson quizzes, answer choices, and learner attempt results |
| `FinalExamAttempt` | Final-exam score and pass result |
| `CourseCertificate` | Issued certificate and unique public verification code |
| `CourseReview` | Learner's course rating and optional review |
| `LearningPlan` | Generated course study schedule |
| `PasskeyCredential`, `PasskeyChallenge`, `PasskeyProof` | WebAuthn credential and short-lived verification state |

Alembic migrations in `backend/migrations/versions/` create and evolve this schema. Use `alembic upgrade head` to apply all migrations to the configured database.

## Development and testing

Install the development test dependencies from the repository root:

```bash
python -m pip install -r backend/requirements-dev.txt
```

Run the API regression tests against a temporary SQLite database:

```bash
python -m pytest -q
```

The tests cover login and password reset, author ownership, course language and payment access, lesson completion, final exams, certificate issuance, and video skip protection. CI runs these tests and also checks Python and JavaScript syntax and Docker Compose configuration.

To run the syntax checks locally:

```bash
python -m compileall -q backend/app backend/migrations
node --check apps/web/app.js
node --check apps/web/verify.js
node --check apps/web/portal-auth.js
node --check apps/web/reset-password.js
docker compose --env-file .env.compose.example config --quiet
```

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

Authors can attach multi-question quizzes to lessons and configure a separate final exam. Learners can submit quiz attempts and review their own results. After every lesson is completed, learners can take the final exam. Its pass mark is configured by the author and defaults to 70%; a fresh passkey verification proof is required to submit the exam and request a certificate.

## Certificates and public verification

A learner who passes the final exam can request a course certificate. New issuance requires a fresh passkey verification proof. Existing certificates can be viewed from the learner account.

Each certificate has a unique verification code and a public verification link. The page at `/app/verify.html` works without an account and checks the submitted code against the database. A code is reported valid only when a corresponding certificate record exists.

## Course reviews and analytics

Enrolled learners can submit or update a 1–5 star review after completing a course. Public course previews show the rating summary. Course authors can view enrollment, completion, rating, and final-exam pass statistics for courses they own.

## Deployment

The repository includes a Docker image, Docker Compose setup, and a Render Blueprint. Docker Compose has been validated by CI. GitHub currently hosts the project source code; GitHub Pages is not enabled, so the repository URL is not a working app URL. A free Render PostgreSQL database exists, but no Render web service has been created and no public app URL is available. The database is on Render's 30-day free plan, so it is temporary and must not be treated as permanent storage. See [deployment status and next steps](docs/deployment.md).

For a local container run, install Docker Desktop, then from the repository root:

```bash
cp .env.compose.example .env
test -f backend/.env || cp backend/.env.example backend/.env
```

Set a private random `SECRET_KEY` in `backend/.env` and a long URL-safe `POSTGRES_PASSWORD` in the root `.env`. Add SMTP, AI, and payment credentials there only if those features are being used. Then start the app:

```bash
docker compose up --build
```

The container waits for PostgreSQL, applies Alembic migrations, and starts the app at [http://localhost:8000/app](http://localhost:8000/app). Uploaded materials and profile pictures are stored in `backend/storage`; PostgreSQL data uses a named Docker volume. `docker compose down` keeps both. `docker compose down -v` deletes the database volume and all database records.

Before a public deployment, use a managed PostgreSQL database and persistent private object storage for uploads, serve the app over HTTPS, configure `WEBAUTHN_RP_ID` and `WEBAUTHN_ORIGIN` for the final domain, and set `PUBLIC_APP_URL` and `FRONTEND_BASE_URL` to that domain. Configure SMTP, AI, and GlobalPay credentials in the host's secret manager. Back up PostgreSQL and uploaded files, and verify `/health`, account recovery, learner and author access, payments, exams, and certificate verification. See [deployment preparation](docs/deployment.md) for the remaining release steps.

## Known limitations

- No public cloud app deployment or URL is available yet. Render's GitHub repository access must be fixed before creating the web service.
- `DATABASE_URL` is configurable. A temporary free Render database exists, but it expires after 30 days and is not yet connected to a deployed app.
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
| Week 7: cloud deployment | In progress; Render Blueprint and temporary free database are ready, but GitHub access blocks the web service; public URL and live health-check evidence remain |
| Week 8: midterm | Review checkpoint |
| Week 9: decomposition | [Microservices discussion](docs/decomposition-review.md) |
| Week 10: security review | [Security review and follow-up items](docs/security-audit.md) |
| Project development and AI assistance | [AI collaboration log](AI_LOG.md) |

StudyFlow AI is the student’s project and the student wrote its code. The log records that Codex occasionally helped fix errors and run tests. The student should review it for accuracy before submission.
# StadyFlow

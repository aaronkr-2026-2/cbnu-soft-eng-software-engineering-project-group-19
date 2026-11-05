<div align="center">
  <a href="https://github.com/aaronkr-2026-2/cbnu-soft-eng-software-engineering-project-group-19">
    <img src="docs/assets/studyflow-logo.svg" alt="StudyFlow AI — learn at your pace" width="410">
  </a>
  <h3>Personalized learning, from first lesson to verified certificate.</h3>
  <p>Explore courses, follow your progress, test what you know, and share a certificate others can verify.</p>
  <p><a href="https://github.com/killashaw8"><img alt="GitHub profile: killashaw8" src="https://img.shields.io/badge/GitHub-killashaw8-181717?style=for-the-badge&logo=github&logoColor=white"></a></p>
  <p>
    <a href="https://github.com/aaronkr-2026-2/cbnu-soft-eng-software-engineering-project-group-19"><img alt="GitHub repository" src="https://img.shields.io/badge/GitHub-StudyFlow_AI-181717?style=for-the-badge&logo=github&logoColor=white"></a>
    <a href="https://fastapi.tiangolo.com/"><img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-API-009688?style=for-the-badge&logo=fastapi&logoColor=white"></a>
    <a href="https://www.postgresql.org/"><img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-Database-4169E1?style=for-the-badge&logo=postgresql&logoColor=white"></a>
  </p>
</div>

<p align="center">
  <a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white"></a>
  <a href="https://fastapi.tiangolo.com/"><img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white"></a>
  <a href="https://www.postgresql.org/"><img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white"></a>
  <a href="https://www.sqlalchemy.org/"><img alt="SQLAlchemy" src="https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white"></a>
  <a href="https://developer.mozilla.org/en-US/docs/Web/JavaScript"><img alt="JavaScript" src="https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black"></a>
  <a href="https://developer.mozilla.org/en-US/docs/Web/HTML"><img alt="HTML5" src="https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white"></a>
  <a href="https://developer.mozilla.org/en-US/docs/Web/CSS"><img alt="CSS3" src="https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white"></a>
</p>

---

## ✨ About StudyFlow AI

StudyFlow AI is a multilingual learning platform for independent learners, course authors, and certificate verifiers. Learners can move through a course at their own pace, while authors can publish lessons and assessments and organizations can verify certificates without creating an account.

**Product vision:** Give every learner a clear route from choosing a course to demonstrating what they learned, in a language that works for them.

### What you can do

| 🎓 Learn | 🧑‍🏫 Create | 🏅 Verify |
|:--|:--|:--|
| Browse and preview courses, enroll, follow lessons, and track progress. | Create courses, lessons, and quizzes; publish content and review course analytics. | Take lesson quizzes and a final exam, earn a uniquely coded certificate, and let anyone check it publicly. |

- **Four interface languages:** Uzbek, English, Russian, and Korean.
- **Personal learning tools:** recommendations, weekly study plans, and a learner dashboard.
- **Extra account security:** device passkeys before submitting a final exam or issuing a certificate.

## 🧭 Project map

| Resource | What it covers |
|:--|:--|
| [Product vision and pitch](docs/vision-and-pitch.md) | Idea, intended users, product vision, and chosen stack |
| [Personas and user stories](docs/personas-and-user-stories.md) | Retrospective personas, user stories, and acceptance criteria |
| [Agile process](docs/agile-process.md) | Lightweight planning, review, and retrospective workflow |
| [Architecture and critique](docs/architecture-and-critique.md) | Current design diagram, strengths, and risks |
| [Decomposition review](docs/decomposition-review.md) | Week 9 decision on whether microservices fit |
| [AI collaboration log](AI_LOG.md) | AI assistance and project decisions to review |

## 🏗️ Architecture

StudyFlow AI currently uses a **modular monolith**: one FastAPI application serves the web interface and feature-focused API routes. PostgreSQL stores the learning data; Alembic manages schema migrations.

```text
Browser (HTML · CSS · JavaScript)
              │
              ▼
        FastAPI application
       ├── Accounts & passkeys
       ├── Courses & lessons
       ├── Quizzes & certificates
       └── Plans, reviews & analytics
              │
              ▼
          PostgreSQL
```

## 🚀 Run locally

**You’ll need:** Python 3.11+ and PostgreSQL, with a local database named `studyflow_db`.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set a private `SECRET_KEY` in `backend/.env`, start PostgreSQL, and create the database:

```bash
createdb studyflow_db
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open the app at **[http://127.0.0.1:8000/app](http://127.0.0.1:8000/app)** or the API docs at **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**.

> Passkeys are configured for localhost during development. Before production, set `WEBAUTHN_RP_ID` and `WEBAUTHN_ORIGIN` to the deployed domain and HTTPS origin. The database URL is currently set in `backend/app/database.py`; externalize it before cloud deployment.

## 🌱 Course milestones

This repository contains the project work through **Week 9** of the course schedule.

- **Weeks 2–3:** idea, technology stack, working MVP, and product vision.
- **Week 4:** retrospective personas and user stories.
- **Week 5:** lightweight Agile process retrofit.
- **Week 6:** architecture diagram and design critique.
- **Week 7:** cloud deployment details still need to be added; no public deployment URL is recorded yet.
- **Week 8:** midterm review checkpoint.
- **Week 9:** modular-monolith vs. microservices discussion.

## 🌐 Current status

The project runs locally. Team member names and roles, a public cloud URL, and real user research were not present in the project files; add verified details when available.

---

<div align="center">
  <sub>Built for the Advanced Software Engineering semester project · StudyFlow AI</sub>
</div>

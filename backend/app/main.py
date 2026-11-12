from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers.analytics import router as analytics_router
from app.routers.assignments import router as assignments_router
from app.routers.auth import router as auth_router
from app.routers.passkeys import router as passkeys_router
from app.routers.courses import router as courses_router
from app.routers.lessons import router as lessons_router
from app.routers.enrollments import router as enrollments_router
from app.routers.payments import router as payments_router
from app.routers.progress import router as progress_router
from app.routers.reviews import router as reviews_router
from app.routers.quizzes import router as quizzes_router
from app.routers.certificates import public_router as public_certificates_router
from app.routers.certificates import router as certificates_router
from app.routers.personalization import (
    learning_plans_router,
    recommendations_router,
)

app = FastAPI(
    title="StudyFlow AI",
    description="AI-powered Personalized Self-Learning Platform",
    version="1.0.0",
)

app.include_router(auth_router)
app.include_router(assignments_router)
app.include_router(passkeys_router)
app.include_router(courses_router)
app.include_router(analytics_router)
app.include_router(lessons_router)
app.include_router(enrollments_router)
app.include_router(payments_router)
app.include_router(progress_router)
app.include_router(reviews_router)
app.include_router(quizzes_router)
app.include_router(certificates_router)
app.include_router(public_certificates_router)
app.include_router(recommendations_router)
app.include_router(learning_plans_router)

web_directory = Path(__file__).resolve().parents[2] / "apps" / "web"
app.mount("/app", StaticFiles(directory=web_directory, html=True), name="web")


@app.get("/")
def home():
    return {
        "message": "Welcome to StudyFlow AI!",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}

import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.ai import AIConfigurationError, AIProviderError, generate_course_recommendations
from app.core.dependencies import get_current_user
from app.core.schemes.personalization import (
    CourseRecommendation,
    LearningPlanGenerate,
    LearningPlanItem,
    LearningPlanResponse,
    RecommendationResponse,
)
from app.database import get_db
from app.models import (
    Course,
    Enrollment,
    Lesson,
    LessonProgress,
    LearningPlan,
    Quiz,
    QuizAttempt,
    User,
)

recommendations_router = APIRouter(prefix="/recommendations", tags=["Personalized Learning"])
learning_plans_router = APIRouter(prefix="/learning-plans", tags=["Personalized Learning"] )

_LEVELS = ("beginner", "intermediate", "advanced")
_RECOMMENDATION_REASONS = {
    "uz": {
        "level": "Quiz natijangizga mos daraja",
        "near": "Hozirgi darajangizga yaqin",
        "beginner": "Boshlang‘ich bosqichdan boshlash uchun mos",
        "interest": "Qiziqishingizga mos mavzu",
    },
    "en": {
        "level": "Matches the level suggested by your quiz results",
        "near": "Close to your current level",
        "beginner": "A good starting point for beginners",
        "interest": "Matches your learning interest",
    },
    "ru": {
        "level": "Соответствует уровню по результатам тестов",
        "near": "Близко к вашему текущему уровню",
        "beginner": "Подходит для начала обучения с основ",
        "interest": "Соответствует вашим интересам",
    },
    "ko": {
        "level": "퀴즈 결과에 맞는 수준입니다",
        "near": "현재 수준과 가깝습니다",
        "beginner": "기초부터 시작하기에 적합합니다",
        "interest": "관심 있는 주제와 맞아요",
    },
}
_STUDY_GUIDANCE = {
    "uz": (
        "Darsni o‘qing va qisqa qayd yozing; quiz bo‘lsa, yakunda topshiring.",
        "Darsni o‘qing va asosiy fikrlarni qayd qiling.",
    ),
    "en": (
        "Study the lesson and take brief notes; complete the quiz if available.",
        "Study the lesson and note its key ideas.",
    ),
    "ru": (
        "Изучите урок и сделайте краткие заметки; при наличии пройдите тест.",
        "Изучите урок и запишите основные идеи.",
    ),
    "ko": (
        "강의를 학습하고 간단히 메모하세요. 퀴즈가 있으면 마지막에 풀어 보세요.",
        "강의를 학습하고 핵심 내용을 메모하세요.",
    ),
}


def learner_profile(user_id: uuid.UUID, db: Session) -> tuple[float | None, str]:
    scores = [
        row[0]
        for row in (
            db.query(QuizAttempt.score_percent)
            .filter(QuizAttempt.user_id == user_id)
            .order_by(QuizAttempt.submitted_at.desc())
            .limit(20)
            .all()
        )
    ]
    if not scores:
        return None, "beginner"
    average = round(sum(scores) / len(scores), 2)
    if average < 60:
        return average, "beginner"
    if average < 80:
        return average, "intermediate"
    return average, "advanced"


def build_reasons(course: Course, language: str, level: str, has_quiz_history: bool, interest: str = "", lesson_matches: bool = False) -> tuple[int, list[str]]:
    copy = _RECOMMENDATION_REASONS.get(language, _RECOMMENDATION_REASONS["uz"])
    score = 0
    reasons: list[str] = []
    wanted = {part.casefold() for part in interest.split() if len(part) > 1}
    course_text = " ".join((course.title or "", course.description or "", course.category or "")).casefold()
    if wanted and (any(word in course_text for word in wanted) or lesson_matches):
        score += 80
        reasons.append(copy["interest"])
    level_distance = abs(_LEVELS.index(course.level) - _LEVELS.index(level))
    if level_distance == 0:
        score += 40
        reasons.append(copy["level"])
    elif level_distance == 1:
        score += 20
        reasons.append(copy["near"])
    else:
        score += 5
    if not has_quiz_history and course.level == "beginner":
        reasons.append(copy["beginner"])
    return score, reasons


@recommendations_router.get("/me", response_model=RecommendationResponse)
def get_my_recommendations(
    limit: int = Query(default=5, ge=1, le=20),
    interest: str | None = Query(default=None, min_length=1, max_length=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecommendationResponse:
    average_score, estimated_level = learner_profile(current_user.id, db)
    enrolled_ids = {
        row[0]
        for row in db.query(Enrollment.course_id).filter(Enrollment.user_id == current_user.id).all()
    }
    courses = (
        db.query(Course)
        .filter(Course.is_published.is_(True))
        .order_by(Course.created_at.desc())
        .all()
    )
    matching_course_ids: set[uuid.UUID] = set()
    if interest:
        pattern = f"%{interest.strip()}%"
        matching_course_ids = {
            row[0] for row in db.query(Lesson.course_id).filter(
                or_(Lesson.title.ilike(pattern), Lesson.content.ilike(pattern))
            ).all()
        }
    candidates: list[tuple[int, Course, list[str]]] = []
    for course in courses:
        if course.id in enrolled_ids:
            continue
        score, reasons = build_reasons(
            course, current_user.preferred_language, estimated_level, average_score is not None,
            interest or "", course.id in matching_course_ids,
        )
        candidates.append((score, course, reasons))
    candidates.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)

    ai_powered = False
    recommended_courses: list[tuple[int, Course, list[str]]] | None = None
    if interest and candidates:
        available = [
            {"course_id": str(course.id), "title": course.title, "subject": course.category, "level": course.level}
            for _, course, _ in candidates[:30]
        ]
        try:
            result = generate_course_recommendations(
                interest, estimated_level, current_user.preferred_language, available
            )
            course_map = {str(course.id): (score, course, reasons) for score, course, reasons in candidates}
            selected = []
            seen = set()
            ai_items = result.get("recommendations", []) if isinstance(result, dict) else []
            for item in ai_items if isinstance(ai_items, list) else []:
                if not isinstance(item, dict):
                    continue
                course_id = str(item.get("course_id", ""))
                if course_id in course_map and course_id not in seen:
                    score, course, local_reasons = course_map[course_id]
                    reason = item.get("reason")
                    selected.append((score, course, [reason] if isinstance(reason, str) and reason.strip() else local_reasons))
                    seen.add(course_id)
            if selected:
                recommended_courses = selected
                ai_powered = True
        except (AIConfigurationError, AIProviderError, ValueError, TypeError):
            pass
    if recommended_courses is None:
        recommended_courses = candidates

    return RecommendationResponse(
        preferred_language=current_user.preferred_language,
        estimated_level=estimated_level,
        average_quiz_score=average_score,
        ai_powered=ai_powered,
        recommendations=[
            CourseRecommendation(
                course_id=course.id,
                title=course.title,
                description=course.description,
                language=course.language,
                level=course.level,
                match_score=score,
                reasons=reasons,
            )
            for score, course, reasons in recommended_courses[:limit]
        ],
    )


def to_plan_response(plan: LearningPlan, course: Course, db: Session) -> LearningPlanResponse:
    total_lessons = db.query(Lesson).filter(Lesson.course_id == course.id).count()
    completed_lessons = (
        db.query(LessonProgress.id)
        .join(Lesson, Lesson.id == LessonProgress.lesson_id)
        .filter(Lesson.course_id == course.id, LessonProgress.user_id == plan.user_id)
        .count()
    )
    return LearningPlanResponse(
        id=plan.id,
        course_id=course.id,
        course_title=course.title,
        weekly_study_days=plan.weekly_study_days,
        session_minutes=plan.session_minutes,
        estimated_weeks=plan.estimated_weeks,
        completed_lessons=completed_lessons,
        total_lessons=total_lessons,
        plan_items=[LearningPlanItem(**item) for item in plan.plan_data],
        generated_at=plan.generated_at,
    )


@learning_plans_router.post("/generate", response_model=LearningPlanResponse, status_code=status.HTTP_201_CREATED)
def generate_learning_plan(
    request: LearningPlanGenerate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LearningPlanResponse:
    course = (
        db.query(Course)
        .filter(Course.id == request.course_id, Course.is_published.is_(True))
        .first()
    )
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Published course not found")
    enrollment = (
        db.query(Enrollment.id)
        .filter(Enrollment.course_id == course.id, Enrollment.user_id == current_user.id)
        .first()
    )
    if enrollment is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Enroll in the course to generate a plan")

    lessons = (
        db.query(Lesson)
        .filter(Lesson.course_id == course.id)
        .order_by(Lesson.position, Lesson.created_at)
        .all()
    )
    if not lessons:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Course has no lessons yet")
    completed_ids = {
        row[0]
        for row in (
            db.query(LessonProgress.lesson_id)
            .filter(LessonProgress.user_id == current_user.id)
            .join(Lesson, Lesson.id == LessonProgress.lesson_id)
            .filter(Lesson.course_id == course.id)
            .all()
        )
    }
    remaining = [lesson for lesson in lessons if lesson.id not in completed_ids]
    guidance_with_quiz, guidance_without_quiz = _STUDY_GUIDANCE.get(
        current_user.preferred_language, _STUDY_GUIDANCE["uz"]
    )
    items = []
    for index, lesson in enumerate(remaining):
        has_quiz = db.query(Quiz.id).filter(Quiz.lesson_id == lesson.id).first() is not None
        items.append(
            {
                "session_number": index + 1,
                "week_number": index // request.weekly_study_days + 1,
                "study_day": index % request.weekly_study_days + 1,
                "lesson_id": lesson.id,
                "lesson_title": lesson.title,
                "session_minutes": request.session_minutes,
                "quiz_available": has_quiz,
                "guidance": guidance_with_quiz
                if has_quiz
                else guidance_without_quiz,
            }
        )
    estimated_weeks = math.ceil(len(items) / request.weekly_study_days) if items else 0
    plan = LearningPlan(
        user_id=current_user.id,
        course_id=course.id,
        weekly_study_days=request.weekly_study_days,
        session_minutes=request.session_minutes,
        estimated_weeks=estimated_weeks,
        plan_data=[
            {**item, "lesson_id": str(item["lesson_id"])} for item in items
        ],
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return to_plan_response(plan, course, db)


@learning_plans_router.get("/me", response_model=list[LearningPlanResponse])
def list_my_learning_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[LearningPlanResponse]:
    records = (
        db.query(LearningPlan, Course)
        .join(Course, Course.id == LearningPlan.course_id)
        .filter(LearningPlan.user_id == current_user.id)
        .order_by(LearningPlan.generated_at.desc())
        .all()
    )
    return [to_plan_response(plan, course, db) for plan, course in records]

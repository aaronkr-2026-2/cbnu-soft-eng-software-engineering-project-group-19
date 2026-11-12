import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_author
from app.core.ai import AIConfigurationError, AIProviderError, generate_quiz_json
from app.core.passkeys import consume_passkey_proof
from app.core.localization import get_final_exam_content_translation, get_quiz_content_translation
from app.core.schemes.quiz import (
    QuizAttemptCreate,
    QuizAttemptResponse,
    FinalExamAttemptCreate,
    FinalExamAttemptResponse,
    FinalExamQuestionResponse,
    FinalExamResponse,
    FinalExamManageQuestion,
    FinalExamManageResponse,
    FinalExamManageUpsert,
    QuizCreate,
    QuizUpdate,
    QuizManageResponse,
    QuizManageQuestionResponse,
    QuizQuestionResponse,
    QuizResponse,
)
from app.database import get_db
from app.models import (
    Course,
    CourseFinalExam,
    CourseFinalExamQuestion,
    CourseTranslation,
    Enrollment,
    FinalExamAttempt,
    LessonProgress,
    Lesson,
    LessonTranslation,
    Quiz,
    QuizAttempt,
    QuizQuestion,
    User,
)

router = APIRouter(tags=["Quizzes and Assessments"])
RESOURCE_DIR = Path(__file__).resolve().parents[2] / "storage" / "course-materials"


def get_lesson_context(course_id: uuid.UUID, lesson_id: uuid.UUID, db: Session) -> tuple[Course, Lesson]:
    course = db.query(Course).filter(Course.id == course_id).first()
    lesson = (
        db.query(Lesson)
        .filter(Lesson.id == lesson_id, Lesson.course_id == course_id)
        .first()
    )
    if course is None or lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course or lesson not found")
    return course, lesson


def is_enrolled(course_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> bool:
    return (
        db.query(Enrollment.id)
        .filter(Enrollment.course_id == course_id, Enrollment.user_id == user_id)
        .first()
        is not None
    )


def get_quiz(lesson_id: uuid.UUID, db: Session) -> Quiz | None:
    return db.query(Quiz).filter(Quiz.lesson_id == lesson_id).first()


def to_quiz_response(quiz: Quiz, db: Session) -> QuizResponse:
    questions = (
        db.query(QuizQuestion)
        .filter(QuizQuestion.quiz_id == quiz.id)
        .order_by(QuizQuestion.position)
        .all()
    )
    return QuizResponse(
        id=quiz.id,
        lesson_id=quiz.lesson_id,
        title=quiz.title,
        passing_score=quiz.passing_score,
        questions=[
            QuizQuestionResponse(
                id=question.id,
                prompt=question.prompt,
                choices=question.choices,
                points=question.points,
                position=question.position,
            )
            for question in questions
        ],
    )


def to_quiz_manage_response(quiz: Quiz, db: Session) -> QuizManageResponse:
    questions = (
        db.query(QuizQuestion)
        .filter(QuizQuestion.quiz_id == quiz.id)
        .order_by(QuizQuestion.position)
        .all()
    )


def extract_quiz_material(lesson: Lesson) -> str:
    material = (lesson.content or "").strip()
    if lesson.resource_type == "pdf" and lesson.resource_key:
        resource_path = (RESOURCE_DIR / Path(lesson.resource_key).name).resolve()
        if resource_path.parent != RESOURCE_DIR.resolve() or not resource_path.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uploaded lesson PDF was not found")
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(resource_path))
            pdf_text = "\n".join((page.extract_text() or "") for page in reader.pages[:50])
        except ImportError:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="PDF text extraction is not installed") from None
        except Exception:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Could not extract text from this PDF") from None
        material = "\n\n".join(part for part in (material, pdf_text.strip()) if part)
    if lesson.resource_type in {"audio", "video"} and len(material) < 80:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Add a text transcript to the lesson before generating a quiz from audio or video")
    if len(material) < 80:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Add at least 80 characters of lesson text or upload a text-based PDF")
    return material[:24000]


@router.post(
    "/courses/{course_id}/lessons/{lesson_id}/quiz/generate",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_lesson_quiz(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> QuizResponse:
    course, lesson = get_lesson_context(course_id, lesson_id, db)
    if course.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the course owner can generate a quiz")
    existing = get_quiz(lesson.id, db)
    if existing and db.query(QuizAttempt.id).filter(QuizAttempt.quiz_id == existing.id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This quiz has learner attempts and cannot be regenerated")
    material = extract_quiz_material(lesson)
    try:
        quiz_data = QuizCreate.model_validate(generate_quiz_json(course.title, lesson.title, material))
    except AIConfigurationError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI_API_KEY is not configured on the server") from None
    except AIProviderError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from None
    except Exception:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="AI returned an invalid quiz; try again") from None
    if existing is None:
        existing = Quiz(lesson_id=lesson.id, title=quiz_data.title, passing_score=60)
        db.add(existing)
        db.flush()
    else:
        existing.title = quiz_data.title
        db.query(QuizQuestion).filter(QuizQuestion.quiz_id == existing.id).delete(synchronize_session=False)
    for position, question in enumerate(quiz_data.questions, start=1):
        db.add(QuizQuestion(
            quiz_id=existing.id, prompt=question.prompt, choices=question.choices,
            correct_index=question.correct_index, points=question.points, position=position,
        ))
    db.commit()
    db.refresh(existing)
    return to_quiz_response(existing, db)
    return QuizManageResponse(
        id=quiz.id,
        lesson_id=quiz.lesson_id,
        title=quiz.title,
        passing_score=quiz.passing_score,
        questions=[
            QuizManageQuestionResponse(
                id=question.id,
                prompt=question.prompt,
                choices=question.choices,
                correct_index=question.correct_index,
                points=question.points,
                position=question.position,
            )
            for question in questions
        ],
    )


def to_attempt_response(attempt: QuizAttempt, question_count: int) -> QuizAttemptResponse:
    return QuizAttemptResponse(
        id=attempt.id,
        quiz_id=attempt.quiz_id,
        correct_count=attempt.correct_count,
        total_questions=question_count,
        earned_points=attempt.earned_points,
        total_points=attempt.total_points,
        score_percent=attempt.score_percent,
        passed=attempt.passed,
        submitted_at=attempt.submitted_at,
    )


@router.post(
    "/courses/{course_id}/lessons/{lesson_id}/quiz",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quiz(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    quiz_data: QuizCreate,
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> QuizResponse:
    course, lesson = get_lesson_context(course_id, lesson_id, db)
    if course.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the course owner can create a quiz")
    if get_quiz(lesson.id, db) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A quiz already exists for this lesson")

    quiz = Quiz(lesson_id=lesson.id, title=quiz_data.title, passing_score=quiz_data.passing_score)
    db.add(quiz)
    db.flush()
    for position, question_data in enumerate(quiz_data.questions, start=1):
        db.add(
            QuizQuestion(
                quiz_id=quiz.id,
                prompt=question_data.prompt,
                choices=question_data.choices,
                correct_index=question_data.correct_index,
                points=question_data.points,
                position=position,
            )
        )
    db.commit()
    db.refresh(quiz)
    return to_quiz_response(quiz, db)


@router.get(
    "/courses/{course_id}/lessons/{lesson_id}/quiz",
    response_model=QuizResponse,
)
def read_quiz(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    language: str = Query("uz", pattern="^(uz|en|ru|ko)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuizResponse:
    course, lesson = get_lesson_context(course_id, lesson_id, db)
    if course.owner_id != current_user.id and not is_enrolled(course.id, current_user.id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Enroll in the course to access its quiz")
    quiz = get_quiz(lesson.id, db)
    if quiz is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    response = to_quiz_response(quiz, db)
    questions = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz.id).order_by(QuizQuestion.position).all()
    localized = get_quiz_content_translation(lesson, course, quiz, questions, language, db)
    if localized:
        response.title = localized["title"]
        response.questions = [question.model_copy(update={"prompt": item["prompt"], "choices": item["choices"]})
                              for question, item in zip(response.questions, localized["questions"])]
    return response


@router.get(
    "/courses/{course_id}/lessons/{lesson_id}/quiz/manage",
    response_model=QuizManageResponse,
)
def read_quiz_for_owner(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> QuizManageResponse:
    course, lesson = get_lesson_context(course_id, lesson_id, db)
    if course.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the course owner can manage this quiz")
    quiz = get_quiz(lesson.id, db)
    if quiz is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    return to_quiz_manage_response(quiz, db)


@router.put(
    "/courses/{course_id}/lessons/{lesson_id}/quiz",
    response_model=QuizResponse,
)
def update_quiz(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    quiz_data: QuizUpdate,
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> QuizResponse:
    course, lesson = get_lesson_context(course_id, lesson_id, db)
    if course.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the course owner can update a quiz")
    quiz = get_quiz(lesson.id, db)
    if quiz is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    if db.query(QuizAttempt.id).filter(QuizAttempt.quiz_id == quiz.id).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This quiz has learner attempts. Delete it to reset the attempt history before editing.",
        )

    quiz.title = quiz_data.title
    quiz.passing_score = quiz_data.passing_score
    db.query(LessonTranslation).filter(LessonTranslation.lesson_id == lesson.id).update({LessonTranslation.quiz_content: None}, synchronize_session=False)
    db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz.id).delete(synchronize_session=False)
    for position, question_data in enumerate(quiz_data.questions, start=1):
        db.add(
            QuizQuestion(
                quiz_id=quiz.id,
                prompt=question_data.prompt,
                choices=question_data.choices,
                correct_index=question_data.correct_index,
                points=question_data.points,
                position=position,
            )
        )
    db.commit()
    db.refresh(quiz)
    return to_quiz_response(quiz, db)


@router.delete(
    "/courses/{course_id}/lessons/{lesson_id}/quiz",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_quiz(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> None:
    course, lesson = get_lesson_context(course_id, lesson_id, db)
    if course.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the course owner can delete a quiz")
    quiz = get_quiz(lesson.id, db)
    if quiz is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    db.delete(quiz)
    db.query(LessonTranslation).filter(LessonTranslation.lesson_id == lesson.id).update({LessonTranslation.quiz_content: None}, synchronize_session=False)
    db.commit()


@router.post(
    "/courses/{course_id}/lessons/{lesson_id}/quiz/attempts",
    response_model=QuizAttemptResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_quiz_attempt(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    attempt_data: QuizAttemptCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuizAttemptResponse:
    _, lesson = get_lesson_context(course_id, lesson_id, db)
    if not is_enrolled(course_id, current_user.id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Enroll in the course to submit an attempt")
    quiz = get_quiz(lesson.id, db)
    if quiz is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

    questions = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz.id).all()
    question_by_id = {question.id: question for question in questions}
    selected_answers = {str(answer.question_id): answer.selected_index for answer in attempt_data.answers}
    if len(selected_answers) != len(attempt_data.answers):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="A question was answered more than once")
    if set(selected_answers) != {str(question.id) for question in questions}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Submit exactly one answer for every question")

    earned_points = 0
    correct_count = 0
    total_points = sum(question.points for question in questions)
    for question_id, selected_index in selected_answers.items():
        question = question_by_id[uuid.UUID(question_id)]
        if selected_index >= len(question.choices):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Selected choice is out of range")
        if selected_index == question.correct_index:
            correct_count += 1
            earned_points += question.points

    score_percent = round(earned_points / total_points * 100, 2) if total_points else 0.0
    attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=current_user.id,
        answers=selected_answers,
        correct_count=correct_count,
        earned_points=earned_points,
        total_points=total_points,
        score_percent=score_percent,
        passed=score_percent >= quiz.passing_score,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return to_attempt_response(attempt, len(questions))


@router.get(
    "/courses/{course_id}/lessons/{lesson_id}/quiz/attempts/me",
    response_model=list[QuizAttemptResponse],
)
def list_my_quiz_attempts(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[QuizAttemptResponse]:
    _, lesson = get_lesson_context(course_id, lesson_id, db)
    if not is_enrolled(course_id, current_user.id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Enroll in the course to view attempts")
    quiz = get_quiz(lesson.id, db)
    if quiz is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    question_count = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz.id).count()
    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.quiz_id == quiz.id, QuizAttempt.user_id == current_user.id)
        .order_by(QuizAttempt.submitted_at.desc())
        .all()
    )
    return [to_attempt_response(attempt, question_count) for attempt in attempts]


def get_final_exam_context(course_id: uuid.UUID, user_id: uuid.UUID, db: Session):
    course = db.query(Course).filter(Course.id == course_id).first()
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    if not is_enrolled(course_id, user_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Enroll in the course first")
    lesson_rows = db.query(Lesson).filter(Lesson.course_id == course_id).order_by(Lesson.position).all()
    if not lesson_rows:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Course has no lessons")
    completed_ids = {
        row[0] for row in db.query(LessonProgress.lesson_id)
        .filter(LessonProgress.user_id == user_id, LessonProgress.lesson_id.in_([lesson.id for lesson in lesson_rows]))
        .all()
    }
    if len(completed_ids) != len(lesson_rows):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Complete every lesson before the final exam")
    exam = db.query(CourseFinalExam).filter(CourseFinalExam.course_id == course_id).first()
    if exam is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The course author has not set up the final exam")
    questions = db.query(CourseFinalExamQuestion).filter(
        CourseFinalExamQuestion.exam_id == exam.id
    ).order_by(CourseFinalExamQuestion.position).all()
    if not questions:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The course final exam has no questions")
    return course, exam, questions


def to_final_exam_manage_response(exam: CourseFinalExam, db: Session) -> FinalExamManageResponse:
    questions = db.query(CourseFinalExamQuestion).filter(
        CourseFinalExamQuestion.exam_id == exam.id
    ).order_by(CourseFinalExamQuestion.position).all()
    return FinalExamManageResponse(
        id=exam.id, course_id=exam.course_id, title=exam.title, passing_score=exam.passing_score,
        questions=[FinalExamManageQuestion(
            id=question.id, lesson_title=exam.title, prompt=question.prompt, choices=question.choices,
            correct_index=question.correct_index, position=question.position,
        ) for question in questions],
    )


@router.get("/courses/{course_id}/final-exam/manage", response_model=FinalExamManageResponse)
def read_final_exam_for_owner(
    course_id: uuid.UUID,
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> FinalExamManageResponse:
    course = db.query(Course).filter(Course.id == course_id, Course.owner_id == current_user.id).first()
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    exam = db.query(CourseFinalExam).filter(CourseFinalExam.course_id == course_id).first()
    if exam is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Final exam not configured")
    return to_final_exam_manage_response(exam, db)


@router.put("/courses/{course_id}/final-exam/manage", response_model=FinalExamManageResponse)
def save_final_exam_for_owner(
    course_id: uuid.UUID,
    exam_data: FinalExamManageUpsert,
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> FinalExamManageResponse:
    course = db.query(Course).filter(Course.id == course_id, Course.owner_id == current_user.id).first()
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    exam = db.query(CourseFinalExam).filter(CourseFinalExam.course_id == course_id).first()
    if exam and db.query(FinalExamAttempt.id).filter(FinalExamAttempt.course_id == course_id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Final exam already has attempts; editing it would invalidate learner results")
    if exam is None:
        exam = CourseFinalExam(course_id=course_id, title=exam_data.title, passing_score=exam_data.passing_score)
        db.add(exam)
        db.flush()
    else:
        exam.title = exam_data.title
        exam.passing_score = exam_data.passing_score
        db.query(CourseFinalExamQuestion).filter(CourseFinalExamQuestion.exam_id == exam.id).delete(synchronize_session=False)
    for position, question in enumerate(exam_data.questions, start=1):
        db.add(CourseFinalExamQuestion(
            exam_id=exam.id, prompt=question.prompt, choices=question.choices,
            correct_index=question.correct_index, position=position,
        ))
    db.query(CourseTranslation).filter(CourseTranslation.course_id == course.id).update({CourseTranslation.final_exam_content: None}, synchronize_session=False)
    db.commit()
    db.refresh(exam)
    return to_final_exam_manage_response(exam, db)


@router.get("/courses/{course_id}/final-exam", response_model=FinalExamResponse)
def read_final_exam(
    course_id: uuid.UUID,
    language: str = Query("uz", pattern="^(uz|en|ru|ko)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FinalExamResponse:
    course, exam, questions = get_final_exam_context(course_id, current_user.id, db)
    latest = (db.query(FinalExamAttempt).filter(
        FinalExamAttempt.course_id == course_id, FinalExamAttempt.user_id == current_user.id
    ).order_by(FinalExamAttempt.submitted_at.desc()).first())
    localized = get_final_exam_content_translation(course, exam, questions, language, db)
    title = localized["title"] if localized else exam.title
    return FinalExamResponse(
        course_id=course_id,
        title=title,
        passing_score=exam.passing_score,
        questions=[FinalExamQuestionResponse(
            id=question.id, lesson_title=title,
            prompt=(localized["questions"][index]["prompt"] if localized else question.prompt),
            choices=(localized["questions"][index]["choices"] if localized else question.choices), position=question.position
        ) for index, question in enumerate(questions)],
        latest_score=latest.score_percent if latest else None,
        passed=any(attempt.passed for attempt in db.query(FinalExamAttempt).filter(
            FinalExamAttempt.course_id == course_id, FinalExamAttempt.user_id == current_user.id
        ).all()),
    )


@router.post("/courses/{course_id}/final-exam/attempts", response_model=FinalExamAttemptResponse, status_code=status.HTTP_201_CREATED)
def submit_final_exam(
    course_id: uuid.UUID,
    attempt_data: FinalExamAttemptCreate,
    passkey_proof: str | None = Header(default=None, alias="X-Passkey-Proof"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FinalExamAttemptResponse:
    _, exam, questions = get_final_exam_context(course_id, current_user.id, db)
    question_by_id = {question.id: question for question in questions}
    selected = {str(answer.question_id): answer.selected_index for answer in attempt_data.answers}
    if len(selected) != len(attempt_data.answers) or set(selected) != {str(question_id) for question_id in question_by_id}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Submit exactly one answer for every exam question")
    correct = 0
    for question_id, choice_index in selected.items():
        question = question_by_id[uuid.UUID(question_id)]
        if choice_index >= len(question.choices):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Selected choice is out of range")
        correct += int(choice_index == question.correct_index)
    score = round(correct / len(question_by_id) * 100, 2)
    consume_passkey_proof(passkey_proof, current_user.id, "final_exam", db)
    attempt = FinalExamAttempt(
        user_id=current_user.id, course_id=course_id, answers=selected, correct_count=correct,
        total_questions=len(question_by_id), score_percent=score, passed=score >= exam.passing_score,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return FinalExamAttemptResponse(
        id=attempt.id, course_id=course_id, correct_count=correct, total_questions=len(question_by_id),
        score_percent=score, passed=attempt.passed, submitted_at=attempt.submitted_at,
    )

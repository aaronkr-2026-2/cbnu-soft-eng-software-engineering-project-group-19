from sqlalchemy.orm import Session

from app.core.ai import AIConfigurationError, AIProviderError, translate_assessment, translate_course, translate_lesson, translate_module
from app.models import Course, CourseFinalExam, CourseFinalExamQuestion, CourseModule, CourseModuleTranslation, CourseTranslation, Lesson, LessonTranslation, Quiz, QuizQuestion


def get_course_translation(course: Course, language: str, db: Session) -> CourseTranslation | None:
    if language == course.language:
        return None
    translation = db.query(CourseTranslation).filter(
        CourseTranslation.course_id == course.id,
        CourseTranslation.language == language,
    ).first()
    if translation:
        return translation
    try:
        localized = translate_course(course.title, course.description, course.category, language)
    except (AIConfigurationError, AIProviderError):
        return None
    translation = CourseTranslation(course_id=course.id, language=language, **localized)
    db.add(translation)
    db.commit()
    db.refresh(translation)
    return translation


def get_lesson_translation(lesson: Lesson, course: Course, language: str, db: Session) -> LessonTranslation | None:
    if language == course.language:
        return None
    translation = db.query(LessonTranslation).filter(
        LessonTranslation.lesson_id == lesson.id,
        LessonTranslation.language == language,
    ).first()
    if translation:
        return translation
    try:
        localized = translate_lesson(lesson.title, lesson.content, language)
    except (AIConfigurationError, AIProviderError):
        return None
    translation = LessonTranslation(lesson_id=lesson.id, language=language, **localized)
    db.add(translation)
    db.commit()
    db.refresh(translation)
    return translation


def get_module_translation(module: CourseModule, course: Course, language: str, db: Session) -> CourseModuleTranslation | None:
    if language == course.language:
        return None
    translation = db.query(CourseModuleTranslation).filter(
        CourseModuleTranslation.module_id == module.id,
        CourseModuleTranslation.language == language,
    ).first()
    if translation:
        return translation
    try:
        translated_title = translate_module(module.title, language)
    except (AIConfigurationError, AIProviderError):
        return None
    translation = CourseModuleTranslation(module_id=module.id, language=language, title=translated_title)
    db.add(translation)
    db.commit()
    db.refresh(translation)
    return translation


def get_quiz_content_translation(lesson: Lesson, course: Course, quiz: Quiz, questions: list[QuizQuestion], language: str, db: Session) -> dict | None:
    if language == course.language:
        return None
    translation = get_lesson_translation(lesson, course, language, db)
    if translation is None:
        return None
    if translation.quiz_content:
        return translation.quiz_content
    try:
        localized = translate_assessment(quiz.title, [{"prompt": q.prompt, "choices": q.choices} for q in questions], language)
    except (AIConfigurationError, AIProviderError):
        return None
    translation.quiz_content = localized
    db.commit()
    return localized


def get_final_exam_content_translation(course: Course, exam: CourseFinalExam, questions: list[CourseFinalExamQuestion], language: str, db: Session) -> dict | None:
    if language == course.language:
        return None
    translation = get_course_translation(course, language, db)
    if translation is None:
        return None
    if translation.final_exam_content:
        return translation.final_exam_content
    try:
        localized = translate_assessment(exam.title, [{"prompt": q.prompt, "choices": q.choices} for q in questions], language)
    except (AIConfigurationError, AIProviderError):
        return None
    translation.final_exam_content = localized
    db.commit()
    return localized

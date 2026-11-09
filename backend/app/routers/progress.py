import uuid
from copy import deepcopy
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.schemes.progress import CourseProgressResponse, LessonProgressResponse, VideoWatchReport, VideoWatchResponse
from app.database import get_db
from app.models import Course, Enrollment, Lesson, LessonProgress, User, VideoWatchProgress

router = APIRouter(prefix="/courses/{course_id}/progress", tags=["Progress"])


def require_enrollment(course_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> None:
    enrollment = (
        db.query(Enrollment)
        .filter(Enrollment.course_id == course_id, Enrollment.user_id == user_id)
        .first()
    )
    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Enroll in the course to track progress",
        )


def _video_watch_items(watch: VideoWatchProgress | None) -> dict[str, dict]:
    if watch is None:
        return {}
    if watch.item_progress:
        items = deepcopy(watch.item_progress)
        for item in items.values():
            if "intervals" not in item:
                covered = min(float(item.get("watched_seconds", 0)), float(item.get("last_position_seconds", 0)))
                item["intervals"] = [[0.0, covered]] if covered > 0 else []
        return items
    # Keep progress made before per-item tracking was introduced.
    return {"0": {
        "watched_seconds": watch.watched_seconds,
        "duration_seconds": watch.duration_seconds,
        "last_position_seconds": watch.last_position_seconds,
        "last_reported_at": watch.last_reported_at.isoformat(),
        "intervals": [[0.0, min(watch.watched_seconds, watch.last_position_seconds)]] if watch.watched_seconds > 0 else [],
    }}


def _covered_seconds(item: dict) -> float:
    intervals = sorted(item.get("intervals", []), key=lambda interval: float(interval[0]))
    total = 0.0
    end = -1.0
    for start, stop in intervals:
        start, stop = float(start), float(stop)
        if stop <= start:
            continue
        total += stop - start if start >= end else max(0.0, stop - end)
        end = max(end, stop)
    return total


def _contiguous_position(item: dict) -> float:
    position = 0.0
    for start, end in sorted(item.get("intervals", []), key=lambda interval: float(interval[0])):
        start, end = float(start), float(end)
        if start > position + 0.25:
            break
        position = max(position, end)
    return position


def video_watch_response(watch: VideoWatchProgress | None, item_index: int = 0) -> VideoWatchResponse:
    item_count = watch.item_count if watch else 1
    items = _video_watch_items(watch)
    total_watched = sum(_covered_seconds(item) for item in items.values())
    total_duration = sum(float(item.get("duration_seconds", 0)) for item in items.values())
    item_percentages = [
        min(100.0, _covered_seconds(item) / float(item["duration_seconds"]) * 100)
        for item in items.values() if float(item.get("duration_seconds", 0)) > 0
    ]
    percent = round(sum(item_percentages) / item_count, 1) if item_count else 0.0
    def item_finished(item: dict) -> bool:
        duration = float(item.get("duration_seconds", 0))
        tolerance = min(1.5, max(0.5, duration * 0.005))
        return (
            bool(item.get("completed"))
            and _covered_seconds(item) >= duration - tolerance
            and float(item.get("last_position_seconds", 0)) >= duration - tolerance
        )

    can_complete = item_count > 0 and all(
        item_finished(items.get(str(index), {})) for index in range(item_count)
    )
    selected_item = items.get(str(item_index), {})
    furthest = _contiguous_position(selected_item) if selected_item else 0.0
    return VideoWatchResponse(
        watched_seconds=total_watched,
        duration_seconds=total_duration,
        furthest_position_seconds=furthest,
        completion_percent=min(100.0, percent),
        can_complete=can_complete,
        item_count=item_count,
    )


def to_response(progress: LessonProgress, course_id: uuid.UUID) -> LessonProgressResponse:
    return LessonProgressResponse(
        course_id=str(course_id),
        lesson_id=str(progress.lesson_id),
        completed_at=progress.completed_at,
    )


@router.post(
    "/lessons/{lesson_id}/complete",
    response_model=LessonProgressResponse,
)
def complete_lesson(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LessonProgressResponse:
    require_enrollment(course_id, current_user.id, db)

    lesson = (
        db.query(Lesson)
        .filter(Lesson.id == lesson_id, Lesson.course_id == course_id)
        .first()
    )
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found in this course",
        )

    if lesson.resource_type == "video" and (lesson.resource_key or lesson.external_video_url):
        watch = db.query(VideoWatchProgress).filter_by(user_id=current_user.id, lesson_id=lesson.id).first()
        if not video_watch_response(watch).can_complete:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Watch the video to the end before completing this lesson")

    progress = (
        db.query(LessonProgress)
        .filter(
            LessonProgress.user_id == current_user.id,
            LessonProgress.lesson_id == lesson.id,
        )
        .first()
    )
    if progress is None:
        progress = LessonProgress(user_id=current_user.id, lesson_id=lesson.id)
        db.add(progress)
        db.commit()
        db.refresh(progress)

    return to_response(progress, course_id)


@router.post("/lessons/{lesson_id}/video-watch", response_model=VideoWatchResponse)
def report_video_watch(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    report: VideoWatchReport,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VideoWatchResponse:
    require_enrollment(course_id, current_user.id, db)
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id, Lesson.course_id == course_id).first()
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found in this course")
    if lesson.resource_type != "video" or not (lesson.resource_key or lesson.external_video_url):
        raise HTTPException(status_code=409, detail="This lesson has no video")
    if report.position_seconds > report.duration_seconds + 2:
        raise HTTPException(status_code=422, detail="Video position exceeds its duration")

    now = datetime.now(timezone.utc)
    watch = db.query(VideoWatchProgress).filter_by(user_id=current_user.id, lesson_id=lesson.id).first()
    if watch is None:
        watch = VideoWatchProgress(
            user_id=current_user.id, lesson_id=lesson.id, watched_seconds=0,
            duration_seconds=0, last_position_seconds=report.position_seconds,
            last_reported_at=now, item_count=report.item_count, item_progress={},
        )
        db.add(watch)
    items = deepcopy(watch.item_progress) if watch.item_progress is not None else _video_watch_items(watch)
    if watch.item_count != report.item_count:
        # A different playlist size is a changed viewing requirement.
        items = {}
        watch.item_count = report.item_count
    if report.item_index >= report.item_count:
        raise HTTPException(status_code=422, detail="Video item index exceeds the playlist size")
    item_key = str(report.item_index)
    item = items.get(item_key)
    if item is None or abs(float(item.get("duration_seconds", report.duration_seconds)) - report.duration_seconds) > max(2, report.duration_seconds * 0.02):
        item = {
            "watched_seconds": 0.0,
            "duration_seconds": report.duration_seconds,
            "last_position_seconds": report.position_seconds,
            "last_reported_at": now.isoformat(),
            "intervals": [],
            "completed": False,
        }
    else:
        item.setdefault("intervals", [])
        item.setdefault("completed", False)
        if not item["intervals"] and float(item.get("watched_seconds", 0)) > 0:
            legacy_covered = min(float(item["watched_seconds"]), float(item.get("last_position_seconds", 0)))
            if legacy_covered > 0:
                item["intervals"] = [[0.0, legacy_covered]]
        last_reported = datetime.fromisoformat(item["last_reported_at"])
        if last_reported.tzinfo is None:
            last_reported = last_reported.replace(tzinfo=timezone.utc)
        elapsed = max(0.0, (now - last_reported).total_seconds())
        position_delta = report.position_seconds - float(item["last_position_seconds"])
        movement_valid = abs(position_delta) <= elapsed * report.playback_rate + 1.5
        if movement_valid and position_delta > 0:
            interval_start = max(0.0, float(item["last_position_seconds"]))
            interval_end = min(report.duration_seconds, report.position_seconds)
            if interval_end > interval_start:
                item["intervals"].append([interval_start, interval_end])
                merged = []
                for start, end in sorted(item["intervals"], key=lambda interval: float(interval[0])):
                    if not merged or float(start) > float(merged[-1][1]) + 0.05:
                        merged.append([float(start), float(end)])
                    else:
                        merged[-1][1] = max(float(merged[-1][1]), float(end))
                item["intervals"] = merged
                item["watched_seconds"] = _covered_seconds(item)
        # Record the new cursor even after a seek, but add no coverage for the
        # skipped interval. The learner can still watch the missing section.
        item["last_position_seconds"] = report.position_seconds
        tolerance = min(1.5, max(0.5, report.duration_seconds * 0.005))
        if report.ended and movement_valid and report.position_seconds >= report.duration_seconds - tolerance:
            item["completed"] = _covered_seconds(item) >= report.duration_seconds - tolerance
        # A seek adds no covered interval; later playback can fill the gap.
        item["last_reported_at"] = now.isoformat()
    items[item_key] = item
    watch.item_progress = items
    watch.watched_seconds = sum(_covered_seconds(value) for value in items.values())
    watch.duration_seconds = sum(float(value.get("duration_seconds", 0)) for value in items.values())
    watch.last_position_seconds = float(item.get("last_position_seconds", 0))
    watch.last_reported_at = now
    db.commit()
    db.refresh(watch)
    return video_watch_response(watch, report.item_index)


@router.get("/lessons/{lesson_id}/video-watch", response_model=VideoWatchResponse)
def get_video_watch_progress(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    item_index: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VideoWatchResponse:
    require_enrollment(course_id, current_user.id, db)
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id, Lesson.course_id == course_id).first()
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found in this course")
    if lesson.resource_type != "video" or not (lesson.resource_key or lesson.external_video_url):
        raise HTTPException(status_code=409, detail="This lesson has no video")
    watch = db.query(VideoWatchProgress).filter_by(user_id=current_user.id, lesson_id=lesson.id).first()
    return video_watch_response(watch, item_index)


@router.get("/me", response_model=CourseProgressResponse)
def get_my_course_progress(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CourseProgressResponse:
    course = db.query(Course).filter(Course.id == course_id).first()
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )
    require_enrollment(course_id, current_user.id, db)

    total_lessons = db.query(Lesson).filter(Lesson.course_id == course_id).count()
    completed_ids = [
        row[0]
        for row in (
            db.query(LessonProgress.lesson_id)
            .join(Lesson, Lesson.id == LessonProgress.lesson_id)
            .filter(
                LessonProgress.user_id == current_user.id,
                Lesson.course_id == course_id,
            )
            .all()
        )
    ]
    completed_count = len(completed_ids)
    progress_percent = round(completed_count / total_lessons * 100, 2) if total_lessons else 0.0

    return CourseProgressResponse(
        course_id=str(course_id),
        total_lessons=total_lessons,
        completed_lessons=completed_count,
        progress_percent=progress_percent,
        completed_lesson_ids=[str(lesson_id) for lesson_id in completed_ids],
    )

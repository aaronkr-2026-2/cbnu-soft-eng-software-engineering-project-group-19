"""Replace generated lesson videos with public YouTube lessons."""

from importlib import import_module
from uuid import UUID

import sqlalchemy as sa
from alembic import op

from migrations.academy_video_content import IT_COURSES, video_key
from migrations.language_starters import COPY, LESSONS, PHRASES, USAGE

revision = "92f3ab46c18d"
down_revision = "8cde17f45a20"
branch_labels = None
depends_on = None

bundled = import_module("migrations.versions.8cde17f45a20_academy_lesson_videos")
YOUTUBE = {
    "uz": ("UQXVGoV-JFA", "WFUJZtuoTzk", "qX2VYs5ihT4"),
    "en": ("I_tRSrPru94", "hycQfflSS4c", "DPYJQSA-x50"),
    "ru": ("f8PUjIaoSyQ", "QtGf6vkJDzg", "QBUOq_JL7zg"),
    "ko": ("gwObbXUJkBY", "U66nI-6q1c8", "aEWGmuEFjsI"),
    "html": {
        "uz": ("0yqDnBf_0B0", "_RsHpkPg0EI", "ue6gjdSuIJA"),
        "en": ("YOsMJQfwqow", "tFUdY3X-V5A", "4tJR9VBEGw8"),
        "ru": ("B5RhnA-EUsU", "tm13AvnOx5k", "PoJaRi7Ug7Q"),
        "ko": ("T7h8O7dpJIg", "7neASrWEFEM", "ZhvyBHOnYB8"),
    },
    "python": {
        "uz": ("4-Sj_owtx3Q", "PQTJT44_5L8", "_aDyBPYAeyU"),
        "en": ("DB9Cq6TSTuQ", "KWgYha0clzw", "vg7Hwd9TANY"),
        "ru": ("8hzpSR_Qaj8", "5BRzUFyOWYI", "NUrEyTW4JuU"),
        "ko": ("brYrRAEyKYM", "VWWbcnIIp24", "QQ2HtuuKnf8"),
    },
}


def replace_videos(connection, *, restore=False):
    lesson = bundled.LESSON
    for course_id, subject, source in bundled.course_videos():
        video_ids = YOUTUBE[subject][source] if subject in {"html", "python"} else YOUTUBE[subject]
        for position, video_id in enumerate(video_ids, 1):
            key = video_key(subject, source, position)
            url = f"https://www.youtube.com/watch?v={video_id}"
            if restore:
                match = (lesson.c.external_video_url == url, lesson.c.resource_key.is_(None))
                fields = dict(
                    resource_key=key, resource_mime_type="video/mp4", external_video_url=None
                )
            else:
                match = (lesson.c.resource_key == key, lesson.c.external_video_url.is_(None))
                fields = dict(resource_key=None, resource_mime_type=None, external_video_url=url)

            connection.execute(
                lesson.update()
                .where(
                    lesson.c.course_id == course_id,
                    lesson.c.position == position,
                    lesson.c.resource_type == "video",
                    *match,
                )
                .values(**fields)
            )


def add_starter_lesson_translations(connection):
    lesson = sa.table("lessons", sa.column("id", sa.Uuid()))
    translation = sa.table(
        "lesson_translations",
        sa.column("id", sa.Uuid()),
        sa.column("lesson_id", sa.Uuid()),
        sa.column("language", sa.String()),
        sa.column("title", sa.String()),
        sa.column("content", sa.Text()),
    )
    for source, targets in USAGE.items():
        for target in targets:
            course_id = bundled.starter_id(source, target)
            for unit, names in enumerate(LESSONS):
                lesson_id = bundled.starter_id(course_id, "lesson", unit)
                if (
                    connection.scalar(sa.select(lesson.c.id).where(lesson.c.id == lesson_id))
                    is None
                ):
                    continue
                for locale in COPY.keys() - {source}:
                    exists = sa.select(translation.c.id).where(
                        translation.c.lesson_id == lesson_id, translation.c.language == locale
                    )
                    if connection.scalar(exists) is not None:
                        continue
                    title, opening = names[locale]
                    usage = USAGE[locale].get(target)
                    phrases = PHRASES[unit][target]
                    if locale != target:
                        phrases = [
                            f"{foreign} — {native}"
                            for foreign, native in zip(phrases, PHRASES[unit][locale], strict=True)
                        ]
                    blocks = [opening]
                    if usage:
                        blocks.append(usage[unit])
                    blocks.extend(("\n".join(phrases), COPY[locale]["practice"]))
                    connection.execute(
                        translation.insert().values(
                            id=bundled.starter_id(lesson_id, "translation", locale),
                            lesson_id=lesson_id,
                            language=locale,
                            title=title,
                            content="\n\n".join(blocks),
                        )
                    )


def add_it_course_translations(connection):
    course = sa.table(
        "courses",
        sa.column("id", sa.Uuid()),
        sa.column("language", sa.String()),
        sa.column("title", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("category", sa.String()),
    )
    translation = sa.table(
        "course_translations",
        sa.column("id", sa.Uuid()),
        sa.column("course_id", sa.Uuid()),
        sa.column("language", sa.String()),
        sa.column("title", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("category", sa.String()),
    )
    for subject in ("html", "python"):
        ids = [UUID(courses[subject]) for courses in IT_COURSES.values()]
        editions = (
            connection.execute(
                sa.select(
                    course.c.id,
                    course.c.language,
                    course.c.title,
                    course.c.description,
                    course.c.category,
                ).where(course.c.id.in_(ids))
            )
            .mappings()
            .all()
        )
        for edition in editions:
            for localized in editions:
                locale = localized["language"]
                if locale == edition["language"]:
                    continue
                exists = sa.select(translation.c.id).where(
                    translation.c.course_id == edition["id"], translation.c.language == locale
                )
                if connection.scalar(exists) is not None:
                    continue
                connection.execute(
                    translation.insert().values(
                        id=bundled.starter_id(edition["id"], "title", locale),
                        course_id=edition["id"],
                        language=locale,
                        title=localized["title"],
                        description=localized["description"],
                        category=localized["category"],
                    )
                )


def upgrade():
    connection = op.get_bind()
    replace_videos(connection)
    add_starter_lesson_translations(connection)
    add_it_course_translations(connection)


def downgrade():
    replace_videos(op.get_bind(), restore=True)

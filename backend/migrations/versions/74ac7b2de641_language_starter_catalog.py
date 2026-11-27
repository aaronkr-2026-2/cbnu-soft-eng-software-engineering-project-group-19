"""Publish the academy's initial multilingual language courses."""

from secrets import token_urlsafe
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op
from pwdlib import PasswordHash

from migrations.language_starters import COPY, LESSONS, PHRASES, USAGE, build_question

revision = "74ac7b2de641"
down_revision = "63ae21b90d45"
branch_labels = None
depends_on = None


def content_id(*parts):
    key = "/".join(("scholward-academy", "language-starters", *map(str, parts)))
    return uuid5(NAMESPACE_URL, key)


def seed_language_courses(connection):
    metadata = sa.MetaData()
    ids = {
        "users": (),
        "courses": ("owner_id",),
        "course_translations": ("course_id",),
        "lessons": ("course_id",),
        "quizzes": ("lesson_id",),
        "quiz_questions": ("quiz_id",),
        "course_final_exams": ("course_id",),
        "course_final_exam_questions": ("exam_id",),
    }
    tables = {
        name: sa.Table(
            name,
            metadata,
            sa.Column("id", sa.Uuid(), primary_key=True),
            *(sa.Column(column, sa.Uuid()) for column in related_ids),
            autoload_with=connection,
        )
        for name, related_ids in ids.items()
    }

    def insert(table_name, **fields):
        connection.execute(tables[table_name].insert().values(**fields))

    def exists(table_name, item_id):
        table = tables[table_name]
        return connection.execute(sa.select(table.c.id).where(table.c.id == item_id)).first()

    owner_id = content_id("owner")
    if not exists("users", owner_id):
        insert(
            "users",
            id=owner_id,
            email="language-catalog@scholward.invalid",
            full_name="SCHOLWARD Academy",
            account_type="author",
            hashed_password=PasswordHash.recommended().hash(token_urlsafe(48)),
            token_version=0,
            preferred_language="uz",
            is_active=False,
        )

    for source, copy in COPY.items():
        for target, usage in USAGE[source].items():
            course_id = content_id(source, target)
            if exists("courses", course_id):
                continue
            title = copy["titles"][target]
            insert(
                "courses",
                id=course_id,
                owner_id=owner_id,
                title=title,
                description=copy["description"],
                category=copy["category"],
                price_uzs=0,
                language=source,
                level="beginner",
                is_published=True,
                banner_key=f"{course_id.hex}.svg",
            )
            for locale, translation in COPY.items():
                if locale == source:
                    continue
                insert(
                    "course_translations",
                    id=content_id(course_id, "title", locale),
                    course_id=course_id,
                    language=locale,
                    title=translation["titles"][target],
                    description=translation["description"],
                    category=translation["category"],
                )
            for unit, names in enumerate(LESSONS):
                lesson_id = content_id(course_id, "lesson", unit)
                lesson_title, opening = names[source]
                blocks = [
                    opening,
                    usage[unit],
                    "\n".join(
                        f"{foreign} — {native}"
                        for foreign, native in zip(
                            PHRASES[unit][target], PHRASES[unit][source], strict=True
                        )
                    ),
                    copy["practice"],
                ]
                insert(
                    "lessons",
                    id=lesson_id,
                    course_id=course_id,
                    title=lesson_title,
                    content="\n\n".join(blocks),
                    position=unit + 1,
                    resource_type="text",
                )
                quiz_id = content_id(lesson_id, "quiz")
                insert(
                    "quizzes",
                    id=quiz_id,
                    lesson_id=lesson_id,
                    title=copy["quiz"],
                    passing_score=75,
                )
                for index in range(4):
                    question = build_question(unit, source, target, index, reverse=False)
                    insert(
                        "quiz_questions",
                        id=content_id(quiz_id, index),
                        quiz_id=quiz_id,
                        position=index + 1,
                        explanation=copy["explanation"].format(
                            PHRASES[unit][target][index], PHRASES[unit][source][index]
                        ),
                        points=1,
                        **question,
                    )
            exam_id = content_id(course_id, "exam")
            insert(
                "course_final_exams",
                id=exam_id,
                course_id=course_id,
                title=copy["exam"],
                passing_score=75,
            )
            for unit in range(len(LESSONS)):
                for index in range(4):
                    position = unit * 4 + index + 1
                    insert(
                        "course_final_exam_questions",
                        id=content_id(exam_id, position),
                        exam_id=exam_id,
                        position=position,
                        **build_question(unit, source, target, index + 2, reverse=True),
                    )


def upgrade():
    seed_language_courses(op.get_bind())


def downgrade():
    # Keep published courses and their enrollments, quiz results and certificates.
    pass

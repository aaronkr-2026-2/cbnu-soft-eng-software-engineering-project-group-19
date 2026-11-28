"""Attach bundled videos to language lessons and unfilled IT lessons."""

from importlib import import_module
from uuid import UUID

import sqlalchemy as sa
from alembic import op

from migrations.academy_video_content import IT_COURSES, video_key
from migrations.language_starters import LESSONS, USAGE

revision = "8cde17f45a20"
down_revision = "74ac7b2de641"
branch_labels = None
depends_on = None

starter_id = import_module("migrations.versions.74ac7b2de641_language_starter_catalog").content_id

LESSON = sa.table(
    "lessons",
    sa.column("course_id", sa.Uuid()),
    sa.column("position", sa.Integer()),
    sa.column("resource_type", sa.String()),
    sa.column("resource_key", sa.String()),
    sa.column("resource_mime_type", sa.String()),
    sa.column("external_video_url", sa.String()),
)


def course_videos():
    for source, targets in USAGE.items():
        for target in targets:
            yield starter_id(source, target), target, source
        for subject, course_id in IT_COURSES[source].items():
            yield UUID(course_id), subject, source


def attach_bundled_videos(connection):
    for course_id, subject, source in course_videos():
        for position in range(1, len(LESSONS) + 1):
            connection.execute(
                LESSON.update()
                .where(
                    LESSON.c.course_id == course_id,
                    LESSON.c.position == position,
                    LESSON.c.resource_type == "text",
                    LESSON.c.resource_key.is_(None),
                    LESSON.c.external_video_url.is_(None),
                )
                .values(
                    resource_type="video",
                    resource_key=video_key(subject, source, position),
                    resource_mime_type="video/mp4",
                )
            )


def upgrade():
    attach_bundled_videos(op.get_bind())


def downgrade():
    for course_id, subject, source in course_videos():
        for position in range(1, len(LESSONS) + 1):
            op.execute(
                LESSON.update()
                .where(
                    LESSON.c.course_id == course_id,
                    LESSON.c.position == position,
                    LESSON.c.resource_key == video_key(subject, source, position),
                )
                .values(resource_type="text", resource_key=None, resource_mime_type=None)
            )

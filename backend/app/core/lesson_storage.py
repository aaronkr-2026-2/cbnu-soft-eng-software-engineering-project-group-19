import re
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryFile
from typing import BinaryIO

from fastapi import HTTPException
from fastapi.responses import FileResponse, Response, StreamingResponse
from sqlalchemy import delete, func, insert, select
from sqlalchemy.orm import Session

from app.models import LessonResourceChunk, LessonResourceFile

RESOURCE_DIR = Path(__file__).resolve().parents[2] / "storage" / "course-materials"
RESOURCE_CHUNK_BYTES = 1024 * 1024
MAX_TOTAL_RESOURCE_BYTES = 512 * 1024 * 1024
RESOURCE_QUOTA_LOCK = 1248391761
RESOURCE_HEADERS = {
    "Cache-Control": "private, no-store",
    "X-Content-Type-Options": "nosniff",
    "Accept-Ranges": "bytes",
}


def save_resource(
    db: Session, key: str, size: int, source: BinaryIO, replacing: str | None = None
) -> None:
    if db.get_bind().dialect.name == "postgresql":
        db.execute(select(func.pg_advisory_xact_lock(RESOURCE_QUOTA_LOCK)))
    total = select(func.coalesce(func.sum(LessonResourceFile.size), 0))
    if replacing:
        total = total.where(LessonResourceFile.key != replacing)
    if db.scalar(total) + size > MAX_TOTAL_RESOURCE_BYTES:
        raise HTTPException(status_code=413, detail="Course material storage limit reached")

    db.execute(insert(LessonResourceFile).values(key=key, size=size))
    for position, chunk in enumerate(iter(lambda: source.read(RESOURCE_CHUNK_BYTES), b"")):
        db.execute(insert(LessonResourceChunk).values(file_key=key, position=position, data=chunk))


def delete_resources(db: Session, keys: list[str]) -> None:
    if keys:
        db.execute(delete(LessonResourceChunk).where(LessonResourceChunk.file_key.in_(keys)))
        db.execute(delete(LessonResourceFile).where(LessonResourceFile.key.in_(keys)))


def legacy_resource_path(key: str) -> Path:
    return RESOURCE_DIR / Path(key).name


def iter_resource(db: Session, key: str, start: int, end: int) -> Iterator[bytes]:
    first, last = start // RESOURCE_CHUNK_BYTES, end // RESOURCE_CHUNK_BYTES
    chunks = db.execute(
        select(LessonResourceChunk.position, LessonResourceChunk.data)
        .where(
            LessonResourceChunk.file_key == key,
            LessonResourceChunk.position.between(first, last),
        )
        .order_by(LessonResourceChunk.position),
        execution_options={"yield_per": 1},
    )
    with chunks:
        for position, data in chunks:
            offset = position * RESOURCE_CHUNK_BYTES
            yield data[max(0, start - offset) : end - offset + 1]


def resource_response(db: Session, key: str, media_type: str, range_header: str | None) -> Response:
    resource = db.scalar(
        select(LessonResourceFile).where(LessonResourceFile.key == key).with_for_update(read=True)
    )
    if resource is None:
        path = legacy_resource_path(key).resolve()
        if path.parent != RESOURCE_DIR.resolve() or not path.is_file():
            raise HTTPException(status_code=404, detail="Course resource not found")
        return FileResponse(path, media_type=media_type, headers=RESOURCE_HEADERS)

    size = resource.size
    start, end = 0, size - 1
    headers = RESOURCE_HEADERS.copy()
    # Browsers typically request one interval. Serve the full resource for compound ranges.
    if range_header and "," not in range_header:
        match = re.fullmatch(r"bytes=([0-9]{0,20})-([0-9]{0,20})", range_header)
        if match and any(match.groups()):
            first, last = match.groups()
            if first:
                start = int(first)
                if last:
                    end = min(int(last), end)
            else:
                start = max(0, size - int(last))
        else:
            start = size
        if start >= size or end < start:
            return Response(
                status_code=416, headers={**headers, "Content-Range": f"bytes */{size}"}
            )
        headers["Content-Range"] = f"bytes {start}-{end}/{size}"
    headers["Content-Length"] = str(end - start + 1)
    return StreamingResponse(
        iter_resource(db, key, start, end),
        status_code=206 if "Content-Range" in headers else 200,
        media_type=media_type,
        headers=headers,
    )


@contextmanager
def open_resource(db: Session, key: str) -> Iterator[BinaryIO]:
    resource = db.scalar(
        select(LessonResourceFile).where(LessonResourceFile.key == key).with_for_update(read=True)
    )
    if resource is None:
        path = legacy_resource_path(key).resolve()
        if path.parent != RESOURCE_DIR.resolve() or not path.is_file():
            raise HTTPException(status_code=404, detail="Uploaded lesson PDF was not found")
        with path.open("rb") as file:
            yield file
        return
    with TemporaryFile() as file:
        for chunk in iter_resource(db, key, 0, resource.size - 1):
            file.write(chunk)
        file.seek(0)
        yield file

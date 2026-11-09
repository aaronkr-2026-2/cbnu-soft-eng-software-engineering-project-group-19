FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

RUN apt-get update \
    && apt-get install --no-install-recommends -y libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv/studyflow
COPY backend/requirements.txt /srv/studyflow/backend/requirements.txt
RUN pip install --no-cache-dir -r /srv/studyflow/backend/requirements.txt

COPY backend /srv/studyflow/backend
COPY apps/web /srv/studyflow/apps/web
RUN mkdir -p /srv/studyflow/backend/storage/avatars \
    /srv/studyflow/backend/storage/course-materials \
    /srv/studyflow/backend/storage/lesson-banners \
    /srv/studyflow/backend/storage/course-banners

WORKDIR /srv/studyflow/backend
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

# Deployment preparation

## Render deployment

The repository includes a Render Blueprint in `render.yaml`. It provisions the Docker web service and private PostgreSQL connection in Singapore. The app generates its signing key and uses Render's HTTPS hostname for passkeys, links, and redirects.

The Blueprint uses only Render's free plans. Free web services sleep when idle, do not support persistent disks, and free PostgreSQL expires after 30 days. Uploaded local files can disappear when the service restarts. This setup is for a temporary demo; keep backups and don't rely on it for permanent learner data. [Render free service limits](https://render.com/docs/free)

To launch after creating a Render account:

1. Connect the GitHub repository that contains this project to Render.
2. In Render, choose **New → Blueprint** and select that repository's `main` branch.
3. Confirm the web service and database both show the free plan before applying the Blueprint.
4. Enter SMTP credentials in Render's secret prompts if password reset emails are needed. Do not put them in GitHub or `render.yaml`. AI features remain unavailable until an API key is configured.
5. Wait for the first deploy, then verify `/health`, `/app/`, account login, password reset, course enrollment, and certificates.

The Render free subdomain is enough to start; a custom domain can be connected later. Real paid-course checkout additionally needs production GlobalPay merchant credentials, which are not part of this Blueprint.

## What is ready

- The Docker image installs the backend requirements, serves the static web app, and exposes `/health`.
- Docker Compose starts PostgreSQL and waits for it to become healthy.
- The app applies Alembic migrations before starting FastAPI.
- PostgreSQL data uses a named volume. Uploaded course materials, banners, and profile photos use the persistent `backend/storage` mount.
- The app reads runtime secrets from `backend/.env` locally or from the hosting provider's secret settings.

## Local container run

1. Install Docker Desktop.
2. Copy `.env.compose.example` to the repository root as `.env`. To keep the existing app on port 8000 running alongside Docker, set `HOST_PORT=8001` and `WEBAUTHN_ORIGIN=http://localhost:8001` in that file.
3. If `backend/.env` does not already exist, copy `backend/.env.example` to that path. Keep any existing SMTP or AI settings in place.
4. Set a strong random `SECRET_KEY` and a long URL-safe `POSTGRES_PASSWORD`. Leave the local WebAuthn values at `localhost` for a local run.
5. Run `docker compose up --build` from the repository root.
6. Open `http://localhost:8000/app` and check `http://localhost:8000/health`.

Keep the two `.env` files private. They are excluded from Git and the Docker build context. Do not run `docker compose down -v` unless intentionally deleting all local database records.

## Before a public release

1. Choose a hosting provider and configure a public domain with HTTPS.
2. Provision managed PostgreSQL and a private storage service for uploads. The current local `backend/storage` mount is suitable for a single persistent machine; it is not shared between multiple app instances and can be lost with ephemeral hosting disks.
3. Set `DATABASE_URL`, `SECRET_KEY`, `WEBAUTHN_RP_ID`, `WEBAUTHN_ORIGIN`, `PUBLIC_APP_URL`, and `FRONTEND_BASE_URL` in the provider's secret/configuration settings. Use the exact HTTPS site origin for WebAuthn.
4. Configure SMTP for password recovery, AI credentials for AI features, and production GlobalPay merchant credentials if paid courses will be sold.
5. Configure scheduled database and file backups, then verify account registration, login, password reset, course enrollment, lesson playback, payment confirmation, final exams, certificates, and `/health` on the deployed site.

The repository does not contain cloud credentials, a domain, a provider configuration, or a production payment merchant account. The Docker setup is therefore a deployment package, not a live public deployment. The container currently runs one Uvicorn process; use a managed platform and shared object storage before scaling to multiple instances.

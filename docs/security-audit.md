# Security review (Week 10)

Date: 2026-11-06
Scope: source-code review of the FastAPI backend, SQLAlchemy authorization paths, and browser app. This is a course milestone review, not a penetration test or production-host assessment.

## Changes made

- The backend now refuses a missing, short, or known placeholder `SECRET_KEY`. Use a private random value of at least 32 bytes in `backend/.env`; do not commit it.
- Password changes now increment a per-user token version. Tokens issued before the change are rejected on the next authenticated request. Existing tokens without a version are treated as version `0` for compatibility until that user changes their password.
- A database migration adds the token-version column with a zero default for existing users.

## Reviewed protections

- Passwords are stored with `pwdlib`'s recommended password hashing implementation.
- JWT validation pins the configured algorithm, checks expiry, and resolves the subject to an active database user.
- Course and lesson write routes check course ownership; learner access to private course material is checked against enrollment.
- Passkey challenges expire and are consumed once. Step-up proofs are short-lived and consumed during certificate issuance.
- Profile images have a size limit, an allowlist of image types, signature checks, generated filenames, and authenticated retrieval.
- Browser templates escape course and lesson text before placing it in HTML. Bearer tokens are stored in `localStorage`, which increases the impact of any future cross-site scripting bug.

## Remaining work and deployment controls

- Add request throttling for login and registration at the application or trusted edge-proxy layer. No rate limiter is currently configured; ensure the proxy's client-IP handling matches the actual deployment topology.
- Consider moving browser authentication to `HttpOnly`, `Secure`, `SameSite` cookies if the deployment architecture is changed to support them; this requires CSRF protections and coordinated frontend/API changes.
- Review the deployed host's TLS, secret injection, database access, backups, and proxy headers before calling the service production-ready. This repository review did not inspect a live deployment.
- Login errors are generic, but missing accounts skip password verification, so response timing may still differ. A dummy-hash verification can reduce this signal; rate limiting should accompany it.
- Image signatures are checked, but files are not decoded/re-encoded by the server. A production upload pipeline should decode, dimension-limit, and re-encode images.

## Validation

Static checks should confirm the migration chain, Python syntax, JavaScript syntax, and whitespace integrity. The database migration and end-to-end authentication behavior must be exercised in the project's configured development environment before deployment. No live production security test was performed.

# Build Log

## 2026-11-20 · Code style pass

| Linter                   | Errors before | Errors after | Warnings after |
| ------------------------ | ------------: | -----------: | -------------: |
| Ruff (tracked Python)    |            20 |            0 |              0 |
| ESLint (browser scripts) |             6 |            0 |              0 |
| **Total**                |        **26** |        **0** |          **0** |

- Configured pinned Ruff, Prettier, and ESLint. Formatted all tracked files supported by the two
  formatters in a dedicated commit. Enabled format and lint checks on every GitHub push and pull
  request.
- Fixed undefined names and unreachable response code in author quiz management. Removed unused
  imports, a dead frontend auth redirect, and an unused assignment lookup. Renamed quiz generation
  locals and extracted draft validation from the route. Named the PDF, text, and score thresholds.
- Checked three registration inputs on the server. Email must have a valid format, full name must
  be 2–150 characters after trimming, and password must be 8–128 characters. The form displays
  field-level validation messages.
- Handled HTTP errors and lost or timed-out connections in the course catalog. Each error displays
  a localized message and a retry button. Exercised these paths with simulated responses.
- Started the app locally with a temporary SQLite database. Opened the home page, checked the
  course catalog, registered a test learner, and verified the signed-in profile in the browser.
- Backend tests passed (15). Pytest reported one existing Starlette deprecation warning. Docker
  Compose configuration validation passed. The live PostgreSQL migration check remains in CI
  because the local sandbox blocked PostgreSQL shared memory.

### Verification follow-up

- Tested passkey registration options for an authenticated test learner. The configured
  `http://localhost:8000` origin returned HTTP 200 with a challenge and RP ID `localhost`.
  The unconfigured smoke-test origin on port 8175 returned HTTP 403 as expected. Hardware passkey
  enrollment was outside this API check.
- Ran `alembic upgrade head` against a fresh in-memory PGlite PostgreSQL instance over TCP.
  `alembic current` confirmed `c7d4e2a910bf (head)`. CI still checks the migration on standard
  PostgreSQL.

# StudyFlow style guide

## Code

- MUST format Python with Ruff and JavaScript, TypeScript, and supported markup with Prettier so diffs focus on the
  intended change.
- MUST pass Ruff and ESLint with zero errors and warnings so unused code and invalid references
  cannot enter the repository.
- MUST pass the mobile TypeScript check in strict mode with no unused variables or parameters so
  type mistakes and stale code are caught before device testing.
- MUST validate input format and bounds on the server because clients can bypass browser validation.
- MUST keep credentials and reset tokens out of logs, source files, and user-facing errors because
  they grant access.
- SHOULD use names that describe the domain value and name significant thresholds so readers know
  what each value means.
- SHOULD give each function one job and use guard clauses for invalid states so the main flow
  remains easy to follow.
- SHOULD keep formatting, fixes, and refactors in separate commits so changes can be reviewed and
  reverted independently.

## UI

- MUST show an actionable error when an API request fails or the connection drops so users can
  recover without guessing.
- MUST label form controls and announce errors with an accessible status or alert so keyboard and
  screen-reader users can complete the same flows.
- MUST provide web and mobile UI copy in Uzbek, English, Russian, and Korean so the interface stays
  usable after a language change.
- SHOULD reuse established button, form, and spacing styles so users can recognize familiar
  actions.
- SHOULD preserve entered values while users correct errors so they can retry without retyping.

Run `ruff format --check backend tests`, `ruff check backend tests`, `npm run format:check`, `npm run lint`,
and `npm --prefix apps/mobile run check` before pushing. GitHub Actions runs these checks on every push and pull request.

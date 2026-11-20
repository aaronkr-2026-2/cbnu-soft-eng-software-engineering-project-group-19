# StudyFlow style guide

## Code

- MUST format Python with Ruff and supported web and text files with Prettier so diffs focus on the
  intended change.
- MUST pass Ruff and ESLint with zero errors and warnings so unused code and invalid references
  cannot enter the repository.
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
- MUST provide supported UI copy in Uzbek, English, Russian, and Korean so a language change leaves
  the interface usable.
- SHOULD reuse established button, form, and spacing styles so users can recognize familiar
  actions.
- SHOULD preserve entered values while users correct errors so they can retry without retyping.

Run `ruff format --check backend tests`, `ruff check backend tests`, `npm run format:check`, and
`npm run lint` before pushing. GitHub Actions runs these checks on every push and pull request.

# AI Collaboration Log

StudyFlow AI is my project. I wrote the project code, developed its features, and made the main project decisions.

During development, I occasionally used ChatGPT/Codex to help understand errors, suggest or make corrections to some bugs, and run tests. I reviewed the results and decided which changes to use. AI was a support tool; I remained responsible for the project and its final work.

## 2026-11-20 · Code style pass

Codex configured formatting and lint checks, fixed the lint findings, and helped implement
registration validation and recoverable catalog errors. Codex ran the backend suite, simulated
catalog failures and retry, and checked the local learner flow in a browser. The measured results
and verification limits are recorded in the [Build Log](docs/BUILD_LOG.md).

## 2026-11-21 · Mobile code style checks

Codex found that the new mobile TypeScript files were outside the shared formatting check. Codex
extended the Prettier file list, enabled unused-code checks in TypeScript, and wired the mobile
check into GitHub Actions. The [Build Log](docs/BUILD_LOG.md) records the local results.

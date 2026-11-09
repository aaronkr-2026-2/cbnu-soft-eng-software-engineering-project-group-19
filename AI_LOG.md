# AI Collaboration Log

StudyFlow AI is the student's project. The student defined the product, requested the features, made project decisions, and remains responsible for reviewing, understanding, and presenting the work. ChatGPT/Codex was used as an assistant for implementation, documentation, troubleshooting, and checks described below. This log records AI assistance transparently; it does not claim that AI is the project author.

## Week 2–9 project documentation and repository preparation — 2026-11-06
**Tool(s) used:** ChatGPT/Codex and command-line Git tools.
**Student request:** Prepare the existing StudyFlow AI project for the supplied course milestones through Week 9 and the provided GitHub Classroom repository.
**Existing project elements retained:** The existing backend, frontend, migrations, and feature structure were copied from the local project. The course-provided project guide and original repository instructions were preserved.
**AI assistance provided:** Added a project README, `.gitignore`, pitch and vision, assumption-based personas and user stories, a proposed lightweight Agile process, an architecture diagram and critique, and a Week 9 decomposition discussion, and removed pre-existing trailing whitespace found by the submission check. The repository review did not support claims of cloud deployment, team membership, user research, prior Scrum practice, or automated tests, so those claims were not added.
**Issue observed and resolution:** Codex's first attempt to write the milestone files failed because it had not created the `docs/` directory. The shell reported the missing directory; Codex then created it and checked that the files existed. The student should review this entry and add any issues they personally identified.
## README presentation update — 2026-11-06
**Tool(s) used:** ChatGPT/Codex.
**Student request:** Improve the GitHub project page with a StudyFlow AI logo and clickable technology logos.
**Existing project elements retained:** The project description, course milestones, local setup instructions, and deployment caveats.
**AI assistance provided:** Added a reusable SVG wordmark and redesigned the root README with clickable badges linking to the project and official technology documentation. Kept the current local-only deployment status visible.
**Issue observed and resolution:** No student-identified issue was reported for this update; the student should add any they noticed.

## README reference correction — 2026-11-06
**Tool(s) used:** ChatGPT/Codex.
**Student request:** Use the Group 1 README as a visual reference for StudyFlow AI.
**Existing project elements retained:** The StudyFlow logo, clickable technology badges, documentation links, and project overview.
**AI assistance provided:** Removed the individual profile badge that had been added by mistake; the reference was for styling only.
**Issue observed and resolution:** Codex mistook a username visible in the reference context for a requested profile link. The user clarified that it was only an example; the badge was removed.

## README restructuring — 2026-11-06
**Tool(s) used:** ChatGPT/Codex.
**Student request:** Restructure the project README to follow the organization and level of detail of the Group 1 reference.
**Existing project elements retained:** StudyFlow's logo, technology badges, and verified product and setup information.
**AI assistance provided:** Reorganized the README around features, quick start, environment, API, development, architecture, feature-specific guides, deployment, limitations, and course records. Kept the cloud demo status explicit because no public deployment URL is available.
**Issue observed and resolution:** The prior version emphasized visual styling but did not mirror the reference README's overall structure.

## Detailed project README — 2026-11-06
**Tool(s) used:** ChatGPT/Codex.
**Student request:** Expand the StudyFlow project README to match the detail and organization of the Group 1 reference while documenting this project's own implementation.
**Existing project elements retained:** Existing setup, environment, architecture, project milestones, limitations, and feature summary.
**AI assistance provided:** Added the complete route catalog, request examples, learner/course-author/verifier workflows, and a database model overview based on the current FastAPI OpenAPI schema and Pydantic models. Did not invent a live deployment or automated test suite.
**Issue observed and resolution:** The previously listed personal project repository link no longer resolves; this update is made in the active Classroom project repository.

## Security review — 2026-11-06
**Tool(s) used:** ChatGPT/Codex.
**Student request:** Continue the StudyFlow AI project after the Week 9 milestone.
**Existing project elements retained:** The modular monolith architecture, existing login flow, passkey checks, and course ownership rules.
**AI assistance provided:** Added strong JWT signing-key validation and token-version checks so changing a password invalidates existing access tokens. Added the database migration and documented this source review and its deployment follow-up items.
**Issue observed and resolution:** `compileall` could not write bytecode into the protected cache folders; Python syntax was instead checked without creating files.

## Separate learner and author portals — 2026-11-06
**Tool(s) used:** ChatGPT/Codex.
**Student request:** Give ordinary learners and course authors separate sign-in pages and menus.
**Existing project elements retained:** Existing course ownership checks, learner course workflows, passkey support, and the four interface languages.
**AI assistance provided:** Added `learner` and `author` account types, distinct login and registration pages, role-specific dashboards, and backend checks on course, lesson, quiz, and analytics author routes. Existing course owners are migrated as authors; other accounts remain learners.
**Issue observed and resolution:** No issue identified by the student was reported for this change; record any found during review.

## Coursera-inspired author course builder — 2026-11-06
**Tool(s) used:** ChatGPT/Codex.
**Student request:** Remove learner-facing copy from the author account and support courses with text, PDF, video, and audio lessons using Coursera as a reference.
**Existing project elements retained:** The course and ordered-lesson model, author ownership checks, lesson quizzes, final exams, and the four-language interface.
**AI assistance provided:** Author sign-in now opens the course studio first. Added text/PDF/video/audio lesson formats, authenticated author uploads, short-lived resource links for enrolled learners, file type/size checks, and a Coursera-inspired authoring guide. Large files remain local in this prototype; production object storage is documented as future deployment work.
**Issue observed and resolution:** No issue identified by the student was reported; the student should review media upload and playback before submission.

## Lesson cleanup, AI banners, and lesson-language switching — 2026-11-08
**Tool(s) used:** ChatGPT/Codex, FastAPI TestClient, local PostgreSQL, Node syntax checker.
**Student request:** Remove the movie/cinema lesson material, add AI-generated lesson banners, translate lesson content when learners change UI language, and align the content model with Course → Module → Lesson → Learning Material → Quiz/Assignment.
**Existing project elements retained:** Existing course, lesson, quiz, final-exam, enrollment, and progress records; the existing lesson upload flow; current author permissions.
**AI assistance provided:** Removed the three matching “kino/multik” lessons and unpublished their now-empty courses while preserving enrollments. Added a cached per-language lesson translation table and automatic translation lookup for Uzbek, English, Russian, and Korean UI languages. Added automatic lesson-banner generation on save when `AI_API_KEY` is configured, plus an author action to retry or replace it; each generation can incur image API charges. Added signed links for draft banners. Added a content-model note: Module, multi-item Learning Material, and Assignment tables remain a later schema migration because the current prototype stores one text body and one optional file on Lesson.
**Validation:** Applied migration `e8b3c0a1912f`; Node and Python syntax checks passed. API checks passed for source-language fallback, cached translation behavior (mocked provider), banner storage/access (mocked image provider), and missing-key handling. Live AI translation and image generation were not run because `AI_API_KEY` is not configured.
**Issue observed and resolution:** No additional user-caught error was reported during this change; review the migration and content behavior before submission.

## Course catalog localization correction — 2026-11-08
**Tool(s) used:** ChatGPT/Codex, FastAPI TestClient, local PostgreSQL, Node syntax checker.
**Student request:** Fix the issue where switching interface language changed menus but course listings and course details stayed in Uzbek.
**Existing project elements retained:** Course source language, course and lesson IDs, and the source Uzbek text.
**AI assistance provided:** The catalog and enrollment screens were not sending the selected language, and the catalog API had no course-translation lookup. Added cached course title, description, and category translations, wired the catalog/detail/enrollment UI to the selected language, and seeded English/Russian/Korean translations for the three existing demo courses and their six lessons. New content still needs `AI_API_KEY` for automatic translation.
**Validation:** Applied migrations `f1a8c72d9e30` and `a47d1c86e502`. TestClient confirmed all three catalog languages and localized course title, description, category, preview, lesson, and enrollment responses. Mocked translations were removed; seeded course translations are retained.
**Issue observed and resolution:** The first catalog test expected one mock translation call even though the endpoint localized every published course; the assertion was corrected and all checks passed.

## Assessment localization and author ownership — 2026-11-08
**Tool(s) used:** ChatGPT/Codex, local PostgreSQL, FastAPI TestClient, Node syntax checker.
**Student request:** Translate all learner-facing course content and ensure one author cannot manage another author's lessons.
**Existing project elements retained:** Question IDs, correct-answer indexes, choice order, scores, and existing course ownership rules.
**AI assistance provided:** Added cached translations for quiz and final-exam titles, prompts, and choices in English, Russian, and Korean. Translation preserves question and choice order so submitted answers still map to the original correct-answer indexes. The learner UI now requests the selected language. Existing owner checks already scope course and lesson updates/deletes and assessment management to the course owner; these checks were retained and verified with a second author account.
**Validation:** Applied migration `b6c4e97a21fd`; seeded translations for current published demo assessments. Confirmed the Python demo quiz and final exam return Uzbek, English, Russian, and Korean content through the API. A temporary second author received 404 for another author's course/lesson edits and deletes, and 403 for quiz management; the temporary account was deleted. Python syntax, Node syntax, and `git diff --check` passed. Automatic translation of newly authored assessment content requires `AI_API_KEY`; no live provider request is made when it is absent.
**Issue observed and resolution:** The demo database also contained two unpublished cleanup courses, so seeded assessment translations were limited to published courses.

## Course-language catalog, banners, and video completion — 2026-11-08
**Tool(s) used:** ChatGPT/Codex, FastAPI TestClient, local PostgreSQL, Node syntax checker, web research.
**Student request:** Show only courses authored in the selected language; let authors create content in the selected language; add course cover art and more IT courses in each language; and require learners to finish course videos.
**Existing project elements retained:** The course, lesson, quiz, final-exam, enrollment, and progress structures; existing author ownership restrictions; public third-party video hosting.
**AI assistance provided:** The public catalog now filters on the course's original language. The new-course form follows the interface language, and an existing course's language becomes fixed once it has lessons so source text cannot be mislabeled. Added generated course banner illustrations, seeded English/Russian/Korean editions of Python, FastAPI, and Git/Linux, and linked public videos where a suitable language-matched course was found. Added secure YouTube-link authoring. For videos uploaded to StudyFlow, the player blocks forward seeking and speed changes, while the backend requires at least 95% confirmed watch progress before lesson completion. Embedded YouTube players retain normal controls because YouTube's developer policies prohibit blocking their standard playback controls; those external videos can still be skipped.
**Validation:** Applied migration `c5d92a6f1340`. TestClient confirmed three courses and working banner images in each of Uzbek, English, Russian, and Korean. It also confirmed uploaded-video completion is denied without viewing, a forward seek adds no watch time, and a course with lessons rejects source-language changes. Temporary test data was removed. Python and JavaScript syntax and `git diff --check` passed.
**Issue observed and resolution:** The first catalog-count check included the temporary video test course; the test was corrected to run the language catalog checks before adding temporary data.
## Topic-specific course and lesson banners — 2026-11-08
**Tool(s) used:** Codex, Python/SQLAlchemy, Node syntax checker.
**Student request:** Replace the disliked generic banners with course/lesson-topic artwork, generate lesson banners from lesson content when AI is available, and let authors upload their own.
**AI assistance provided:** Replaced generated course SVG covers with subject motifs for Python, APIs/FastAPI, and Git/Linux. New lessons automatically request AI banner generation when `AI_API_KEY` exists and fall back to a subject illustration otherwise. Added author-only PNG/JPEG/WebP banner uploads for courses and lessons (8 MB limit), with old manually uploaded banners preserved when course details change. Added upload controls to the author portal and responsive banner sizing.
**Validation:** Refreshed 14 generated course banners and added 24 missing lesson banners in the local database. `node --check`, Python AST syntax parsing, and `git diff --check` passed. AI key is not configured in the current environment, so live image generation could not be exercised; topic-specific fallback banners were used.
**Issue observed and resolution:** The initial local database command used the wrong Python environment; reran it with `backend/.venv` and completed the banner refresh.
## Free video courses, certificate printing, password recovery, and GitHub project link — 2026-11-08
**Tool(s) used:** Codex, FastAPI, SQLAlchemy/PostgreSQL, GitHub CLI, web search, Node syntax checker.
**Student request:** Add free video lessons in every supported language with quizzes and final exams, print certificates once, allow forgotten-password recovery, and fix the StudyFlow AI link on the GitHub profile.
**AI assistance provided:** Completed the free Python lessons with public creator-hosted YouTube videos in Uzbek, English, Russian, and Korean. Confirmed all 12 published courses already have a quiz for each lesson and a final exam. Removed the two empty unpublished `mulfiim` and `kino` drafts previously requested for deletion. Updated print CSS so the certificate fits a single landscape page. Added a 30-minute, one-use email reset flow, rate limited per IP, plus translated reset pages and login links. The email flow uses SMTP credentials rather than exposing reset tokens in the UI. Corrected the malformed GitHub profile README link from localhost to the existing team repository and published the README fix to the user's public profile repository.
**Validation:** Checked all 12 published courses: no lesson quiz or final exam was missing. All 8 lessons in the four free Python courses now have video links. Local API served the reset page and new auth route; the reset-email endpoint correctly reported SMTP unavailable because the local environment has no SMTP settings. Node and Python syntax and `git diff --check` passed.
**Issue observed and resolution:** The personal GitHub remote points to a misspelled repository that does not exist. The user's account has no public StudyFlow repository; the profile project link now opens the private team repository and therefore only works for people with access to that repository.

## Documentation aligned with current project status — 2026-11-10
**AI assistance provided:** Updated the README, architecture critique, security review, deployment guide, and this log to reflect the current implemented features, regression tests, CI checks, Docker setup, and Render deployment state. Replaced outdated statements claiming tests/CI or database configuration were absent.
**Current release status:** GitHub Actions CI passes. Docker and the free-only Render Blueprint are prepared. A temporary free Render PostgreSQL database exists, but Render has not deployed the web service because GitHub repository access is still blocked. There is no public application URL; the free database expires after 30 days. No paid hosting resource is part of this setup.
**Remaining release work:** Restore Render's GitHub repository access, deploy the Blueprint only on free plans, configure secrets in Render, verify migrations and the live health/auth/course/certificate flows, and record the public URL and evidence. Keep the database and uploaded files backed up before treating any hosted data as durable.

# AI Collaboration Log

## Week 2–9 project documentation and repository preparation — 2026-11-06
**Tool(s) used:** ChatGPT/Codex and command-line Git tools.
**What I asked for:** Prepare the existing StudyFlow AI project for the supplied course milestones through Week 9 and the provided GitHub Classroom repository.
**What I kept as-is:** The existing backend, frontend, migrations, and feature structure were copied from the local project. The course-provided project guide and original repository instructions were preserved.
**What I changed or rejected, and why:** Added a project README, `.gitignore`, pitch and vision, assumption-based personas and user stories, a proposed lightweight Agile process, an architecture diagram and critique, and a Week 9 decomposition discussion, and removed pre-existing trailing whitespace found by the submission check. I did not claim cloud deployment, team membership, user research, prior Scrum practice, or automated tests because the inspected repository did not provide evidence for those claims.
**Something the AI got wrong that I had to catch:** Codex's first attempt to write the milestone files failed because it had not created the `docs/` directory. The shell reported the missing directory; Codex then created it and checked that the files existed. Add any other mistakes you personally caught, and review this entry for accuracy before submission.
## README presentation update — 2026-11-06
**Tool(s) used:** ChatGPT/Codex.
**What I asked for:** Improve the GitHub project page with a StudyFlow AI logo and clickable technology logos.
**What I kept as-is:** The project description, course milestones, local setup instructions, and deployment caveats.
**What I changed or rejected, and why:** Added a reusable SVG wordmark and redesigned the root README with clickable badges linking to the project and official technology documentation. Kept the current local-only deployment status visible.
**Something the AI got wrong that I had to catch:** No additional student-caught error has been reported for this update; add any you noticed before submission.

## README reference correction — 2026-11-06
**Tool(s) used:** ChatGPT/Codex.
**What I asked for:** Use the Group 1 README as a visual reference for StudyFlow AI.
**What I kept as-is:** The StudyFlow logo, clickable technology badges, documentation links, and project overview.
**What I changed or rejected, and why:** Removed the individual profile badge that had been added by mistake; the reference was for styling only.
**Something the AI got wrong that I had to catch:** Codex mistook a username visible in the reference context for a requested profile link. The user clarified that it was only an example; the badge was removed.

## README restructuring — 2026-11-06
**Tool(s) used:** ChatGPT/Codex.
**What I asked for:** Restructure the project README to follow the organization and level of detail of the Group 1 reference.
**What I kept as-is:** StudyFlow's logo, technology badges, and verified product and setup information.
**What I changed or rejected, and why:** Reorganized the README around features, quick start, environment, API, development, architecture, feature-specific guides, deployment, limitations, and course records. Kept the cloud demo status explicit because no public deployment URL is available.
**Something the AI got wrong that I had to catch:** The prior version emphasized visual styling but did not mirror the reference README's overall structure.

## Detailed project README — 2026-11-06
**Tool(s) used:** ChatGPT/Codex.
**What I asked for:** Expand the StudyFlow project README to match the detail and organization of the Group 1 reference while documenting this project's own implementation.
**What I kept as-is:** Existing setup, environment, architecture, project milestones, limitations, and feature summary.
**What I changed or rejected, and why:** Added the complete route catalog, request examples, learner/course-author/verifier workflows, and a database model overview based on the current FastAPI OpenAPI schema and Pydantic models. Did not invent a live deployment or automated test suite.
**Something the AI got wrong that I had to catch:** The previously listed personal project repository link no longer resolves; this update is made in the active Classroom project repository.

## Security review — 2026-11-06
**Tool(s) used:** ChatGPT/Codex.
**What I asked for:** Continue the StudyFlow AI project after the Week 9 milestone.
**What I kept as-is:** The modular monolith architecture, existing login flow, passkey checks, and course ownership rules.
**What I changed or rejected, and why:** Added strong JWT signing-key validation and token-version checks so changing a password invalidates existing access tokens. Added the database migration and documented this source review and its deployment follow-up items.
**Something the AI got wrong that I had to catch:** `compileall` could not write bytecode into the protected cache folders; Python syntax was instead checked without creating files.

## Separate learner and author portals — 2026-11-06
**Tool(s) used:** ChatGPT/Codex.
**What I asked for:** Give ordinary learners and course authors separate sign-in pages and menus.
**What I kept as-is:** Existing course ownership checks, learner course workflows, passkey support, and the four interface languages.
**What I changed or rejected, and why:** Added `learner` and `author` account types, distinct login and registration pages, role-specific dashboards, and backend checks on course, lesson, quiz, and analytics author routes. Existing course owners are migrated as authors; other accounts remain learners.
**Something the AI got wrong that I had to catch:** No user-caught error has been reported for this change; note any issue found during review before submission.

## Coursera-inspired author course builder — 2026-11-06
**Tool(s) used:** ChatGPT/Codex.
**What I asked for:** Remove learner-facing copy from the author account and support courses with text, PDF, video, and audio lessons using Coursera as a reference.
**What I kept as-is:** The course and ordered-lesson model, author ownership checks, lesson quizzes, final exams, and the four-language interface.
**What I changed or rejected, and why:** Author sign-in now opens the course studio first. Added text/PDF/video/audio lesson formats, authenticated author uploads, short-lived resource links for enrolled learners, file type/size checks, and a Coursera-inspired authoring guide. Large files remain local in this prototype; production object storage is documented as future deployment work.
**Something the AI got wrong that I had to catch:** No user-caught issue has been reported yet; review the media upload and learner playback flow before submission.

## Lesson cleanup, AI banners, and lesson-language switching — 2026-11-08
**Tool(s) used:** ChatGPT/Codex, FastAPI TestClient, local PostgreSQL, Node syntax checker.
**What I asked for:** Remove the movie/cinema lesson material, add AI-generated lesson banners, translate lesson content when learners change UI language, and align the content model with Course → Module → Lesson → Learning Material → Quiz/Assignment.
**What I kept as-is:** Existing course, lesson, quiz, final-exam, enrollment, and progress records; the existing lesson upload flow; current author permissions.
**What I changed or rejected, and why:** Removed the three matching “kino/multik” lessons and unpublished their now-empty courses while preserving enrollments. Added a cached per-language lesson translation table and automatic translation lookup for Uzbek, English, Russian, and Korean UI languages. Added automatic lesson-banner generation on save when `AI_API_KEY` is configured, plus an author action to retry or replace it; each generation can incur image API charges. Added signed links for draft banners. Added a content-model note: Module, multi-item Learning Material, and Assignment tables remain a later schema migration because the current prototype stores one text body and one optional file on Lesson.
**Validation:** Applied migration `e8b3c0a1912f`; Node and Python syntax checks passed. API checks passed for source-language fallback, cached translation behavior (mocked provider), banner storage/access (mocked image provider), and missing-key handling. Live AI translation and image generation were not run because `AI_API_KEY` is not configured.
**Something the AI got wrong that I had to catch:** No additional user-caught error was reported during this change; review the migration and content behavior before submission.

## Course catalog localization correction — 2026-11-08
**Tool(s) used:** ChatGPT/Codex, FastAPI TestClient, local PostgreSQL, Node syntax checker.
**What I asked for:** Fix the issue where switching interface language changed menus but course listings and course details stayed in Uzbek.
**What I kept as-is:** Course source language, course and lesson IDs, and the source Uzbek text.
**What I changed or rejected, and why:** The catalog and enrollment screens were not sending the selected language, and the catalog API had no course-translation lookup. Added cached course title, description, and category translations, wired the catalog/detail/enrollment UI to the selected language, and seeded English/Russian/Korean translations for the three existing demo courses and their six lessons. New content still needs `AI_API_KEY` for automatic translation.
**Validation:** Applied migrations `f1a8c72d9e30` and `a47d1c86e502`. TestClient confirmed all three catalog languages and localized course title, description, category, preview, lesson, and enrollment responses. Mocked translations were removed; seeded course translations are retained.
**Something the AI got wrong that I had to catch:** The first catalog test expected one mock translation call even though the endpoint localized every published course; the assertion was corrected and all checks passed.

## Assessment localization and author ownership — 2026-11-08
**Tool(s) used:** ChatGPT/Codex, local PostgreSQL, FastAPI TestClient, Node syntax checker.
**What I asked for:** Translate all learner-facing course content and ensure one author cannot manage another author's lessons.
**What I kept as-is:** Question IDs, correct-answer indexes, choice order, scores, and existing course ownership rules.
**What I changed or rejected, and why:** Added cached translations for quiz and final-exam titles, prompts, and choices in English, Russian, and Korean. Translation preserves question and choice order so submitted answers still map to the original correct-answer indexes. The learner UI now requests the selected language. Existing owner checks already scope course and lesson updates/deletes and assessment management to the course owner; I retained and will verify those checks with a second author account.
**Validation:** Applied migration `b6c4e97a21fd`; seeded translations for current published demo assessments. Confirmed the Python demo quiz and final exam return Uzbek, English, Russian, and Korean content through the API. A temporary second author received 404 for another author's course/lesson edits and deletes, and 403 for quiz management; the temporary account was deleted. Python syntax, Node syntax, and `git diff --check` passed. Automatic translation of newly authored assessment content requires `AI_API_KEY`; no live provider request is made when it is absent.
**Something the AI got wrong that I had to catch:** The demo database also contains two unpublished cleanup courses, so I limited seeded assessment translations to published courses.

## Course-language catalog, banners, and video completion — 2026-11-08
**Tool(s) used:** ChatGPT/Codex, FastAPI TestClient, local PostgreSQL, Node syntax checker, web research.
**What I asked for:** Show only courses authored in the selected language; let authors create content in the selected language; add course cover art and more IT courses in each language; and require learners to finish course videos.
**What I kept as-is:** The course, lesson, quiz, final-exam, enrollment, and progress structures; existing author ownership restrictions; public third-party video hosting.
**What I changed or rejected, and why:** The public catalog now filters on the course's original language. The new-course form follows the interface language, and an existing course's language becomes fixed once it has lessons so source text cannot be mislabeled. Added generated course banner illustrations, seeded English/Russian/Korean editions of Python, FastAPI, and Git/Linux, and linked public videos where a suitable language-matched course was found. Added secure YouTube-link authoring. For videos uploaded to StudyFlow, the player blocks forward seeking and speed changes, while the backend requires at least 95% confirmed watch progress before lesson completion. Embedded YouTube players retain normal controls because YouTube's developer policies prohibit blocking their standard playback controls; those external videos can still be skipped.
**Validation:** Applied migration `c5d92a6f1340`. TestClient confirmed three courses and working banner images in each of Uzbek, English, Russian, and Korean. It also confirmed uploaded-video completion is denied without viewing, a forward seek adds no watch time, and a course with lessons rejects source-language changes. Temporary test data was removed. Python and JavaScript syntax and `git diff --check` passed.
**Something the AI got wrong that I had to catch:** The first catalog-count check included the temporary video test course; the test was corrected to run the language catalog checks before adding temporary data.
## Topic-specific course and lesson banners — 2026-11-08
**Tool(s) used:** Codex, Python/SQLAlchemy, Node syntax checker.
**What I asked for:** Replace the disliked generic banners with course/lesson-topic artwork, generate lesson banners from lesson content when AI is available, and let authors upload their own.
**What I changed or rejected, and why:** Replaced generated course SVG covers with subject motifs for Python, APIs/FastAPI, and Git/Linux. New lessons automatically request AI banner generation when `AI_API_KEY` exists and fall back to a subject illustration otherwise. Added author-only PNG/JPEG/WebP banner uploads for courses and lessons (8 MB limit), with old manually uploaded banners preserved when course details change. Added upload controls to the author portal and responsive banner sizing.
**Validation:** Refreshed 14 generated course banners and added 24 missing lesson banners in the local database. `node --check`, Python AST syntax parsing, and `git diff --check` passed. AI key is not configured in the current environment, so live image generation could not be exercised; topic-specific fallback banners were used.
**Something the AI got wrong that I had to catch:** The initial local database command used the wrong Python environment; reran it with `backend/.venv` and completed the banner refresh.
## Free video courses, certificate printing, password recovery, and GitHub project link — 2026-11-08
**Tool(s) used:** Codex, FastAPI, SQLAlchemy/PostgreSQL, GitHub CLI, web search, Node syntax checker.
**What I asked for:** Add free video lessons in every supported language with quizzes and final exams, print certificates once, allow forgotten-password recovery, and fix the StudyFlow AI link on the GitHub profile.
**What I changed or rejected, and why:** Completed the free Python lessons with public creator-hosted YouTube videos in Uzbek, English, Russian, and Korean. Confirmed all 12 published courses already have a quiz for each lesson and a final exam. Removed the two empty unpublished `mulfiim` and `kino` drafts previously requested for deletion. Updated print CSS so the certificate fits a single landscape page. Added a 30-minute, one-use email reset flow, rate limited per IP, plus translated reset pages and login links. The email flow uses SMTP credentials rather than exposing reset tokens in the UI. Corrected the malformed GitHub profile README link from localhost to the existing team repository and published the README fix to the user's public profile repository.
**Validation:** Checked all 12 published courses: no lesson quiz or final exam was missing. All 8 lessons in the four free Python courses now have video links. Local API served the reset page and new auth route; the reset-email endpoint correctly reported SMTP unavailable because the local environment has no SMTP settings. Node and Python syntax and `git diff --check` passed.
**Something the AI got wrong that I had to catch:** The personal GitHub remote points to a misspelled repository that does not exist. The user's account has no public StudyFlow repository; the profile project link now opens the private team repository and therefore only works for people with access to that repository.

## Documentation aligned with current project status — 2026-11-10
**What I changed:** Updated the README, architecture critique, security review, deployment guide, and this log to reflect the current implemented features, regression tests, CI checks, Docker setup, and Render deployment state. Replaced outdated statements claiming tests/CI or database configuration were absent.
**Current release status:** GitHub Actions CI passes. Docker and the free-only Render Blueprint are prepared. A temporary free Render PostgreSQL database exists, but Render has not deployed the web service because GitHub repository access is still blocked. There is no public application URL; the free database expires after 30 days. No paid hosting resource is part of this setup.
**Remaining release work:** Restore Render's GitHub repository access, deploy the Blueprint only on free plans, configure secrets in Render, verify migrations and the live health/auth/course/certificate flows, and record the public URL and evidence. Keep the database and uploaded files backed up before treating any hosted data as durable.

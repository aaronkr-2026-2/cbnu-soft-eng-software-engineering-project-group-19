# Week 4: Retrospective personas and user stories

These are working, assumption-based personas inferred from the product features. They are not based on interviews or measured user research; validate them with real learners and course authors.

## Persona 1: Self-paced learner

**Name:** Dilnoza (composite persona)
**Goal:** Learn a skill around work or school commitments and understand what remains.
**Needs:** Lessons in a language she understands, visible progress, quizzes, and a clear completion path.
**Pain points to validate:** Losing track of unfinished material; not knowing whether she has met the course requirements.

**User stories**

- As a learner, I want to browse and preview courses so I can choose a course before enrolling.
- As a learner, I want to mark lessons complete and see my progress so I know what remains.
- As a learner, I want to take lesson quizzes and a final exam so I can check my understanding.
- As a learner, I want to see my certificates so I can share evidence of courses I have completed.

## Persona 2: Course author

**Name:** Aziz (composite persona)
**Goal:** Publish a small course and understand how learners are engaging with it.
**Needs:** Course and lesson authoring, quizzes, publishing controls, and basic analytics.
**Pain points to validate:** Keeping course structure and assessment material organized; seeing where learners stop.

**User stories**

- As a course author, I want to create and edit courses, lessons, and quizzes so I can maintain course content.
- As a course author, I want to publish or unpublish a course so I can control when learners can enroll.
- As a course author, I want enrollment, completion, rating, and exam statistics so I can improve my course.

## Persona 3: Certificate verifier

**Name:** Hiring coordinator (composite persona)
**Goal:** Check whether a presented StudyFlow AI certificate is recorded as valid.
**Needs:** A public verification page that works without registration and reports a clear result.
**Pain points to validate:** Asking a learner to create an account just to verify a credential; uncertainty about whether a certificate was altered.

**User stories**

- As a verifier, I want to enter a certificate verification code without signing in so I can check its recorded status.
- As a verifier, I want the result to identify the course and certificate holder so I can compare it with the document presented.

## Initial acceptance criteria to refine

- Course preview is available before enrollment for published courses.
- A signed-in learner can see lesson completion and course progress.
- A final exam is available only after completing required lessons and quizzes.
- A certificate is issued only after passing the final exam.
- Public verification does not require an account and reports only certificates found in the database.

These criteria describe intended behavior; verify them against the current implementation and turn them into automated tests in the later testing milestone.

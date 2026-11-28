# Week 9: Microservices and decomposition discussion

## Decision

Keep StudyFlow AI as a modular monolith for the current project. Microservices are not justified by the current evidence: the repository has one application, one database, and no measured traffic, independent scaling requirement, or separate teams that would benefit from independent service deployment.

## Candidate boundaries if constraints change

1. **Identity and credentials:** accounts, sessions, passkey credentials, and authentication challenges.
2. **Learning content:** courses, lessons, enrollment, and lesson progress.
3. **Assessment and credentials:** quizzes, final exams, attempts, certificate issuance, and public verification.
4. **Discovery and insights:** recommendations, study plans, reviews, and author analytics.

These are conceptual domain boundaries inside the current app, not a proposed immediate service split.

## Costs of splitting now

- Network calls introduce timeouts, retries, partial failure, and distributed transaction problems.
- Authentication and authorization would need secure cross-service contracts.
- A shared relational data model would become harder to update consistently.
- Separate deployment, secrets, observability, and CI increase operational work.
- The project has no load or team-ownership evidence showing that these costs would solve a current problem.

## Revisit triggers

Reconsider service extraction only when a domain has an independent scaling bottleneck, a separate team owns it, release coupling causes measurable delays, or a compliance boundary requires isolation. First strengthen module boundaries and tests inside the monolith. If extraction becomes justified, start with a read-heavy or independently deployable boundary and define data ownership before moving code.

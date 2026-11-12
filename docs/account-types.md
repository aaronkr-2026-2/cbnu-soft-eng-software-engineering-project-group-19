# Learner and author accounts

StudyFlow AI has two account types with separate sign-in portals:

- Learners: `/app/learner-login.html`. Their menu contains courses and lessons, completed courses, certificates, profile, and the course catalog.
- Authors: `/app/author-login.html`. Their menu contains owned courses, course creation, and the catalog. They see course management and analytics for courses they own.

The selected account type is stored in the `users.account_type` database column. The API checks it at login and on author-only endpoints; hiding a menu in the browser is not the security boundary. A login attempt on the wrong portal is rejected. Course owners that existed before this change are migrated as authors; other existing accounts become learners.

The same email cannot create a second account because email addresses remain unique. Use a different email for the separate author account. Authors who want to study should use a learner account.

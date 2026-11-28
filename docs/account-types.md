# Learner and author accounts

SCHOLWARD Academy supports two separate accounts.

- Learners sign up and sign in at `/app/learner-login.html`.
- Authors sign in at `/app/author-login.html`. A new author must use an invitation sent to their email address. An invitation expires after 24 hours, can be used once, and works only for the recipient's address.

The same email cannot be used for both accounts. The server checks the account role at sign-in and on author-only actions. It also verifies course ownership before granting author access to private course data.

## Managing invitations

After applying the database migrations, run these commands from `backend` on a trusted host configured with the academy database and email provider.

```sh
python -m app.author_invites list-authors
python -m app.author_invites issue approved-author@example.com
```

The invitation command emails the link to the approved recipient. Review existing author accounts with `list-authors`. Accounts created before invitations were introduced retain their current access until the operator reviews them.

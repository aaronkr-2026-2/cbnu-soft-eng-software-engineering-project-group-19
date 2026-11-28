from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlsplit

from app import author_invites
from app.core.author_invitations import token_digest
from app.database import get_db
from app.models import AuthorInvitation
from tests.helpers import create_test_author_invitation, login, register


def test_author_invitation_matches_recipient_and_can_only_be_used_once(client):
    address = "invited@example.com"
    token = create_test_author_invitation(client, address)
    payload = {
        "email": address,
        "full_name": "Invited Author",
        "password": "correct-horse-42",
        "account_type": "author",
    }
    assert client.post("/auth/register", json=payload).status_code == 403
    payload["author_invite"] = token
    assert (
        client.post(
            "/auth/register", json={**payload, "email": "different@example.com"}
        ).status_code
        == 403
    )
    created = client.post("/auth/register", json=payload)
    assert created.status_code == 201
    assert created.json()["account_type"] == "author"
    assert client.post("/auth/register", json=payload).status_code == 403
    assert client.get("/courses", headers=login(client, address, "author")).status_code == 200

    learner = "ordinary-learner@example.com"
    register(client, learner)
    assert client.get("/courses", headers=login(client, learner)).status_code == 403


def test_expired_invitation_cannot_create_author(client):
    address = "expired-invite@example.com"
    token = create_test_author_invitation(client, address)
    with contextmanager(client.app.dependency_overrides[get_db])() as db:
        db.get(AuthorInvitation, token_digest(token)).expires_at = datetime.now(UTC) - timedelta(
            seconds=1
        )
        db.commit()
    result = client.post(
        "/auth/register",
        json={
            "email": address,
            "full_name": "Expired Invitation",
            "password": "correct-horse-42",
            "account_type": "author",
            "author_invite": token,
        },
    )
    assert result.status_code == 403


def test_invite_cli_emails_link_and_stores_only_the_digest(client, monkeypatch):
    sent = []
    session = contextmanager(client.app.dependency_overrides[get_db])
    monkeypatch.setattr(author_invites, "SessionLocal", session)
    monkeypatch.setattr(
        author_invites,
        "configured_email_sender",
        lambda: (lambda *message: sent.append(message)),
    )
    monkeypatch.setenv("PUBLIC_APP_URL", "https://scholward-academy.vercel.app")

    author_invites.issue_invitation("expected@example.com")

    recipient, subject, body = sent[0]
    assert recipient == "expected@example.com"
    assert "SCHOLWARD Academy" in subject
    link = next(line for line in body.splitlines() if line.startswith("https://"))
    parsed = urlsplit(link)
    assert parsed.path == "/app/author-login.html" and not parsed.query
    token = parse_qs(parsed.fragment)["invite"][0]
    with session() as db:
        assert db.get(AuthorInvitation, token) is None
        assert db.get(AuthorInvitation, token_digest(token)).email == recipient

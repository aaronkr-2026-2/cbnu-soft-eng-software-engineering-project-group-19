from contextlib import contextmanager

from app.core.author_invitations import create_author_invitation
from app.database import get_db


def create_test_author_invitation(client, email: str) -> str:
    with contextmanager(client.app.dependency_overrides[get_db])() as db:
        token = create_author_invitation(db, email)
        db.commit()
    return token


def register(client, email: str, account_type: str = "learner") -> dict:
    invitation = (
        {"author_invite": create_test_author_invitation(client, email)}
        if account_type == "author"
        else {}
    )
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "full_name": email.split("@")[0].title(),
            "password": "correct-horse-42",
            "account_type": account_type,
            **invitation,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def login(client, email: str, account_type: str = "learner") -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "correct-horse-42",
            "account_type": account_type,
        },
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}

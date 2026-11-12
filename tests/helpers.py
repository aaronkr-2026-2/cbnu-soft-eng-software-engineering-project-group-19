def register(client, email: str, account_type: str = "learner") -> dict:
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "full_name": email.split("@")[0].title(),
            "password": "correct-horse-42",
            "account_type": account_type,
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

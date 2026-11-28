"""Manage author invitations from a trusted host with access to the academy database."""

import argparse
import os
from urllib.parse import urlencode

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import delete, func, select

from app.core.author_invitations import create_author_invitation, token_digest
from app.core.email_delivery import (
    SENDER_NAME,
    EmailConfigurationError,
    EmailDeliveryError,
    configured_email_sender,
)
from app.database import SessionLocal
from app.models import AuthorInvitation, User

PUBLIC_SITE = "https://scholward-academy.vercel.app"


def issue_invitation(email: str) -> None:
    recipient = validate_email(email, check_deliverability=False).normalized
    frontend = (os.getenv("PUBLIC_APP_URL") or PUBLIC_SITE).rstrip("/")
    app_url = frontend if frontend.endswith("/app") else frontend + "/app"
    send_email = configured_email_sender()
    with SessionLocal() as db:
        existing = db.scalar(select(User.id).where(func.lower(User.email) == recipient.lower()))
        if existing:
            raise ValueError("An account already exists for that email")
        token = create_author_invitation(db, recipient)
        db.commit()
        url = f"{app_url}/author-login.html#{urlencode({'invite': token})}"
        try:
            send_email(
                recipient,
                f"Your invitation to teach at {SENDER_NAME}",
                f"Create your {SENDER_NAME} author account using this link within 24 hours:\n"
                f"{url}\n\nUse the email address that received this invitation.",
            )
        except EmailDeliveryError:
            db.execute(
                delete(AuthorInvitation).where(
                    AuthorInvitation.token_digest == token_digest(token),
                    AuthorInvitation.used_at.is_(None),
                )
            )
            db.commit()
            raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    issue = commands.add_parser("issue", help="Email a single-use author invitation")
    issue.add_argument("email")
    commands.add_parser("list-authors", help="List existing author accounts for review")
    args = parser.parse_args()
    if args.command == "issue":
        try:
            issue_invitation(args.email)
        except (
            EmailNotValidError,
            EmailConfigurationError,
            EmailDeliveryError,
            ValueError,
        ) as error:
            parser.exit(1, f"{error}\n")
        print("Author invitation sent.")
        return
    with SessionLocal() as db:
        authors = db.scalars(
            select(User).where(User.account_type == "author").order_by(User.created_at, User.id)
        )
        for author in authors:
            state = "active" if author.is_active else "inactive"
            print(f"{author.created_at.isoformat()}\t{state}\t{author.email}")


if __name__ == "__main__":
    main()

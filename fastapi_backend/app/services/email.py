# app/services/email.py

import logging
from pathlib import Path
from functools import lru_cache
from typing import List, Dict

from fastapi import HTTPException, status
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

from app.core.config import settings
from app.models.users.users import User

logger = logging.getLogger(__name__)


@lru_cache()
def get_email_config() -> ConnectionConfig:
    templates_dir = Path(__file__).parent.parent / settings.TEMPLATE_DIR
    return ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
        MAIL_STARTTLS=settings.MAIL_STARTTLS,
        MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
        USE_CREDENTIALS=settings.USE_CREDENTIALS,
        VALIDATE_CERTS=settings.VALIDATE_CERTS,
        TEMPLATE_FOLDER=templates_dir,
    )


@lru_cache()
def get_mailer() -> FastMail:
    """Return a cached FastMail instance with our config."""
    return FastMail(get_email_config())


async def send_email(
    *,
    subject: str,
    recipients: List[str],
    template_name: str,
    body: Dict[str, str],
) -> None:
    """
    Send a templated HTML email.
    Raises HTTPException(500) on failure.
    """
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        template_body=body,
        subtype=MessageType.html,
    )
    fm = get_mailer()
    try:
        await fm.send_message(message, template_name=template_name)
    except Exception as e:
        logger.error("Failed to send email %s to %s: %s", template_name, recipients, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to send email, please try again later",
        )


async def send_reset_password_email(user: User, token: str) -> None:
    """
    Sends a password reset link to the user.
    Expects a Jinja2 template at 'password_reset.html' with {{ username }} and {{ link }}.
    """
    params = {"token": token}
    link = f"{settings.FRONTEND_URL}/password-recovery/confirm?token={token}"
    await send_email(
        subject="Password Recovery",
        recipients=[user.email],
        template_name="password_reset.html",
        body={"username": user.email, "link": link},
    )


async def send_verification_email(user: User, token: str) -> None:
    """
    Sends an account-verification link to the user.
    Expects a Jinja2 template at 'verify_account.html' with {{ username }} and {{ link }}.
    """
    link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    await send_email(
        subject="Please verify your email",
        recipients=[user.email],
        template_name="verify_account.html",
        body={"username": user.full_name or user.email, "link": link},
    )

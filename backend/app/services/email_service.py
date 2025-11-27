"""
Guardian Email Service

Email delivery for authentication tokens.
"""

import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_token_email(
    email: str,
    token: str,
    subject: Optional[str] = None
) -> bool:
    """
    Send a 6-digit authentication token via email.

    Args:
        email: Recipient email address
        token: The 6-digit token to send
        subject: Optional custom subject line

    Returns:
        bool: True if email sent (or simulated in dev mode)

    Note:
        In development mode without Mailgun credentials,
        the token is logged instead of sent.
    """
    if not settings.mailgun_api_key or not settings.mailgun_domain:
        # Development mode - log token instead of sending
        logger.warning(
            f"[DEV MODE] Token for {email}: {token} "
            f"(Email not sent - Mailgun not configured)"
        )
        return True

    subject = subject or f"Your {settings.app_name} login code"

    # Build email content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; padding: 20px;">
            <h1 style="color: #333; margin-bottom: 10px;">{settings.app_name}</h1>
            <p style="color: #666; font-size: 16px;">Your login code is:</p>
            <div style="background: #f5f5f5; border-radius: 8px; padding: 20px; margin: 20px 0;">
                <span style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #333;">
                    {token}
                </span>
            </div>
            <p style="color: #666; font-size: 14px;">
                This code expires in {settings.token_expiry_minutes} minutes.
            </p>
            <p style="color: #999; font-size: 12px; margin-top: 30px;">
                If you didn't request this code, you can safely ignore this email.
            </p>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    {settings.app_name}

    Your login code is: {token}

    This code expires in {settings.token_expiry_minutes} minutes.

    If you didn't request this code, you can safely ignore this email.
    """

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.mailgun.net/v3/{settings.mailgun_domain}/messages",
                auth=("api", settings.mailgun_api_key),
                data={
                    "from": f"{settings.mailgun_from_name} <{settings.mailgun_from_email}>",
                    "to": email,
                    "subject": subject,
                    "text": text_content,
                    "html": html_content,
                }
            )

            if response.status_code == 200:
                logger.info(f"Token email sent to {email}")
                return True
            else:
                logger.error(
                    f"Mailgun error: {response.status_code} - {response.text}"
                )
                return False

    except Exception as e:
        logger.error(f"Failed to send email to {email}: {e}")
        # Always return True for security (don't reveal email delivery status)
        return True

"""
Email service for sending authentication tokens via Mailgun.

This module handles email delivery using Mailgun's API for sending
6-digit authentication tokens to users with white-label branding.
"""

import logging
from typing import Optional
import requests
from requests.exceptions import RequestException, Timeout

from app.core.config import get_settings
from app.services.template_service import get_template_service


logger = logging.getLogger(__name__)
settings = get_settings()
template_service = get_template_service()


async def send_token_email(email: str, token: str) -> bool:
    """
    Send a 6-digit authentication token via email using Mailgun.

    This function is designed to ALWAYS return True (security by obscurity).
    Even if the email fails to send, we return success to avoid revealing
    whether an email address exists in the system.

    Args:
        email: Recipient's email address
        token: 6-digit authentication token

    Returns:
        bool: Always returns True (see security note above)

    Example:
        >>> success = await send_token_email("user@example.com", "123456")
        >>> print(success)
        True

    Security Note:
        This function always returns True to prevent attackers from
        enumerating valid email addresses. Actual send status is only
        logged internally.
    """
    # Validate Mailgun configuration
    if not settings.mailgun_api_key or not settings.mailgun_domain:
        logger.error(
            "Mailgun not configured. Set MAILGUN_API_KEY and MAILGUN_DOMAIN "
            "environment variables."
        )
        # Still return True for security (don't reveal misconfiguration)
        return True

    # Render email body from template with branding
    try:
        email_body = template_service.render_token_email(
            token=token,
            format_type="text"
        )
    except Exception as e:
        logger.error(f"Failed to render email template: {e}")
        # Use fallback template
        email_body = template_service.get_fallback_template(
            template_type="token_text",
            context={"token": token}
        )

    # Mailgun API configuration
    url = f"https://api.mailgun.net/v3/{settings.mailgun_domain}/messages"
    auth = ("api", settings.mailgun_api_key)

    # Email data
    data = {
        "from": f"{settings.mailgun_from_name} <{settings.mailgun_from_email}>",
        "to": email,
        "subject": f"Your {settings.app_name} Login Code",
        "text": email_body
    }

    try:
        # Send email via Mailgun API
        response = requests.post(
            url,
            auth=auth,
            data=data,
            timeout=10  # 10 second timeout
        )

        # Check response status
        if response.status_code == 200:
            logger.info(f"Token email sent successfully to {_mask_email(email)}")
        else:
            logger.error(
                f"Mailgun API error: {response.status_code} - {response.text} "
                f"(Email: {_mask_email(email)})"
            )

    except Timeout:
        logger.error(
            f"Mailgun API timeout while sending to {_mask_email(email)}"
        )

    except RequestException as e:
        logger.error(
            f"Network error sending email to {_mask_email(email)}: {str(e)}"
        )

    except Exception as e:
        logger.error(
            f"Unexpected error sending email to {_mask_email(email)}: {str(e)}",
            exc_info=True
        )

    # Always return True for security reasons
    # Don't reveal whether email send succeeded or failed
    return True


def _mask_email(email: str) -> str:
    """
    Mask an email address for logging/security purposes.

    Masks the username part while preserving domain.
    Examples:
        - "user@example.com" → "u***@example.com"
        - "a@example.com" → "a***@example.com"
        - "verylongemail@example.com" → "v***@example.com"

    Args:
        email: Email address to mask

    Returns:
        str: Masked email address

    Example:
        >>> _mask_email("user@example.com")
        'u***@example.com'
    """
    if '@' not in email:
        return "***"

    username, domain = email.split('@', 1)

    if len(username) <= 1:
        return f"{username}***@{domain}"

    return f"{username[0]}***@{domain}"


async def send_token_email_sync(email: str, token: str) -> bool:
    """
    Synchronous wrapper for send_token_email.

    Used in non-async contexts or when email sending needs to be synchronous.

    Args:
        email: Recipient's email address
        token: 6-digit authentication token

    Returns:
        bool: Always returns True (see send_token_email for details)
    """
    return await send_token_email(email, token)

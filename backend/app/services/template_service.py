"""
Email template service for customizable white-label email generation.

This module provides a flexible template system using Jinja2 for rendering
email templates with branding and dynamic content. Supports both plain text
and HTML email formats with white-label customization.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound
from jinja2.exceptions import TemplateError

from app.core.config import get_settings


logger = logging.getLogger(__name__)
settings = get_settings()


class TemplateService:
    """
    Service for loading and rendering email templates with branding variables.

    This service manages email template rendering using Jinja2, supporting
    both plain text and HTML formats. It automatically injects branding
    variables from application settings and allows custom context variables.

    Features:
    - Jinja2 template engine with full syntax support
    - Automatic branding variable injection
    - Support for plain text and HTML templates
    - File-based template loading with fallback mechanisms
    - Comprehensive error handling and logging

    Example:
        >>> service = TemplateService()
        >>> content = service.render_template(
        ...     "token_email.txt",
        ...     {"token": "123456"}
        ... )
    """

    def __init__(self, template_path: Optional[str] = None):
        """
        Initialize the template service with a template directory.

        Args:
            template_path: Optional custom path to template directory.
                          If not provided, uses settings.email_template_path
                          or default "app/templates/email"
        """
        # Determine template directory
        if template_path:
            self.template_path = Path(template_path)
        elif hasattr(settings, 'email_template_path') and settings.email_template_path:
            self.template_path = Path(settings.email_template_path)
        else:
            # Default to app/templates/email relative to project root
            self.template_path = Path(__file__).parent.parent / "templates" / "email"

        # Ensure template directory exists
        if not self.template_path.exists():
            logger.warning(
                f"Template directory not found: {self.template_path}. "
                "Creating directory..."
            )
            self.template_path.mkdir(parents=True, exist_ok=True)

        # Initialize Jinja2 environment
        try:
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.template_path)),
                autoescape=False,  # We control template content
                trim_blocks=True,
                lstrip_blocks=True,
            )
            logger.info(f"Template service initialized with path: {self.template_path}")
        except Exception as e:
            logger.error(f"Failed to initialize Jinja2 environment: {e}")
            raise

    def _get_branding_context(self) -> Dict[str, Any]:
        """
        Get branding variables from application settings.

        This method extracts white-label branding configuration from
        settings and prepares it for template injection. These variables
        are automatically available in all templates.

        Returns:
            Dict[str, Any]: Dictionary of branding variables including:
                - company_name: Application/company name
                - app_name: Application name (alias)
                - support_email: Support email address
                - brand_primary_color: Primary brand color (hex)
                - expiry_minutes: Token expiry time in minutes
                - token_length: Expected token length

        Example:
            >>> service = TemplateService()
            >>> context = service._get_branding_context()
            >>> print(context['company_name'])
            'My Company'
        """
        branding_context = {
            # Core branding
            "company_name": getattr(settings, 'company_name', settings.app_name),
            "app_name": settings.app_name,
            "support_email": getattr(settings, 'support_email', 'support@example.com'),
            "brand_primary_color": getattr(settings, 'brand_primary_color', '#007bff'),

            # Authentication settings (useful for email content)
            "expiry_minutes": settings.token_expiry_minutes,
            "token_length": settings.token_length,
        }

        return branding_context

    def render_template(
        self,
        template_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Render an email template with provided context and branding variables.

        This method loads a template file and renders it with both the provided
        context variables and automatic branding variables from settings. The
        branding variables are merged with the context, with context variables
        taking precedence if there are conflicts.

        Args:
            template_name: Name of template file (e.g., "token_email.txt")
            context: Optional dictionary of variables to pass to template.
                    Common variables:
                    - token: Authentication token
                    - user_email: Recipient email
                    - custom_message: Additional message content

        Returns:
            str: Rendered template content as string

        Raises:
            TemplateNotFoundError: If template file doesn't exist
            TemplateRenderError: If template rendering fails

        Example:
            >>> service = TemplateService()
            >>> html = service.render_template(
            ...     "token_email.html",
            ...     {"token": "123456", "user_email": "user@example.com"}
            ... )
        """
        try:
            # Load template
            template = self.jinja_env.get_template(template_name)

            # Merge branding context with provided context
            render_context = self._get_branding_context()
            if context:
                render_context.update(context)

            # Render template
            rendered_content = template.render(**render_context)

            logger.debug(f"Successfully rendered template: {template_name}")
            return rendered_content

        except TemplateNotFound:
            logger.error(f"Template not found: {template_name} in {self.template_path}")
            raise TemplateNotFoundError(
                f"Email template '{template_name}' not found"
            )

        except TemplateError as e:
            logger.error(
                f"Template rendering error for {template_name}: {e}",
                exc_info=True
            )
            raise TemplateRenderError(
                f"Failed to render template '{template_name}': {str(e)}"
            )

        except Exception as e:
            logger.error(
                f"Unexpected error rendering template {template_name}: {e}",
                exc_info=True
            )
            raise TemplateRenderError(
                f"Unexpected error rendering template '{template_name}': {str(e)}"
            )

    def get_fallback_template(
        self,
        template_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get a hardcoded fallback template when file template is unavailable.

        This method provides emergency fallback templates that are embedded
        in code, ensuring email functionality even if template files are
        missing or corrupted. Should only be used as a last resort.

        Args:
            template_type: Type of template ('token_text' or 'token_html')
            context: Optional context variables for rendering

        Returns:
            str: Rendered fallback template content

        Example:
            >>> service = TemplateService()
            >>> fallback = service.get_fallback_template(
            ...     'token_text',
            ...     {'token': '123456'}
            ... )
        """
        # Get branding context
        render_context = self._get_branding_context()
        if context:
            render_context.update(context)

        # Fallback templates
        fallback_templates = {
            'token_text': """Hello,

Your verification code is:

{{ token }}

This code will expire in {{ expiry_minutes }} minutes.

If you didn't request this code, please ignore this email.

Best regards,
{{ company_name }}
{{ support_email }}
""",
            'token_html': """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: {{ brand_primary_color }};">{{ company_name }}</h2>
        <p>Hello,</p>
        <p>Your verification code is:</p>
        <div style="background-color: #f4f4f4; padding: 20px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 8px; margin: 20px 0;">
            {{ token }}
        </div>
        <p>This code will expire in <strong>{{ expiry_minutes }} minutes</strong>.</p>
        <p>If you didn't request this code, please ignore this email.</p>
        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
        <p style="color: #666; font-size: 12px;">
            Best regards,<br>
            {{ company_name }}<br>
            {{ support_email }}
        </p>
    </div>
</body>
</html>
"""
        }

        template_string = fallback_templates.get(template_type)
        if not template_string:
            logger.error(f"Unknown fallback template type: {template_type}")
            raise ValueError(f"Unknown fallback template type: {template_type}")

        # Render fallback template using Jinja2
        template = Template(template_string)
        rendered = template.render(**render_context)

        logger.warning(f"Using fallback template for type: {template_type}")
        return rendered

    def render_token_email(
        self,
        token: str,
        format_type: str = "text"
    ) -> str:
        """
        Convenience method to render token authentication email.

        This is a high-level method specifically for rendering authentication
        token emails. It handles both text and HTML formats and automatically
        falls back to embedded templates if files are missing.

        Args:
            token: 6-digit authentication token
            format_type: Email format - "text" or "html" (default: "text")

        Returns:
            str: Rendered email content ready to send

        Raises:
            ValueError: If format_type is not "text" or "html"

        Example:
            >>> service = TemplateService()
            >>> text_email = service.render_token_email("123456", "text")
            >>> html_email = service.render_token_email("123456", "html")
        """
        if format_type not in ['text', 'html']:
            raise ValueError(f"Invalid format_type: {format_type}. Must be 'text' or 'html'")

        # Determine template filename
        template_name = f"token_email.{format_type}" if format_type == "text" else "token_email.html"

        # Context for token email
        context = {
            "token": token,
        }

        try:
            # Try to render from file template
            return self.render_template(template_name, context)

        except (TemplateNotFoundError, TemplateRenderError) as e:
            logger.warning(
                f"Failed to load template file {template_name}, using fallback: {e}"
            )
            # Fall back to embedded template
            fallback_type = f"token_{format_type}"
            return self.get_fallback_template(fallback_type, context)


# Custom exceptions
class TemplateNotFoundError(Exception):
    """Raised when a template file cannot be found."""
    pass


class TemplateRenderError(Exception):
    """Raised when template rendering fails."""
    pass


# Singleton instance for convenience
_template_service_instance: Optional[TemplateService] = None


def get_template_service() -> TemplateService:
    """
    Get singleton instance of TemplateService.

    This function ensures only one TemplateService instance exists
    throughout the application lifecycle, improving performance by
    reusing the Jinja2 environment.

    Returns:
        TemplateService: Singleton template service instance

    Example:
        >>> from app.services.template_service import get_template_service
        >>> service = get_template_service()
        >>> email = service.render_token_email("123456")
    """
    global _template_service_instance

    if _template_service_instance is None:
        _template_service_instance = TemplateService()

    return _template_service_instance

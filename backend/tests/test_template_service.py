"""
Unit tests for template service.

Tests email template rendering with Jinja2 and white-label customization.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from jinja2.exceptions import TemplateNotFound as Jinja2TemplateNotFound

from app.core.config import get_settings
from app.services.template_service import (
    TemplateNotFoundError,
    TemplateRenderError,
    TemplateService,
    get_template_service,
)

settings = get_settings()


class TestTemplateServiceInitialization:
    """Tests for TemplateService initialization."""

    def test_init_default_path(self):
        """Test initialization with default template path."""
        service = TemplateService()

        # Verify template path is set
        assert service.template_path is not None
        assert isinstance(service.template_path, Path)

    def test_init_custom_path(self, tmp_path):
        """Test initialization with custom template path."""
        custom_path = tmp_path / "custom_templates"
        custom_path.mkdir()

        service = TemplateService(template_path=str(custom_path))

        # Verify custom path is used
        assert service.template_path == custom_path

    def test_init_creates_missing_directory(self, tmp_path):
        """Test that initialization creates missing template directory."""
        missing_path = tmp_path / "missing" / "templates"

        service = TemplateService(template_path=str(missing_path))

        # Verify directory was created
        assert missing_path.exists()
        assert missing_path.is_dir()

    def test_init_jinja_environment(self):
        """Test that Jinja2 environment is properly initialized."""
        service = TemplateService()

        # Verify Jinja2 environment exists
        assert service.jinja_env is not None
        assert hasattr(service.jinja_env, "get_template")

    @patch("app.services.template_service.Environment")
    def test_init_jinja_environment_failure(self, mock_env, tmp_path):
        """Test handling of Jinja2 environment initialization failure."""
        mock_env.side_effect = Exception("Jinja2 init error")

        with pytest.raises(Exception, match="Jinja2 init error"):
            TemplateService(template_path=str(tmp_path))


class TestBrandingContext:
    """Tests for branding context generation."""

    def test_get_branding_context_structure(self):
        """Test that branding context has expected structure."""
        service = TemplateService()
        context = service._get_branding_context()

        # Verify required keys
        required_keys = [
            "company_name",
            "app_name",
            "support_email",
            "brand_primary_color",
            "expiry_minutes",
            "token_length",
        ]
        for key in required_keys:
            assert key in context

    def test_get_branding_context_values_from_settings(self):
        """Test that branding context uses values from settings."""
        service = TemplateService()
        context = service._get_branding_context()

        # Verify values match settings
        assert context["app_name"] == settings.app_name
        assert context["expiry_minutes"] == settings.token_expiry_minutes
        assert context["token_length"] == settings.token_length

    def test_get_branding_context_company_name_fallback(self):
        """Test company_name falls back to app_name if not set."""
        service = TemplateService()
        context = service._get_branding_context()

        # Should use company_name if available, else app_name
        if hasattr(settings, "company_name"):
            assert context["company_name"] == settings.company_name
        else:
            assert context["company_name"] == settings.app_name

    def test_get_branding_context_support_email_default(self):
        """Test support_email has default value."""
        service = TemplateService()
        context = service._get_branding_context()

        # Should have support_email (either from settings or default)
        assert "support_email" in context
        assert "@" in context["support_email"]

    def test_get_branding_context_brand_color_default(self):
        """Test brand_primary_color has default value."""
        service = TemplateService()
        context = service._get_branding_context()

        # Should have brand color
        assert "brand_primary_color" in context
        assert context["brand_primary_color"].startswith("#")


class TestRenderTemplate:
    """Tests for template rendering."""

    def test_render_template_simple(self, tmp_path):
        """Test rendering a simple template."""
        # Create template file
        template_path = tmp_path / "templates"
        template_path.mkdir()
        template_file = template_path / "simple.txt"
        template_file.write_text("Hello {{ name }}!")

        # Render template
        service = TemplateService(template_path=str(template_path))
        result = service.render_template("simple.txt", {"name": "World"})

        assert result == "Hello World!"

    def test_render_template_with_branding(self, tmp_path):
        """Test that branding variables are available in templates."""
        # Create template using branding variables
        template_path = tmp_path / "templates"
        template_path.mkdir()
        template_file = template_path / "branded.txt"
        template_file.write_text("Welcome to {{ app_name }}!")

        # Render template
        service = TemplateService(template_path=str(template_path))
        result = service.render_template("branded.txt")

        assert settings.app_name in result

    def test_render_template_context_overrides_branding(self, tmp_path):
        """Test that context variables override branding variables."""
        # Create template
        template_path = tmp_path / "templates"
        template_path.mkdir()
        template_file = template_path / "override.txt"
        template_file.write_text("Name: {{ app_name }}")

        # Render with override
        service = TemplateService(template_path=str(template_path))
        result = service.render_template("override.txt", {"app_name": "Custom App"})

        assert result == "Name: Custom App"

    def test_render_template_not_found(self, tmp_path):
        """Test rendering non-existent template raises error."""
        template_path = tmp_path / "templates"
        template_path.mkdir()

        service = TemplateService(template_path=str(template_path))

        with pytest.raises(TemplateNotFoundError):
            service.render_template("nonexistent.txt")

    def test_render_template_syntax_error(self, tmp_path):
        """Test rendering template with syntax error raises error."""
        # Create template with syntax error
        template_path = tmp_path / "templates"
        template_path.mkdir()
        template_file = template_path / "error.txt"
        template_file.write_text("Hello {{ name ")  # Missing closing brace

        service = TemplateService(template_path=str(template_path))

        with pytest.raises(TemplateRenderError):
            service.render_template("error.txt")

    def test_render_template_with_loops(self, tmp_path):
        """Test rendering template with Jinja2 loops."""
        # Create template with loop
        template_path = tmp_path / "templates"
        template_path.mkdir()
        template_file = template_path / "loop.txt"
        template_file.write_text("{% for item in items %}{{ item }},{% endfor %}")

        service = TemplateService(template_path=str(template_path))
        result = service.render_template("loop.txt", {"items": [1, 2, 3]})

        assert result == "1,2,3,"

    def test_render_template_with_conditionals(self, tmp_path):
        """Test rendering template with conditionals."""
        # Create template with conditional
        template_path = tmp_path / "templates"
        template_path.mkdir()
        template_file = template_path / "conditional.txt"
        template_file.write_text("{% if show_message %}Hello{% else %}Goodbye{% endif %}")

        service = TemplateService(template_path=str(template_path))

        # Test with True
        result_true = service.render_template("conditional.txt", {"show_message": True})
        assert result_true == "Hello"

        # Test with False
        result_false = service.render_template("conditional.txt", {"show_message": False})
        assert result_false == "Goodbye"

    def test_render_template_whitespace_control(self, tmp_path):
        """Test that template whitespace control works."""
        # Create template with whitespace
        template_path = tmp_path / "templates"
        template_path.mkdir()
        template_file = template_path / "whitespace.txt"
        template_file.write_text("Line 1\n{% if true %}\nLine 2\n{% endif %}\nLine 3")

        service = TemplateService(template_path=str(template_path))
        result = service.render_template("whitespace.txt")

        # trim_blocks and lstrip_blocks should reduce whitespace
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result

    @patch("app.services.template_service.logger")
    def test_render_template_logs_debug(self, mock_logger, tmp_path):
        """Test that successful rendering logs debug message."""
        template_path = tmp_path / "templates"
        template_path.mkdir()
        template_file = template_path / "simple.txt"
        template_file.write_text("Hello")

        service = TemplateService(template_path=str(template_path))
        service.render_template("simple.txt")

        # Verify debug logging
        mock_logger.debug.assert_called_once()

    @patch("app.services.template_service.logger")
    def test_render_template_logs_error_on_not_found(self, mock_logger, tmp_path):
        """Test that template not found logs error."""
        template_path = tmp_path / "templates"
        template_path.mkdir()

        service = TemplateService(template_path=str(template_path))

        with pytest.raises(TemplateNotFoundError):
            service.render_template("missing.txt")

        # Verify error logging
        mock_logger.error.assert_called_once()


class TestFallbackTemplate:
    """Tests for fallback template functionality."""

    def test_get_fallback_template_token_text(self):
        """Test getting fallback text template for token email."""
        service = TemplateService()
        result = service.get_fallback_template("token_text", {"token": "123456"})

        # Verify content
        assert "123456" in result
        assert "expire" in result.lower()
        assert settings.app_name in result or settings.company_name in result

    def test_get_fallback_template_token_html(self):
        """Test getting fallback HTML template for token email."""
        service = TemplateService()
        result = service.get_fallback_template("token_html", {"token": "654321"})

        # Verify HTML structure
        assert "<!DOCTYPE html>" in result
        assert "654321" in result
        assert "<html>" in result
        assert "</html>" in result

    def test_get_fallback_template_includes_branding(self):
        """Test that fallback templates include branding variables."""
        service = TemplateService()
        result = service.get_fallback_template("token_text", {"token": "123456"})

        # Should contain branding info
        context = service._get_branding_context()
        assert context["company_name"] in result or context["app_name"] in result

    def test_get_fallback_template_invalid_type(self):
        """Test fallback template with invalid type raises error."""
        service = TemplateService()

        with pytest.raises(ValueError, match="Unknown fallback template type"):
            service.get_fallback_template("invalid_type")

    def test_get_fallback_template_with_custom_context(self):
        """Test fallback template uses custom context variables."""
        service = TemplateService()
        result = service.get_fallback_template("token_text", {"token": "999999"})

        assert "999999" in result

    @patch("app.services.template_service.logger")
    def test_get_fallback_template_logs_warning(self, mock_logger):
        """Test that using fallback template logs warning."""
        service = TemplateService()
        service.get_fallback_template("token_text", {"token": "123456"})

        # Verify warning logged
        mock_logger.warning.assert_called_once()


class TestRenderTokenEmail:
    """Tests for convenience token email rendering."""

    def test_render_token_email_text_format(self):
        """Test rendering token email in text format."""
        service = TemplateService()
        result = service.render_token_email("123456", "text")

        # Should contain token
        assert "123456" in result

    def test_render_token_email_html_format(self):
        """Test rendering token email in HTML format."""
        service = TemplateService()
        result = service.render_token_email("654321", "html")

        # Should contain token and HTML
        assert "654321" in result
        assert "<" in result and ">" in result

    def test_render_token_email_invalid_format(self):
        """Test rendering token email with invalid format raises error."""
        service = TemplateService()

        with pytest.raises(ValueError, match="Invalid format_type"):
            service.render_token_email("123456", "xml")

    def test_render_token_email_default_format(self):
        """Test rendering token email uses text as default format."""
        service = TemplateService()
        result = service.render_token_email("123456")

        # Should render as text (no HTML tags expected)
        assert "123456" in result

    def test_render_token_email_with_file_template(self, tmp_path):
        """Test token email rendering uses file template when available."""
        # Create custom token template
        template_path = tmp_path / "templates"
        template_path.mkdir()
        template_file = template_path / "token_email.text"
        template_file.write_text("Your code: {{ token }}")

        service = TemplateService(template_path=str(template_path))
        result = service.render_token_email("999999", "text")

        assert result == "Your code: 999999"

    def test_render_token_email_falls_back_on_missing_file(self):
        """Test token email falls back to embedded template on file error."""
        # Use non-existent template directory
        service = TemplateService()
        # Even without file templates, should work via fallback
        result = service.render_token_email("888888", "text")

        assert "888888" in result

    def test_render_token_email_includes_expiry_info(self):
        """Test token email includes expiry information."""
        service = TemplateService()
        result = service.render_token_email("123456", "text")

        # Should mention expiry time
        assert str(settings.token_expiry_minutes) in result

    def test_render_token_email_includes_company_info(self):
        """Test token email includes company/app information."""
        service = TemplateService()
        result = service.render_token_email("123456", "text")

        # Should contain company or app name
        context = service._get_branding_context()
        assert context["company_name"] in result or context["app_name"] in result

    @patch("app.services.template_service.logger")
    def test_render_token_email_logs_warning_on_fallback(self, mock_logger, tmp_path):
        """Test that using fallback logs warning."""
        # Create service with empty template directory
        template_path = tmp_path / "templates"
        template_path.mkdir()

        service = TemplateService(template_path=str(template_path))
        service.render_token_email("123456", "text")

        # Should log warning about using fallback
        assert any("fallback" in str(call).lower() for call in mock_logger.warning.call_args_list)


class TestGetTemplateService:
    """Tests for singleton template service function."""

    def test_get_template_service_returns_instance(self):
        """Test that get_template_service returns TemplateService instance."""
        service = get_template_service()

        assert isinstance(service, TemplateService)

    def test_get_template_service_singleton(self):
        """Test that get_template_service returns same instance."""
        # Reset singleton for test
        import app.services.template_service as ts_module

        ts_module._template_service_instance = None

        # Get service twice
        service1 = get_template_service()
        service2 = get_template_service()

        # Should be same instance
        assert service1 is service2

    def test_get_template_service_initializes_once(self):
        """Test that template service is only initialized once."""
        # Reset singleton
        import app.services.template_service as ts_module

        ts_module._template_service_instance = None

        # Get service multiple times
        services = [get_template_service() for _ in range(5)]

        # All should be same instance
        assert all(s is services[0] for s in services)


class TestTemplateServiceIntegration:
    """Integration tests for template service."""

    def test_full_workflow_text_email(self, tmp_path):
        """Test complete workflow of rendering text email."""
        # Create custom template
        template_path = tmp_path / "templates"
        template_path.mkdir()
        template_file = template_path / "token_email.text"
        template_file.write_text(
            """Hello,

Your verification code for {{ app_name }} is:

{{ token }}

This code will expire in {{ expiry_minutes }} minutes.

Best regards,
{{ company_name }}"""
        )

        # Render template
        service = TemplateService(template_path=str(template_path))
        result = service.render_token_email("123456", "text")

        # Verify complete rendering
        assert "123456" in result
        assert settings.app_name in result
        assert str(settings.token_expiry_minutes) in result

    def test_full_workflow_html_email(self, tmp_path):
        """Test complete workflow of rendering HTML email."""
        # Create custom HTML template
        template_path = tmp_path / "templates"
        template_path.mkdir()
        template_file = template_path / "token_email.html"
        template_file.write_text(
            """<!DOCTYPE html>
<html>
<head>
    <title>{{ app_name }}</title>
</head>
<body>
    <h1 style="color: {{ brand_primary_color }};">{{ company_name }}</h1>
    <p>Your code: <strong>{{ token }}</strong></p>
    <p>Expires in {{ expiry_minutes }} minutes</p>
</body>
</html>"""
        )

        # Render template
        service = TemplateService(template_path=str(template_path))
        result = service.render_token_email("999999", "html")

        # Verify HTML structure and content
        assert "<!DOCTYPE html>" in result
        assert "999999" in result
        assert settings.app_name in result
        assert settings.brand_primary_color in result

    def test_mixed_branding_and_custom_variables(self, tmp_path):
        """Test template with both branding and custom variables."""
        # Create template
        template_path = tmp_path / "templates"
        template_path.mkdir()
        template_file = template_path / "custom.txt"
        template_file.write_text("{{ greeting }}, your token is {{ token }} for {{ app_name }}")

        # Render with custom variable
        service = TemplateService(template_path=str(template_path))
        result = service.render_template("custom.txt", {"token": "111111", "greeting": "Welcome"})

        # Should include both custom and branding variables
        assert "Welcome" in result
        assert "111111" in result
        assert settings.app_name in result


class TestTemplateServiceExceptions:
    """Tests for custom exception classes."""

    def test_template_not_found_error(self):
        """Test TemplateNotFoundError can be raised."""
        with pytest.raises(TemplateNotFoundError):
            raise TemplateNotFoundError("Template missing")

    def test_template_render_error(self):
        """Test TemplateRenderError can be raised."""
        with pytest.raises(TemplateRenderError):
            raise TemplateRenderError("Render failed")

    def test_exceptions_are_exception_subclasses(self):
        """Test that custom exceptions are Exception subclasses."""
        assert issubclass(TemplateNotFoundError, Exception)
        assert issubclass(TemplateRenderError, Exception)

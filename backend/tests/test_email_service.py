"""
Unit tests for email service.

Tests email sending via Mailgun API with mocking.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from app.services import email_service


class TestEmailSending:
    """Tests for email sending functionality."""

    @pytest.mark.asyncio
    @patch("app.services.email_service.requests.post")
    async def test_send_token_email_success(self, mock_post):
        """Test successful email sending via Mailgun."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Send email
        result = await email_service.send_token_email("user@example.com", "123456")

        # Always returns True for security
        assert result is True

        # Verify Mailgun API was called
        assert mock_post.called

    @pytest.mark.asyncio
    @patch("app.services.email_service.requests.post")
    async def test_send_token_email_api_error(self, mock_post):
        """Test email sending with Mailgun API error."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        # Send email
        result = await email_service.send_token_email("user@example.com", "123456")

        # Still returns True for security (don't reveal errors)
        assert result is True

    @pytest.mark.asyncio
    @patch("app.services.email_service.requests.post")
    async def test_send_token_email_timeout(self, mock_post):
        """Test email sending with timeout."""
        # Mock timeout
        mock_post.side_effect = requests.exceptions.Timeout()

        # Send email
        result = await email_service.send_token_email("user@example.com", "123456")

        # Still returns True for security
        assert result is True

    @pytest.mark.asyncio
    @patch("app.services.email_service.requests.post")
    async def test_send_token_email_network_error(self, mock_post):
        """Test email sending with network error."""
        # Mock network error
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        # Send email
        result = await email_service.send_token_email("user@example.com", "123456")

        # Still returns True for security
        assert result is True

    @pytest.mark.asyncio
    @patch("app.services.email_service.requests.post")
    async def test_send_token_email_unexpected_error(self, mock_post):
        """Test email sending with unexpected error."""
        # Mock unexpected error
        mock_post.side_effect = Exception("Unexpected error")

        # Send email
        result = await email_service.send_token_email("user@example.com", "123456")

        # Still returns True for security
        assert result is True

    @pytest.mark.asyncio
    @patch("app.services.email_service.requests.post")
    async def test_send_token_email_format(self, mock_post):
        """Test that email is formatted correctly."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Send email
        await email_service.send_token_email("user@example.com", "123456")

        # Verify API call parameters
        assert mock_post.called
        call_args = mock_post.call_args

        # Check URL
        url = call_args[0][0]
        assert "api.mailgun.net" in url

        # Check data contains required fields
        data = call_args[1]["data"]
        assert "from" in data
        assert "to" in data
        assert data["to"] == "user@example.com"
        assert "subject" in data
        assert "text" in data
        assert "123456" in data["text"]

    @pytest.mark.asyncio
    @patch("app.services.email_service.settings")
    @patch("app.services.email_service.requests.post")
    async def test_send_token_email_missing_config(self, mock_post, mock_settings):
        """Test email sending with missing Mailgun configuration."""
        # Mock missing configuration
        mock_settings.mailgun_api_key = ""
        mock_settings.mailgun_domain = ""

        # Send email
        result = await email_service.send_token_email("user@example.com", "123456")

        # Still returns True for security
        assert result is True

        # Mailgun API should not be called
        assert not mock_post.called


class TestEmailMasking:
    """Tests for email masking functionality."""

    def test_mask_email_normal(self):
        """Test masking a normal email address."""
        masked = email_service._mask_email("user@example.com")
        assert masked == "u***@example.com"

    def test_mask_email_single_char(self):
        """Test masking email with single character username."""
        masked = email_service._mask_email("a@example.com")
        assert masked == "a***@example.com"

    def test_mask_email_long_username(self):
        """Test masking email with long username."""
        masked = email_service._mask_email("verylongemail@example.com")
        assert masked == "v***@example.com"

    def test_mask_email_invalid(self):
        """Test masking invalid email (no @ symbol)."""
        masked = email_service._mask_email("notanemail")
        assert masked == "***"

    def test_mask_email_preserves_domain(self):
        """Test that domain is preserved in masking."""
        masked = email_service._mask_email("test@mydomain.co.uk")
        assert "@mydomain.co.uk" in masked
        assert masked.startswith("t***")


class TestEmailTemplate:
    """Tests for email template functionality."""

    @pytest.mark.asyncio
    @patch("app.services.email_service.requests.post")
    async def test_email_contains_token(self, mock_post):
        """Test that email body contains the token."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        token = "987654"
        await email_service.send_token_email("user@example.com", token)

        # Get email body from call
        call_args = mock_post.call_args
        data = call_args[1]["data"]
        email_body = data["text"]

        assert token in email_body

    @pytest.mark.asyncio
    @patch("app.services.email_service.requests.post")
    async def test_email_contains_expiry_info(self, mock_post):
        """Test that email body contains expiry information."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        await email_service.send_token_email("user@example.com", "123456")

        # Get email body from call
        call_args = mock_post.call_args
        data = call_args[1]["data"]
        email_body = data["text"]

        # Should mention expiry (in minutes)
        assert "expire" in email_body.lower()
        assert "minute" in email_body.lower()

    @pytest.mark.asyncio
    @patch("app.services.email_service.requests.post")
    async def test_email_contains_app_name(self, mock_post):
        """Test that email body contains application name."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        await email_service.send_token_email("user@example.com", "123456")

        # Get email body from call
        call_args = mock_post.call_args
        data = call_args[1]["data"]
        email_body = data["text"]

        from app.core.config import get_settings

        settings = get_settings()

        # Should contain app name
        assert settings.app_name in email_body

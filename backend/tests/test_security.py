"""
Tests for the security module placeholder functions.

This module tests that the placeholder security functions correctly
raise NotImplementedError, as they are scheduled for Sprint 2.
"""

import pytest

from app.core import security


class TestSecurityPlaceholders:
    """Tests for security placeholder functions."""

    @pytest.mark.asyncio
    async def test_create_access_token_raises_not_implemented(self):
        """Test that create_access_token raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            await security.create_access_token({"user_id": "123"})

        assert "Sprint 2" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_access_token_with_expiry_raises_not_implemented(self):
        """Test that create_access_token with expiry raises NotImplementedError."""
        from datetime import timedelta

        with pytest.raises(NotImplementedError) as exc_info:
            await security.create_access_token({"user_id": "123"}, timedelta(hours=1))

        assert "Sprint 2" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_token_raises_not_implemented(self):
        """Test that verify_token raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            await security.verify_token("some_token")

        assert "Sprint 2" in str(exc_info.value)

    def test_generate_auth_token_raises_not_implemented(self):
        """Test that generate_auth_token raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            security.generate_auth_token()

        assert "Sprint 2" in str(exc_info.value)

    def test_generate_auth_token_with_length_raises_not_implemented(self):
        """Test that generate_auth_token with custom length raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            security.generate_auth_token(length=8)

        assert "Sprint 2" in str(exc_info.value)

    def test_hash_token_raises_not_implemented(self):
        """Test that hash_token raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            security.hash_token("some_token")

        assert "Sprint 2" in str(exc_info.value)

    def test_verify_token_hash_raises_not_implemented(self):
        """Test that verify_token_hash raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            security.verify_token_hash("token", "hashed_token")

        assert "Sprint 2" in str(exc_info.value)

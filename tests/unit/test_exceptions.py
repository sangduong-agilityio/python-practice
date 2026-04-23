"""Unit tests for custom exceptions.

Tests that custom exceptions are properly defined and can be
instantiated with appropriate messages.
"""

import pytest

from app.core.exceptions import (
    InvalidFieldException,
    PermissionDeniedException,
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
)


class TestResourceNotFoundException:
    """Tests for ResourceNotFoundException."""

    def test_exception_message(self):
        """Test exception includes resource type and message."""
        exc = ResourceNotFoundException("user")

        str_exc = str(exc)
        assert "user" in str_exc.lower() or "not found" in str_exc.lower()

    def test_exception_instantiation(self):
        """Test exception can be raised and caught."""
        with pytest.raises(ResourceNotFoundException):
            raise ResourceNotFoundException("project")

    def test_different_resource_types(self):
        """Test exception works with different resource types."""
        for resource_type in ["user", "project", "task", "tag"]:
            exc = ResourceNotFoundException(resource_type)
            assert resource_type in str(exc).lower()


class TestPermissionDeniedException:
    """Tests for PermissionDeniedException."""

    def test_exception_message(self):
        """Test exception message."""
        exc = PermissionDeniedException(
            "Only project owner can delete projects")

        str_exc = str(exc)
        assert "deleted" in str_exc.lower() or "project" in str_exc.lower()

    def test_exception_instantiation(self):
        """Test exception can be raised and caught."""
        with pytest.raises(PermissionDeniedException):
            raise PermissionDeniedException("Access denied")

    def test_custom_message(self):
        """Test exception accepts custom messages."""
        msg = "User is not owner of this resource"
        exc = PermissionDeniedException(msg)
        assert msg in str(exc)


class TestResourceAlreadyExistsException:
    """Tests for ResourceAlreadyExistsException."""

    def test_exception_message(self):
        """Test exception includes resource details."""
        exc = ResourceAlreadyExistsException(
            "User with email test@example.com already exists")

        str_exc = str(exc)
        assert "already" in str_exc.lower() or "exists" in str_exc.lower()

    def test_exception_instantiation(self):
        """Test exception can be raised and caught."""
        with pytest.raises(ResourceAlreadyExistsException):
            raise ResourceAlreadyExistsException(
                "Project with name 'My Project' already exists")

    def test_different_field_types(self):
        """Test exception works with different field types."""
        exc_email = ResourceAlreadyExistsException(
            "User with email test@example.com already exists")
        exc_username = ResourceAlreadyExistsException(
            "User with username testuser already exists")

        assert "email" in str(exc_email).lower(
        ) or "test@example.com" in str(exc_email)
        assert "username" in str(exc_username).lower(
        ) or "testuser" in str(exc_username)


class TestInvalidFieldException:
    """Tests for InvalidFieldException."""

    def test_exception_message(self):
        """Test exception includes field information."""
        exc = InvalidFieldException("owner_id")

        str_exc = str(exc)
        assert "owner_id" in str_exc or "field" in str_exc.lower() or "cannot" in str_exc.lower()

    def test_exception_instantiation(self):
        """Test exception can be raised and caught."""
        with pytest.raises(InvalidFieldException):
            raise InvalidFieldException("id")

    def test_blocked_field_names(self):
        """Test exception for various blocked field names."""
        blocked_fields = ["id", "created_at",
                          "updated_at", "owner_id", "project_id"]

        for field in blocked_fields:
            exc = InvalidFieldException(field)
            str_exc = str(exc)
            # Should contain either field name or generic message about not updatable
            assert field in str_exc or "cannot" in str_exc.lower()

    def test_multiple_resource_types(self):
        """Test exception captures field names correctly."""
        for field_name in ["protected_field", "id", "created_at", "owner_id"]:
            exc = InvalidFieldException(field_name)
            str_exc = str(exc)
            # Should capture the field name in exception message
            assert field_name in str_exc or "cannot" in str_exc.lower()


class TestExceptionHierarchy:
    """Tests for exception inheritance and relationships."""

    def test_all_exceptions_inherit_exception(self):
        """Test all custom exceptions inherit from Exception."""
        assert issubclass(ResourceNotFoundException, Exception)
        assert issubclass(PermissionDeniedException, Exception)
        assert issubclass(ResourceAlreadyExistsException, Exception)
        assert issubclass(InvalidFieldException, Exception)

    def test_exception_catching(self):
        """Test exceptions can be caught as base Exception."""
        with pytest.raises(Exception):  # noqa: B017
            raise ResourceNotFoundException("user")

        with pytest.raises(Exception):  # noqa: B017
            raise PermissionDeniedException("No permission")

    def test_specific_exception_not_caught_by_wrong_handler(self):
        """Test specific exception type checking."""
        try:
            raise ResourceNotFoundException("user")
        except PermissionDeniedException:
            pytest.fail(
                "ResourceNotFoundException caught by PermissionDeniedException handler")
        except ResourceNotFoundException:
            pass  # Expected

    def test_exception_attributes(self):
        """Test exceptions can store additional information."""
        exc = InvalidFieldException("id")

        # Should be able to convert to string
        str_repr = str(exc)
        assert len(str_repr) > 0


class TestExceptionRaiseableScenarios:
    """Integration tests for exception raising scenarios."""

    @pytest.mark.asyncio
    async def test_not_found_scenario(self):
        """Test not found exception in typical scenario."""
        with pytest.raises(ResourceNotFoundException) as exc_info:
            # Simulate service method
            raise ResourceNotFoundException("user")

        assert "user" in str(exc_info.value).lower(
        ) or "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_permission_scenario(self):
        """Test permission exception in typical scenario."""
        with pytest.raises(PermissionDeniedException) as exc_info:
            # Simulate authorization check
            user_id = 1
            owner_id = 2
            if user_id != owner_id:
                raise PermissionDeniedException(
                    "User is not the project owner")

        assert "owner" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_already_exists_scenario(self):
        """Test already exists exception in typical scenario."""
        email = "existing@example.com"

        with pytest.raises(ResourceAlreadyExistsException) as exc_info:
            # Simulate duplicate check
            raise ResourceAlreadyExistsException(
                f"User with email {email} already exists")

        assert "already" in str(exc_info.value).lower(
        ) or email in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_field_scenario(self):
        """Test invalid field exception in typical scenario."""
        with pytest.raises(InvalidFieldException) as exc_info:
            # Simulate field validation
            blocked_field = "owner_id"
            raise InvalidFieldException(blocked_field)

        assert "owner_id" in str(exc_info.value) or "cannot" in str(
            exc_info.value).lower()

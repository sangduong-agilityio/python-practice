"""Unit tests for validation utilities.

Simple unit tests for field validation without database dependency.
"""

import pytest
from app.core.validation import validate_updatable_field
from app.core.exceptions import InvalidFieldException


class TestValidateUpdatableField:
    """Test suite for validate_updatable_field utility."""

    def test_valid_field_passes(self):
        """Test validation passes for whitelisted field."""
        # Should not raise
        validate_updatable_field("name", {"name", "description"}, "project")

    def test_invalid_field_raises(self):
        """Test validation fails for non-whitelisted field."""
        with pytest.raises(InvalidFieldException):
            validate_updatable_field(
                "owner_id", {"name", "description"}, "project")

    def test_protected_fields_blocked(self):
        """Test that protected fields cannot be updated."""
        protected_fields = ["id", "created_at", "updated_at"]
        for field in protected_fields:
            with pytest.raises(InvalidFieldException):
                validate_updatable_field(field, {"name"}, "resource")

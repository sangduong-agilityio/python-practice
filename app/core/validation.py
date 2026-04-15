"""
Validation utilities for field updates and data integrity.

Centralized validation functions to ensure consistent enforcement
of business rules across the application.
"""

import structlog

from app.core.exceptions import InvalidFieldException

log = structlog.get_logger(__name__)


def validate_updatable_field(field_name: str, allowed_fields: set[str], resource_type: str = "resource") -> None:
    """Validate that a field is in the whitelist of updatable fields.

    Logs security events and raises InvalidFieldException if the field
    cannot be updated, preventing unauthorized field modifications.

    Args:
        field_name: The field name to validate.
        allowed_fields: Set of field names that are allowed to be updated.
        resource_type: Type of resource (e.g., "task", "project") for logging.

    Raises:
        InvalidFieldException: If field_name is not in allowed_fields.
    """
    if field_name not in allowed_fields:
        log.warning(
            "blocked_field_update_attempt",
            field=field_name,
            resource_type=resource_type,
            allowed_fields=sorted(allowed_fields),
        )
        raise InvalidFieldException(field_name)

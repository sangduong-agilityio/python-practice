"""
Custom Domain Exceptions.

Defining these custom exceptions allows the service layer to raise business logic
errors (pure Python exceptions) without tying them to HTTP status codes or FastAPI's
HTTPException. The global exception handler in main.py will map these to correct HTTP responses.
"""


class AppException(Exception):
    """Base exception for all application-level errors."""

    def __init__(self, message: str):
        self.message = message


class ResourceNotFoundException(AppException):
    """Raised when a requested database entity (Model) cannot be found."""

    def __init__(self, resource_name: str):
        super().__init__(f"{resource_name} not found")


class AuthenticationFailedException(AppException):
    """Raised when login credentials are invalid."""

    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message)


class PermissionDeniedException(AppException):
    """Raised when a user lacks the authorization to perform an action (e.g., modifying another user's resource)."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message)


class ResourceAlreadyExistsException(AppException):
    """Raised when creating an entity violates a uniqueness constraint (e.g., duplicated email or tag name)."""

    def __init__(self, message: str):
        super().__init__(message)


class InvalidFieldException(AppException):
    """Raised when attempting to update a field that cannot be modified."""

    def __init__(self, field_name: str):
        super().__init__(f"Cannot update field: {field_name}")

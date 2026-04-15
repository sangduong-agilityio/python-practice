"""
Central error messages and constants for the application.

Centralizing error messages ensures consistency and makes i18n easier.
All user-facing error messages should be defined here.
"""


class ErrorMessages:
    """User-facing error messages returned in HTTP responses."""

    # Authentication
    INVALID_CREDENTIALS = "Incorrect email or password"
    INVALID_TOKEN = "Invalid or expired token"
    ACCOUNT_INACTIVE = "User account is inactive"

    # User errors
    EMAIL_ALREADY_REGISTERED = "Email is already registered"
    USERNAME_ALREADY_TAKEN = "Username is already taken"
    USER_NOT_FOUND = "User not found"

    # Project errors
    PROJECT_NOT_FOUND = "Project not found"

    # Task errors
    TASK_NOT_FOUND = "Task not found"
    ASSIGNEE_NOT_FOUND = "Assignee not found"

    # Tag errors
    TAG_NOT_FOUND = "Tag not found"
    TAG_ALREADY_EXISTS = "Tag with this name already exists"

    # Permission errors
    INSUFFICIENT_PERMISSIONS = "You do not have permission to access this resource"
    ONLY_PROJECT_OWNER_CAN_ACTION = "Only the project owner can perform this action"

    # Validation errors
    INVALID_INPUT_DATA = "Invalid input data"
    INTERNAL_SERVER_ERROR = "Internal server error"


class Headers:
    """HTTP header names used throughout the application."""

    REQUEST_ID = "X-Request-ID"
    AUTHORIZATION = "Authorization"


class CacheNamespaces:
    """Cache key namespace prefixes for Redis."""

    PROJECTS = "projects:user"
    TAGS = "tags:all"
    TOKEN_BLACKLIST = "token_blacklist"


class Timeouts:
    """Timeout and TTL constants in seconds/minutes."""

    CACHE_DEFAULT_TTL_SECONDS = 60
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7


class UpdatableFields:
    """Whitelisted fields that can be updated via API for each resource.

    This protects system fields (id, created_at, owner_id, etc.) from being
    modified by users, preventing security vulnerabilities like privilege escalation.
    """

    PROJECT = {"name", "description"}
    TASK = {"title", "description", "priority",
            "status", "due_date", "assignee_id"}
    USER = {"username", "email", "hashed_password", "is_active"}
    TAG = {"name"}

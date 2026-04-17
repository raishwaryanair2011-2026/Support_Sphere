"""
Centralised exception hierarchy.
Raising these anywhere in the app produces consistent HTTP error responses
via the handlers registered in main.py.
"""
from typing import Any, Dict, Optional


class AppException(Exception):
    """Base for all application exceptions."""

    status_code: int = 500
    detail: str = "An unexpected error occurred"

    def __init__(
        self,
        detail: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ):
        self.detail = detail or self.__class__.detail
        self.extra = extra or {}
        super().__init__(self.detail)


class BadRequestException(AppException):
    status_code = 400
    detail = "Bad request"


class UnauthorizedException(AppException):
    status_code = 401
    detail = "Unauthorized"


class ForbiddenException(AppException):
    status_code = 403
    detail = "Forbidden"


class NotFoundException(AppException):
    status_code = 404
    detail = "Resource not found"


class ConflictException(AppException):
    status_code = 409
    detail = "Conflict"


class UnprocessableEntityException(AppException):
    status_code = 422
    detail = "Unprocessable entity"


class ServiceUnavailableException(AppException):
    status_code = 503
    detail = "Service temporarily unavailable"

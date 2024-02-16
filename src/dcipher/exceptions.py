from __future__ import annotations

from typing import Union

import httpx
from requests import Request as RequestsRequest
from typing_extensions import Literal

__all__ = [
    "BadRequestError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "UnprocessableEntityError",
    "RateLimitError",
    "InternalServerError",
    "WorkflowFailedException",
]


class DcipherError(Exception):
    pass


class APIError(DcipherError):
    message: str
    request: Union[httpx.Request, RequestsRequest]

    body: object | None
    """The API response body.

    If the API responded with a valid JSON structure then this property will be the
    decoded result.

    If it isn't a valid JSON structure then this will be the raw response.

    If there was no response associated with this error then it will be `None`.
    """

    def __init__(self, message: str, request: Union[httpx.Request,
                                                    RequestsRequest],
                 body: object | None = None):
        super().__init__(message)
        self.request = request
        self.message = message
        self.body = body


class APIStatusError(APIError):
    """Raised when an API response has a status code of 4xx or 5xx."""

    response: Union[httpx.Request, RequestsRequest]
    status_code: int

    def __init__(self, message: str, *, response: Union[httpx.Request,
                                                        RequestsRequest],
                 body: object | None = None) -> None:
        super().__init__(message, response.request, body=body)
        self.response = response
        self.status_code = response.status_code


class BadRequestError(APIStatusError):
    # pyright: ignore[reportIncompatibleVariableOverride]
    status_code: Literal[400] = 400


class AuthenticationError(APIStatusError):
    # pyright: ignore[reportIncompatibleVariableOverride]
    status_code: Literal[401] = 401


class PermissionDeniedError(APIStatusError):
    # pyright: ignore[reportIncompatibleVariableOverride]
    status_code: Literal[403] = 403


class NotFoundError(APIStatusError):
    # pyright: ignore[reportIncompatibleVariableOverride]
    status_code: Literal[404] = 404


class ConflictError(APIStatusError):
    # pyright: ignore[reportIncompatibleVariableOverride]
    status_code: Literal[409] = 409


class UnprocessableEntityError(APIStatusError):
    # pyright: ignore[reportIncompatibleVariableOverride]
    status_code: Literal[422] = 422


class RateLimitError(APIStatusError):
    # pyright: ignore[reportIncompatibleVariableOverride]
    status_code: Literal[429] = 429


class InternalServerError(APIStatusError):
    pass


class WorkflowFailedException(DcipherError):
    pass

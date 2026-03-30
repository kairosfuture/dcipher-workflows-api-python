import json

from httpx import NetworkError, TimeoutException
from requests.exceptions import ConnectionError, Timeout

from .exceptions import ConflictError, InternalServerError, RateLimitError

# json.JSONDecodeError covers response.json() failures (requests + httpx).
RETRIABLE_EXCEPTIONS = (ConnectionError, Timeout,
                        ConflictError, RateLimitError,
                        InternalServerError, TimeoutException, NetworkError,
                        json.JSONDecodeError)

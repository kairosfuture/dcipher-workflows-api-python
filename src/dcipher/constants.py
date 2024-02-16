from httpx import NetworkError, TimeoutException
from requests.exceptions import ConnectionError, Timeout

from .exceptions import ConflictError, InternalServerError, RateLimitError

RETRIABLE_EXCEPTIONS = (ConnectionError, Timeout,
                        ConflictError, RateLimitError,
                        InternalServerError, TimeoutException, NetworkError)

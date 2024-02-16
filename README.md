# Dcipher Workflows API Python API library

The Dcipher Workflows Python library provides convenient access to the Dcipher Workflows API from any Python 3.7+
application. It offers both synchronous and asynchronous clients powered by [httpx](https://github.com/encode/httpx).

## Documentation

The REST API documentation can be found [on app.dcipheranalytics.com/workflows](https://app.dcipheranalytics.com/workflows).

## Installation

```sh
pip install dcipher
```

## Usage

```python
import os
from dcipher import Dcipher

client = Dcipher(
    # This is the default and can be omitted
    api_key=os.environ.get("DCIPHER_API_KEY"),
)

client.run_flow(
    flow_id="65cf2f3e..",
    params={"param1": "...", "param2": "...."}, # param names are set by workflow user
    save_path="output.json",
)
```

While you can provide an `api_key` keyword argument,
we recommend using [python-dotenv](https://pypi.org/project/python-dotenv/)
to add `DCIPHER_API_KEY="my-dcipher-api-key"` to your `.env` file
so that your API Key is not stored in source control.

## Async usage

Simply import `AsyncDcipher` instead of `Dcipher` and use `await` with each API call:

```python
import os
import asyncio
from dcipher import AsyncDcipher

client = AsyncDcipher(
    # This is the default and can be omitted
    api_key=os.environ.get("DCIPHER_API_KEY"),
)


async def main() -> None:
    await client.run_flow(
        flow_id="65cf2f3e..",
        params={"param1": "...", "param2": "...."}, # param names are set by workflow user
        save_path="output.json",
    )


asyncio.run(main())
```

Functionality between the synchronous and asynchronous clients is otherwise identical.

## Handling errors

When the API returns a non-success status code (that is, 4xx or 5xx
response), a subclass of `APIStatusError` is raised, containing an error message.

In case Timeout or Connection errors occur, the client auto-retries with exponential back-off using `tenacity`.

Error codes are as follows:

| Status Code | Error Type                 |
| ----------- | -------------------------- |
| 400         | `BadRequestError`          |
| 401         | `AuthenticationError`      |
| 403         | `PermissionDeniedError`    |
| 404         | `NotFoundError`            |
| 422         | `UnprocessableEntityError` |
| 429         | `RateLimitError`           |
| >=500       | `InternalServerError`      |

### Retries

Certain errors are automatically retried by default, with a short exponential backoff.
Connection errors (for example, due to a network connectivity problem), 408 Request Timeout, 409 Conflict,
429 Rate Limit, and >=500 Internal errors are all retried by default.

You can use the `max_retries` option to configure or disable retry settings.

## Advanced

### Logging

We use the standard library [`logging`](https://docs.python.org/3/library/logging.html) module.

You can enable logging by setting the environment variable `DCIPHER_LOG` to `debug`.

```shell
$ export DCIPHER_LOG=debug
```


## Requirements

Python 3.7 or higher.

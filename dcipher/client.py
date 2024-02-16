import json
import os
from time import sleep
from typing import Any, Dict, Optional, Union

import requests
from httpx import Response as HTTPXResponse
from requests import Response as RequestsResponse
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from .constants import RETRIABLE_EXCEPTIONS
from .exceptions import (
    APIStatusError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    InternalServerError,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableEntityError,
    WorkflowFailedException,
)
from .logger import setup_logger

logger = setup_logger()


class Dcipher:

    def __init__(self, api_key: Optional[str], max_retries: int = 100):
        self.api_key = api_key or os.environ.get("DCIPHER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Please either provide api_key or set DCIPHER_API_KEY environment variable.")  # noqa
        self.max_retries = max_retries

    def _prepare_request_params(self, flow_id: str, params: Dict[str, Any]) \
            -> Dict:
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
        }
        endpoint_url_template = "https://api.dcipheranalytics.com/flows/{}/run"

        endpoint_url = endpoint_url_template.format(flow_id)
        body = {
            "pipelineParams": params,
        }
        return {
            "url": endpoint_url,
            "headers": headers,
            "data": json.dumps(body),
        }

    def _prepare_status_params(self, flow_id: str, task_id: str) -> Dict:
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
        }
        status_endpoint_url_template = "https://api.dcipheranalytics.com/flows/{}/status"  # noqa
        status_endpoint_url = status_endpoint_url_template.format(flow_id)
        url = f"{status_endpoint_url}?taskId={task_id}"
        return {
            "url": url,
            "headers": headers,
        }

    def run_flow(self,
                 flow_id: str,
                 params: Dict[str, Any],
                 save_path: Optional[str]):

        request_params = self._prepare_request_params(
            flow_id=flow_id, params=params)

        @retry(wait=wait_random_exponential(min=1, max=15),
               stop=stop_after_attempt(self.max_retries),
               retry=retry_if_exception_type(
                   exception_types=RETRIABLE_EXCEPTIONS),
               )
        def send_post_request():
            response = requests.post(**request_params, timeout=60)
            try:
                response.raise_for_status()
            except Exception:
                raise self._make_status_error(response=response)
            return response.json()

        response = send_post_request()

        response_url = response["signedResponseURL"]
        running_task_id = response["taskId"]
        logger.debug(f"Running taskId: {running_task_id}")

        sleep(5)

        @retry(wait=wait_random_exponential(min=1, max=15),
               stop=stop_after_attempt(self.max_retries),
               retry=retry_if_exception_type(
                   exception_types=RETRIABLE_EXCEPTIONS),
               )
        def get_status():
            params = self._prepare_status_params(
                flow_id=flow_id, task_id=running_task_id)
            status_response = requests.get(**params, timeout=60)
            try:
                status_response.raise_for_status()
            except Exception:
                raise self._make_status_error(response=status_response)
            return status_response.json()

        while (True):
            status_response = get_status()
            status = status_response["status"]
            message = status_response.get("message", "")

            if status == "SUCCEEDED":
                logger.debug("Workflow has SUCCEEDED. Saving results")
                self._save_result(url=response_url, save_path=save_path)
                break

            if status == "FAILED":
                message = f"Workflow has failed. Reason: {message}"
                raise WorkflowFailedException(message)

            logger.debug(f"Status is {status}. Waiting for 3 more seconds")
            sleep(3)

    def _save_result(self, url: str, save_path: str):
        # Send a GET request to the URL
        response = requests.get(url)

        # Check if the request was successful (status code <300)
        if response.status_code < 300:
            with open(save_path, "wb") as file:
                file.write(response.content)

            logger.info(
                f"Output file is downloaded successfully to: {save_path}")
        else:
            response.raise_for_status()

    def _make_status_error(self, response: Union[RequestsResponse,
                                                 HTTPXResponse]):
        status_code_to_exception = {
            400: BadRequestError,
            401: AuthenticationError,
            403: PermissionDeniedError,
            409: ConflictError,
            422: UnprocessableEntityError,
            429: RateLimitError,
        }

        if response.status_code >= 500:
            exception_class = InternalServerError
        else:
            exception_class = status_code_to_exception.get(
                response.status_code, APIStatusError)

        message = response.json().get("message", "")
        return exception_class(message=message, response=response)

import asyncio
from typing import Any, Dict, Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from .client import Dcipher
from .constants import RETRIABLE_EXCEPTIONS
from .exceptions import WorkflowFailedException
from .logger import setup_logger

logger = setup_logger()


class AsyncDcipher(Dcipher):

    async def run_flow(self,
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
        async def send_post_request():
            async with httpx.AsyncClient() as client:
                response = await client.post(**request_params, timeout=60)
                try:
                    response.raise_for_status()
                except Exception:
                    raise self._make_status_error(response=response)
                return response.json()

        response = await send_post_request()

        response_url = response["signedResponseURL"]
        running_task_id = response["taskId"]
        logger.debug(f"Running taskId: {running_task_id}")

        await asyncio.sleep(3)

        @retry(wait=wait_random_exponential(min=1, max=15),
               stop=stop_after_attempt(self.max_retries),
               retry=retry_if_exception_type(
                   exception_types=RETRIABLE_EXCEPTIONS),
               )
        async def get_status():
            params = self._prepare_status_params(
                flow_id=flow_id, task_id=running_task_id)

            async with httpx.AsyncClient() as client:
                status_response = await client.get(**params, timeout=60)
                try:
                    status_response.raise_for_status()
                except Exception:
                    raise self._make_status_error(response=status_response)
                return status_response.json()

        while (True):
            status_response = await get_status()
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
            await asyncio.sleep(3)

import logging
import os
import sys

LOG_LEVEL = os.environ.get("DCIPHER_LOG", "ERROR")


def setup_logger():
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    )
    handler.setFormatter(formatter)

    # default logger
    default_logger = logging.getLogger()
    # remove default handler with formatter
    default_logger.handlers.clear()
    default_logger.setLevel(getattr(logging, LOG_LEVEL.upper()))
    default_logger.addHandler(handler)

    # subloggers
    for loggername in ["httpx", "httpcore", "asyncio", "urllib3"]:
        sublogger = logging.getLogger(loggername)
        sublogger.setLevel(getattr(logging, 'WARN'))

    return default_logger

import time
import functools
from typing import Callable, Any
import requests
from utils.logger import logger
from config.settings import settings

def retry_on_failure(
    retries: int = None,
    backoff_factor: float = None,
    status_codes_to_retry: tuple = (500, 502, 503, 504, 429)
) -> Callable:
    """
    Decorator to retry requests upon hitting network issues, timeouts, or specific HTTP status codes.
    
    Args:
        retries: Maximum number of retries (defaults to config settings).
        backoff_factor: Multiplier for backoff delay (defaults to config settings).
        status_codes_to_retry: Tuples of HTTP status codes to retry on.
    """
    max_retries = retries if retries is not None else settings.max_retries
    delay_factor = backoff_factor if backoff_factor is not None else settings.backoff_factor

    def decorator(func: Callable[..., requests.Response]) -> Callable[..., requests.Response]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> requests.Response:
            attempt = 0
            while attempt <= max_retries:
                try:
                    response = func(*args, **kwargs)
                    # Check if status code is subject to retry
                    if response.status_code in status_codes_to_retry:
                        logger.warning(
                            f"HTTP {response.status_code} received. "
                            f"Retrying attempt {attempt + 1}/{max_retries}..."
                        )
                    else:
                        return response
                except (requests.exceptions.ConnectionError,
                        requests.exceptions.Timeout,
                        requests.exceptions.ChunkedEncodingError) as exc:
                    logger.warning(
                        f"Exception '{exc.__class__.__name__}' encountered. "
                        f"Retrying attempt {attempt + 1}/{max_retries}..."
                    )
                    if attempt == max_retries:
                        raise exc
                
                # Calculate exponential backoff: delay = factor * 2^attempt
                sleep_time = delay_factor * (2 ** attempt)
                logger.info(f"Sleeping for {sleep_time:.2f} seconds before retrying...")
                time.sleep(sleep_time)
                attempt += 1

            # If all retries exhausted, return the last response (could be 5xx / 429)
            return response
        return wrapper
    return decorator

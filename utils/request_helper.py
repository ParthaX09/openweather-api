import time
from typing import Dict, Any, Optional
import requests
from utils.logger import logger
from utils.retry import retry_on_failure

class RequestHelper:
    """Wrapper class over the requests library to provide transparent logging, timing, and error safety."""

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()

    @retry_on_failure()
    def send_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs: Any
    ) -> requests.Response:
        """
        Sends an HTTP request with built-in logging, timing, and error handling.
        
        Args:
            method: HTTP verb (GET, POST, etc.)
            url: Full endpoint target URL.
            params: Dictionary of query parameters.
            headers: Dictionary of headers.
            json_data: JSON payload.
            timeout: Maximum wait time.
        """
        method = method.upper()
        
        # Log request details (redact api key if present)
        logged_params = self._redact_sensitive_data(params)
        logger.info(f"API Request: {method} {url} | Params: {logged_params} | JSON: {json_data}")
        
        start_time = time.perf_counter()
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                json=json_data,
                timeout=timeout,
                **kwargs
            )
        except requests.exceptions.RequestException as exc:
            logger.error(f"API Connection failure: {exc}")
            raise exc

        end_time = time.perf_counter()
        response_time_ms = (end_time - start_time) * 1000
        
        # Inject response time metadata to standard response object (for assertions)
        response.elapsed_ms = response_time_ms
        
        # Log response details
        logger.info(
            f"API Response: {response.status_code} | "
            f"Time: {response_time_ms:.2f}ms | "
            f"Size: {len(response.content)} bytes"
        )
        logger.debug(f"Response Body: {response.text[:2000]}") # Truncate long bodies in debug
        
        return response

    @staticmethod
    def _redact_sensitive_data(params: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Ensures API keys/secrets are not logged in plain text."""
        if not params:
            return params
        redacted = params.copy()
        for key in ["appid", "api_key", "token", "password", "secret"]:
            if key in redacted:
                redacted[key] = "********"
        return redacted

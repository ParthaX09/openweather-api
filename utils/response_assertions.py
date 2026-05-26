from typing import Any, Dict, List, Union
import requests
from utils.logger import logger

class ResponseAssertions:
    """Enterprise-level API assertion class for deep validation of response bodies, structures, and metadata."""

    @staticmethod
    def get_nested_value(data: Union[Dict[str, Any], List[Any]], path: str) -> Any:
        """
        Retrieves a nested value from a dictionary or list using dot notation (e.g. 'main.temp' or 'weather.0.main').
        
        Args:
            data: The JSON payload.
            path: Dot-separated path to target value.
        """
        if not path:
            return data
        parts = path.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict):
                if part not in current:
                    raise KeyError(f"Path segment '{part}' not found in dictionary. Current structure: {current}")
                current = current[part]
            elif isinstance(current, list):
                try:
                    idx = int(part)
                    current = current[idx]
                except ValueError:
                    raise TypeError(f"Attempted to access list using non-integer path segment '{part}'. Current structure: {current}")
                except IndexError:
                    raise IndexError(f"Index {idx} out of range for list. Current length: {len(current)}")
            else:
                raise TypeError(f"Cannot traverse path segment '{part}' on primitive type: {type(current)} (value: {current})")
        return current

    @classmethod
    def assert_status_code(cls, response: requests.Response, expected_code: int) -> None:
        """Asserts response status code, outputting full body on failure for easier debugging."""
        actual_code = response.status_code
        if actual_code != expected_code:
            error_msg = f"Status code mismatch! Expected {expected_code}, got {actual_code}. Response: {response.text}"
            logger.error(error_msg)
            assert actual_code == expected_code, error_msg

    @classmethod
    def assert_response_time(cls, response: requests.Response, max_allowed_ms: float) -> None:
        """Asserts response time is below threshold."""
        actual_ms = getattr(response, "elapsed_ms", response.elapsed.total_seconds() * 1000)
        if actual_ms > max_allowed_ms:
            error_msg = f"Response latency threshold exceeded! Max allowed: {max_allowed_ms}ms, Actual: {actual_ms:.2f}ms"
            logger.warning(error_msg)
            assert actual_ms <= max_allowed_ms, error_msg
        logger.info(f"Response latency check passed: {actual_ms:.2f}ms (threshold: {max_allowed_ms}ms)")

    @classmethod
    def assert_field_exists(cls, data: Union[Dict[str, Any], List[Any]], path: str) -> None:
        """Asserts that a nested field path exists in the response JSON."""
        if not path:
            return
        try:
            cls.get_nested_value(data, path)
        except (KeyError, TypeError, IndexError) as exc:
            error_msg = f"Required field path '{path}' does not exist: {exc}"
            logger.error(error_msg)
            assert False, error_msg

    @classmethod
    def assert_field_value(cls, data: Union[Dict[str, Any], List[Any]], path: str, expected: Any) -> None:
        """Asserts that a nested field path has the exact expected value."""
        cls.assert_field_exists(data, path)
        actual = cls.get_nested_value(data, path)
        if actual != expected:
            error_msg = f"Field value mismatch at '{path}'! Expected: {expected} ({type(expected)}), Got: {actual} ({type(actual)})"
            logger.error(error_msg)
            assert actual == expected, error_msg

    @classmethod
    def assert_field_type(cls, data: Union[Dict[str, Any], List[Any]], path: str, expected_type: Union[type, tuple]) -> None:
        """Asserts that a nested field has the expected Python type."""
        cls.assert_field_exists(data, path)
        actual = cls.get_nested_value(data, path)
        if not isinstance(actual, expected_type):
            error_msg = f"Field type mismatch at '{path}'! Expected type: {expected_type}, Got: {type(actual)} (value: {actual})"
            logger.error(error_msg)
            assert isinstance(actual, expected_type), error_msg

    @classmethod
    def assert_field_range(cls, data: Union[Dict[str, Any], List[Any]], path: str, min_val: float, max_val: float) -> None:
        """Asserts that a numeric field is within the specified inclusive range."""
        cls.assert_field_exists(data, path)
        actual = cls.get_nested_value(data, path)
        if not isinstance(actual, (int, float)):
            error_msg = f"Cannot perform range check on non-numeric value at '{path}'! Value: {actual} ({type(actual)})"
            logger.error(error_msg)
            assert False, error_msg
        if not (min_val <= actual <= max_val):
            error_msg = f"Field value at '{path}' out of range [{min_val}, {max_val}]! Actual value: {actual}"
            logger.error(error_msg)
            assert min_val <= actual <= max_val, error_msg

    @classmethod
    def assert_array_not_empty(cls, data: Union[Dict[str, Any], List[Any]], path: str) -> None:
        """Asserts that a nested array exists and contains at least one item."""
        cls.assert_field_exists(data, path)
        actual = cls.get_nested_value(data, path)
        if not isinstance(actual, list):
            error_msg = f"Field at '{path}' is not a list! Type: {type(actual)}"
            logger.error(error_msg)
            assert False, error_msg
        if len(actual) == 0:
            error_msg = f"Array at '{path}' is empty!"
            logger.error(error_msg)
            assert len(actual) > 0, error_msg

    @classmethod
    def assert_array_length(cls, data: Union[Dict[str, Any], List[Any]], path: str, expected_len: int) -> None:
        """Asserts that a nested array has the exact expected length."""
        cls.assert_field_exists(data, path)
        actual = cls.get_nested_value(data, path)
        if not isinstance(actual, list):
            error_msg = f"Field at '{path}' is not a list! Type: {type(actual)}"
            logger.error(error_msg)
            assert False, error_msg
        actual_len = len(actual)
        if actual_len != expected_len:
            error_msg = f"Array length mismatch at '{path}'! Expected length: {expected_len}, Got: {actual_len}"
            logger.error(error_msg)
            assert actual_len == expected_len, error_msg

    @classmethod
    def assert_header_value(cls, response: requests.Response, header_name: str, expected_val: str) -> None:
        """Asserts that a specific HTTP response header matches the expected value (case-insensitive key)."""
        actual_val = response.headers.get(header_name)
        if not actual_val:
            error_msg = f"Response header '{header_name}' is missing!"
            logger.error(error_msg)
            assert False, error_msg
        if actual_val.lower() != expected_val.lower():
            error_msg = f"Header value mismatch for '{header_name}'! Expected: '{expected_val}', Got: '{actual_val}'"
            logger.error(error_msg)
            assert actual_val.lower() == expected_val.lower(), error_msg

    @classmethod
    def assert_content_type(cls, response: requests.Response, expected_content_type: str) -> None:
        """Asserts that the Content-Type header starts with the expected content type string."""
        cls.assert_header_value(response, "Content-Type", response.headers.get("Content-Type", ""))
        actual = response.headers.get("Content-Type", "")
        if expected_content_type not in actual:
            error_msg = f"Content-Type mismatch! Expected part of: '{expected_content_type}', Got: '{actual}'"
            logger.error(error_msg)
            assert expected_content_type in actual, error_msg
            
    @classmethod
    def assert_payload_size(cls, response: requests.Response, max_size_bytes: int) -> None:
        """Asserts that the response body payload size in bytes is under the limit."""
        size = len(response.content)
        if size > max_size_bytes:
            error_msg = f"Payload size limit exceeded! Max: {max_size_bytes} bytes, Actual: {size} bytes"
            logger.error(error_msg)
            assert size <= max_size_bytes, error_msg
        logger.info(f"Payload size check passed: {size} bytes (threshold: {max_size_bytes} bytes)")

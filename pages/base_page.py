from typing import Dict, Any, Optional
import requests
from config.settings import settings
from utils.request_helper import RequestHelper

class BasePage:
    """Foundational Page Object class representing the base API service."""

    def __init__(self, request_helper: Optional[RequestHelper] = None):
        # Allow passing an existing request_helper (sharing session context)
        self.request_helper = request_helper or RequestHelper()
        self.base_url = settings.base_url
        self.api_key = settings.api_key
        self.default_timeout = settings.timeout

    def get_common_params(self) -> Dict[str, Any]:
        """Provides parameters like appid (API Key) that are required by all endpoints."""
        return {
            "appid": self.api_key
        }

    def get_common_headers(self) -> Dict[str, Any]:
        """Returns standard headers used across API calls."""
        return {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

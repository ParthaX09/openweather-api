from typing import Dict, Any, Optional
import requests
from pages.base_page import BasePage

class PollutionPage(BasePage):
    """Page Object for Air Pollution API endpoints."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.current_endpoint = "/data/2.5/air_pollution"
        self.forecast_endpoint = "/data/2.5/air_pollution/forecast"
        self.history_endpoint = "/data/2.5/air_pollution/history"

    def get_current_pollution(
        self,
        lat: Any,
        lon: Any,
        custom_params: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """Fetches current air pollution data."""
        params = self.get_common_params()
        params["lat"] = lat
        params["lon"] = lon
        if custom_params:
            params.update(custom_params)

        url = f"{self.base_url}{self.current_endpoint}"
        return self.request_helper.send_request(
            method="GET",
            url=url,
            params=params,
            headers=self.get_common_headers(),
            timeout=self.default_timeout
        )

    def get_forecast_pollution(
        self,
        lat: Any,
        lon: Any,
        custom_params: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """Fetches air pollution forecast data."""
        params = self.get_common_params()
        params["lat"] = lat
        params["lon"] = lon
        if custom_params:
            params.update(custom_params)

        url = f"{self.base_url}{self.forecast_endpoint}"
        return self.request_helper.send_request(
            method="GET",
            url=url,
            params=params,
            headers=self.get_common_headers(),
            timeout=self.default_timeout
        )

    def get_history_pollution(
        self,
        lat: Any,
        lon: Any,
        start: Any,
        end: Any,
        custom_params: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """Fetches historical air pollution data."""
        params = self.get_common_params()
        params["lat"] = lat
        params["lon"] = lon
        params["start"] = start
        params["end"] = end
        if custom_params:
            params.update(custom_params)

        url = f"{self.base_url}{self.history_endpoint}"
        return self.request_helper.send_request(
            method="GET",
            url=url,
            params=params,
            headers=self.get_common_headers(),
            timeout=self.default_timeout
        )

from typing import Dict, Any, Optional
import requests
from pages.base_page import BasePage

class ForecastPage(BasePage):
    """Page Object for 5-Day / 3-Hour Forecast API endpoints."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.endpoint = "/data/2.5/forecast"

    def get_forecast_by_city(
        self,
        city_name: str,
        units: Optional[str] = None,
        cnt: Optional[int] = None,
        custom_params: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """Fetches 5 day / 3 hour weather forecast by city name."""
        params = self.get_common_params()
        params["q"] = city_name
        if units:
            params["units"] = units
        if cnt is not None:
            params["cnt"] = cnt
        
        if custom_params:
            params.update(custom_params)

        url = f"{self.base_url}{self.endpoint}"
        return self.request_helper.send_request(
            method="GET",
            url=url,
            params=params,
            headers=self.get_common_headers(),
            timeout=self.default_timeout
        )

    def get_forecast_by_coordinates(
        self,
        lat: Any,
        lon: Any,
        units: Optional[str] = None,
        cnt: Optional[int] = None,
        custom_params: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """Fetches 5 day / 3 hour weather forecast by latitude and longitude."""
        params = self.get_common_params()
        params["lat"] = lat
        params["lon"] = lon
        if units:
            params["units"] = units
        if cnt is not None:
            params["cnt"] = cnt
        
        if custom_params:
            params.update(custom_params)

        url = f"{self.base_url}{self.endpoint}"
        return self.request_helper.send_request(
            method="GET",
            url=url,
            params=params,
            headers=self.get_common_headers(),
            timeout=self.default_timeout
        )

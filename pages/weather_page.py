from typing import Dict, Any, Optional
import requests
from pages.base_page import BasePage

class WeatherPage(BasePage):
    """Page Object for Current Weather API endpoints."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.endpoint = "/data/2.5/weather"

    def get_weather_by_city(
        self,
        city_name: str,
        units: Optional[str] = None,
        lang: Optional[str] = None,
        custom_params: Optional[Dict[str, Any]] = None,
        custom_headers: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """Fetches current weather by city name."""
        params = self.get_common_params()
        params["q"] = city_name
        if units:
            params["units"] = units
        if lang:
            params["lang"] = lang
        
        if custom_params:
            params.update(custom_params)

        headers = self.get_common_headers()
        if custom_headers:
            headers.update(custom_headers)

        url = f"{self.base_url}{self.endpoint}"
        return self.request_helper.send_request(
            method="GET",
            url=url,
            params=params,
            headers=headers,
            timeout=self.default_timeout
        )

    def get_weather_by_coordinates(
        self,
        lat: Any,
        lon: Any,
        units: Optional[str] = None,
        custom_params: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """Fetches current weather by latitude and longitude."""
        params = self.get_common_params()
        params["lat"] = lat
        params["lon"] = lon
        if units:
            params["units"] = units
        
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

    def get_weather_by_zip(
        self,
        zip_code: str,
        custom_params: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """Fetches current weather by zip code (e.g. 94040,us)."""
        params = self.get_common_params()
        params["zip"] = zip_code
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

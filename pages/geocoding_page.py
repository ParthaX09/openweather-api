from typing import Dict, Any, Optional
import requests
from pages.base_page import BasePage

class GeocodingPage(BasePage):
    """Page Object for Geocoding API endpoints."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.direct_endpoint = "/geo/1.0/direct"
        self.reverse_endpoint = "/geo/1.0/reverse"

    def get_coordinates_by_city(
        self,
        city_name: str,
        limit: Optional[int] = None,
        custom_params: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """Fetches coordinates for a given city name (Direct Geocoding)."""
        params = self.get_common_params()
        params["q"] = city_name
        if limit is not None:
            params["limit"] = limit
            
        if custom_params:
            params.update(custom_params)

        url = f"{self.base_url}{self.direct_endpoint}"
        return self.request_helper.send_request(
            method="GET",
            url=url,
            params=params,
            headers=self.get_common_headers(),
            timeout=self.default_timeout
        )

    def get_city_by_coordinates(
        self,
        lat: Any,
        lon: Any,
        limit: Optional[int] = None,
        custom_params: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """Fetches city details for given coordinates (Reverse Geocoding)."""
        params = self.get_common_params()
        params["lat"] = lat
        params["lon"] = lon
        if limit is not None:
            params["limit"] = limit

        if custom_params:
            params.update(custom_params)

        url = f"{self.base_url}{self.reverse_endpoint}"
        return self.request_helper.send_request(
            method="GET",
            url=url,
            params=params,
            headers=self.get_common_headers(),
            timeout=self.default_timeout
        )

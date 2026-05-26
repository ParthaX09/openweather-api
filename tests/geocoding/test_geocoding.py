import pytest
from concurrent.futures import ThreadPoolExecutor
from utils.response_assertions import ResponseAssertions as Assert
from utils.schema_validator import SchemaValidator
from config.settings import settings

@pytest.mark.geocoding
class TestGeocoding:
    """Detailed test suite for the Geocoding API endpoints."""

    # 1-8. Positive Test Cases
    @pytest.mark.positive
    @pytest.mark.parametrize("city,expected_country,expected_state", [
        ("London", "GB", "England"),
        ("Tokyo", "JP", None),
        ("Sydney", "AU", "New South Wales")
    ])
    def test_direct_geocoding_positive(self, geocoding_page, city, expected_country, expected_state):
        """Validates geocoding results, matching state, country, and coordinate presence."""
        response = geocoding_page.get_coordinates_by_city(city_name=city)
        Assert.assert_status_code(response, 200)
        Assert.assert_content_type(response, "application/json")
        
        data = response.json()
        assert isinstance(data, list)
        Assert.assert_array_not_empty(data, "")
        
        # Verify first match details
        Assert.assert_field_value(data, "0.name", city)
        Assert.assert_field_value(data, "0.country", expected_country)
        if expected_state:
            Assert.assert_field_value(data, "0.state", expected_state)
        
        # Verify coordinates
        Assert.assert_field_type(data, "0.lat", float)
        Assert.assert_field_type(data, "0.lon", float)

    @pytest.mark.positive
    @pytest.mark.parametrize("lat,lon,expected_name,expected_country", [
        (51.5074, -0.1278, "London", "GB"),
        (35.6762, 139.6503, "Tokyo", "JP")
    ])
    def test_reverse_geocoding_positive(self, geocoding_page, lat, lon, expected_name, expected_country):
        """Validates reverse geocoding to resolve coordinates to readable city metadata."""
        response = geocoding_page.get_city_by_coordinates(lat=lat, lon=lon)
        Assert.assert_status_code(response, 200)
        
        data = response.json()
        assert isinstance(data, list)
        Assert.assert_array_not_empty(data, "")
        
        Assert.assert_field_value(data, "0.name", expected_name)
        Assert.assert_field_value(data, "0.country", expected_country)

    # 9-12. Schema Contract Verification
    @pytest.mark.schema
    @pytest.mark.parametrize("city", ["London", "Tokyo"])
    def test_geocoding_schema_validation(self, geocoding_page, city):
        """Checks schema integrity of geocoding responses."""
        response = geocoding_page.get_coordinates_by_city(city_name=city)
        Assert.assert_status_code(response, 200)
        SchemaValidator.validate_json(response.json(), "geocoding_schema.json")

    # 13-16. Business Logic Validation (Limits Parameter)
    @pytest.mark.positive
    @pytest.mark.parametrize("limit_val", [1, 2, 5])
    def test_direct_geocoding_limit_parameter(self, geocoding_page, limit_val):
        """Validates that the 'limit' parameter strictly caps results array length."""
        response = geocoding_page.get_coordinates_by_city(city_name="London", limit=limit_val)
        Assert.assert_status_code(response, 200)
        
        data = response.json()
        assert isinstance(data, list)
        # Length should be less than or equal to limit_val
        assert len(data) <= limit_val

    # 17-24. Negative & Edge Test Cases
    @pytest.mark.negative
    @pytest.mark.parametrize("invalid_city", ["InvalidCityXYZ123", "NonExistentPlaceNameHere", " "])
    def test_direct_geocoding_invalid_city(self, geocoding_page, invalid_city):
        """Validates that search for invalid cities returns a status 200 with an empty list."""
        response = geocoding_page.get_coordinates_by_city(city_name=invalid_city)
        Assert.assert_status_code(response, 200)
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.negative
    @pytest.mark.parametrize("lat,lon", [
        (95.0, 0.0),
        (0.0, -185.0)
    ])
    def test_reverse_geocoding_invalid_coordinates(self, geocoding_page, lat, lon):
        """Validates reverse geocoding with out-of-bounds coordinates yields bad request error."""
        response = geocoding_page.get_city_by_coordinates(lat=lat, lon=lon)
        # Note: OpenWeather returns 400 Bad Request or empty list. The mock returns 400.
        assert response.status_code in [400, 404]

    @pytest.mark.security
    def test_geocoding_unauthorized_key(self, geocoding_page):
        """Validates authorization check on direct geocoding."""
        response = geocoding_page.get_coordinates_by_city(
            city_name="London",
            custom_params={"appid": ""}
        )
        Assert.assert_status_code(response, 401)

    # 25-30. Performance & Size Validation
    @pytest.mark.performance
    def test_geocoding_response_time_performance(self, geocoding_page):
        """Validates geocoding latency constraints."""
        response = geocoding_page.get_coordinates_by_city(city_name="London")
        Assert.assert_status_code(response, 200)
        Assert.assert_response_time(response, settings.max_response_time_ms)

    @pytest.mark.performance
    def test_geocoding_payload_size_performance(self, geocoding_page):
        """Validates size limits of geocoding payloads."""
        response = geocoding_page.get_coordinates_by_city(city_name="London")
        Assert.assert_status_code(response, 200)
        Assert.assert_payload_size(response, settings.max_payload_size_bytes)

    @pytest.mark.performance
    def test_geocoding_concurrency(self, geocoding_page):
        """Checks concurrency limits and thread safety."""
        cities = ["London", "Tokyo", "Sydney", "Cairo"]
        
        def call_api(city_name):
            return geocoding_page.get_coordinates_by_city(city_name=city_name)
            
        with ThreadPoolExecutor(max_workers=4) as executor:
            responses = list(executor.map(call_api, cities))
            
        for response in responses:
            Assert.assert_status_code(response, 200)
            assert isinstance(response.json(), list)

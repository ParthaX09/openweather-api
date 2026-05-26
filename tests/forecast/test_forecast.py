import pytest
from concurrent.futures import ThreadPoolExecutor
from utils.response_assertions import ResponseAssertions as Assert
from utils.schema_validator import SchemaValidator
from config.settings import settings

@pytest.mark.forecast
class TestForecast:
    """Detailed test suite for the 5-Day / 3-Hour Forecast API endpoints."""

    # 1-8. Positive Test Cases
    @pytest.mark.positive
    @pytest.mark.parametrize("city", ["London", "Tokyo", "Cairo", "Sydney"])
    def test_forecast_by_city_positive(self, forecast_page, city):
        """Validates forecast object structures, lists, and headers for valid city inputs."""
        response = forecast_page.get_forecast_by_city(city_name=city)
        Assert.assert_status_code(response, 200)
        Assert.assert_content_type(response, "application/json")
        
        data = response.json()
        Assert.assert_field_value(data, "city.name", city)
        Assert.assert_field_type(data, "list", list)
        Assert.assert_array_not_empty(data, "list")
        
        # Check coordinates and standard details of forecast city nested block
        Assert.assert_field_type(data, "city.coord.lat", float)
        Assert.assert_field_type(data, "city.coord.lon", float)

    @pytest.mark.positive
    @pytest.mark.parametrize("lat,lon,expected_name", [
        (51.5074, -0.1278, "London"),
        (35.6762, 139.6503, "Tokyo")
    ])
    def test_forecast_by_coordinates_positive(self, forecast_page, lat, lon, expected_name):
        """Validates forecast retrieval using latitude and longitude coordinates."""
        response = forecast_page.get_forecast_by_coordinates(lat=lat, lon=lon)
        Assert.assert_status_code(response, 200)
        
        data = response.json()
        Assert.assert_field_value(data, "city.name", expected_name)
        # Check first item structure
        Assert.assert_field_exists(data, "list.0.main.temp")
        Assert.assert_field_exists(data, "list.0.weather.0.description")

    # 9-12. Schema Validation
    @pytest.mark.schema
    @pytest.mark.parametrize("city", ["London", "Tokyo"])
    def test_forecast_schema_validation(self, forecast_page, city):
        """Validates forecast response schema integrity."""
        response = forecast_page.get_forecast_by_city(city_name=city)
        Assert.assert_status_code(response, 200)
        SchemaValidator.validate_json(response.json(), "forecast_schema.json")

    # 13-16. Business Logic Validation
    @pytest.mark.positive
    @pytest.mark.parametrize("cnt_val", [1, 3, 5])
    def test_forecast_cnt_limit_parameter(self, forecast_page, cnt_val):
        """Validates the business requirement that the 'cnt' parameter limits returned timestamps."""
        response = forecast_page.get_forecast_by_city(city_name="London", cnt=cnt_val)
        Assert.assert_status_code(response, 200)
        
        data = response.json()
        # Assert returned list count matches cnt parameter
        # Note: the mock server handles cnt correctly, live API also handles it
        Assert.assert_array_length(data, "list", cnt_val)
        Assert.assert_field_value(data, "cnt", cnt_val)

    # 17-24. Negative Test Cases
    @pytest.mark.negative
    @pytest.mark.parametrize("invalid_city", ["InvalidCityXYZ123", "NonExistentPlaceNameHere"])
    def test_forecast_error_invalid_city(self, forecast_page, invalid_city):
        """Validates error response structure for invalid city query in forecast."""
        response = forecast_page.get_forecast_by_city(city_name=invalid_city)
        Assert.assert_status_code(response, 404)
        
        data = response.json()
        SchemaValidator.validate_json(data, "error_schema.json")
        Assert.assert_field_value(data, "message", "city not found")

    @pytest.mark.negative
    @pytest.mark.parametrize("lat,lon", [
        (92.0, 0.0),
        (0.0, -182.0)
    ])
    def test_forecast_invalid_coordinates(self, forecast_page, lat, lon):
        """Validates forecast error response for out-of-range coordinates."""
        response = forecast_page.get_forecast_by_coordinates(lat=lat, lon=lon)
        Assert.assert_status_code(response, 400)
        
        data = response.json()
        SchemaValidator.validate_json(data, "error_schema.json")

    @pytest.mark.security
    def test_forecast_unauthorized_key(self, forecast_page):
        """Validates forecast security authentication checks."""
        response = forecast_page.get_forecast_by_city(
            city_name="London",
            custom_params={"appid": ""}
        )
        Assert.assert_status_code(response, 401)
        SchemaValidator.validate_json(response.json(), "error_schema.json")

    # 25-28. Edge Cases
    @pytest.mark.edge
    @pytest.mark.parametrize("city", ["Reykjavík", "Frankfurt/Oder"])
    def test_forecast_city_names_edge(self, forecast_page, city):
        """Validates forecast responses when querying with special characters or accents."""
        response = forecast_page.get_forecast_by_city(city_name=city)
        Assert.assert_status_code(response, 200)
        Assert.assert_field_exists(response.json(), "list")

    # 29-33. Performance & Size Validation
    @pytest.mark.performance
    def test_forecast_response_time_performance(self, forecast_page):
        """Validates forecast response latency."""
        response = forecast_page.get_forecast_by_city(city_name="London")
        Assert.assert_status_code(response, 200)
        Assert.assert_response_time(response, settings.max_response_time_ms)

    @pytest.mark.performance
    def test_forecast_payload_size_performance(self, forecast_page):
        """Validates payload size constraints (forecast payloads can be larger)."""
        response = forecast_page.get_forecast_by_city(city_name="London")
        Assert.assert_status_code(response, 200)
        # Check forecast payload is within limits
        Assert.assert_payload_size(response, settings.max_payload_size_bytes)

    @pytest.mark.performance
    def test_forecast_concurrency(self, forecast_page):
        """Validates system behavior under rapid, concurrent requests."""
        cities = ["London", "Tokyo", "Cairo", "Sydney"]
        
        def call_api(city_name):
            return forecast_page.get_forecast_by_city(city_name=city_name)
            
        with ThreadPoolExecutor(max_workers=4) as executor:
            responses = list(executor.map(call_api, cities))
            
        for response in responses:
            Assert.assert_status_code(response, 200)
            Assert.assert_field_exists(response.json(), "list")

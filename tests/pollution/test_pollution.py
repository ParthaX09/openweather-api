import pytest
import time
from concurrent.futures import ThreadPoolExecutor
from utils.response_assertions import ResponseAssertions as Assert
from utils.schema_validator import SchemaValidator
from utils.data_generator import DataGenerator
from config.settings import settings

@pytest.mark.pollution
class TestPollution:
    """Detailed test suite for the Air Pollution API endpoints (current, forecast, history)."""

    # 1-8. Positive Test Cases
    @pytest.mark.positive
    @pytest.mark.parametrize("lat,lon", [
        (51.5074, -0.1278), # London
        (35.6762, 139.6503), # Tokyo
        (-33.8688, 151.2093) # Sydney
    ])
    def test_current_pollution_positive(self, pollution_page, lat, lon):
        """Validates current air pollution components exist and values are within valid thresholds."""
        response = pollution_page.get_current_pollution(lat=lat, lon=lon)
        Assert.assert_status_code(response, 200)
        Assert.assert_content_type(response, "application/json")
        
        data = response.json()
        Assert.assert_field_range(data, "coord.lat", lat - 0.1, lat + 0.1)
        Assert.assert_field_range(data, "coord.lon", lon - 0.1, lon + 0.1)
        
        # Validate AQI (Air Quality Index) falls in range 1-5
        Assert.assert_field_type(data, "list.0.main.aqi", int)
        Assert.assert_field_range(data, "list.0.main.aqi", 1, 5)

        # Validate existence and non-negativity of pollution components
        for comp in ["co", "no", "no2", "o3", "so2", "pm2_5", "pm10", "nh3"]:
            path = f"list.0.components.{comp}"
            Assert.assert_field_type(data, path, (int, float))
            Assert.assert_field_range(data, path, 0.0, 10000.0)

    @pytest.mark.positive
    @pytest.mark.parametrize("lat,lon", [
        (51.5074, -0.1278),
        (35.6762, 139.6503)
    ])
    def test_forecast_pollution_positive(self, pollution_page, lat, lon):
        """Validates forecasted air pollution contains a valid array of pollution points."""
        response = pollution_page.get_forecast_pollution(lat=lat, lon=lon)
        Assert.assert_status_code(response, 200)
        
        data = response.json()
        Assert.assert_field_type(data, "list", list)
        Assert.assert_array_not_empty(data, "list")
        
        # Verify first entry has correct structured keys
        Assert.assert_field_exists(data, "list.0.main.aqi")
        Assert.assert_field_exists(data, "list.0.components.co")

    @pytest.mark.positive
    def test_historical_pollution_positive(self, pollution_page):
        """Validates retrieval of historical air pollution values using Unix timestamps."""
        start_time, end_time = DataGenerator.generate_pollution_time_range(days_back=3)
        
        response = pollution_page.get_history_pollution(
            lat=51.5074,
            lon=-0.1278,
            start=start_time,
            end=end_time
        )
        Assert.assert_status_code(response, 200)
        
        data = response.json()
        Assert.assert_field_type(data, "list", list)
        # Verify historical response is within coordinates
        Assert.assert_field_exists(data, "list.0.dt")

    # 9-12. Schema Verification
    @pytest.mark.schema
    @pytest.mark.parametrize("lat,lon", [
        (51.5074, -0.1278),
        (35.6762, 139.6503)
    ])
    def test_pollution_schema_validation(self, pollution_page, lat, lon):
        """Checks schema validation of the air pollution response payload."""
        response = pollution_page.get_current_pollution(lat=lat, lon=lon)
        Assert.assert_status_code(response, 200)
        SchemaValidator.validate_json(response.json(), "pollution_schema.json")

    # 13-20. Negative & Edge Test Cases
    @pytest.mark.negative
    @pytest.mark.parametrize("lat,lon", [
        (95.0, 0.0),
        (-95.0, 0.0),
        (0.0, 185.0),
        (0.0, -185.0)
    ])
    def test_pollution_error_invalid_coords(self, pollution_page, lat, lon):
        """Validates that out-of-range coords for pollution query returns a schema-compliant error response."""
        response = pollution_page.get_current_pollution(lat=lat, lon=lon)
        Assert.assert_status_code(response, 400)
        
        data = response.json()
        SchemaValidator.validate_json(data, "error_schema.json")
        Assert.assert_field_exists(data, "message")

    @pytest.mark.negative
    @pytest.mark.parametrize("param_override", [
        {"lat": None},
        {"lon": None}
    ])
    def test_pollution_missing_params(self, pollution_page, param_override):
        """Validates pollution API error response for missing location parameters."""
        response = pollution_page.get_current_pollution(
            lat=param_override.get("lat"),
            lon=param_override.get("lon")
        )
        assert response.status_code in [400, 404]

    @pytest.mark.security
    def test_pollution_unauthorized_key(self, pollution_page):
        """Validates that unauthorized calls to Air Pollution API return a 401 response."""
        response = pollution_page.get_current_pollution(
            lat=51.5074,
            lon=-0.1278,
            custom_params={"appid": ""}
        )
        Assert.assert_status_code(response, 401)
        SchemaValidator.validate_json(response.json(), "error_schema.json")

    # 21-25. Performance Validation
    @pytest.mark.performance
    def test_pollution_response_time_performance(self, pollution_page):
        """Validates pollution response latency limits."""
        response = pollution_page.get_current_pollution(lat=51.5074, lon=-0.1278)
        Assert.assert_status_code(response, 200)
        Assert.assert_response_time(response, settings.max_response_time_ms)

    @pytest.mark.performance
    def test_pollution_payload_size_performance(self, pollution_page):
        """Validates pollution payload size constraints."""
        response = pollution_page.get_current_pollution(lat=51.5074, lon=-0.1278)
        Assert.assert_status_code(response, 200)
        Assert.assert_payload_size(response, settings.max_payload_size_bytes)

    @pytest.mark.performance
    def test_pollution_concurrency(self, pollution_page):
        """Validates pollution API safety under concurrent load."""
        coords = [(51.5074, -0.1278), (35.6762, 139.6503), (-33.8688, 151.2093)] * 3
        
        def call_api(lat_lon):
            return pollution_page.get_current_pollution(lat=lat_lon[0], lon=lat_lon[1])
            
        with ThreadPoolExecutor(max_workers=3) as executor:
            responses = list(executor.map(call_api, coords))
            
        for response in responses:
            Assert.assert_status_code(response, 200)
            Assert.assert_field_exists(response.json(), "list")

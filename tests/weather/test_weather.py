import pytest
import time
from concurrent.futures import ThreadPoolExecutor
from utils.response_assertions import ResponseAssertions as Assert
from utils.schema_validator import SchemaValidator
from config.settings import settings

@pytest.mark.weather
class TestCurrentWeather:
    """Detailed test suite for the Current Weather API endpoints."""

    # 1-10. Positive Test Cases
    @pytest.mark.positive
    @pytest.mark.parametrize("city", ["London", "Tokyo", "Cairo", "Sydney", "Rio de Janeiro"])
    def test_weather_by_city_positive(self, weather_page, city):
        """Validates weather object structure, fields, and headers for valid city inputs."""
        response = weather_page.get_weather_by_city(city_name=city)
        
        # 1. Assert status code is 200
        Assert.assert_status_code(response, 200)
        
        # 2. Validate Response Content Type and headers
        Assert.assert_content_type(response, "application/json")
        Assert.assert_header_value(response, "Server", "openresty")
        
        # 3. Parse JSON and validate basic business values
        data = response.json()
        Assert.assert_field_value(data, "name", city)
        Assert.assert_field_type(data, "name", str)
        Assert.assert_field_type(data, "id", int)
        
        # 4. Deep coordinate checks
        Assert.assert_field_type(data, "coord.lon", float)
        Assert.assert_field_type(data, "coord.lat", float)
        Assert.assert_field_range(data, "coord.lon", -180.0, 180.0)
        Assert.assert_field_range(data, "coord.lat", -90.0, 90.0)

        # 5. Temperature and Humidity field and range validations
        # Temperatures are in Kelvin by default (typically 0K to ~330K on Earth)
        Assert.assert_field_type(data, "main.temp", (int, float))
        Assert.assert_field_range(data, "main.temp", 0.0, 350.0)
        Assert.assert_field_type(data, "main.feels_like", (int, float))
        Assert.assert_field_range(data, "main.humidity", 0, 100)
        
        # 6. Nested object structures (weather description)
        Assert.assert_array_not_empty(data, "weather")
        Assert.assert_field_type(data, "weather.0.id", int)
        Assert.assert_field_type(data, "weather.0.main", str)
        Assert.assert_field_type(data, "weather.0.description", str)

    @pytest.mark.positive
    @pytest.mark.parametrize("lat,lon,expected_name", [
        (51.5074, -0.1278, "London"),
        (35.6762, 139.6503, "Tokyo"),
        (-33.8688, 151.2093, "Sydney")
    ])
    def test_weather_by_coordinates_positive(self, weather_page, lat, lon, expected_name):
        """Validates retrieval of weather by valid latitude/longitude coordinates."""
        response = weather_page.get_weather_by_coordinates(lat=lat, lon=lon)
        Assert.assert_status_code(response, 200)
        
        data = response.json()
        Assert.assert_field_value(data, "name", expected_name)
        # Lat/Lon tolerance of 0.1 degree due to possible server rounding
        Assert.assert_field_range(data, "coord.lat", lat - 0.1, lat + 0.1)
        Assert.assert_field_range(data, "coord.lon", lon - 0.1, lon + 0.1)

    @pytest.mark.positive
    @pytest.mark.parametrize("zip_code", ["94040,us", "SW1A,gb"])
    def test_weather_by_zip_code_positive(self, weather_page, zip_code):
        """Validates weather retrieval using ZIP codes."""
        response = weather_page.get_weather_by_zip(zip_code=zip_code)
        Assert.assert_status_code(response, 200)
        
        data = response.json()
        Assert.assert_field_exists(data, "sys.country")
        Assert.assert_field_exists(data, "name")

    # 11-14. Schema Contract Validation
    @pytest.mark.schema
    @pytest.mark.parametrize("city", ["London", "Tokyo", "Cairo"])
    def test_weather_schema_validation(self, weather_page, city):
        """Performs strict JSON schema contract validation against the weather schema."""
        response = weather_page.get_weather_by_city(city_name=city)
        Assert.assert_status_code(response, 200)
        SchemaValidator.validate_json(response.json(), "weather_schema.json")

    # 15-22. Negative Test Cases
    @pytest.mark.negative
    @pytest.mark.parametrize("invalid_city", ["InvalidCityXYZ123", "NonExistentPlaceNameHere", " "])
    def test_weather_error_invalid_city(self, weather_page, invalid_city):
        """Validates that query for a non-existent or empty city results in a schema-compliant error response."""
        response = weather_page.get_weather_by_city(city_name=invalid_city)
        Assert.assert_status_code(response, 404)
        
        # Verify schema of error payload
        data = response.json()
        SchemaValidator.validate_json(data, "error_schema.json")
        Assert.assert_field_value(data, "cod", "404" if isinstance(data.get("cod"), str) else 404)
        Assert.assert_field_value(data, "message", "city not found")

    @pytest.mark.negative
    @pytest.mark.parametrize("param_override", [
        {"lat": ""},
        {"lon": ""},
        {"lat": None, "lon": 12.3}
    ])
    def test_weather_missing_parameters(self, weather_page, param_override):
        """Validates error response structure when coordinates are incomplete or missing."""
        response = weather_page.get_weather_by_coordinates(
            lat=param_override.get("lat"),
            lon=param_override.get("lon")
        )
        # Missing critical parameters should result in error codes (400 or 404 depending on parsing)
        assert response.status_code in [400, 404]
        SchemaValidator.validate_json(response.json(), "error_schema.json")

    @pytest.mark.negative
    @pytest.mark.parametrize("lat,lon", [
        (91.0, 0.0),
        (-91.0, 0.0),
        (0.0, 181.0),
        (0.0, -181.0)
    ])
    def test_weather_invalid_coordinates(self, weather_page, lat, lon):
        """Validates that coordinate boundaries are strictly enforced."""
        response = weather_page.get_weather_by_coordinates(lat=lat, lon=lon)
        Assert.assert_status_code(response, 400)
        
        data = response.json()
        SchemaValidator.validate_json(data, "error_schema.json")
        Assert.assert_field_exists(data, "message")

    @pytest.mark.security
    def test_weather_unauthorized_key(self, weather_page):
        """Validates security behavior when requesting with an empty/invalid appid."""
        response = weather_page.get_weather_by_city(
            city_name="London",
            custom_params={"appid": ""}
        )
        Assert.assert_status_code(response, 401)
        
        data = response.json()
        SchemaValidator.validate_json(data, "error_schema.json")
        Assert.assert_field_value(data, "cod", 401)
        assert "Invalid API key" in data.get("message", "")

    # 23-28. Edge Cases
    @pytest.mark.edge
    @pytest.mark.parametrize("city", [
        "Athens (Αθήνα)",   # Unicode with brackets
        "Reykjavík",        # Accent characters
        "Al-Quds (القدس)"  # Arabic script
    ])
    def test_weather_city_names_unicode(self, weather_page, city):
        """Validates that Unicode city names are processed correctly."""
        response = weather_page.get_weather_by_city(city_name=city)
        Assert.assert_status_code(response, 200)
        
        data = response.json()
        Assert.assert_field_exists(data, "main.temp")
        # Unicode inputs may map to ASCII or localized city names in OpenWeather API
        Assert.assert_field_type(data, "name", str)

    @pytest.mark.edge
    @pytest.mark.parametrize("city", [
        "New-York",
        "St. John's",
        "Frankfurt/Oder"
    ])
    def test_weather_city_names_special_chars(self, weather_page, city):
        """Validates processing of special characters in city names."""
        response = weather_page.get_weather_by_city(city_name=city)
        Assert.assert_status_code(response, 200)
        
        data = response.json()
        Assert.assert_field_exists(data, "coord.lat")

    @pytest.mark.edge
    @pytest.mark.parametrize("long_city", [
        "Llanfairpwllgwyngyllgogerychwyrndrobwllllantysiliogogogoch",
        "Taumatawhakatangihangakoauauotamateaturipukakapikimaungahoronukupokaiwhenuakitanatahu"
    ])
    def test_weather_city_names_very_long(self, weather_page, long_city):
        """Validates behavior with extremely long location names (boundary strings)."""
        response = weather_page.get_weather_by_city(city_name=long_city)
        # Long city might return 200 if supported in DB, or 404. It should not result in 500 crash.
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            Assert.assert_field_exists(response.json(), "main")
        else:
            SchemaValidator.validate_json(response.json(), "error_schema.json")

    # 29-34. Business Logic Validation
    @pytest.mark.positive
    @pytest.mark.parametrize("units,min_temp,max_temp", [
        ("metric", -50.0, 60.0),       # Celsius typical range
        ("imperial", -58.0, 140.0),    # Fahrenheit typical range
        ("standard", 220.0, 330.0)      # Kelvin typical range
    ])
    def test_weather_units_parameter(self, weather_page, units, min_temp, max_temp):
        """Verifies units translation logic: metric (C), imperial (F), standard (K)."""
        response = weather_page.get_weather_by_city(city_name="London", units=units)
        Assert.assert_status_code(response, 200)
        
        temp = response.json()["main"]["temp"]
        Assert.assert_field_range(response.json(), "main.temp", min_temp, max_temp)

    # 35-40. Performance Validation
    @pytest.mark.performance
    @pytest.mark.parametrize("city", ["London", "Tokyo", "Cairo"])
    def test_weather_response_time_performance(self, weather_page, city):
        """Validates that API latency does not exceed threshold."""
        response = weather_page.get_weather_by_city(city_name=city)
        Assert.assert_status_code(response, 200)
        Assert.assert_response_time(response, settings.max_response_time_ms)

    @pytest.mark.performance
    @pytest.mark.parametrize("city", ["London", "Tokyo", "Cairo"])
    def test_weather_payload_size_performance(self, weather_page, city):
        """Validates that payload data size is within acceptable threshold."""
        response = weather_page.get_weather_by_city(city_name=city)
        Assert.assert_status_code(response, 200)
        Assert.assert_payload_size(response, settings.max_payload_size_bytes)

    @pytest.mark.performance
    def test_weather_concurrency(self, weather_page):
        """Validates system behavior under rapid, concurrent requests (10 threads)."""
        cities = ["London", "Tokyo", "Cairo", "Sydney", "New York"] * 2
        
        def call_api(city_name):
            return weather_page.get_weather_by_city(city_name=city_name)
            
        with ThreadPoolExecutor(max_workers=5) as executor:
            responses = list(executor.map(call_api, cities))
            
        for response in responses:
            # Under concurrent loads, status code must still be correct
            Assert.assert_status_code(response, 200)
            Assert.assert_field_exists(response.json(), "main.temp")
            Assert.assert_response_time(response, settings.max_response_time_ms)

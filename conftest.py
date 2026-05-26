import pytest
import requests
import json
from pathlib import Path
from unittest.mock import MagicMock
from config.settings import settings
from utils.request_helper import RequestHelper
from utils.mock_server import MockServer
from pages.weather_page import WeatherPage
from pages.forecast_page import ForecastPage
from pages.geocoding_page import GeocodingPage
from pages.pollution_page import PollutionPage

def pytest_addoption(parser):
    """Adds command line options to pytest."""
    parser.addoption(
        "--live", 
        action="store_true", 
        default=False, 
        help="Run tests against the live OpenWeatherMap API instead of mock server"
    )

# Ensure settings are validated at start of test run
@pytest.fixture(scope="session", autouse=True)
def validate_settings():
    settings.validate()

# ----------------- Request Interception / Mocking -----------------

@pytest.fixture(scope="session", autouse=True)
def mock_api_interceptor(request):
    """
    Conditionally mocks all HTTP requests to OpenWeatherMap API.
    If the --live flag is NOT passed, or if the API key is 'api_key' (default placeholder),
    it wraps RequestHelper.send_request to return mock responses offline.
    """
    is_live = request.config.getoption("--live")
    # If the user is using the placeholder api_key, force mock mode to prevent 401 errors
    if settings.api_key == "api_key" or not is_live:
        
        # Intercept send_request on RequestHelper
        original_send = RequestHelper.send_request
        
        def mocked_send(self, method, url, params=None, headers=None, json_data=None, timeout=None, **kwargs):
            params = params or {}
            appid = params.get("appid", "")
            
            # Create a mock response object
            mock_res = requests.Response()
            mock_res.url = url
            mock_res.status_code = 200
            
            # Map request to mocked endpoint
            if "/data/2.5/weather" in url:
                status, data = MockServer.get_weather_mock(
                    q=params.get("q"),
                    lat=params.get("lat"),
                    lon=params.get("lon"),
                    zip_code=params.get("zip"),
                    units=params.get("units"),
                    appid=appid
                )
            elif "/data/2.5/forecast" in url:
                status, data = MockServer.get_forecast_mock(
                    q=params.get("q"),
                    lat=params.get("lat"),
                    lon=params.get("lon"),
                    cnt=params.get("cnt"),
                    units=params.get("units"),
                    appid=appid
                )
            elif "/geo/1.0/direct" in url:
                status, data = MockServer.get_geocoding_direct_mock(
                    q=params.get("q"),
                    appid=appid
                )
            elif "/geo/1.0/reverse" in url:
                status, data = MockServer.get_geocoding_reverse_mock(
                    lat=params.get("lat"),
                    lon=params.get("lon"),
                    appid=appid
                )
            elif "/data/2.5/air_pollution" in url: # matches air_pollution, /forecast, /history
                status, data = MockServer.get_pollution_mock(
                    lat=params.get("lat"),
                    lon=params.get("lon"),
                    appid=appid
                )
            else:
                # 404 for invalid endpoints
                status = 404
                data = {"cod": "404", "message": "Internal error: endpoint not mocked"}
            
            mock_res.status_code = status
            mock_res._content = json.dumps(data).encode("utf-8")
            
            # Mock headers
            mock_res.headers = {
                "Content-Type": "application/json; charset=utf-8",
                "Server": "openresty",
                "Connection": "keep-alive"
            }
            
            # Add request time metric
            mock_res.elapsed_ms = 45.2 # Simulate quick local execution
            return mock_res

        # Patch RequestHelper.send_request
        RequestHelper.send_request = mocked_send
        yield
        # Restore original
        RequestHelper.send_request = original_send
    else:
        yield

# ----------------- Shared HTTP Session and Page Objects -----------------

@pytest.fixture(scope="session")
def api_session():
    """Provides a single shared HTTP session for all test requests."""
    session = requests.Session()
    yield session
    session.close()

@pytest.fixture(scope="session")
def request_helper(api_session):
    """Provides RequestHelper instance wrapper."""
    return RequestHelper(session=api_session)

@pytest.fixture(scope="session")
def weather_page(request_helper):
    """Provides WeatherPage Page Object."""
    return WeatherPage(request_helper=request_helper)

@pytest.fixture(scope="session")
def forecast_page(request_helper):
    """Provides ForecastPage Page Object."""
    return ForecastPage(request_helper=request_helper)

@pytest.fixture(scope="session")
def geocoding_page(request_helper):
    """Provides GeocodingPage Page Object."""
    return GeocodingPage(request_helper=request_helper)

@pytest.fixture(scope="session")
def pollution_page(request_helper):
    """Provides PollutionPage Page Object."""
    return PollutionPage(request_helper=request_helper)

# ----------------- Static Test Data Loading -----------------

@pytest.fixture(scope="session")
def static_data():
    """Loads all static data JSON files into a unified dictionary."""
    data_dir = Path(__file__).resolve().parent / "data"
    loaded_data = {}
    
    for json_file in data_dir.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            loaded_data[json_file.stem] = json.load(f)
            
    return loaded_data

# ----------------- HTML Report Enhancements -----------------

def pytest_html_report_title(report):
    report.title = "OpenWeatherMap API Automation Report"

def pytest_configure(config):
    """Adds system configuration metadata to the HTML report."""
    if hasattr(config, "_metadata"):
        config._metadata["Environment"] = settings.env
        config._metadata["Base URL"] = settings.base_url
        config._metadata["Timeout Config"] = f"{settings.timeout}s"
        config._metadata["Max Retries"] = str(settings.max_retries)
        
        # Remove potentially sensitive keys from metadata display
        config._metadata.pop("JAVA_HOME", None)
        config._metadata.pop("Plugins", None)
        config._metadata.pop("Packages", None)
        config._metadata.pop("Platform", None)

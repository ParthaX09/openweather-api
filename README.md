# OpenWeatherMap API Automation Framework
An enterprise-grade, highly scalable API test automation suite built with Python, Pytest, Requests, and JSON Schema validation following the Page Object Model (POM) architectural design pattern.

---

## 🌟 Mentoring Guide: Designing Enterprise-Grade API Automation

Welcome to the OpenWeatherMap API automation project. As a Senior QA Automation Architect, my goal is to guide you through the architectural decisions behind this framework. Testing APIs at an enterprise scale requires more than sending HTTP requests and checking `assert response.status_code == 200`. It demands modularity, resilience, deep assertions, contract safety, performance tracking, and dry-run capability.

Here is a breakdown of our architecture:

### 1. Page Object Model (POM) for API Testing
In web testing, POM separates UI elements and actions from test logic. In API testing, **POM separates HTTP endpoints and request logic from test verification.**
* **Pages (`pages/`)**: Contain endpoint paths, parameters, and wrappers for sending HTTP verbs. They *do not* assert outcomes. They return `requests.Response` objects.
* **Tests (`tests/`)**: Contain test scenarios, execution flow, parameters, and assertions. They *never* define raw URLs or build HTTP request queries directly.

### 2. Deep Assertions vs. Brittle Assertions
A common rookie mistake is asserting only status codes. This framework focuses on:
* **Contract/Schema Validation**: Verifies JSON structures, required fields, and primitive data types using JSON Schema.
* **Business Boundary Validation**: Verifies that temperature scales fall within physical ranges (e.g., metric vs. imperial), coordinates correspond to geographic limits (-90 to +90 lat), and air quality indices are strictly between 1 and 5.
* **Latency Validation**: Ensures API response times fall under an acceptable threshold (e.g., 1.5 seconds) to catch performance regressions.
* **Payload Size Validation**: Prevents memory exhaustion by checking response sizes.

### 3. Resilient Request Helper and Retries
Flaky networks kill test builds. The `RequestHelper` intercepts every request, logs its detailed inputs (with sensitive keys like `appid` redacted), and wraps execution with a custom **Exponential Backoff Retry** mechanism (`retry_on_failure`) to retry requests upon transient server errors (5xx) or rate limits (429).

### 4. Interactive Mock/Offline Capability
To prevent rate-limit blocks and allow CI pipelines to run instantly and reliably without external internet connections or payment tokens, we built an automatic **Mock Interceptor** (`mock_api_interceptor` in `conftest.py`). If the `--live` flag is not specified, or if the configuration uses the default placeholder `api_key`, all requests are redirected to a local `MockServer` that returns valid schema-compliant mock objects.

---

## 📁 Directory Structure

```text
openweather/
│
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI/CD Pipeline
│
├── config/
│   ├── config.json              # Static/default settings & thresholds
│   └── settings.py              # Environment variable parsing and config management
│
├── data/
│   ├── cities.json              # Parametrization list for cities
│   ├── coordinates.json         # Parametrization coordinates (lat/lon)
│   └── edge_cases.json          # Specialized edge cases (very long, Unicode)
│
├── pages/
│   ├── base_page.py             # Base API Client wrapping session & auth
│   ├── weather_page.py          # Current Weather API page object
│   ├── forecast_page.py         # 5-Day Forecast API page object
│   ├── geocoding_page.py        # Geocoding API page object
│   └── pollution_page.py        # Air Pollution API page object
│
├── schemas/
│   ├── weather_schema.json      # Current Weather response contract
│   ├── forecast_schema.json     # Forecast response contract
│   ├── geocoding_schema.json    # Geocoding response contract
│   ├── pollution_schema.json    # Air Pollution response contract
│   └── error_schema.json        # Standard API Error response contract
│
├── tests/
│   ├── weather/
│   │   └── test_weather.py      # Current Weather test suite (41 test cases)
│   ├── forecast/
│   │   └── test_forecast.py     # Weather Forecast test suite (33 test cases)
│   ├── geocoding/
│   │   └── test_geocoding.py    # Geocoding test suite (30 test cases)
│   └── pollution/
│       └── test_pollution.py    # Air Pollution test suite (25 test cases)
│
├── utils/
│   ├── logger.py                # Logging system config (console & log file rotation)
│   ├── retry.py                 # Custom exponential backoff decorator
│   ├── request_helper.py        # HTTP wrapper logging request/response & timings
│   ├── schema_validator.py      # JSON Schema validation handler
│   ├── response_assertions.py   # Specialized assert class for deep API testing
│   └── data_generator.py        # Dynamic test data generator
│
├── logs/                        # Running log output files (.gitignored except folder)
├── reports/                     # Output Pytest HTML reports
├── .env                         # Custom environment variables
├── .env.example                 # Environment variables blueprint
├── conftest.py                  # Pytest fixtures and mock interception hook
├── pytest.ini                   # Pytest configurations and custom markers
├── requirements.txt             # Python packages listing
└── README.md                    # Mentoring & project documentation
```

---

## 🛠️ CLI Setup Commands

To recreate or build upon this folder structure from scratch, you can use these shell commands:

```bash
# Create directory structure
mkdir -p .github/workflows config data pages schemas tests/weather tests/forecast tests/geocoding tests/pollution utils logs reports

# Initialize requirements, config and setup files
touch requirements.txt pytest.ini conftest.py .env .env.example README.md
touch config/config.json config/settings.py
touch data/cities.json data/coordinates.json data/edge_cases.json
touch pages/base_page.py pages/weather_page.py pages/forecast_page.py pages/geocoding_page.py pages/pollution_page.py
touch schemas/weather_schema.json schemas/forecast_schema.json schemas/geocoding_schema.json schemas/pollution_schema.json schemas/error_schema.json
touch utils/logger.py utils/retry.py utils/request_helper.py utils/schema_validator.py utils/response_assertions.py utils/data_generator.py
```

---

## 🚀 Getting Started

### 1. Prerequisites
Ensure you have **Python 3.8+** installed. (Python 3.11 is recommended).

### 2. Installation
Install the required dependencies inside a virtual environment:
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Credentials
Copy `.env.example` to `.env` and fill in your OpenWeatherMap API Key if running in live mode:
```bash
cp .env.example .env
```
Inside `.env`:
```ini
OPENWEATHER_API_KEY=your_actual_api_key_here
OPENWEATHER_BASE_URL=https://api.openweathermap.org
ENV=staging
```

---

## 🖥️ Running Tests

The test runner handles the mocking layer dynamically. If you run without `--live` or if your `.env` contains the default `api_key` placeholder, it runs tests **offline** using the mock interceptor.

### Run all tests offline (Fast, mock data, no API key required)
```bash
pytest
```

### Run all tests against the live API (Requires valid key in `.env`)
```bash
pytest --live
```

### Run tests matching a specific API area
```bash
# Run only Weather tests
pytest -m weather

# Run only Forecast tests
pytest -m forecast
```

### Run tests matching custom execution markers
```bash
# Run only positive scenarios
pytest -m positive

# Run only schema contract verification
pytest -m schema

# Run only negative and security tests
pytest -m "negative or security"

# Run only performance constraints validation
pytest -m performance
```

---

## 📊 Viewing HTML Reports & Execution Logs

### Pytest HTML Report
Pytest generates a detailed, styled, self-contained HTML report at:
`reports/report.html`

Open this in any browser to review pass rates, assertions, metadata, and execution durations.

### Logging Framework
All execution steps, request specs, response body previews, and warnings are logged under:
`logs/framework.log`

Example log output:
```text
2026-05-26 12:05:00 [    INFO] API Request: GET https://api.openweathermap.org/data/2.5/weather | Params: {'appid': '********', 'q': 'London'} | JSON: None (request_helper.py:31)
2026-05-26 12:05:00 [    INFO] API Response: 200 | Time: 45.20ms | Size: 456 bytes (request_helper.py:53)
2026-05-26 12:05:00 [    INFO] Schema validation passed successfully for weather_schema.json. (schema_validator.py:37)
2026-05-26 12:05:00 [    INFO] Response latency check passed: 45.20ms (threshold: 1500.0ms) (response_assertions.py:46)
```

---

## ⚙️ CI/CD Pipeline

This project is fully CI/CD ready and includes configuration blueprints for both **GitHub Actions** and **Jenkins**.

### 1. GitHub Actions (`.github/workflows/ci.yml`)
* Automatically runs **offline mock tests** on every push or pull request to verify code integrity instantly.
* Automatically runs **live integration tests** on scheduled nightly builds, using credentials bound safely from Repository Secrets.
* Uploads HTML test reports and logging files automatically as test build artifacts.

### 2. Jenkins Pipeline (`Jenkinsfile`)
A declarative pipeline file ([Jenkinsfile](file:///Users/user/Desktop/Project/openweather/Jenkinsfile)) is included in the project root.

#### Setup Instructions:
1. **Configure Credentials**:
   * Navigate to Jenkins -> Manage Jenkins -> Credentials.
   * Add a new **Secret Text** credential named `openweather-api-key` and paste your OpenWeatherMap API token.
2. **Create Pipeline**:
   * Create a new "Pipeline" or "Multibranch Pipeline" project in Jenkins.
   * Point the configuration to your Git repository containing the project and set the Script Path to `Jenkinsfile`.
3. **Pipeline Features**:
   * **Parameterization**: Includes a `RUN_LIVE_TESTS` boolean checkbox parameter. Check it to run tests against the real OpenWeatherMap API, or leave unchecked to run against the mock database offline.
   * **JUnit Reporting**: Integrates with the Jenkins JUnit plugin to publish structured XML test results (`reports/junit.xml`) directly in the build UI dashboard for visual trends.
   * **Artifact Archiving**: Archives the Pytest HTML report (`reports/report.html`) and execution log output (`logs/framework.log`) automatically in the build workspace history.


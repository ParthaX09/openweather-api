import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Base Directory path
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env
load_dotenv(dotenv_path=BASE_DIR / ".env")

class Settings:
    """Manages system configuration loading environment variables and config.json fallback."""
    
    def __init__(self):
        # 1. Load config.json file
        config_path = BASE_DIR / "config" / "config.json"
        if config_path.exists():
            with open(config_path, "r") as f:
                self._config = json.load(f)
        else:
            self._config = {}

        # 2. Determine environment
        self.env = os.getenv("ENV", self._config.get("default_env", "staging")).lower()
        env_config = self._config.get("environments", {}).get(self.env, {})

        # 3. Resolve configs (Env variable takes precedence over config.json config)
        self.base_url = os.getenv("OPENWEATHER_BASE_URL", env_config.get("base_url", "https://api.openweathermap.org"))
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        
        # Read numbers with fallback
        try:
            self.timeout = float(os.getenv("TIMEOUT", env_config.get("timeout", 10.0)))
        except (ValueError, TypeError):
            self.timeout = 10.0

        try:
            self.max_retries = int(os.getenv("MAX_RETRIES", env_config.get("max_retries", 3)))
        except (ValueError, TypeError):
            self.max_retries = 3

        try:
            self.backoff_factor = float(os.getenv("BACKOFF_FACTOR", env_config.get("backoff_factor", 1.0)))
        except (ValueError, TypeError):
            self.backoff_factor = 1.0

        # Performance limits
        limits = self._config.get("limits", {})
        self.max_response_time_ms = limits.get("max_response_time_ms", 1500)
        self.max_payload_size_bytes = limits.get("max_payload_size_bytes", 1048576)

    def validate(self):
        """Verifies if critical config fields are populated."""
        if not self.api_key:
            raise ValueError("API Key is missing! Set OPENWEATHER_API_KEY environment variable.")
        if not self.base_url:
            raise ValueError("Base URL is missing! Set OPENWEATHER_BASE_URL environment variable.")

# Global settings instance
settings = Settings()

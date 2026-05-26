import random
import string
import time
from typing import Dict, Any, Tuple

class DataGenerator:
    """Utility class to dynamically generate various payloads, inputs, and coordinates for test execution."""

    @staticmethod
    def generate_random_string(length: int = 10, use_special: bool = False, use_spaces: bool = False) -> str:
        """Generates a random string of specified length."""
        chars = string.ascii_letters + string.digits
        if use_special:
            chars += "!@#$%^&*()_+=-[]{}|;:,.<>?"
        if use_spaces:
            chars += "    "
        return "".join(random.choice(chars) for _ in range(length))

    @staticmethod
    def generate_random_coordinates() -> Tuple[float, float]:
        """Generates random valid latitude and longitude."""
        lat = round(random.uniform(-90.0, 90.0), 4)
        lon = round(random.uniform(-180.0, 180.0), 4)
        return lat, lon

    @staticmethod
    def generate_pollution_time_range(days_back: int = 5) -> Tuple[int, int]:
        """
        Generates Unix timestamps for start and end times suitable for the Air Pollution historical API.
        
        Args:
            days_back: Number of days back to query history.
        """
        now = int(time.time())
        start = now - (days_back * 24 * 60 * 60)
        # historical end is 1 hour ahead of start to limit payload size
        end = start + 3600
        return start, end

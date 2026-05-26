import time
from typing import Dict, Any, Tuple, Optional, Union

class MockServer:
    """Mock database and engine to return valid JSON structures for offline/placeholder testing."""

    # Pre-defined database of cities to allow real lookup behavior in mock mode
    COORDINATES_MAP = [
        {"name": "London", "lat": 51.5074, "lon": -0.1278, "country": "GB", "state": "England"},
        {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503, "country": "JP", "state": None},
        {"name": "Sydney", "lat": -33.8688, "lon": 151.2093, "country": "AU", "state": "New South Wales"},
        {"name": "Cairo", "lat": 30.0444, "lon": 31.2357, "country": "EG", "state": None},
        {"name": "Quito", "lat": -0.1807, "lon": -78.4678, "country": "EC", "state": None},
        {"name": "Mountain View", "lat": 37.3861, "lon": -122.0839, "country": "US", "state": "California"},
        {"name": "New York", "lat": 40.7128, "lon": -74.0060, "country": "US", "state": "New York"},
        {"name": "Paris", "lat": 48.8566, "lon": 2.3522, "country": "FR", "state": "Île-de-France"},
        {"name": "Berlin", "lat": 52.5200, "lon": 13.4050, "country": "DE", "state": "Berlin"},
        {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "country": "IN", "state": "Maharashtra"},
        {"name": "Rio de Janeiro", "lat": -22.9068, "lon": -43.1729, "country": "BR", "state": "Rio de Janeiro"},
        {"name": "Moscow", "lat": 55.7558, "lon": 37.6173, "country": "RU", "state": "Moscow"},
        {"name": "Null Island", "lat": 0.0, "lon": 0.0, "country": "ocean", "state": None},
        {"name": "North Pole", "lat": 90.0, "lon": 0.0, "country": "arctic", "state": None},
        {"name": "South Pole", "lat": -90.0, "lon": 0.0, "country": "antarctic", "state": None},
        {"name": "Date Line East", "lat": 0.0, "lon": 180.0, "country": "ocean", "state": None},
        {"name": "Date Line West", "lat": 0.0, "lon": -180.0, "country": "ocean", "state": None}
    ]

    @staticmethod
    def _parse_coord(val: Any) -> Optional[float]:
        """Safely casts a coordinate to float, returning None on failure or empty inputs."""
        if val is None or val == "":
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    @classmethod
    def _find_city_by_name(cls, name: str) -> Optional[Dict[str, Any]]:
        if not name:
            return None
        name_clean = name.strip().lower()
        # Direct match or partial match
        for entry in cls.COORDINATES_MAP:
            if entry["name"].lower() == name_clean or name_clean in entry["name"].lower():
                return entry
        return None

    @classmethod
    def _find_city_by_coords(cls, lat: float, lon: float) -> Dict[str, Any]:
        """Finds closest pre-defined city or returns a default generic struct."""
        best_match = None
        min_dist = 999999.0
        
        for entry in cls.COORDINATES_MAP:
            dist = abs(entry["lat"] - lat) + abs(entry["lon"] - lon)
            if dist < min_dist:
                min_dist = dist
                best_match = entry
                
        # If match is close enough, use it
        if best_match and min_dist < 2.0:
            return best_match
            
        return {"name": f"Location_{lat}_{lon}", "lat": lat, "lon": lon, "country": "Unknown", "state": None}

    @classmethod
    def _convert_temperature(cls, kelvin_temp: float, units: Optional[str]) -> float:
        """Converts temperature according to units parameter: standard=Kelvin, metric=Celsius, imperial=Fahrenheit."""
        if not units or units == "standard":
            return round(kelvin_temp, 2)
        elif units == "metric":
            return round(kelvin_temp - 273.15, 2)
        elif units == "imperial":
            # (K - 273.15) * 9/5 + 32
            return round((kelvin_temp - 273.15) * 1.8 + 32, 2)
        return round(kelvin_temp, 2)

    @classmethod
    def get_weather_mock(
        cls,
        q: Optional[str] = None,
        lat: Optional[Any] = None,
        lon: Optional[Any] = None,
        zip_code: Optional[str] = None,
        units: Optional[str] = None,
        appid: str = ""
    ) -> Tuple[int, Dict[str, Any]]:
        if appid != "api_key" and not appid:
            return 401, {"cod": 401, "message": "Invalid API key. Please see https://openweathermap.org/faq#error401 for more info."}
        
        # 1. Coordinate lookup and boundary checking
        is_coord_query = lat is not None or lon is not None
        if is_coord_query:
            parsed_lat = cls._parse_coord(lat)
            parsed_lon = cls._parse_coord(lon)
            
            if parsed_lat is None or parsed_lon is None:
                return 400, {"cod": "400", "message": "Nothing to geocode"}
                
            if parsed_lat < -90 or parsed_lat > 90:
                return 400, {"cod": "400", "message": "wrong latitude"}
            if parsed_lon < -180 or parsed_lon > 180:
                return 400, {"cod": "400", "message": "wrong longitude"}
                
            city_entry = cls._find_city_by_coords(parsed_lat, parsed_lon)
            city_name = city_entry["name"]
            resolved_lat = city_entry["lat"]
            resolved_lon = city_entry["lon"]
            country = city_entry["country"]
        
        # 2. ZIP lookup
        elif zip_code:
            city_name = "Mountain View"
            resolved_lat = 37.3861
            resolved_lon = -122.0839
            country = "US"
            
        # 3. City name lookup
        else:
            if not q or q.strip() == "" or q in ["InvalidCityXYZ123", "NonExistentPlaceNameHere", "None"]:
                return 404, {"cod": "404", "message": "city not found"}
                
            city_entry = cls._find_city_by_name(q)
            if city_entry:
                city_name = city_entry["name"]
                resolved_lat = city_entry["lat"]
                resolved_lon = city_entry["lon"]
                country = city_entry["country"]
            else:
                city_name = q
                resolved_lat = 51.5074
                resolved_lon = -0.1278
                country = "GB"

        # Apply units temperature conversion
        temp_val = cls._convert_temperature(288.15, units)
        feels_val = cls._convert_temperature(287.45, units)
        temp_min_val = cls._convert_temperature(286.15, units)
        temp_max_val = cls._convert_temperature(290.15, units)
        
        return 200, {
            "coord": {"lon": resolved_lon, "lat": resolved_lat},
            "weather": [
                {"id": 800, "main": "Clear", "description": "clear sky", "icon": "01d"}
            ],
            "base": "stations",
            "main": {
                "temp": temp_val,
                "feels_like": feels_val,
                "temp_min": temp_min_val,
                "temp_max": temp_max_val,
                "pressure": 1013,
                "humidity": 67,
                "sea_level": 1013,
                "grnd_level": 1009
            },
            "visibility": 10000,
            "wind": {"speed": 4.1, "deg": 80, "gust": 5.5},
            "clouds": {"all": 0},
            "dt": int(time.time()),
            "sys": {
                "type": 1,
                "id": 1414,
                "country": country,
                "sunrise": int(time.time()) - 20000,
                "sunset": int(time.time()) + 20000
            },
            "timezone": 3600,
            "id": 2643743,
            "name": city_name,
            "cod": 200
        }

    @classmethod
    def get_forecast_mock(
        cls,
        q: Optional[str] = None,
        lat: Optional[Any] = None,
        lon: Optional[Any] = None,
        cnt: Optional[Any] = None,
        units: Optional[str] = None,
        appid: str = ""
    ) -> Tuple[int, Dict[str, Any]]:
        if appid != "api_key" and not appid:
            return 401, {"cod": 401, "message": "Invalid API key."}
        
        is_coord_query = lat is not None or lon is not None
        if is_coord_query:
            parsed_lat = cls._parse_coord(lat)
            parsed_lon = cls._parse_coord(lon)
            
            if parsed_lat is None or parsed_lon is None:
                return 400, {"cod": "400", "message": "Nothing to geocode"}
                
            if parsed_lat < -90 or parsed_lat > 90:
                return 400, {"cod": "400", "message": "wrong latitude"}
            if parsed_lon < -180 or parsed_lon > 180:
                return 400, {"cod": "400", "message": "wrong longitude"}
                
            city_entry = cls._find_city_by_coords(parsed_lat, parsed_lon)
            city_name = city_entry["name"]
            resolved_lat = city_entry["lat"]
            resolved_lon = city_entry["lon"]
            country = city_entry["country"]
        else:
            if not q or q.strip() == "" or q in ["InvalidCityXYZ123", "NonExistentPlaceNameHere"]:
                return 404, {"cod": "404", "message": "city not found"}
                
            city_entry = cls._find_city_by_name(q)
            if city_entry:
                city_name = city_entry["name"]
                resolved_lat = city_entry["lat"]
                resolved_lon = city_entry["lon"]
                country = city_entry["country"]
            else:
                city_name = q
                resolved_lat = 51.5074
                resolved_lon = -0.1278
                country = "GB"

        now = int(time.time())
        forecast_list = []
        
        # Determine list length based on cnt limit
        list_length = 5
        if cnt is not None:
            try:
                list_length = int(cnt)
            except (ValueError, TypeError):
                pass
                
        for i in range(list_length):
            forecast_list.append({
                "dt": now + (i * 10800),
                "main": {
                    "temp": cls._convert_temperature(285.0 + i, units),
                    "feels_like": cls._convert_temperature(284.0 + i, units),
                    "temp_min": cls._convert_temperature(283.0, units),
                    "temp_max": cls._convert_temperature(287.0, units),
                    "pressure": 1012 + i,
                    "sea_level": 1012,
                    "grnd_level": 1008,
                    "humidity": 70 + i,
                    "temp_kf": 0.5 * i
                },
                "weather": [
                    {"id": 800 + i, "main": "Clouds", "description": "few clouds", "icon": "02d"}
                ],
                "clouds": {"all": 20 + i * 5},
                "wind": {"speed": 3.5 + i, "deg": 120, "gust": 4.5},
                "visibility": 10000,
                "pop": 0.1 * i,
                "sys": {"pod": "d" if i % 2 == 0 else "n"},
                "dt_txt": "2026-05-26 12:00:00"
            })

        return 200, {
            "cod": "200",
            "message": 0,
            "cnt": len(forecast_list),
            "list": forecast_list,
            "city": {
                "id": 2643743,
                "name": city_name,
                "coord": {"lat": resolved_lat, "lon": resolved_lon},
                "country": country,
                "population": 1000000,
                "timezone": 3600,
                "sunrise": now - 20000,
                "sunset": now + 20000
            }
        }

    @classmethod
    def get_geocoding_direct_mock(cls, q: str, appid: str = "") -> Tuple[int, list]:
        if appid != "api_key" and not appid:
            return 401, []
        
        if not q or q.strip() == "" or q in ["InvalidCityXYZ123", "NonExistentPlaceNameHere"]:
            return 200, []

        city_entry = cls._find_city_by_name(q)
        if city_entry:
            return 200, [
                {
                    "name": city_entry["name"],
                    "local_names": {"en": city_entry["name"], "feature_name": city_entry["name"]},
                    "lat": city_entry["lat"],
                    "lon": city_entry["lon"],
                    "country": city_entry["country"],
                    "state": city_entry["state"]
                }
            ]

        return 200, [
            {
                "name": q,
                "local_names": {"en": q, "feature_name": q},
                "lat": 51.5074,
                "lon": -0.1278,
                "country": "GB",
                "state": "England"
            }
        ]

    @classmethod
    def get_geocoding_reverse_mock(cls, lat: Any, lon: Any, appid: str = "") -> Tuple[int, list]:
        if appid != "api_key" and not appid:
            return 401, []

        parsed_lat = cls._parse_coord(lat)
        parsed_lon = cls._parse_coord(lon)
        
        if parsed_lat is None or parsed_lon is None:
            return 400, []

        if abs(parsed_lat) > 90 or abs(parsed_lon) > 180:
            return 400, []

        city_entry = cls._find_city_by_coords(parsed_lat, parsed_lon)
        return 200, [
            {
                "name": city_entry["name"],
                "lat": parsed_lat,
                "lon": parsed_lon,
                "country": city_entry["country"],
                "state": city_entry["state"]
            }
        ]

    @classmethod
    def get_pollution_mock(cls, lat: Any, lon: Any, appid: str = "") -> Tuple[int, Dict[str, Any]]:
        if appid != "api_key" and not appid:
            return 401, {"cod": 401, "message": "Invalid API key."}

        parsed_lat = cls._parse_coord(lat)
        parsed_lon = cls._parse_coord(lon)

        if parsed_lat is None or parsed_lon is None:
            return 400, {"cod": "400", "message": "wrong latitude/longitude"}

        if abs(parsed_lat) > 90 or abs(parsed_lon) > 180:
            return 400, {"cod": "400", "message": "wrong latitude/longitude"}

        return 200, {
            "coord": {"lon": parsed_lon, "lat": parsed_lat},
            "list": [
                {
                    "dt": int(time.time()),
                    "main": {"aqi": 3},
                    "components": {
                        "co": 201.9,
                        "no": 0.01,
                        "no2": 3.8,
                        "o3": 60.1,
                        "so2": 1.5,
                        "pm2_5": 10.5,
                        "pm10": 15.2,
                        "nh3": 0.4
                    }
                }
            ]
        }

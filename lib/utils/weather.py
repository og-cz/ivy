from datetime import datetime, timezone, timedelta
from typing import Optional
import requests

try:
    import config

    GEOCODE_URL = config.GEOCODE_URL
    FORECAST_URL = config.FORECAST_URL
except ModuleNotFoundError:
    GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def decode_weather_code(code: int) -> tuple[bool, str]:
    """
    Return (is_sunny, description) based on Open-Meteo weathercode.
    """
    if code == 0:
        return True, "Clear"
    if code in (1, 2):
        return True, "Partly Cloudy"
    if code == 3:
        return False, "Cloudy"
    if code in (45, 48):
        return False, "Foggy"
    if 51 <= code <= 67:
        return False, "Rainy"
    if 71 <= code <= 77:
        return False, "Snowy"
    if 80 <= code <= 82:
        return False, "Rainy"
    if 85 <= code <= 86:
        return False, "Snowy"
    if 95 <= code <= 99:
        return False, "Stormy"
    return False, "Unknown"


def get_city_weather(city: str) -> Optional[dict]:
    """
    Get current date, time, and weather for a city.

    Returns dict with:
    - date (str): Local date in format "October 15, 2025"
    - time (str): Local time in 12-hour format (e.g., "02:30 PM")
    - is_sunny (bool): True if weather is sunny/clear
    - temperature (float): Temperature in Celsius
    - weather_description (str): Weather condition
    - city_name (str): Full city name with country

    Returns None if city not found or error occurs.
    """
    try:
        with requests.Session() as session:
            params = {"name": city, "count": 1, "language": "en", "format": "json"}
            data = session.get(GEOCODE_URL, params=params, timeout=15).json()

            results = data.get("results") or []
            if not results:
                return None

            loc = results[0]
            city_name = loc.get("name", city)
            country = loc.get("country")
            full_city_name = f"{city_name}, {country}" if country else city_name

            weather_params = {
                "latitude": loc["latitude"],
                "longitude": loc["longitude"],
                "current_weather": "true",
                "timezone": loc.get("timezone", "UTC"),
            }
            weather_data = session.get(
                FORECAST_URL, params=weather_params, timeout=15
            ).json()

        current = weather_data.get("current_weather") or {}
        temperature = current.get("temperature")
        weather_code = int(current.get("weathercode", 0))

        # Local time and date using API-provided UTC offset
        offset_seconds = int(weather_data.get("utc_offset_seconds", 0))
        local_dt = datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)

        is_sunny, weather_desc = decode_weather_code(weather_code)

        return {
            "date": local_dt.strftime("%B %d, %Y"),
            "time": local_dt.strftime("%I:%M %p"),
            "is_sunny": is_sunny,
            "temperature": temperature,
            "weather_description": weather_desc,
            "city_name": full_city_name,
        }
    except Exception as e:
        print(f"Error fetching weather for {city}: {e}")
        return None

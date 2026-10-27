from typing import Optional, Dict, Any
import requests
import config

IP_API = getattr(
    config,
    "IP_API",
    "http://ip-api.com/json/?fields=status,message,city,regionName,country,lat,lon,timezone,query",
)

# location doesn't change while Ivy runs, so look it up once
_cached_location: Optional[Dict[str, Any]] = None


def detect_city_via_ip() -> Optional[Dict[str, Any]]:
    global _cached_location
    if _cached_location is not None:
        return _cached_location

    try:
        data = requests.get(IP_API, timeout=10).json()
    except Exception:
        return None

    if data.get("status") != "success":
        return None

    city = data.get("city")
    country = data.get("country")
    _cached_location = {
        "city": city,
        "region": data.get("regionName"),
        "country": country,
        "latitude": data.get("lat"),
        "longitude": data.get("lon"),
        "timezone": data.get("timezone"),
        "ip": data.get("query"),
        "label": ", ".join([p for p in [city, country] if p]),
    }
    return _cached_location

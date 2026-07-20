import requests
import logging
from typing import List, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Major port coordinates
PORT_COORDINATES = {
    "Shanghai": {"lat": 31.2304, "lon": 121.4737},
    "Singapore": {"lat": 1.3521, "lon": 103.8198},
    "Rotterdam": {"lat": 51.9244, "lon": 4.4777},
    "Antwerp": {"lat": 51.2602, "lon": 4.4025},
    "Hong Kong": {"lat": 22.3193, "lon": 114.1694},
    "Los Angeles": {"lat": 34.0522, "lon": -118.2437},
    "Long Beach": {"lat": 33.7701, "lon": -118.1937},
    "Hamburg": {"lat": 53.5511, "lon": 9.9937},
    "Busan": {"lat": 35.1796, "lon": 129.0756},
    "Qingdao": {"lat": 36.0671, "lon": 120.3826},
    "Guangzhou": {"lat": 23.1291, "lon": 113.2644},
    "Shenzhen": {"lat": 22.5431, "lon": 114.0579},
    "Tianjin": {"lat": 39.0842, "lon": 117.2007},
    "Osaka": {"lat": 34.6937, "lon": 135.5023},
    "Tokyo": {"lat": 35.6762, "lon": 139.6503},
}

def get_weather_events() -> List[Dict]:
    """Fetch weather events from Open-Meteo API"""
    weather_events = []
    
    # Thresholds for extreme weather
    EXTREME_WIND_THRESHOLD = 80  # km/h
    EXTREME_RAIN_THRESHOLD = 50  # mm/day
    EXTREME_SNOW_THRESHOLD = 30  # cm/day
    
    for port_name, coords in PORT_COORDINATES.items():
        try:
            # Get weather forecast
            url = f"https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": coords["lat"],
                "longitude": coords["lon"],
                "daily": ["wind_speed_10m_max", "precipitation_sum", "snowfall_sum"],
                "forecast_days": 5,
                "timezone": "UTC"
            }
            
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                
                # Check for extreme weather
                for i, date in enumerate(data["daily"]["time"]):
                    wind_speed = data["daily"]["wind_speed_10m_max"][i]
                    precipitation = data["daily"]["precipitation_sum"][i]
                    snowfall = data["daily"]["snowfall_sum"][i]
                    
                    severity = 0
                    event_type = None
                    description = None
                    
                    if wind_speed > EXTREME_WIND_THRESHOLD:
                        severity = min(100, (wind_speed - EXTREME_WIND_THRESHOLD) * 2)
                        event_type = "windstorm"
                        description = f"Extreme wind speed of {wind_speed:.1f} km/h detected"
                    
                    if precipitation > EXTREME_RAIN_THRESHOLD:
                        rain_severity = min(100, (precipitation - EXTREME_RAIN_THRESHOLD) * 2)
                        if rain_severity > severity:
                            severity = rain_severity
                            event_type = "flood"
                            description = f"Heavy rainfall of {precipitation:.1f} mm/day detected"
                    
                    if snowfall > EXTREME_SNOW_THRESHOLD:
                        snow_severity = min(100, (snowfall - EXTREME_SNOW_THRESHOLD) * 3)
                        if snow_severity > severity:
                            severity = snow_severity
                            event_type = "snowstorm"
                            description = f"Heavy snowfall of {snowfall:.1f} cm/day detected"
                    
                    if severity > 0:
                        weather_events.append({
                            "title": f"{event_type.capitalize()} at {port_name}",
                            "description": description,
                            "location": port_name,
                            "severity": severity,
                            "estimated_duration_days": 3 if severity < 50 else 7,
                            "date": date
                        })
            
        except Exception as e:
            logger.error(f"Error fetching weather for {port_name}: {e}")
    
    return weather_events

def get_weather_forecast(lat: float, lon: float, days: int = 5) -> Dict:
    """Get detailed weather forecast for a location"""
    try:
        url = f"https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": ["temperature_2m_max", "temperature_2m_min", 
                     "wind_speed_10m_max", "precipitation_sum", "snowfall_sum",
                     "weather_code"],
            "forecast_days": days,
            "timezone": "UTC"
        }
        
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error(f"Error fetching weather forecast: {e}")
    
    return {}
from dataclasses import dataclass

import requests


class WeatherServiceError(Exception):
    pass


@dataclass
class WeatherSnapshot:
    temperature: float
    windspeed: float
    weathercode: int
    source: str

    def to_dict(self) -> dict:
        return {
            "temperature": self.temperature,
            "windspeed": self.windspeed,
            "weathercode": self.weathercode,
            "source": self.source,
        }


def get_weather_for_city(city: str) -> WeatherSnapshot:
    geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
    weather_url = "https://api.open-meteo.com/v1/forecast"

    geo_resp = requests.get(geocode_url, params={"name": city, "count": 1}, timeout=8)
    if geo_resp.status_code != 200:
        raise WeatherServiceError("Не удалось получить координаты города.")

    geo_data = geo_resp.json()
    if not geo_data.get("results"):
        raise WeatherServiceError("Город не найден.")

    first = geo_data["results"][0]
    lat, lon = first["latitude"], first["longitude"]

    weather_resp = requests.get(
        weather_url,
        params={"latitude": lat, "longitude": lon, "current": "temperature_2m,wind_speed_10m,weather_code"},
        timeout=8,
    )
    if weather_resp.status_code != 200:
        raise WeatherServiceError("Не удалось получить прогноз.")

    current = weather_resp.json().get("current", {})
    return WeatherSnapshot(
        temperature=float(current.get("temperature_2m", 0)),
        windspeed=float(current.get("wind_speed_10m", 0)),
        weathercode=int(current.get("weather_code", -1)),
        source="Open-Meteo",
    )


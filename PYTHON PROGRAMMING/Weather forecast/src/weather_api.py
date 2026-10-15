"""
Reusable functions for the Weather Forecast Mini-Project.

This module contains:
- API request handling
- Geocoding
- Open-Meteo forecast retrieval
- Norway MET forecast retrieval
- Weather-code decoding
- Forecast JSON parsing
"""

import json
import time
from typing import Any

import requests
import pandas as pd


class WeatherAPIError(Exception):
    """Raised when a weather API request fails after all retries."""


# Open-Meteo weather code descriptions
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def request_with_retry(
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 10,
    retries: int = 3,
) -> requests.Response:
    """
    Make an HTTP GET request with timeout, error handling and retries.

    Parameters
    ----------
    url : str
        URL to request.
    params : dict, optional
        Query parameters.
    headers : dict, optional
        HTTP headers.
    timeout : float
        Maximum number of seconds for one request.
    retries : int
        Maximum number of retries.

    Returns
    -------
    requests.Response
        Successful HTTP response.

    Raises
    ------
    WeatherAPIError
        If all attempts fail.
    """

    last_error = None

    for attempt in range(retries + 1):
        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout,
            )

            # Retry server-side errors.
            if 500 <= response.status_code <= 599:
                response.raise_for_status()

            # Raise for 4xx and other unsuccessful responses.
            response.raise_for_status()

            return response

        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as exc:
            last_error = exc

            if attempt == retries:
                break

            # Exponential backoff:
            # 1, 2, 4 seconds for attempts.
            sleep_time = 2 ** attempt
            time.sleep(sleep_time)

    raise WeatherAPIError(
        f"Request failed after {retries + 1} attempts: {last_error}"
    )


def geocode(name: str, timeout: float = 10) -> list[dict[str, Any]]:
    """
    Convert a city/location name into candidate geographic locations.

    Parameters
    ----------
    name : str
        City or location name.
    timeout : float
        Request timeout.

    Returns
    -------
    list[dict]
        Candidate locations returned by Open-Meteo.

    Raises
    ------
    ValueError
        If the name is empty or no locations are found.
    WeatherAPIError
        If the API request fails.
    """

    if not name.strip():
        raise ValueError("Location name cannot be empty.")

    url = "https://geocoding-api.open-meteo.com/v1/search"

    params = {
        "name": name,
        "count": 10,
        "language": "en",
        "format": "json",
    }

    response = request_with_retry(
        url,
        params=params,
        timeout=timeout,
    )

    data = response.json()

    # Results key may be absent.
    results = data.get("results", [])

    if not results:
        raise ValueError(f"No location found for '{name}'.")

    return results


def select_location(
    candidates: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Select a location from geocoding candidates.

    If there is only one candidate it is returned automatically.
    If there are multiple candidates, the user is asked to select one.
    """

    if len(candidates) == 1:
        return candidates[0]

    print("\nMultiple locations were found:\n")

    for index, location in enumerate(candidates, start=1):
        name = location.get("name", "Unknown")
        country = location.get("country", "Unknown")
        admin = location.get("admin1", "")
        latitude = location.get("latitude")
        longitude = location.get("longitude")

        print(
            f"{index}. {name}, {admin}, {country} "
            f"({latitude}, {longitude})"
        )

    while True:
        try:
            choice = int(input("Select a location number: "))

            if 1 <= choice <= len(candidates):
                return candidates[choice - 1]

            print("Please choose a valid number.")

        except ValueError:
            print("Please enter a number.")


def get_forecast(
    latitude: float,
    longitude: float,
    days: int = 5,
    timeout: float = 10,
) -> dict[str, Any]:
    """
    Retrieve a daily forecast from Open-Meteo.

    Parameters
    ----------
    latitude : float
        Location latitude.
    longitude : float
        Location longitude.
    days : int
        Number of forecast days.
    timeout : float
        Request timeout.

    Returns
    -------
    dict
        Open-Meteo forecast JSON.
    """

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90.")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180.")

    if days < 1 or days > 16:
        raise ValueError("Days must be between 1 and 16.")

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": (
            "temperature_2m_max,"
            "temperature_2m_min,"
            "precipitation_sum,"
            "wind_speed_10m_max,"
            "weather_code"
        ),
        "forecast_days": days,
        "timezone": "auto",
    }

    response = request_with_retry(
        url,
        params=params,
        timeout=timeout,
    )

    return response.json()


def weather_code_description(code: int) -> str:
    """
    Convert an Open-Meteo weather code into a readable description.
    """

    return WEATHER_CODES.get(code, "Unknown weather condition")


def forecast_to_dataframe(data: dict[str, Any]) -> pd.DataFrame:
    """
    Convert Open-Meteo forecast JSON into a pandas DataFrame.

    Returns
    -------
    pandas.DataFrame
        Forecast data with readable column names and units.
    """

    daily = data.get("daily")

    if not daily:
        raise ValueError("Forecast JSON does not contain daily data.")

    required_columns = [
        "time",
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "wind_speed_10m_max",
        "weather_code",
    ]

    missing = [
        column for column in required_columns
        if column not in daily
    ]

    if missing:
        raise ValueError(
            f"Forecast data is missing columns: {missing}"
        )

    dataframe = pd.DataFrame(
        {
            "Date": daily["time"],
            "Max Temperature (°C)": daily["temperature_2m_max"],
            "Min Temperature (°C)": daily["temperature_2m_min"],
            "Precipitation (mm)": daily["precipitation_sum"],
            "Max Wind Speed (km/h)": daily["wind_speed_10m_max"],
            "Weather Code": daily["weather_code"],
        }
    )

    dataframe["Weather Description"] = dataframe[
        "Weather Code"
    ].apply(weather_code_description)

    return dataframe


def get_met_norway_forecast(
    latitude: float,
    longitude: float,
    email: str,
    timeout: float = 10,
) -> dict[str, Any]:
    """
    Retrieve weather information from Norway MET Locationforecast API.

    Parameters
    ----------
    latitude : float
        Latitude.
    longitude : float
        Longitude.
    email : str
        Contact email for the User-Agent.
    timeout : float
        Request timeout.

    Returns
    -------
    dict
        MET Norway JSON response.
    """

    if not email or "@" not in email:
        raise ValueError(
            "A valid university email is required for the User-Agent."
        )

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90.")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180.")

    url = (
        "https://api.met.no/weatherapi/locationforecast/2.0/complete"
    )

    headers = {
        "User-Agent": f"UCU Weather Forecast Student Project ({email})"
    }

    params = {
        "lat": latitude,
        "lon": longitude,
    }

    response = request_with_retry(
        url,
        params=params,
        headers=headers,
        timeout=timeout,
    )

    return response.json()
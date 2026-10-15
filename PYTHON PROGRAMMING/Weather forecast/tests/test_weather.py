
import json
from pathlib import Path

import pandas as pd
import pytest

from src.weather_api import (
    WeatherAPIError,
    forecast_to_dataframe,
    weather_code_description,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SAMPLE_FILE = PROJECT_ROOT / "sample_data" / "forecast_sample.json"


def load_sample_forecast():
    """Load the saved sample forecast JSON."""

    with open(SAMPLE_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def test_sample_json_loads():
    """Check that the sample JSON can be loaded."""

    data = load_sample_forecast()

    assert isinstance(data, dict)


def test_forecast_has_daily_data():
    """Check that daily forecast data exists."""

    data = load_sample_forecast()

    assert "daily" in data


def test_forecast_dataframe_is_created():
    """Check that JSON can be converted to a DataFrame."""

    data = load_sample_forecast()

    dataframe = forecast_to_dataframe(data)

    assert isinstance(dataframe, pd.DataFrame)


def test_forecast_dataframe_has_five_rows():
    """Check that five forecast days are parsed."""

    data = load_sample_forecast()

    dataframe = forecast_to_dataframe(data)

    assert len(dataframe) == 5


def test_required_columns_exist():
    """Check that all expected output columns exist."""

    data = load_sample_forecast()

    dataframe = forecast_to_dataframe(data)

    expected_columns = [
        "Date",
        "Max Temperature (°C)",
        "Min Temperature (°C)",
        "Precipitation (mm)",
        "Max Wind Speed (km/h)",
        "Weather Code",
        "Weather Description",
    ]

    for column in expected_columns:
        assert column in dataframe.columns


def test_weather_code_zero():
    """Check that weather code 0 is decoded correctly."""

    assert weather_code_description(0) == "Clear sky"


def test_weather_code_61():
    """Check that weather code 61 is decoded correctly."""

    assert weather_code_description(61) == "Slight rain"


def test_unknown_weather_code():
    """Check the edge case of an unknown weather code."""

    assert weather_code_description(999) == "Unknown weather condition"
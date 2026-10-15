Weather Forecasting Tool

A simple Python project that retrieves weather forecasts from Open-Meteo and MET Norway APIs. It supports location search, forecast retrieval, and conversion of daily weather data into a readable table.

Features
Searches for locations by name.
Retrieves daily forecasts, including temperature, rainfall, wind speed, and weather conditions.
Converts forecast data into a Pandas DataFrame.
Handles API failures using timeouts, retries, and exponential backoff.
Supports forecasts from two weather providers.
Requirements
Python 3.10+
requests
pandas

Install dependencies:

pip install requests pandas

Findings

The tool makes weather data easier to retrieve and interpret. Location selection helps avoid choosing the wrong place when multiple matches are returned, while retry handling improves reliability during temporary network or server errors.

Limitations
Forecast accuracy depends on the weather provider and available data.
An internet connection is required.
The location search may return several similar names.
MET Norway requires a valid contact email in the request's User-Agent.
API errors can still occur after all retry attempts.


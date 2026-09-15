"""
tariff.py
---------
Configurable electricity tariff schedule models for Wisp Person 3.
Supports Time-of-Use (TOU), tiered, and custom hourly schedules.

Explicit Units:
- Tariff: currency / kWh (e.g., $/kWh)
"""

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Dict, List, Tuple, Union


# Default Time-Of-Use Schedule:
# 00:00–06:00 -> 4 currency/kWh
# 06:00–12:00 -> 6 currency/kWh
# 12:00–18:00 -> 10 currency/kWh
# 18:00–22:00 -> 8 currency/kWh
# 22:00–24:00 -> 5 currency/kWh
DEFAULT_TARIFF_SCHEDULE: List[Tuple[int, int, float]] = [
    (0, 6, 4.0),
    (6, 12, 6.0),
    (12, 18, 10.0),
    (18, 22, 8.0),
    (22, 24, 5.0),
]


class TariffModel:
    """
    Configurable Time-of-Use (TOU) electricity pricing model.
    """

    def __init__(self, schedule: Union[List[Tuple[int, int, float]], Dict[int, float], None] = None):
        """
        Initializes the TariffModel with a configurable hourly schedule.

        Args:
            schedule: Either a list of (start_hour, end_hour, price) tuples or
                      a dict mapping hour (0..23) to price.
                      If None, DEFAULT_TARIFF_SCHEDULE is used.
        """
        self._hourly_rates: Dict[int, float] = {}

        if schedule is None:
            self._load_from_intervals(DEFAULT_TARIFF_SCHEDULE)
        elif isinstance(schedule, list):
            self._load_from_intervals(schedule)
        elif isinstance(schedule, dict):
            for h in range(24):
                if h not in schedule:
                    raise ValueError(f"Schedule missing rate for hour {h}")
                if schedule[h] < 0:
                    raise ValueError(f"Tariff rate cannot be negative: {schedule[h]}")
                self._hourly_rates[h] = float(schedule[h])
        else:
            raise TypeError("Schedule must be a list of intervals or a dict of {hour: rate}")

    def _load_from_intervals(self, intervals: List[Tuple[int, int, float]]) -> None:
        """Populates 24-hour rate mapping from interval definitions."""
        for start_h, end_h, rate in intervals:
            if rate < 0:
                raise ValueError(f"Tariff rate cannot be negative: {rate}")
            if not (0 <= start_h < end_h <= 24):
                raise ValueError(f"Invalid interval: ({start_h}, {end_h})")
            for h in range(start_h, end_h):
                self._hourly_rates[h] = float(rate)

        # Ensure all 24 hours are covered
        missing = [h for h in range(24) if h not in self._hourly_rates]
        if missing:
            raise ValueError(f"Schedule incomplete. Missing hours: {missing}")

    def get_tariff(self, timestamp: Union[datetime, int, float]) -> float:
        """
        Returns the electricity tariff rate (currency/kWh) for a given timestamp.

        Args:
            timestamp: datetime object, unix epoch seconds (int/float), or hour integer (0..23).

        Returns:
            Tariff rate in currency/kWh.
        """
        if isinstance(timestamp, datetime):
            hour = timestamp.hour
        elif isinstance(timestamp, (int, float)):
            # If passed an hour directly (0..23)
            if 0 <= timestamp <= 23 and isinstance(timestamp, int):
                hour = timestamp
            else:
                # Epoch timestamp
                dt = datetime.fromtimestamp(timestamp)
                hour = dt.hour
        else:
            raise TypeError(f"Unsupported timestamp type: {type(timestamp).__name__}")

        return self._hourly_rates[hour]

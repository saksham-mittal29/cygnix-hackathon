"""
preferences.py
--------------
Occupant comfort preferences model and synthetic testing profiles for Wisp Person 3.

Explicit Units:
- Temperature: Celsius (°C)
- Relative Humidity: Percent (%)
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


# Global Physical / Reasonable Guardrail Bounds for Temperature and Humidity
MIN_REASONABLE_TEMP_C: float = 16.0
MAX_REASONABLE_TEMP_C: float = 30.0
MIN_REASONABLE_HUMIDITY_PCT: float = 20.0
MAX_REASONABLE_HUMIDITY_PCT: float = 80.0


@dataclass
class OccupantPreferences:
    """
    Data model representing an occupant's thermal comfort preferences.
    """
    occupant_id: str = "default_occupant"
    preferred_temperature_low_c: float = 23.0    # °C (default simulation value)
    preferred_temperature_high_c: float = 25.0   # °C (default simulation value)
    preferred_humidity_low_percent: float = 40.0 # % (default simulation value)
    preferred_humidity_high_percent: float = 60.0 # % (default simulation value)

    # Configurable guardrails to prevent extreme unbounded drift
    min_temp_bound_c: float = MIN_REASONABLE_TEMP_C
    max_temp_bound_c: float = MAX_REASONABLE_TEMP_C
    min_humidity_bound_pct: float = MIN_REASONABLE_HUMIDITY_PCT
    max_humidity_bound_pct: float = MAX_REASONABLE_HUMIDITY_PCT

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        """Validates that preference intervals are non-negative, ordered, and within physical guardrails."""
        if self.preferred_temperature_low_c > self.preferred_temperature_high_c:
            raise ValueError(
                f"preferred_temperature_low_c ({self.preferred_temperature_low_c}) "
                f"cannot exceed preferred_temperature_high_c ({self.preferred_temperature_high_c})"
            )
        if self.preferred_humidity_low_percent > self.preferred_humidity_high_percent:
            raise ValueError(
                f"preferred_humidity_low_percent ({self.preferred_humidity_low_percent}) "
                f"cannot exceed preferred_humidity_high_percent ({self.preferred_humidity_high_percent})"
            )
        if self.preferred_temperature_low_c < self.min_temp_bound_c or self.preferred_temperature_high_c > self.max_temp_bound_c:
            raise ValueError(
                f"Temperature preferences [{self.preferred_temperature_low_c}, {self.preferred_temperature_high_c}] °C "
                f"must fall within guardrails [{self.min_temp_bound_c}, {self.max_temp_bound_c}] °C"
            )
        if self.preferred_humidity_low_percent < self.min_humidity_bound_pct or self.preferred_humidity_high_percent > self.max_humidity_bound_pct:
            raise ValueError(
                f"Humidity preferences [{self.preferred_humidity_low_percent}, {self.preferred_humidity_high_percent}] % "
                f"must fall within guardrails [{self.min_humidity_bound_pct}, {self.max_humidity_bound_pct}] %"
            )


# Synthetic Test Profiles (For Testing & Simulation Fixtures ONLY)
def create_eco_profile(occupant_id: str = "synthetic_eco") -> OccupantPreferences:
    """Creates a wider synthetic test preference profile prioritizing energy savings (23 - 26 °C)."""
    return OccupantPreferences(
        occupant_id=occupant_id,
        preferred_temperature_low_c=23.0,
        preferred_temperature_high_c=26.0,
        preferred_humidity_low_percent=35.0,
        preferred_humidity_high_percent=65.0,
    )


def create_comfort_first_profile(occupant_id: str = "synthetic_comfort_first") -> OccupantPreferences:
    """Creates a tighter synthetic test preference profile prioritizing comfort (22 - 24 °C)."""
    return OccupantPreferences(
        occupant_id=occupant_id,
        preferred_temperature_low_c=22.0,
        preferred_temperature_high_c=24.0,
        preferred_humidity_low_percent=40.0,
        preferred_humidity_high_percent=55.0,
    )

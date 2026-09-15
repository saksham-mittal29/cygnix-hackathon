"""
comfort_model.py
----------------
Deterministic thermal comfort evaluation model for Wisp Person 3.
Calculates temperature and humidity deviations and overall comfort penalty.

Units:
- Temperature: Celsius (°C)
- Relative Humidity: Percent (%)
"""

from dataclasses import dataclass
from backend.app.personalization.preferences import OccupantPreferences


@dataclass(frozen=True)
class ComfortEvaluation:
    """
    Structured result of a thermal comfort evaluation.
    """
    is_comfortable: bool
    temperature_deviation_c: float
    humidity_deviation_percent: float
    temperature_penalty: float
    humidity_penalty: float
    comfort_penalty: float


class ComfortModel:
    """
    Evaluates indoor comfort against occupant preferences.
    """

    @staticmethod
    def evaluate(
        indoor_temp_c: float,
        indoor_humidity_pct: float,
        preferences: OccupantPreferences,
    ) -> ComfortEvaluation:
        """
        Evaluates current indoor temperature and humidity against occupant comfort preferences.

        Args:
            indoor_temp_c: Indoor dry-bulb temperature in °C.
            indoor_humidity_pct: Indoor relative humidity in % [0.0, 100.0].
            preferences: OccupantPreferences instance.

        Returns:
            ComfortEvaluation containing deviation metrics and scalar comfort penalty.
        """
        # Input Validation
        if not (-15.0 <= indoor_temp_c <= 60.0):
            raise ValueError(f"Indoor temperature {indoor_temp_c} °C is outside physical sensor limits")
        if not (0.0 <= indoor_humidity_pct <= 100.0):
            raise ValueError(f"Indoor humidity {indoor_humidity_pct} % must be in range [0, 100]")

        # 1. Temperature Deviation
        if indoor_temp_c < preferences.preferred_temperature_low_c:
            temp_dev = preferences.preferred_temperature_low_c - indoor_temp_c
        elif indoor_temp_c > preferences.preferred_temperature_high_c:
            temp_dev = indoor_temp_c - preferences.preferred_temperature_high_c
        else:
            temp_dev = 0.0

        # 2. Humidity Deviation
        if indoor_humidity_pct < preferences.preferred_humidity_low_percent:
            hum_dev = preferences.preferred_humidity_low_percent - indoor_humidity_pct
        elif indoor_humidity_pct > preferences.preferred_humidity_high_percent:
            hum_dev = indoor_humidity_pct - preferences.preferred_humidity_high_percent
        else:
            hum_dev = 0.0

        # 3. Penalty Formulation
        # Penalty grows progressively as distance outside the comfort zone increases
        # Temperature penalty: (deviation + 0.25 * deviation^2)
        temp_penalty = (temp_dev + 0.25 * (temp_dev ** 2)) if temp_dev > 0 else 0.0
        
        # Humidity penalty: scaled by 0.1 to reflect thermal dominance of temperature
        hum_penalty = (0.05 * hum_dev + 0.01 * (hum_dev ** 2)) if hum_dev > 0 else 0.0

        total_penalty = temp_penalty + hum_penalty
        is_comfortable = (temp_dev == 0.0) and (hum_dev == 0.0)

        return ComfortEvaluation(
            is_comfortable=is_comfortable,
            temperature_deviation_c=round(temp_dev, 4),
            humidity_deviation_percent=round(hum_dev, 4),
            temperature_penalty=round(temp_penalty, 4),
            humidity_penalty=round(hum_penalty, 4),
            comfort_penalty=round(total_penalty, 4),
        )

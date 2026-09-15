"""
solar.py
--------
Configurable Solar PV generation model for Wisp Person 3.
Provides explicit power (kW) and energy (kWh) outputs over simulation timesteps.

Units:
- Solar Power: kW
- Solar Energy: kWh (Power * timestep_minutes / 60)
"""

from datetime import datetime
from typing import Dict, List, Tuple, Union
import numpy as np


# Default Anchor Points for Synthetic Solar Profile:
# (hour, power_kW)
DEFAULT_SOLAR_PROFILE_ANCHORS: List[Tuple[float, float]] = [
    (0.0, 0.0),
    (6.0, 0.0),
    (8.0, 0.5),
    (10.0, 2.0),
    (12.0, 4.0),
    (14.0, 3.0),
    (18.0, 0.0),
    (24.0, 0.0),
]


class SolarModel:
    """
    Configurable Solar Photovoltaic (PV) generation model.
    Interpolates diurnal generation curve or accepts discrete profile mappings.
    """

    def __init__(self, profile_anchors: Union[List[Tuple[float, float]], Dict[int, float], None] = None):
        """
        Initializes SolarModel with configurable diurnal generation curve.

        Args:
            profile_anchors: Either a list of (hour_float, power_kW) anchors or
                             a dict mapping hour (0..23) to power_kW.
                             If None, DEFAULT_SOLAR_PROFILE_ANCHORS is used.
        """
        if profile_anchors is None:
            self._anchors = sorted(DEFAULT_SOLAR_PROFILE_ANCHORS, key=lambda x: x[0])
            self._discrete_mode = False
        elif isinstance(profile_anchors, list):
            for h, p in profile_anchors:
                if p < 0:
                    raise ValueError(f"Solar power cannot be negative: {p} kW")
                if not (0.0 <= h <= 24.0):
                    raise ValueError(f"Hour must be in [0, 24], got {h}")
            self._anchors = sorted(profile_anchors, key=lambda x: x[0])
            self._discrete_mode = False
        elif isinstance(profile_anchors, dict):
            for h, p in profile_anchors.items():
                if p < 0:
                    raise ValueError(f"Solar power cannot be negative: {p} kW")
            self._discrete_hourly = {int(k): float(v) for k, v in profile_anchors.items()}
            self._discrete_mode = True
        else:
            raise TypeError("profile_anchors must be a list of (hour, kW) or dict of {hour: kW}")

    def get_solar_power_kW(self, timestamp: Union[datetime, int, float]) -> float:
        """
        Calculates instantaneous solar power generation (kW) at a given timestamp.

        Args:
            timestamp: datetime object, unix epoch timestamp, or hour float (0.0..24.0).

        Returns:
            Available solar power in kW (>= 0.0).
        """
        if isinstance(timestamp, datetime):
            hour_float = timestamp.hour + timestamp.minute / 60.0 + timestamp.second / 3600.0
            hour_int = timestamp.hour
        elif isinstance(timestamp, (int, float)):
            if 0.0 <= timestamp <= 24.0:
                hour_float = float(timestamp)
                hour_int = int(hour_float) % 24
            else:
                dt = datetime.fromtimestamp(timestamp)
                hour_float = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
                hour_int = dt.hour
        else:
            raise TypeError(f"Unsupported timestamp type: {type(timestamp).__name__}")

        if self._discrete_mode:
            return max(0.0, float(self._discrete_hourly.get(hour_int, 0.0)))

        # Continuous linear interpolation across anchor points
        hours = [a[0] for a in self._anchors]
        powers = [a[1] for a in self._anchors]
        power = float(np.interp(hour_float, hours, powers))
        return max(0.0, power)

    def get_solar_energy_kWh(self, timestamp: Union[datetime, int, float], timestep_minutes: float = 5.0) -> float:
        """
        Calculates solar energy generated over a simulation timestep.

        Args:
            timestamp: Simulation timestamp.
            timestep_minutes: Duration of simulation interval in minutes (default: 5.0).

        Returns:
            Solar energy generated in kWh.
        """
        if timestep_minutes <= 0:
            raise ValueError(f"timestep_minutes must be positive, got {timestep_minutes}")
        power_kw = self.get_solar_power_kW(timestamp)
        return power_kw * (timestep_minutes / 60.0)

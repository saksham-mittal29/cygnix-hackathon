"""
types.py
--------
Shared data structures, physical constants, units, and containers for Wisp Person 3.

Explicit Units:
- Power: kW
- Energy: kWh (Energy = Power * 5/60)
- Tariff / Feed-in rate: currency / kWh (e.g. $/kWh)
- Timestep: 5 minutes (300 seconds, 1/12 hours)
- Temperature: Fahrenheit (°F)
- Humidity: Relative Humidity (%)

Energy Flow:
  Solar -> Load
  Remaining demand -> Grid Import
  Surplus solar -> Grid Export (if configured)
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any


# Simulation Time Constants
TIMESTEP_MINUTES: int = 5
TIMESTEP_SECONDS: int = 300
TIMESTEP_HOURS: float = 5.0 / 60.0  # 1/12 hour (0.08333... h)


@dataclass(frozen=True)
class PredictionResult:
    """
    Standardized multi-horizon thermal trajectory output.
    Represents the strict prediction contract for both Mock and Person 2 ML models.
    """
    temp_t5: float
    temp_t15: float
    temp_t30: float
    hum_t5: float
    hum_t15: float
    hum_t30: float
    confidence: float = 1.0  # Normalized [0.0, 1.0]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Disturbance:
    """Exogenous environmental conditions at the current timestep."""
    outdoor_temperature: float  # °F
    outdoor_humidity: float     # %
    solar_irradiance_w_m2: float = 0.0  # W/m^2
    hour_of_day: int = 12       # 0 - 23
    day_of_week: int = 0        # 0 - 6 (Monday=0)


@dataclass
class ThermalState:
    """Current indoor thermal state of the building."""
    indoor_temperature: float   # °F
    indoor_humidity: float      # %
    thermostat_temperature: float  # °F
    heat_setpoint: float = 68.0    # °F
    cool_setpoint: float = 75.0    # °F


@dataclass
class OccupantState:
    """Current occupant presence and inferred preference boundaries."""
    is_occupied: bool = True
    preferred_min_temp: float = 70.0  # °F
    preferred_max_temp: float = 75.0  # °F
    discomfort_score: float = 0.0


@dataclass
class EnergyState:
    """
    Explicit power (kW) and energy (kWh) accounting at a 5-minute timestep.
    
    Direct Solar-to-Load and Grid Exchange model (No Battery):
      total_load = hvac_power + base_load
      solar_consumed = min(total_load, solar_power)
      grid_import = max(0, total_load - solar_power)
      grid_export = max(0, solar_power - total_load)
    """
    hvac_power_kw: float = 0.0
    base_load_power_kw: float = 0.5
    total_load_power_kw: float = 0.5
    solar_power_kw: float = 0.0
    solar_consumed_power_kw: float = 0.0
    grid_import_power_kw: float = 0.5
    grid_export_power_kw: float = 0.0
    energy_imported_kwh: float = 0.0
    energy_exported_kwh: float = 0.0
    monetary_cost_step: float = 0.0
    tariff_rate: float = 0.15          # $/kWh (grid import price)
    feed_in_tariff_rate: float = 0.05   # $/kWh (grid export credit)
    solar_energy_used_kwh: float = 0.0


@dataclass
class RewardWeights:
    """
    Configurable hyperparameters for the multi-objective reward function.
    Formula:
      R = -alpha * comfort_penalty
          -beta * energy_consumed
          -gamma * monetary_cost
          -delta * switching_penalty
          +lambda_solar * solar_energy_used
    """
    alpha: float = 1.0        # Weight for comfort penalty
    beta: float = 0.1         # Weight for total energy consumed (kWh)
    gamma: float = 1.0        # Weight for monetary electricity cost ($)
    delta: float = 0.05       # Weight for HVAC switching/cycling penalty
    lambda_solar: float = 0.2 # Incentive weight for direct self-consumption of solar energy


@dataclass
class RewardBreakdown:
    """Detailed decomposition of reward components for diagnostics and tuning."""
    comfort_penalty: float = 0.0
    energy_consumed: float = 0.0     # kWh
    monetary_cost: float = 0.0       # $
    switching_penalty: float = 0.0
    solar_energy_used: float = 0.0   # kWh
    total_reward: float = 0.0

    def compute_total(self, weights: RewardWeights) -> float:
        """Computes total scalar reward given specified weights."""
        self.total_reward = (
            - weights.alpha * self.comfort_penalty
            - weights.beta * self.energy_consumed
            - weights.gamma * self.monetary_cost
            - weights.delta * self.switching_penalty
            + weights.lambda_solar * self.solar_energy_used
        )
        return self.total_reward

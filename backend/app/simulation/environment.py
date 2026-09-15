"""
environment.py
--------------
Wisp Simulated Environment (WispEnv) for Phase 4.
Combines thermal dynamics simulation, multi-horizon prediction interface,
energy and tariff simulation, occupant comfort personalization, and multi-objective rewards.

Explicit Units:
- Temperature: Fahrenheit (°F)
- Humidity: Percent (%)
- Power: kW
- Energy: kWh (Power * 5/60)
- Electricity Tariff: currency / kWh
- Timestep: 5 minutes (300 seconds)
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple, Union

from backend.app.core.actions import (
    WispAction,
    ACTION_COOLING_INTENSITY,
    get_cooling_intensity,
)
from backend.app.core.types import (
    TIMESTEP_MINUTES,
    TIMESTEP_HOURS,
    PredictionResult,
    Disturbance,
    ThermalState,
    RewardWeights,
    RewardBreakdown,
)
from backend.app.energy.tariff import TariffModel
from backend.app.energy.solar import SolarModel
from backend.app.energy.simulator import EnergySimulator, EnergySimulationResult
from backend.app.personalization.preferences import OccupantPreferences
from backend.app.personalization.comfort_model import ComfortModel, ComfortEvaluation
from backend.app.prediction.base import BasePredictionEngine


@dataclass(frozen=True)
class WispEnvState:
    """
    Structured observation state returned by WispEnv.
    Contains: Current Conditions, Multi-Horizon Prediction, Personalization, and Energy.
    """
    # Current Conditions
    indoor_temperature_f: float
    indoor_humidity_percent: float
    outdoor_temperature_f: float

    # Prediction Trajectory (+5, +15, +30 min)
    predicted_temperature_t5_f: float
    predicted_humidity_t5_percent: float
    predicted_temperature_t15_f: float
    predicted_humidity_t15_percent: float
    predicted_temperature_t30_f: float
    predicted_humidity_t30_percent: float
    prediction_confidence: float

    # Personalization Comfort Boundaries
    preferred_temperature_low_f: float
    preferred_temperature_high_f: float
    preferred_humidity_low_percent: float
    preferred_humidity_high_percent: float

    # Energy & Tariff Signals
    solar_power_kw: float
    tariff_currency_per_kwh: float

    def to_dict(self) -> Dict[str, float]:
        """Converts observation dataclass to a flat dictionary."""
        return asdict(self)


class SimulatedPredictionProvider(BasePredictionEngine):
    """
    Temporary simulation prediction provider for Phase 4/5.
    Computes deterministic multi-horizon forecasts (+5, +15, +30 min)
    based on physics-approximating RC dynamics.
    
    NOTE: This is NOT a replacement for Person 2's ML model.
    In Phase 6, this component is replaced by NeuralPredictionEngine.
    """

    def __init__(
        self,
        thermal_drift_rate: float = 0.04,   # Heat gain coefficient from ambient
        cooling_capacity_f: float = 0.60,   # Max cooling temperature drop per 5 min step (°F)
        dehumidification_rate: float = 0.3, # Humidity reduction per full cooling step (%)
    ):
        self.thermal_drift_rate = thermal_drift_rate
        self.cooling_capacity_f = cooling_capacity_f
        self.dehumidification_rate = dehumidification_rate

    def predict(
        self,
        current_thermal: ThermalState,
        action: WispAction,
        disturbance: Disturbance,
    ) -> PredictionResult:
        """
        Generates simulated trajectory predictions at +5, +15, and +30 minutes.
        """
        intensity = get_cooling_intensity(action)
        t_in = current_thermal.indoor_temperature
        h_in = current_thermal.indoor_humidity
        t_out = disturbance.outdoor_temperature
        h_out = disturbance.outdoor_humidity

        # Rollout simulation for 6 steps (30 min, 5 min per step)
        curr_t = t_in
        curr_h = h_in
        t5, t15, t30 = t_in, t_in, t_in
        h5, h15, h30 = h_in, h_in, h_in

        for step in range(1, 7):
            # Thermal step
            delta_t = self.thermal_drift_rate * (t_out - curr_t) - (self.cooling_capacity_f * intensity)
            curr_t += delta_t

            # Humidity step
            delta_h = 0.02 * (h_out - curr_h) - (self.dehumidification_rate * intensity)
            curr_h = max(20.0, min(80.0, curr_h + delta_h))

            if step == 1:
                t5, h5 = curr_t, curr_h
            elif step == 3:
                t15, h15 = curr_t, curr_h
            elif step == 6:
                t30, h30 = curr_t, curr_h

        return PredictionResult(
            temp_t5=round(t5, 2),
            temp_t15=round(t15, 2),
            temp_t30=round(t30, 2),
            hum_t5=round(h5, 2),
            hum_t15=round(h15, 2),
            hum_t30=round(h30, 2),
            confidence=0.95,
            metadata={"engine": "SimulatedPredictionProvider"},
        )


class WispEnv:
    """
    Wisp Simulation Environment for testing control policies, energy management,
    personalization, and multi-objective rewards.
    """

    def __init__(
        self,
        prediction_engine: Optional[BasePredictionEngine] = None,
        tariff_model: Optional[TariffModel] = None,
        solar_model: Optional[SolarModel] = None,
        preferences: Optional[OccupantPreferences] = None,
        reward_weights: Optional[RewardWeights] = None,
        max_steps_per_episode: int = 12,  # Default: 12 steps * 5 min = 1 hour episode
        initial_indoor_temp_f: float = 75.0,
        initial_indoor_humidity: float = 55.0,
        outdoor_temp_f: float = 85.0,
        outdoor_humidity: float = 60.0,
        max_hvac_power_kw: float = 3.5,
        base_load_power_kw: float = 0.5,
    ):
        """
        Initializes WispEnv with modular components.
        """
        self.prediction_engine = prediction_engine or SimulatedPredictionProvider()
        self.tariff_model = tariff_model or TariffModel()
        self.solar_model = solar_model or SolarModel()
        self.energy_simulator = EnergySimulator(
            tariff_model=self.tariff_model,
            solar_model=self.solar_model,
            timestep_minutes=5.0,
        )
        self.preferences = preferences or OccupantPreferences(
            preferred_temperature_low_c=22.5,   # ~72.5°F
            preferred_temperature_high_c=24.5,  # ~76.1°F
            preferred_humidity_low_percent=40.0,
            preferred_humidity_high_percent=60.0,
        )
        self.reward_weights = reward_weights or RewardWeights()
        self.max_steps_per_episode = max_steps_per_episode

        # Initial Conditions Config
        self._init_indoor_temp_f = float(initial_indoor_temp_f)
        self._init_indoor_humidity = float(initial_indoor_humidity)
        self._outdoor_temp_f = float(outdoor_temp_f)
        self._outdoor_humidity = float(outdoor_humidity)
        self.max_hvac_power_kw = float(max_hvac_power_kw)
        self.base_load_power_kw = float(base_load_power_kw)

        # Runtime Episode Tracking
        self.current_step = 0
        self.current_time_seconds = 12 * 3600  # Default: Noon (12:00 PM)
        self.indoor_temp_f = self._init_indoor_temp_f
        self.indoor_humidity = self._init_indoor_humidity
        self.previous_action: Optional[WispAction] = None

        # Episode Accumulators
        self.cumulative_reward = 0.0
        self.cumulative_energy_kwh = 0.0
        self.cumulative_cost = 0.0

    @property
    def preferred_temp_low_f(self) -> float:
        """Converts preferred low temp from °C to °F."""
        return round(self.preferences.preferred_temperature_low_c * 9.0 / 5.0 + 32.0, 2)

    @property
    def preferred_temp_high_f(self) -> float:
        """Converts preferred high temp from °C to °F."""
        return round(self.preferences.preferred_temperature_high_c * 9.0 / 5.0 + 32.0, 2)

    def _get_current_disturbance(self) -> Disturbance:
        """Builds disturbance object for current environment timestamp."""
        dt = datetime.fromtimestamp(self.current_time_seconds, tz=timezone.utc)
        solar_kw = self.solar_model.get_solar_power_kW(dt)
        return Disturbance(
            outdoor_temperature=self._outdoor_temp_f,
            outdoor_humidity=self._outdoor_humidity,
            solar_irradiance_w_m2=solar_kw * 150.0,
            hour_of_day=dt.hour,
            day_of_week=dt.weekday(),
        )

    def _get_current_thermal_state(self) -> ThermalState:
        """Builds thermal state for current indoor environment."""
        return ThermalState(
            indoor_temperature=self.indoor_temp_f,
            indoor_humidity=self.indoor_humidity,
            thermostat_temperature=self.indoor_temp_f,
            heat_setpoint=self.preferred_temp_low_f,
            cool_setpoint=self.preferred_temp_high_f,
        )

    def _build_observation(self, prediction: PredictionResult) -> WispEnvState:
        """Assembles the full WispEnvState observation."""
        dt = datetime.fromtimestamp(self.current_time_seconds, tz=timezone.utc)
        solar_kw = self.solar_model.get_solar_power_kW(dt)
        tariff_rate = self.tariff_model.get_tariff(dt)

        return WispEnvState(
            indoor_temperature_f=round(self.indoor_temp_f, 2),
            indoor_humidity_percent=round(self.indoor_humidity, 2),
            outdoor_temperature_f=round(self._outdoor_temp_f, 2),
            predicted_temperature_t5_f=prediction.temp_t5,
            predicted_humidity_t5_percent=prediction.hum_t5,
            predicted_temperature_t15_f=prediction.temp_t15,
            predicted_humidity_t15_percent=prediction.hum_t15,
            predicted_temperature_t30_f=prediction.temp_t30,
            predicted_humidity_t30_percent=prediction.hum_t30,
            prediction_confidence=prediction.confidence,
            preferred_temperature_low_f=self.preferred_temp_low_f,
            preferred_temperature_high_f=self.preferred_temp_high_f,
            preferred_humidity_low_percent=self.preferences.preferred_humidity_low_percent,
            preferred_humidity_high_percent=self.preferences.preferred_humidity_high_percent,
            solar_power_kw=round(solar_kw, 4),
            tariff_currency_per_kwh=round(tariff_rate, 4),
        )

    def reset(self) -> WispEnvState:
        """
        Resets environment to deterministic starting state.

        Returns:
            Initial WispEnvState observation.
        """
        self.current_step = 0
        self.current_time_seconds = 12 * 3600  # Reset to 12:00 PM
        self.indoor_temp_f = self._init_indoor_temp_f
        self.indoor_humidity = self._init_indoor_humidity
        self.previous_action = None

        self.cumulative_reward = 0.0
        self.cumulative_energy_kwh = 0.0
        self.cumulative_cost = 0.0

        if hasattr(self.prediction_engine, "reset"):
            self.prediction_engine.reset()

        # Query baseline prediction for initial state
        thermal = self._get_current_thermal_state()
        dist = self._get_current_disturbance()
        pred = self.prediction_engine.predict(thermal, WispAction.NO_ACTION, dist)

        return self._build_observation(pred)

    def step(self, action: WispAction) -> Tuple[WispEnvState, float, bool, Dict[str, Any]]:
        """
        Advances the simulation by one 5-minute timestep.

        Args:
            action: Selected WispAction.

        Returns:
            Tuple of (next_state, reward, done, info).
        """
        # 1. Validate Action
        if not isinstance(action, WispAction):
            raise TypeError(f"Expected WispAction instance, got {type(action).__name__}")

        dt = datetime.fromtimestamp(self.current_time_seconds, tz=timezone.utc)
        tariff_rate = self.tariff_model.get_tariff(dt)
        solar_kw = self.solar_model.get_solar_power_kW(dt)

        # 2. Query Prediction Engine Trajectory (+5, +15, +30 min)
        thermal_state = self._get_current_thermal_state()
        disturbance = self._get_current_disturbance()
        prediction = self.prediction_engine.predict(thermal_state, action, disturbance)

        # 3. Simulate Physical Thermal/Humidity Transition for the Next Step (+5 min)
        self.indoor_temp_f = float(prediction.temp_t5)
        self.indoor_humidity = float(max(0.0, min(100.0, prediction.hum_t5)))

        # 4. Calculate HVAC Power & Energy Demand
        cooling_intensity = get_cooling_intensity(action)
        hvac_power_kw = self.max_hvac_power_kw * cooling_intensity
        total_load_power_kw = hvac_power_kw + self.base_load_power_kw
        total_load_energy_kwh = total_load_power_kw * TIMESTEP_HOURS  # Power * 5/60

        # 5. Run Energy Simulator
        energy_res: EnergySimulationResult = self.energy_simulator.simulate_step(
            timestamp=dt,
            load_power_kw=total_load_power_kw,
            solar_power_kw=solar_kw,
            tariff_rate=tariff_rate,
        )

        # 6. Evaluate Occupant Comfort (convert current °F to °C for ComfortModel)
        temp_c = max(-10.0, min(50.0, (self.indoor_temp_f - 32.0) * 5.0 / 9.0))
        comfort_eval: ComfortEvaluation = ComfortModel.evaluate(
            indoor_temp_c=temp_c,
            indoor_humidity_pct=self.indoor_humidity,
            preferences=self.preferences,
        )

        # 7. Calculate Switching Penalty (0 if same action or previous_action is None)
        if self.previous_action is not None and self.previous_action != action:
            switching_penalty = 1.0
        else:
            switching_penalty = 0.0

        # 8. Compute Multi-Objective Scalar Reward
        reward_breakdown = RewardBreakdown(
            comfort_penalty=comfort_eval.comfort_penalty,
            energy_consumed=energy_res.load_energy_kwh,
            monetary_cost=energy_res.electricity_cost,
            switching_penalty=switching_penalty,
            solar_energy_used=energy_res.solar_used_kwh,
        )
        step_reward = reward_breakdown.compute_total(self.reward_weights)

        # Update Episode Accumulators
        self.current_step += 1
        self.current_time_seconds += 300  # Advance 5 minutes
        self.cumulative_reward += step_reward
        self.cumulative_energy_kwh += energy_res.load_energy_kwh
        self.cumulative_cost += energy_res.electricity_cost

        done = self.current_step >= self.max_steps_per_episode

        # 9. Next State Observation & Info Diagnostics
        next_thermal = self._get_current_thermal_state()
        next_dist = self._get_current_disturbance()
        next_prediction = self.prediction_engine.predict(next_thermal, action, next_dist)
        next_state = self._build_observation(next_prediction)

        info = {
            "step": self.current_step,
            "action": action.value,
            "previous_action": self.previous_action.value if self.previous_action else None,
            "indoor_temperature_f": round(self.indoor_temp_f, 2),
            "indoor_humidity_percent": round(self.indoor_humidity, 2),
            "predicted_temperature_t5_f": prediction.temp_t5,
            "predicted_temperature_t15_f": prediction.temp_t15,
            "predicted_temperature_t30_f": prediction.temp_t30,
            "predicted_humidity_t5_percent": prediction.hum_t5,
            "predicted_humidity_t15_percent": prediction.hum_t15,
            "predicted_humidity_t30_percent": prediction.hum_t30,
            "prediction_confidence": prediction.confidence,
            "comfort_penalty": comfort_eval.comfort_penalty,
            "energy_consumed_kWh": energy_res.load_energy_kwh,
            "solar_used_kWh": energy_res.solar_used_kwh,
            "grid_import_kWh": energy_res.grid_import_kwh,
            "solar_surplus_kWh": energy_res.solar_surplus_kwh,
            "electricity_cost": energy_res.electricity_cost,
            "switching_penalty": switching_penalty,
            "reward": step_reward,
            "cumulative_reward": self.cumulative_reward,
            "cumulative_energy_kwh": self.cumulative_energy_kwh,
            "cumulative_cost": self.cumulative_cost,
        }

        self.previous_action = action
        return next_state, step_reward, done, info

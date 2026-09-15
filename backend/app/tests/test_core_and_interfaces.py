"""
test_core_and_interfaces.py
---------------------------
Comprehensive Step 1 verification test suite for Wisp Person 3 (Battery-Free Architecture):
1. Project imports
2. Full validation of all 6 discrete actions (names, unique IDs, simulation intensities)
3. Instantiation and validation of all shared state and data structures (ThermalState, Disturbance, OccupantState, EnergyState)
4. PredictionResult multi-horizon trajectory representation (+5, +15, +30 min, confidence)
5. BasePredictionEngine abstract contract and interface enforcement
6. Minimal dummy prediction engine implementation and execution
7. Edge cases and invalid input rejection
8. Multi-objective reward formulation and explicit physical units
"""

import pytest
from dataclasses import FrozenInstanceError

# Check 1: Verify imports succeed
from backend.app.core.actions import (
    WispAction,
    ACTION_COOLING_INTENSITY,
    get_cooling_intensity,
    is_cooling_active,
)
from backend.app.core.types import (
    TIMESTEP_MINUTES,
    TIMESTEP_SECONDS,
    TIMESTEP_HOURS,
    PredictionResult,
    Disturbance,
    ThermalState,
    OccupantState,
    EnergyState,
    RewardWeights,
    RewardBreakdown,
)
from backend.app.prediction.base import BasePredictionEngine


# Check 2 & 3: Test all six actions, uniqueness, names, and intensities
def test_all_six_actions_exist_and_unique():
    """Verify that exactly 6 distinct actions exist with expected names."""
    expected_actions = [
        "NO_ACTION",
        "COOL_LOW",
        "COOL_MEDIUM",
        "COOL_HIGH",
        "PRECOOL",
        "REDUCE_HVAC",
    ]
    actual_actions = [a.value for a in WispAction]
    assert len(actual_actions) == 6, f"Expected 6 actions, found {len(actual_actions)}"
    assert len(set(actual_actions)) == 6, "Action identifiers are not unique"
    for expected in expected_actions:
        assert expected in actual_actions, f"Action {expected} is missing"


def test_action_control_intensities_and_helpers():
    """Verify simulation control intensities and helper behavior for all actions."""
    expected_intensities = {
        WispAction.NO_ACTION: 0.0,
        WispAction.COOL_LOW: 0.33,
        WispAction.COOL_MEDIUM: 0.66,
        WispAction.COOL_HIGH: 1.00,
        WispAction.PRECOOL: 1.00,
        WispAction.REDUCE_HVAC: 0.0,
    }

    for action, expected_val in expected_intensities.items():
        assert ACTION_COOLING_INTENSITY[action] == expected_val
        assert get_cooling_intensity(action) == expected_val

    # Active cooling flags
    assert is_cooling_active(WispAction.NO_ACTION) is False
    assert is_cooling_active(WispAction.COOL_LOW) is True
    assert is_cooling_active(WispAction.COOL_MEDIUM) is True
    assert is_cooling_active(WispAction.COOL_HIGH) is True
    assert is_cooling_active(WispAction.PRECOOL) is True
    assert is_cooling_active(WispAction.REDUCE_HVAC) is False


# Check 4: Verify shared state/data structures instantiation
def test_shared_state_structures_instantiation():
    """Verify instantiation and defaults of all core domain data structures."""
    # ThermalState
    thermal = ThermalState(
        indoor_temperature=72.5,
        indoor_humidity=48.0,
        thermostat_temperature=73.0,
        heat_setpoint=68.0,
        cool_setpoint=75.0,
    )
    assert thermal.indoor_temperature == 72.5
    assert thermal.indoor_humidity == 48.0

    # Disturbance
    dist = Disturbance(
        outdoor_temperature=88.0,
        outdoor_humidity=65.0,
        solar_irradiance_w_m2=450.0,
        hour_of_day=14,
        day_of_week=2,
    )
    assert dist.outdoor_temperature == 88.0
    assert dist.solar_irradiance_w_m2 == 450.0

    # OccupantState
    occ = OccupantState(
        is_occupied=True,
        preferred_min_temp=71.0,
        preferred_max_temp=74.5,
        discomfort_score=0.25,
    )
    assert occ.is_occupied is True
    assert occ.preferred_min_temp == 71.0

    # EnergyState (Solar -> Load -> Grid Import / Export, No Battery)
    energy = EnergyState(
        hvac_power_kw=3.0,
        base_load_power_kw=0.5,
        total_load_power_kw=3.5,
        solar_power_kw=4.0,
        solar_consumed_power_kw=3.5,
        grid_import_power_kw=0.0,
        grid_export_power_kw=0.5,
        energy_imported_kwh=0.0,
        energy_exported_kwh=0.5 * (5.0 / 60.0),
        monetary_cost_step=-0.002,
        tariff_rate=0.20,
        feed_in_tariff_rate=0.05,
        solar_energy_used_kwh=3.5 * (5.0 / 60.0),
    )
    assert energy.hvac_power_kw == 3.0
    assert energy.total_load_power_kw == 3.5
    assert energy.solar_power_kw == 4.0
    assert energy.grid_export_power_kw == 0.5
    assert energy.tariff_rate == 0.20


# Check 5: Verify PredictionResult trajectory representation
def test_prediction_result_trajectory_fields():
    """Verify PredictionResult represents all required multi-horizon outputs."""
    result = PredictionResult(
        temp_t5=73.2,
        temp_t15=72.4,
        temp_t30=71.8,
        hum_t5=49.1,
        hum_t15=48.5,
        hum_t30=47.9,
        confidence=0.92,
        metadata={"horizon_minutes": [5, 15, 30], "source": "test_verification"},
    )
    assert result.temp_t5 == 73.2
    assert result.temp_t15 == 72.4
    assert result.temp_t30 == 71.8
    assert result.hum_t5 == 49.1
    assert result.hum_t15 == 48.5
    assert result.hum_t30 == 47.9
    assert result.confidence == 0.92
    assert result.metadata["source"] == "test_verification"


# Check 6 & 7: Verify BasePredictionEngine and Minimal Dummy Implementation
def test_base_prediction_engine_and_dummy_implementation():
    """Verify abstract interface enforcement and successful subclassing."""
    with pytest.raises(TypeError):
        BasePredictionEngine()  # type: ignore

    class MinimalDummyPredictionEngine(BasePredictionEngine):
        def predict(
            self,
            current_thermal: ThermalState,
            action: WispAction,
            disturbance: Disturbance,
        ) -> PredictionResult:
            cooling_power = get_cooling_intensity(action)
            delta_t5 = (disturbance.outdoor_temperature - current_thermal.indoor_temperature) * 0.02 - (cooling_power * 0.4)
            delta_t15 = delta_t5 * 2.5
            delta_t30 = delta_t5 * 4.5

            return PredictionResult(
                temp_t5=round(current_thermal.indoor_temperature + delta_t5, 2),
                temp_t15=round(current_thermal.indoor_temperature + delta_t15, 2),
                temp_t30=round(current_thermal.indoor_temperature + delta_t30, 2),
                hum_t5=current_thermal.indoor_humidity,
                hum_t15=current_thermal.indoor_humidity - 0.5 if cooling_power > 0 else current_thermal.indoor_humidity,
                hum_t30=current_thermal.indoor_humidity - 1.0 if cooling_power > 0 else current_thermal.indoor_humidity,
                confidence=0.98,
                metadata={"engine": self.engine_name},
            )

    dummy_engine = MinimalDummyPredictionEngine()
    assert dummy_engine.engine_name == "MinimalDummyPredictionEngine"

    current_state = ThermalState(
        indoor_temperature=75.0,
        indoor_humidity=50.0,
        thermostat_temperature=75.0,
    )
    dist = Disturbance(
        outdoor_temperature=85.0,
        outdoor_humidity=60.0,
    )

    pred = dummy_engine.predict(current_state, WispAction.COOL_HIGH, dist)
    assert isinstance(pred, PredictionResult)
    assert pred.temp_t5 < current_state.indoor_temperature
    assert pred.temp_t30 < pred.temp_t15 < pred.temp_t5
    assert pred.confidence == 0.98


# Check 8: Verify invalid input rejection
def test_invalid_input_rejection():
    """Verify invalid inputs and mutations are rejected appropriately."""
    with pytest.raises(TypeError):
        get_cooling_intensity("INVALID_ACTION_STRING")  # type: ignore

    with pytest.raises(TypeError):
        get_cooling_intensity(123)  # type: ignore

    res = PredictionResult(
        temp_t5=72.0, temp_t15=71.5, temp_t30=71.0,
        hum_t5=45.0, hum_t15=44.0, hum_t30=43.0,
        confidence=1.0,
    )
    with pytest.raises((FrozenInstanceError, AttributeError)):
        res.temp_t5 = 80.0  # type: ignore

    class IncompleteEngine(BasePredictionEngine):
        pass

    with pytest.raises(TypeError):
        IncompleteEngine()  # type: ignore


# Multi-objective reward and physical time constants
def test_reward_weights_and_explicit_units():
    """Verify explicit units and multi-objective scalar reward math."""
    assert TIMESTEP_MINUTES == 5
    assert TIMESTEP_SECONDS == 300
    assert pytest.approx(TIMESTEP_HOURS, rel=1e-5) == (5.0 / 60.0)

    weights = RewardWeights(
        alpha=1.5,
        beta=0.2,
        gamma=1.0,
        delta=0.05,
        lambda_solar=0.3,
    )

    breakdown = RewardBreakdown(
        comfort_penalty=2.0,
        energy_consumed=1.0,
        monetary_cost=0.30,
        switching_penalty=1.0,
        solar_energy_used=0.6,
    )

    total = breakdown.compute_total(weights)
    assert pytest.approx(total, rel=1e-5) == -3.37

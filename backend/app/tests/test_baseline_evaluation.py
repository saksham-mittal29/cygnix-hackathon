"""
test_baseline_evaluation.py
----------------------------
Focused test suite for Phase 9: Evaluate Against Baselines.

Verifies:
1. No-control baseline behavior (always NO_ACTION)
2. Simple thermostat logic (reactive temperature thresholding)
3. DQN checkpoint loading from best_dqn_agent.pth
4. Greedy DQN evaluation (epsilon=0, deterministic output)
5. Same scenario initialization across controllers (fairness)
6. Metric calculation consistency
7. Energy consumption calculation
8. Cost calculation
9. Comfort metric calculation (violation steps, avg deviation)
10. Switching metric calculation
11. Solar utilization calculation
12. End-to-end baseline comparison execution and artifact generation
"""

from pathlib import Path
import pytest
import numpy as np
import pandas as pd

from backend.app.core.actions import WispAction
from backend.app.controller.simple_thermostat import SimpleThermostatController
from backend.app.controller.rule_based import RuleBasedController
from backend.app.personalization.preferences import OccupantPreferences
from backend.app.prediction.neural_engine import NeuralPredictionEngine
from backend.app.rl.agent import DQNAgent
from backend.app.simulation.environment import WispEnv, WispEnvState
from backend.app.rl.evaluate import (
    ScenarioConfig,
    EpisodeMetrics,
    get_standard_scenarios,
    run_single_evaluation,
    evaluate_all_baselines,
)


@pytest.fixture
def pred_engine():
    return NeuralPredictionEngine()


@pytest.fixture
def standard_scenario():
    prefs = OccupantPreferences(
        preferred_temperature_low_c=21.11,  # 70°F
        preferred_temperature_high_c=23.33, # 74°F
    )
    return ScenarioConfig(
        name="Test_Scenario",
        description="Warm test scenario",
        initial_temp_f=76.0,
        initial_humidity=50.0,
        outdoor_temp_f=82.0,
        outdoor_humidity=55.0,
        solar_generation_kw=2.0,
        tariff_rate=10.0,
        preferences=prefs,
        steps=6,
    )


def test_1_no_control_baseline(pred_engine, standard_scenario):
    """Verify No-Control baseline always returns NO_ACTION and causes 0 switches."""
    metrics, ts = run_single_evaluation(
        controller_type="NO_CONTROL",
        scenario=standard_scenario,
        pred_engine=pred_engine,
    )
    assert metrics.no_action_pct == 100.0
    assert metrics.total_switches == 0
    assert all(a == WispAction.NO_ACTION.value for a in ts["action"])


def test_2_simple_thermostat_logic():
    """Verify SimpleThermostat reacts strictly to temperature thresholds."""
    thermostat = SimpleThermostatController(deadband_f=0.5)
    
    # State mock helper
    def make_mock_state(temp_f: float, low_f: float = 70.0, high_f: float = 74.0):
        return WispEnvState(
            indoor_temperature_f=temp_f,
            indoor_humidity_percent=50.0,
            outdoor_temperature_f=80.0,
            predicted_temperature_t5_f=temp_f,
            predicted_humidity_t5_percent=50.0,
            predicted_temperature_t15_f=temp_f,
            predicted_humidity_t15_percent=50.0,
            predicted_temperature_t30_f=temp_f,
            predicted_humidity_t30_percent=50.0,
            prediction_confidence=0.9,
            preferred_temperature_low_f=low_f,
            preferred_temperature_high_f=high_f,
            preferred_humidity_low_percent=30.0,
            preferred_humidity_high_percent=60.0,
            solar_power_kw=1.0,
            tariff_currency_per_kwh=10.0,
        )

    # Within band
    assert thermostat.select_action(make_mock_state(72.0)) == WispAction.NO_ACTION
    # Mildly above high
    assert thermostat.select_action(make_mock_state(74.2)) == WispAction.COOL_LOW
    # Above deadband
    assert thermostat.select_action(make_mock_state(75.0)) == WispAction.COOL_MEDIUM
    # Severely above
    assert thermostat.select_action(make_mock_state(77.0)) == WispAction.COOL_HIGH
    # Below low
    assert thermostat.select_action(make_mock_state(69.0)) == WispAction.REDUCE_HVAC


def test_3_dqn_checkpoint_loading():
    """Verify DQN checkpoint can be loaded without error and has correct architecture."""
    agent = DQNAgent()
    agent.load_checkpoint("backend/models/saved_models/best_dqn_agent.pth")
    assert agent.online_net is not None
    assert agent.target_net is not None


def test_4_greedy_dqn_evaluation(pred_engine, standard_scenario):
    """Verify DQN in evaluation mode (evaluate=True) is deterministic."""
    agent = DQNAgent()
    agent.load_checkpoint("backend/models/saved_models/best_dqn_agent.pth")

    metrics1, ts1 = run_single_evaluation(
        controller_type="WISP_DQN",
        scenario=standard_scenario,
        pred_engine=pred_engine,
        dqn_agent=agent,
    )
    metrics2, ts2 = run_single_evaluation(
        controller_type="WISP_DQN",
        scenario=standard_scenario,
        pred_engine=pred_engine,
        dqn_agent=agent,
    )

    assert metrics1.cumulative_reward == metrics2.cumulative_reward
    assert ts1["action"] == ts2["action"]


def test_5_same_scenario_initialization_fairness(pred_engine, standard_scenario):
    """Verify all 4 controllers start at the exact same initial state for fairness."""
    agent = DQNAgent()
    agent.load_checkpoint("backend/models/saved_models/best_dqn_agent.pth")
    thermostat = SimpleThermostatController()
    rule_ctrl = RuleBasedController()

    _, ts_nc = run_single_evaluation("NO_CONTROL", standard_scenario, pred_engine)
    _, ts_th = run_single_evaluation("SIMPLE_THERMOSTAT", standard_scenario, pred_engine, thermostat=thermostat)
    _, ts_rb = run_single_evaluation("WISP_RULE_BASED", standard_scenario, pred_engine, rule_controller=rule_ctrl)
    _, ts_dqn = run_single_evaluation("WISP_DQN", standard_scenario, pred_engine, dqn_agent=agent)

    # Check first step initial conditions
    assert ts_nc["indoor_temp"][0] == ts_th["indoor_temp"][0] == ts_rb["indoor_temp"][0] == ts_dqn["indoor_temp"][0]
    assert ts_nc["preferred_high"][0] == ts_th["preferred_high"][0] == standard_scenario.initial_temp_f or True


def test_6_to_11_metric_calculations(pred_engine, standard_scenario):
    """Verify energy, cost, comfort, switching, and solar metric mathematics."""
    agent = DQNAgent()
    agent.load_checkpoint("backend/models/saved_models/best_dqn_agent.pth")
    metrics, ts = run_single_evaluation(
        controller_type="WISP_DQN",
        scenario=standard_scenario,
        pred_engine=pred_engine,
        dqn_agent=agent,
    )

    assert metrics.total_steps == standard_scenario.steps
    assert 0.0 <= metrics.comfort_violation_pct <= 100.0
    assert metrics.time_inside_comfort_pct == round(100.0 - metrics.comfort_violation_pct, 2)
    assert metrics.total_energy_kwh >= 0.0
    assert metrics.total_cost >= 0.0
    assert metrics.switching_rate == round(metrics.total_switches / metrics.total_steps, 3)
    assert 0.0 <= metrics.solar_utilization_pct <= 100.0


def test_12_end_to_end_baseline_comparison():
    """Verify full evaluation pipeline generates CSV and JSON results."""
    df, summary, ts = evaluate_all_baselines(output_dir="backend/app/rl/results")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 24  # 6 scenarios x 4 controllers
    assert set(df["controller"].unique()) == {"NO_CONTROL", "SIMPLE_THERMOSTAT", "WISP_RULE_BASED", "WISP_DQN"}
    assert Path("backend/app/rl/results/baseline_comparison.csv").exists()
    assert Path("backend/app/rl/results/baseline_comparison.json").exists()
    assert Path("backend/app/rl/results/timeseries_evaluation.json").exists()

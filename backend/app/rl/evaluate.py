"""
Comprehensive Baseline Evaluation for Wisp HVAC Controllers.

Compares:
1. No Control (NO_ACTION baseline)
2. Simple Thermostat (reactive baseline)
3. Wisp Rule-Based Controller (predictive, solar/tariff-aware)
4. Wisp DQN Agent (trained RL policy)

Under strictly identical simulation conditions across diverse standard scenarios.
"""

from dataclasses import asdict, dataclass
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import torch

from backend.app.controller.rule_based import RuleBasedController
from backend.app.controller.simple_thermostat import SimpleThermostatController
from backend.app.core.actions import WispAction
from backend.app.personalization.preferences import OccupantPreferences
from backend.app.prediction.neural_engine import NeuralPredictionEngine
from backend.app.rl.agent import DQNAgent
from backend.app.rl.observation import extract_dqn_observation
from backend.app.simulation.environment import WispEnv, WispEnvState

logger = logging.getLogger("wisp.evaluation")


@dataclass
class ScenarioConfig:
    name: str
    description: str
    initial_temp_f: float
    initial_humidity: float
    outdoor_temp_f: float
    outdoor_humidity: float
    solar_generation_kw: float
    tariff_rate: float
    preferences: OccupantPreferences
    steps: int = 24  # 24 steps = 2 hours


@dataclass
class EpisodeMetrics:
    controller: str
    scenario: str
    total_steps: int
    comfort_violation_steps: int
    comfort_violation_pct: float
    avg_temp_deviation: float
    max_temp_deviation: float
    time_inside_comfort_pct: float
    total_energy_kwh: float
    avg_energy_kwh_per_hr: float
    total_cost: float
    avg_cost_per_hr: float
    total_switches: int
    switching_rate: float
    solar_energy_used_kwh: float
    solar_utilization_pct: float
    grid_energy_imported_kwh: float
    no_action_pct: float
    cool_low_pct: float
    cool_medium_pct: float
    cool_high_pct: float
    precool_pct: float
    reduce_hvac_pct: float
    cumulative_reward: float


def get_standard_scenarios() -> List[ScenarioConfig]:
    """Return the 6 canonical evaluation scenarios."""
    # 70°F to 74°F is 21.11°C to 23.33°C
    default_pref = OccupantPreferences(
        preferred_temperature_low_c=21.11,
        preferred_temperature_high_c=23.33,
        preferred_humidity_low_percent=30.0,
        preferred_humidity_high_percent=60.0,
    )
    # Cooler preference: 68°F to 71°F is 20.0°C to 21.67°C
    cool_pref = OccupantPreferences(
        preferred_temperature_low_c=20.0,
        preferred_temperature_high_c=21.67,
        preferred_humidity_low_percent=30.0,
        preferred_humidity_high_percent=55.0,
    )

    return [
        ScenarioConfig(
            name="Scenario_A_Comfortable",
            description="Indoor temp within comfort band (72°F in [70, 74]), mild outdoor (75°F)",
            initial_temp_f=72.0,
            initial_humidity=45.0,
            outdoor_temp_f=75.0,
            outdoor_humidity=50.0,
            solar_generation_kw=0.5,
            tariff_rate=10.0,  # standard tariff
            preferences=default_pref,
            steps=24,
        ),
        ScenarioConfig(
            name="Scenario_B_Moderately_Warm",
            description="Indoor temp above preferred high (77°F > 74°F), warm outdoor (82°F)",
            initial_temp_f=77.0,
            initial_humidity=50.0,
            outdoor_temp_f=82.0,
            outdoor_humidity=55.0,
            solar_generation_kw=1.0,
            tariff_rate=10.0,
            preferences=default_pref,
            steps=24,
        ),
        ScenarioConfig(
            name="Scenario_C_Hot_Outdoor",
            description="Indoor temp warm (78.5°F) with high outdoor thermal load (95°F)",
            initial_temp_f=78.5,
            initial_humidity=55.0,
            outdoor_temp_f=95.0,
            outdoor_humidity=60.0,
            solar_generation_kw=2.0,
            tariff_rate=12.0,
            preferences=default_pref,
            steps=24,
        ),
        ScenarioConfig(
            name="Scenario_D_Solar_Available",
            description="Warm building (76°F) with high solar generation (5.0 kW)",
            initial_temp_f=76.0,
            initial_humidity=48.0,
            outdoor_temp_f=85.0,
            outdoor_humidity=50.0,
            solar_generation_kw=5.0,
            tariff_rate=15.0,
            preferences=default_pref,
            steps=24,
        ),
        ScenarioConfig(
            name="Scenario_E_High_Tariff",
            description="Warm building (75.5°F) with peak electricity tariff (35.0) and no solar",
            initial_temp_f=75.5,
            initial_humidity=50.0,
            outdoor_temp_f=84.0,
            outdoor_humidity=52.0,
            solar_generation_kw=0.0,
            tariff_rate=35.0,
            preferences=default_pref,
            steps=24,
        ),
        ScenarioConfig(
            name="Scenario_F_Personalized_Comfort",
            description="Cooler occupant preference ([68, 71]°F) with indoor temp at 74°F",
            initial_temp_f=74.0,
            initial_humidity=45.0,
            outdoor_temp_f=82.0,
            outdoor_humidity=50.0,
            solar_generation_kw=1.5,
            tariff_rate=10.0,
            preferences=cool_pref,
            steps=24,
        ),
    ]


def run_single_evaluation(
    controller_type: str,
    scenario: ScenarioConfig,
    pred_engine: NeuralPredictionEngine,
    dqn_agent: DQNAgent | None = None,
    rule_controller: RuleBasedController | None = None,
    thermostat: SimpleThermostatController | None = None,
) -> Tuple[EpisodeMetrics, Dict[str, Any]]:
    """
    Run one evaluation episode with exact scenario conditions.
    """
    env = WispEnv(
        prediction_engine=pred_engine,
        preferences=scenario.preferences,
        initial_indoor_temp_f=scenario.initial_temp_f,
        initial_indoor_humidity=scenario.initial_humidity,
        outdoor_temp_f=scenario.outdoor_temp_f,
        outdoor_humidity=scenario.outdoor_humidity,
        max_steps_per_episode=scenario.steps,
    )

    state = env.reset()

    if thermostat:
        thermostat.reset()

    # Trackers
    total_reward = 0.0
    total_energy = 0.0
    total_cost = 0.0
    total_switches = 0
    solar_used = 0.0
    grid_imported = 0.0
    comfort_violation_steps = 0
    temp_deviations = []
    action_counts = {a: 0 for a in WispAction}
    prev_action = WispAction.NO_ACTION

    timeseries = {
        "step": [],
        "indoor_temp": [],
        "indoor_humidity": [],
        "preferred_low": [],
        "preferred_high": [],
        "predicted_temp_t5": [],
        "predicted_temp_t15": [],
        "predicted_temp_t30": [],
        "confidence": [],
        "solar_kw": [],
        "tariff_rate": [],
        "action": [],
        "action_name": [],
        "energy_kwh": [],
        "cost": [],
        "reward": [],
    }

    for step in range(scenario.steps):
        # Select action according to controller type
        if controller_type == "NO_CONTROL":
            action = WispAction.NO_ACTION
        elif controller_type == "SIMPLE_THERMOSTAT":
            assert thermostat is not None
            action = thermostat.select_action(state)
        elif controller_type == "WISP_RULE_BASED":
            assert rule_controller is not None
            action = rule_controller.select_action(state, previous_action=prev_action)
        elif controller_type == "WISP_DQN":
            assert dqn_agent is not None
            action, _ = dqn_agent.select_action(state, evaluate=True)
        else:
            raise ValueError(f"Unknown controller type: {controller_type}")

        # Check for action switch
        if step > 0 and action != prev_action:
            total_switches += 1
        prev_action = action
        action_counts[action] += 1

        # Check comfort deviation
        pref_low = state.preferred_temperature_low_f
        pref_high = state.preferred_temperature_high_f
        t_in = state.indoor_temperature_f
        dev = 0.0
        if t_in < pref_low:
            dev = pref_low - t_in
            comfort_violation_steps += 1
        elif t_in > pref_high:
            dev = t_in - pref_high
            comfort_violation_steps += 1
        temp_deviations.append(dev)

        # Step environment
        next_state, reward, done, info = env.step(action)
        total_reward += reward

        # Record energy/cost/solar
        e_kwh = info.get("energy_consumed_kWh", 0.0)
        c_val = info.get("electricity_cost", 0.0)
        s_kwh = info.get("solar_used_kWh", 0.0)
        grid_kwh = info.get("grid_import_kWh", 0.0)

        total_energy += e_kwh
        total_cost += c_val
        grid_imported += grid_kwh
        solar_used += s_kwh

        # Record timeseries data
        timeseries["step"].append(step)
        timeseries["indoor_temp"].append(round(t_in, 3))
        timeseries["indoor_humidity"].append(round(state.indoor_humidity_percent, 2))
        timeseries["preferred_low"].append(round(pref_low, 2))
        timeseries["preferred_high"].append(round(pref_high, 2))
        timeseries["predicted_temp_t5"].append(round(state.predicted_temperature_t5_f, 3))
        timeseries["predicted_temp_t15"].append(round(state.predicted_temperature_t15_f, 3))
        timeseries["predicted_temp_t30"].append(round(state.predicted_temperature_t30_f, 3))
        timeseries["confidence"].append(round(state.prediction_confidence, 4))
        timeseries["solar_kw"].append(round(state.solar_power_kw, 2))
        timeseries["tariff_rate"].append(round(state.tariff_currency_per_kwh, 4))
        timeseries["action"].append(action.value)
        timeseries["action_name"].append(action.name)
        timeseries["energy_kwh"].append(round(e_kwh, 4))
        timeseries["cost"].append(round(c_val, 4))
        timeseries["reward"].append(round(reward, 4))

        state = next_state
        if done:
            break

    total_steps = len(temp_deviations)
    hours = total_steps * (5.0 / 60.0)
    avg_dev = float(np.mean(temp_deviations)) if temp_deviations else 0.0
    max_dev = float(np.max(temp_deviations)) if temp_deviations else 0.0
    violation_pct = (comfort_violation_steps / total_steps) * 100.0 if total_steps > 0 else 0.0
    time_inside_pct = 100.0 - violation_pct
    solar_util_pct = (solar_used / total_energy * 100.0) if total_energy > 0 else 0.0

    metrics = EpisodeMetrics(
        controller=controller_type,
        scenario=scenario.name,
        total_steps=total_steps,
        comfort_violation_steps=comfort_violation_steps,
        comfort_violation_pct=round(violation_pct, 2),
        avg_temp_deviation=round(avg_dev, 3),
        max_temp_deviation=round(max_dev, 3),
        time_inside_comfort_pct=round(time_inside_pct, 2),
        total_energy_kwh=round(total_energy, 4),
        avg_energy_kwh_per_hr=round(total_energy / max(hours, 0.1), 4),
        total_cost=round(total_cost, 4),
        avg_cost_per_hr=round(total_cost / max(hours, 0.1), 4),
        total_switches=total_switches,
        switching_rate=round(total_switches / max(total_steps, 1), 3),
        solar_energy_used_kwh=round(solar_used, 4),
        solar_utilization_pct=round(solar_util_pct, 2),
        grid_energy_imported_kwh=round(grid_imported, 4),
        no_action_pct=round(action_counts[WispAction.NO_ACTION] / total_steps * 100.0, 1),
        cool_low_pct=round(action_counts[WispAction.COOL_LOW] / total_steps * 100.0, 1),
        cool_medium_pct=round(action_counts[WispAction.COOL_MEDIUM] / total_steps * 100.0, 1),
        cool_high_pct=round(action_counts[WispAction.COOL_HIGH] / total_steps * 100.0, 1),
        precool_pct=round(action_counts[WispAction.PRECOOL] / total_steps * 100.0, 1),
        reduce_hvac_pct=round(action_counts[WispAction.REDUCE_HVAC] / total_steps * 100.0, 1),
        cumulative_reward=round(total_reward, 4),
    )

    return metrics, timeseries


def evaluate_all_baselines(
    checkpoint_path: str = "backend/models/saved_models/best_dqn_agent.pth",
    output_dir: str = "backend/app/rl/results",
) -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, Any]]:
    """
    Run complete evaluation across all 4 controllers and 6 standard scenarios.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Initialize Prediction Engine
    pred_engine = NeuralPredictionEngine()

    # Initialize Controllers
    thermostat = SimpleThermostatController()
    rule_controller = RuleBasedController()
    dqn_agent = DQNAgent()
    dqn_agent.load_checkpoint(checkpoint_path)

    controllers = [
        "NO_CONTROL",
        "SIMPLE_THERMOSTAT",
        "WISP_RULE_BASED",
        "WISP_DQN",
    ]

    scenarios = get_standard_scenarios()
    all_metrics: List[EpisodeMetrics] = []
    all_timeseries: Dict[str, Dict[str, Any]] = {}

    for sc in scenarios:
        for ctrl in controllers:
            m, ts = run_single_evaluation(
                controller_type=ctrl,
                scenario=sc,
                pred_engine=pred_engine,
                dqn_agent=dqn_agent,
                rule_controller=rule_controller,
                thermostat=thermostat,
            )
            all_metrics.append(m)
            key = f"{sc.name}_{ctrl}"
            all_timeseries[key] = ts

    # Convert to DataFrame
    df = pd.DataFrame([asdict(m) for m in all_metrics])

    # Save CSV
    csv_file = out_path / "baseline_comparison.csv"
    df.to_csv(csv_file, index=False)

    # Save JSON
    json_file = out_path / "baseline_comparison.json"
    with open(json_file, "w") as f:
        json.dump(df.to_dict(orient="records"), f, indent=2)

    # Save Time-series
    ts_file = out_path / "timeseries_evaluation.json"
    with open(ts_file, "w") as f:
        json.dump(all_timeseries, f, indent=2)

    # Compute Aggregate Stats per controller
    summary_dict = {}
    for ctrl in controllers:
        sub = df[df["controller"] == ctrl]
        summary_dict[ctrl] = {
            "comfort_violation_pct_mean": round(float(sub["comfort_violation_pct"].mean()), 2),
            "comfort_violation_pct_std": round(float(sub["comfort_violation_pct"].std()), 2),
            "avg_temp_deviation_mean": round(float(sub["avg_temp_deviation"].mean()), 3),
            "avg_temp_deviation_std": round(float(sub["avg_temp_deviation"].std()), 3),
            "max_temp_deviation_mean": round(float(sub["max_temp_deviation"].mean()), 3),
            "time_inside_comfort_pct_mean": round(float(sub["time_inside_comfort_pct"].mean()), 2),
            "total_energy_kwh_mean": round(float(sub["total_energy_kwh"].mean()), 4),
            "total_energy_kwh_std": round(float(sub["total_energy_kwh"].std()), 4),
            "total_cost_mean": round(float(sub["total_cost"].mean()), 4),
            "total_cost_std": round(float(sub["total_cost"].std()), 4),
            "total_switches_mean": round(float(sub["total_switches"].mean()), 2),
            "solar_utilization_pct_mean": round(float(sub["solar_utilization_pct"].mean()), 2),
            "cumulative_reward_mean": round(float(sub["cumulative_reward"].mean()), 4),
            "cumulative_reward_std": round(float(sub["cumulative_reward"].std()), 4),
            "no_action_pct_mean": round(float(sub["no_action_pct"].mean()), 1),
            "cooling_pct_mean": round(float((sub["cool_low_pct"] + sub["cool_medium_pct"] + sub["cool_high_pct"] + sub["precool_pct"]).mean()), 1),
        }

    summary_file = out_path / "baseline_summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary_dict, f, indent=2)

    logger.info(f"Evaluation complete. Results saved to {out_path}")
    return df, summary_dict, all_timeseries


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    df, summary, _ = evaluate_all_baselines()
    print("\n--- BASELINE EVALUATION SUMMARY ---")
    print(json.dumps(summary, indent=2))

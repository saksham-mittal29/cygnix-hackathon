"""
final_benchmark.py
------------------
Final Benchmarking Experiment for Wisp Person 3.

Evaluates 5 controllers head-to-head across 20 diverse 24-hour (288-step) simulation scenarios:
1. NO_CONTROL
2. SIMPLE_THERMOSTAT
3. WISP_RULE_BASED
4. WISP_DQN_ORIGINAL (best_dqn_agent.pth)
5. WISP_DQN_LONG_TRAINED (dqn_phase10_long_training.pth)

Generates:
- final_benchmark_summary.csv / .json
- final_benchmark_timeseries.csv / .json
- dqn_model_comparison.csv / .json
- context_responsiveness.csv / .json
- paired_comparisons.csv / .json
- High-resolution comparative plots (PNG)
- FINAL_BENCHMARK_REPORT.md
"""

from dataclasses import asdict, dataclass
import json
import logging
import math
from pathlib import Path
import random
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
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

logger = logging.getLogger("wisp.final_benchmark")
ACTION_LIST = list(WispAction)


@dataclass
class BenchmarkScenario:
    name: str
    category: str
    description: str
    initial_temp_f: float
    initial_humidity: float
    outdoor_temp_f: float
    outdoor_humidity: float
    solar_generation_kw: float
    tariff_rate: float
    preferences: OccupantPreferences
    steps: int = 288  # 24 hours x 12 steps/hr = 288 steps


@dataclass
class BenchmarkEpisodeMetrics:
    controller: str
    scenario: str
    category: str
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
    grid_energy_kwh: float
    solar_energy_used_kwh: float
    solar_utilization_pct: float
    total_switches: int
    switching_rate: float
    cumulative_reward: float
    avg_reward_per_step: float
    no_action_pct: float
    cool_low_pct: float
    cool_medium_pct: float
    cool_high_pct: float
    precool_pct: float
    reduce_hvac_pct: float
    action_entropy: float
    unique_actions_count: int
    consecutive_identical_pct: float


def get_20_benchmark_scenarios() -> List[BenchmarkScenario]:
    """Generates the 20 canonical 24-hour benchmark scenarios."""
    def make_pref(low_f: float, high_f: float, low_h: float = 30.0, high_h: float = 60.0) -> OccupantPreferences:
        return OccupantPreferences(
            preferred_temperature_low_c=(low_f - 32.0) * 5.0 / 9.0,
            preferred_temperature_high_c=(high_f - 32.0) * 5.0 / 9.0,
            preferred_humidity_low_percent=low_h,
            preferred_humidity_high_percent=high_h,
        )

    p_norm = make_pref(70.0, 74.0)
    p_narrow = make_pref(71.0, 73.0)
    p_cool = make_pref(68.0, 71.0)
    p_warm = make_pref(73.0, 76.0)
    p_wide = make_pref(70.0, 76.0)

    scenarios = [
        # A. Comfortable
        BenchmarkScenario("Scen_01_Comfortable_Spring", "Comfortable", "Mild indoor 72°F in [70,74] with mild outdoor 70°F", 72.0, 45.0, 70.0, 45.0, 2.0, 10.0, p_norm),
        BenchmarkScenario("Scen_02_Comfortable_Autumn", "Comfortable", "Indoor 73°F in [70,74] with outdoor 74°F", 73.0, 48.0, 74.0, 50.0, 1.0, 12.0, p_norm),
        
        # B. Moderately Warm
        BenchmarkScenario("Scen_03_ModWarm_Morning", "Moderately_Warm", "Indoor 76°F > 74°F with outdoor 82°F", 76.0, 50.0, 82.0, 55.0, 3.0, 10.0, p_norm),
        BenchmarkScenario("Scen_04_ModWarm_Afternoon", "Moderately_Warm", "Indoor 77.5°F > 74°F with outdoor 86°F", 77.5, 52.0, 86.0, 50.0, 4.0, 15.0, p_norm),
        
        # C. Severe Heat
        BenchmarkScenario("Scen_05_SevereHeat_PeakSun", "Severe_Heat", "Indoor 80°F with severe outdoor heat 98°F", 80.0, 55.0, 98.0, 45.0, 6.0, 20.0, p_norm),
        BenchmarkScenario("Scen_06_ExtremeHeat_Heatwave", "Severe_Heat", "Indoor 82°F with extreme heatwave 104°F", 82.0, 58.0, 104.0, 40.0, 7.0, 25.0, p_norm),
        
        # D. Overcooled
        BenchmarkScenario("Scen_07_Overcooled_Morning", "Overcooled", "Indoor 67°F < 70°F lower bound with cool outdoor 65°F", 67.0, 40.0, 65.0, 50.0, 0.0, 10.0, p_norm),
        BenchmarkScenario("Scen_08_Overcooled_MildDay", "Overcooled", "Indoor 68.5°F < 70°F with outdoor 72°F", 68.5, 42.0, 72.0, 48.0, 1.0, 10.0, p_norm),
        
        # E. High Solar
        BenchmarkScenario("Scen_09_HighSolar_Abundance", "High_Solar", "Indoor 75.5°F with high solar generation 8.0 kW", 75.5, 48.0, 88.0, 45.0, 8.0, 15.0, p_norm),
        
        # F. No Solar
        BenchmarkScenario("Scen_10_NoSolar_CloudyDay", "No_Solar", "Indoor 76°F with zero solar generation", 76.0, 52.0, 84.0, 60.0, 0.0, 12.0, p_norm),
        
        # G. Low Tariff
        BenchmarkScenario("Scen_11_LowTariff_OffPeak", "Low_Tariff", "Indoor 76°F with off-peak tariff 5.0", 76.0, 48.0, 80.0, 50.0, 1.0, 5.0, p_norm),
        
        # H. Peak Tariff
        BenchmarkScenario("Scen_12_PeakTariff_Spike", "Peak_Tariff", "Indoor 76°F with critical peak tariff 50.0", 76.0, 50.0, 85.0, 50.0, 0.0, 50.0, p_norm),
        
        # I. Narrow Comfort Band
        BenchmarkScenario("Scen_13_Narrow_Band", "Narrow_Pref", "Indoor 73.5°F with tight comfort envelope [71, 73]°F", 73.5, 45.0, 82.0, 50.0, 2.0, 10.0, p_narrow),
        
        # J. Cool Preference
        BenchmarkScenario("Scen_14_Cool_Preference", "Cool_Pref", "Indoor 74°F with cool occupant preference [68, 71]°F", 74.0, 45.0, 80.0, 50.0, 2.0, 10.0, p_cool),
        
        # K. Warm Preference
        BenchmarkScenario("Scen_15_Warm_Preference", "Warm_Pref", "Indoor 75°F with warm occupant preference [73, 76]°F", 75.0, 48.0, 85.0, 50.0, 2.0, 10.0, p_warm),
        
        # L. Wide Envelope
        BenchmarkScenario("Scen_16_Wide_Envelope", "Wide_Pref", "Indoor 75°F with relaxed envelope [70, 76]°F", 75.0, 50.0, 82.0, 50.0, 2.0, 10.0, p_wide),
        
        # M. Rapid Warming Forecast
        BenchmarkScenario("Scen_17_Rapid_Warming", "Forecast_Trend", "Indoor 73°F (currently ok) facing rising outdoor 94°F", 73.0, 45.0, 94.0, 45.0, 4.0, 15.0, p_norm),
        
        # N. Rapid Cooling Forecast
        BenchmarkScenario("Scen_18_Rapid_Cooling", "Forecast_Trend", "Indoor 76°F facing incoming cool front 66°F", 76.0, 48.0, 66.0, 55.0, 1.0, 10.0, p_norm),
        
        # Mixed Dynamic Complex Scenarios
        BenchmarkScenario("Scen_19_Solar_PeakTariff_Mix", "Complex_Mix", "Indoor 77°F, 6 kW solar during peak 45.0 tariff", 77.0, 50.0, 90.0, 45.0, 6.0, 45.0, p_norm),
        BenchmarkScenario("Scen_20_SevereHeat_CoolPref", "Complex_Mix", "Indoor 80°F, 100°F outdoor with cool pref [68, 71]°F", 80.0, 52.0, 100.0, 40.0, 5.0, 15.0, p_cool),
    ]
    return scenarios


def run_single_benchmark_episode(
    controller_name: str,
    scenario: BenchmarkScenario,
    pred_engine: NeuralPredictionEngine,
    agent_original: Optional[DQNAgent] = None,
    agent_long: Optional[DQNAgent] = None,
    rule_ctrl: Optional[RuleBasedController] = None,
    thermostat: Optional[SimpleThermostatController] = None,
) -> Tuple[BenchmarkEpisodeMetrics, List[Dict[str, Any]]]:
    """
    Executes a single 288-step (24-hour) simulation for a specific controller.
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
    actions_sequence: List[WispAction] = []
    action_counts = {a: 0 for a in WispAction}
    prev_action = WispAction.NO_ACTION

    timeseries = []

    for step in range(scenario.steps):
        # Action selection
        if controller_name == "NO_CONTROL":
            action = WispAction.NO_ACTION
        elif controller_name == "SIMPLE_THERMOSTAT":
            assert thermostat is not None
            action = thermostat.select_action(state)
        elif controller_name == "WISP_RULE_BASED":
            assert rule_ctrl is not None
            action = rule_ctrl.select_action(state, previous_action=prev_action)
        elif controller_name == "WISP_DQN_ORIGINAL":
            assert agent_original is not None
            action, _ = agent_original.select_action(state, evaluate=True)
        elif controller_name == "WISP_DQN_LONG_TRAINED":
            assert agent_long is not None
            action, _ = agent_long.select_action(state, evaluate=True)
        else:
            raise ValueError(f"Unknown controller: {controller_name}")

        # Check switching
        if step > 0 and action != prev_action:
            total_switches += 1
        prev_action = action
        actions_sequence.append(action)
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

        # Environment step
        next_state, reward, done, info = env.step(action)
        total_reward += reward

        e_kwh = info.get("energy_consumed_kWh", 0.0)
        c_val = info.get("electricity_cost", 0.0)
        s_kwh = info.get("solar_used_kWh", 0.0)
        g_kwh = info.get("grid_import_kWh", 0.0)

        total_energy += e_kwh
        total_cost += c_val
        solar_used += s_kwh
        grid_imported += g_kwh

        timeseries.append({
            "step": step,
            "minute": step * 5,
            "hour": round(step * 5 / 60.0, 2),
            "scenario": scenario.name,
            "controller": controller_name,
            "indoor_temp_f": round(t_in, 3),
            "preferred_low_f": round(pref_low, 2),
            "preferred_high_f": round(pref_high, 2),
            "predicted_temp_t5_f": round(state.predicted_temperature_t5_f, 3),
            "predicted_temp_t30_f": round(state.predicted_temperature_t30_f, 3),
            "solar_kw": round(state.solar_power_kw, 2),
            "tariff_rate": round(state.tariff_currency_per_kwh, 4),
            "action": action.name,
            "action_val": action.value,
            "energy_kwh": round(e_kwh, 4),
            "cost": round(c_val, 4),
            "reward": round(reward, 4),
        })

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

    # Action distribution metrics
    probs = [cnt / total_steps for cnt in action_counts.values() if cnt > 0]
    entropy = -sum(p * math.log(p) for p in probs) if probs else 0.0
    unique_acts = sum(1 for cnt in action_counts.values() if cnt > 0)
    
    consec_identical = sum(1 for i in range(1, len(actions_sequence)) if actions_sequence[i] == actions_sequence[i-1])
    consec_pct = (consec_identical / max(len(actions_sequence) - 1, 1)) * 100.0

    metrics = BenchmarkEpisodeMetrics(
        controller=controller_name,
        scenario=scenario.name,
        category=scenario.category,
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
        grid_energy_kwh=round(grid_imported, 4),
        solar_energy_used_kwh=round(solar_used, 4),
        solar_utilization_pct=round(solar_util_pct, 2),
        total_switches=total_switches,
        switching_rate=round(total_switches / max(total_steps, 1), 4),
        cumulative_reward=round(total_reward, 4),
        avg_reward_per_step=round(total_reward / max(total_steps, 1), 4),
        no_action_pct=round(action_counts[WispAction.NO_ACTION] / total_steps * 100.0, 1),
        cool_low_pct=round(action_counts[WispAction.COOL_LOW] / total_steps * 100.0, 1),
        cool_medium_pct=round(action_counts[WispAction.COOL_MEDIUM] / total_steps * 100.0, 1),
        cool_high_pct=round(action_counts[WispAction.COOL_HIGH] / total_steps * 100.0, 1),
        precool_pct=round(action_counts[WispAction.PRECOOL] / total_steps * 100.0, 1),
        reduce_hvac_pct=round(action_counts[WispAction.REDUCE_HVAC] / total_steps * 100.0, 1),
        action_entropy=round(entropy, 4),
        unique_actions_count=unique_acts,
        consecutive_identical_pct=round(consec_pct, 2),
    )

    return metrics, timeseries


def run_paired_context_responsiveness_tests(
    long_agent: DQNAgent,
    output_dir: Path,
) -> pd.DataFrame:
    """
    Evaluates isolated paired state tests where ONLY ONE context variable changes.
    """
    pairs = [
        {
            "pair_name": "Pair_1_Tariff_Sensitivity",
            "tested_variable": "Electricity Tariff",
            "desc": "Indoor 75°F near upper bound under Normal (10.0) vs Peak (50.0) tariff",
            "state_A": {"t_in": 75.0, "h_in": 50.0, "t_out": 85.0, "solar": 0.0, "tariff": 10.0, "p_low": 70.0, "p_high": 74.0, "t_p30": 76.0, "conf": 0.90},
            "state_B": {"t_in": 75.0, "h_in": 50.0, "t_out": 85.0, "solar": 0.0, "tariff": 50.0, "p_low": 70.0, "p_high": 74.0, "t_p30": 76.0, "conf": 0.90},
            "cond_A_label": "Normal Tariff ($10.0)",
            "cond_B_label": "Peak Tariff ($50.0)",
        },
        {
            "pair_name": "Pair_2_Solar_Sensitivity",
            "tested_variable": "Solar Generation",
            "desc": "Indoor 75.5°F under Zero Solar (0 kW) vs High Solar (8 kW)",
            "state_A": {"t_in": 75.5, "h_in": 50.0, "t_out": 85.0, "solar": 0.0, "tariff": 15.0, "p_low": 70.0, "p_high": 74.0, "t_p30": 76.5, "conf": 0.90},
            "state_B": {"t_in": 75.5, "h_in": 50.0, "t_out": 85.0, "solar": 8.0, "tariff": 15.0, "p_low": 70.0, "p_high": 74.0, "t_p30": 76.5, "conf": 0.90},
            "cond_A_label": "Zero Solar (0 kW)",
            "cond_B_label": "High Solar (8 kW)",
        },
        {
            "pair_name": "Pair_3_Preference_Sensitivity",
            "tested_variable": "Comfort Preference Envelope",
            "desc": "Indoor 73.5°F under Wide [70, 76]°F vs Narrow [71, 73]°F envelope",
            "state_A": {"t_in": 73.5, "h_in": 45.0, "t_out": 80.0, "solar": 2.0, "tariff": 10.0, "p_low": 70.0, "p_high": 76.0, "t_p30": 74.0, "conf": 0.90},
            "state_B": {"t_in": 73.5, "h_in": 45.0, "t_out": 80.0, "solar": 2.0, "tariff": 10.0, "p_low": 71.0, "p_high": 73.0, "t_p30": 74.0, "conf": 0.90},
            "cond_A_label": "Wide Envelope [70, 76]°F",
            "cond_B_label": "Narrow Envelope [71, 73]°F",
        },
        {
            "pair_name": "Pair_4_Indoor_Temp_Sensitivity",
            "tested_variable": "Indoor Temperature",
            "desc": "Comfortable (72°F) vs Hot (80°F) indoor state",
            "state_A": {"t_in": 72.0, "h_in": 45.0, "t_out": 85.0, "solar": 2.0, "tariff": 10.0, "p_low": 70.0, "p_high": 74.0, "t_p30": 72.5, "conf": 0.90},
            "state_B": {"t_in": 80.0, "h_in": 55.0, "t_out": 85.0, "solar": 2.0, "tariff": 10.0, "p_low": 70.0, "p_high": 74.0, "t_p30": 81.5, "conf": 0.90},
            "cond_A_label": "Comfortable (72°F)",
            "cond_B_label": "Hot (80°F)",
        },
        {
            "pair_name": "Pair_5_Forecast_Trend_Sensitivity",
            "tested_variable": "Predicted Future Trajectory",
            "desc": "Indoor 73°F facing Stable (+0.2°F) vs Rapidly Warming (+3.5°F) forecast",
            "state_A": {"t_in": 73.0, "h_in": 45.0, "t_out": 88.0, "solar": 3.0, "tariff": 15.0, "p_low": 70.0, "p_high": 74.0, "t_p30": 73.2, "conf": 0.90},
            "state_B": {"t_in": 73.0, "h_in": 45.0, "t_out": 88.0, "solar": 3.0, "tariff": 15.0, "p_low": 70.0, "p_high": 74.0, "t_p30": 76.5, "conf": 0.90},
            "cond_A_label": "Stable Forecast (+0.2°F)",
            "cond_B_label": "Rapid Warming (+3.5°F)",
        },
        {
            "pair_name": "Pair_6_Confidence_Sensitivity",
            "tested_variable": "ACI Prediction Confidence",
            "desc": "Indoor 75°F under High Confidence (0.95) vs Low Confidence (0.30)",
            "state_A": {"t_in": 75.0, "h_in": 50.0, "t_out": 85.0, "solar": 2.0, "tariff": 10.0, "p_low": 70.0, "p_high": 74.0, "t_p30": 75.5, "conf": 0.95},
            "state_B": {"t_in": 75.0, "h_in": 50.0, "t_out": 85.0, "solar": 2.0, "tariff": 10.0, "p_low": 70.0, "p_high": 74.0, "t_p30": 75.5, "conf": 0.30},
            "cond_A_label": "High Confidence (0.95)",
            "cond_B_label": "Low Confidence (0.30)",
        },
    ]

    records = []
    for p in pairs:
        def eval_st(st_dict):
            state = WispEnvState(
                indoor_temperature_f=st_dict["t_in"],
                indoor_humidity_percent=st_dict["h_in"],
                outdoor_temperature_f=st_dict["t_out"],
                predicted_temperature_t5_f=st_dict["t_in"] + 0.2,
                predicted_humidity_t5_percent=st_dict["h_in"],
                predicted_temperature_t15_f=st_dict["t_in"] + 0.5,
                predicted_humidity_t15_percent=st_dict["h_in"],
                predicted_temperature_t30_f=st_dict["t_p30"],
                predicted_humidity_t30_percent=st_dict["h_in"],
                prediction_confidence=st_dict["conf"],
                preferred_temperature_low_f=st_dict["p_low"],
                preferred_temperature_high_f=st_dict["p_high"],
                preferred_humidity_low_percent=30.0,
                preferred_humidity_high_percent=60.0,
                solar_power_kw=st_dict["solar"],
                tariff_currency_per_kwh=st_dict["tariff"],
            )
            obs = extract_dqn_observation(state)
            obs_t = torch.tensor(obs, dtype=torch.float32, device=long_agent.device).unsqueeze(0)
            with torch.no_grad():
                q_vals = long_agent.online_net(obs_t).cpu().numpy().flatten()
            act_idx = int(np.argmax(q_vals))
            return q_vals, ACTION_LIST[act_idx].name

        q_A, act_A = eval_st(p["state_A"])
        q_B, act_B = eval_st(p["state_B"])

        rec = {
            "pair_name": p["pair_name"],
            "tested_variable": p["tested_variable"],
            "description": p["desc"],
            "condition_A": p["cond_A_label"],
            "action_A": act_A,
            "Q_A_NO_ACTION": round(float(q_A[0]), 4),
            "Q_A_COOL_LOW": round(float(q_A[1]), 4),
            "Q_A_COOL_MED": round(float(q_A[2]), 4),
            "Q_A_COOL_HIGH": round(float(q_A[3]), 4),
            "Q_A_PRECOOL": round(float(q_A[4]), 4),
            "Q_A_REDUCE": round(float(q_A[5]), 4),
            "condition_B": p["cond_B_label"],
            "action_B": act_B,
            "Q_B_NO_ACTION": round(float(q_B[0]), 4),
            "Q_B_COOL_LOW": round(float(q_B[1]), 4),
            "Q_B_COOL_MED": round(float(q_B[2]), 4),
            "Q_B_COOL_HIGH": round(float(q_B[3]), 4),
            "Q_B_PRECOOL": round(float(q_B[4]), 4),
            "Q_B_REDUCE": round(float(q_B[5]), 4),
            "action_changed": act_A != act_B,
            "max_q_shift": round(float(np.max(np.abs(q_B - q_A))), 4),
        }
        records.append(rec)

    df = pd.DataFrame(records)
    df.to_csv(output_dir / "context_responsiveness.csv", index=False)
    with open(output_dir / "context_responsiveness.json", "w") as f:
        json.dump(records, f, indent=2)

    return df


def generate_benchmark_visualizations(
    df_metrics: pd.DataFrame,
    df_timeseries: pd.DataFrame,
    output_dir: Path,
):
    """
    Generates 8 high-resolution publication-quality PNG plots.
    """
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    controllers = ["NO_CONTROL", "SIMPLE_THERMOSTAT", "WISP_RULE_BASED", "WISP_DQN_ORIGINAL", "WISP_DQN_LONG_TRAINED"]
    colors = ["#7f7f7f", "#1f77b4", "#2ca02c", "#d62728", "#9467bd"]

    # 1. Comfort Violation Comparison
    fig, ax = plt.subplots(figsize=(9, 5))
    df_means = df_metrics.groupby("controller")["comfort_violation_pct"].mean().reindex(controllers)
    df_stds = df_metrics.groupby("controller")["comfort_violation_pct"].std().reindex(controllers)
    ax.bar(controllers, df_means, yerr=df_stds, capsize=5, color=colors, alpha=0.85)
    ax.set_title("Comfort Violation Rate Across 20 24-Hour Scenarios (%)", fontsize=13, fontweight="bold")
    ax.set_ylabel("Violation Percentage (%)")
    plt.xticks(rotation=15)
    plt.tight_layout()
    plt.savefig(output_dir / "plot1_comfort_violation_comparison.png", dpi=200)
    plt.close()

    # 2. Energy Consumption Comparison
    fig, ax = plt.subplots(figsize=(9, 5))
    e_means = df_metrics.groupby("controller")["total_energy_kwh"].mean().reindex(controllers)
    e_stds = df_metrics.groupby("controller")["total_energy_kwh"].std().reindex(controllers)
    ax.bar(controllers, e_means, yerr=e_stds, capsize=5, color=colors, alpha=0.85)
    ax.set_title("Total HVAC Energy Consumed (24-Hour Average kWh)", fontsize=13, fontweight="bold")
    ax.set_ylabel("Energy (kWh)")
    plt.xticks(rotation=15)
    plt.tight_layout()
    plt.savefig(output_dir / "plot2_energy_comparison.png", dpi=200)
    plt.close()

    # 3. Monetary Electricity Cost
    fig, ax = plt.subplots(figsize=(9, 5))
    c_means = df_metrics.groupby("controller")["total_cost"].mean().reindex(controllers)
    c_stds = df_metrics.groupby("controller")["total_cost"].std().reindex(controllers)
    ax.bar(controllers, c_means, yerr=c_stds, capsize=5, color=colors, alpha=0.85)
    ax.set_title("Total Monetary Electricity Cost (24-Hour Average $)", fontsize=13, fontweight="bold")
    ax.set_ylabel("Cost ($)")
    plt.xticks(rotation=15)
    plt.tight_layout()
    plt.savefig(output_dir / "plot3_cost_comparison.png", dpi=200)
    plt.close()

    # 4. Cumulative Reward Comparison
    fig, ax = plt.subplots(figsize=(9, 5))
    r_means = df_metrics.groupby("controller")["cumulative_reward"].mean().reindex(controllers)
    r_stds = df_metrics.groupby("controller")["cumulative_reward"].std().reindex(controllers)
    ax.bar(controllers, r_means, yerr=r_stds, capsize=5, color=colors, alpha=0.85)
    ax.set_title("Cumulative Multi-Objective Reward (24-Hour Average)", fontsize=13, fontweight="bold")
    ax.set_ylabel("Reward")
    plt.xticks(rotation=15)
    plt.tight_layout()
    plt.savefig(output_dir / "plot4_cumulative_reward_comparison.png", dpi=200)
    plt.close()

    # 5. Action Distribution Breakdown
    fig, ax = plt.subplots(figsize=(10, 5.5))
    act_cols = ["no_action_pct", "cool_low_pct", "cool_medium_pct", "cool_high_pct", "precool_pct", "reduce_hvac_pct"]
    act_labels = ["NO_ACTION", "COOL_LOW", "COOL_MED", "COOL_HIGH", "PRECOOL", "REDUCE"]
    means_df = df_metrics.groupby("controller")[act_cols].mean().reindex(controllers)
    bottom = np.zeros(len(controllers))
    for col, lbl in zip(act_cols, act_labels):
        vals = means_df[col].values
        ax.bar(controllers, vals, bottom=bottom, label=lbl, alpha=0.9)
        bottom += vals
    ax.set_title("Action Selection Distribution by Controller (%)", fontsize=13, fontweight="bold")
    ax.set_ylabel("Action Percentage (%)")
    ax.legend(loc="upper right")
    plt.xticks(rotation=15)
    plt.tight_layout()
    plt.savefig(output_dir / "plot5_action_distribution.png", dpi=200)
    plt.close()

    # 6. DQN Original vs Long-Trained Diversity
    fig, ax = plt.subplots(figsize=(8, 5))
    dqn_comp = df_metrics[df_metrics["controller"].isin(["WISP_DQN_ORIGINAL", "WISP_DQN_LONG_TRAINED"])]
    entropy_means = dqn_comp.groupby("controller")["action_entropy"].mean()
    switches_means = dqn_comp.groupby("controller")["total_switches"].mean()
    x = np.arange(2)
    w = 0.35
    ax.bar(x - w/2, entropy_means.values, width=w, label="Action Entropy", color="#1f77b4")
    ax2 = ax.twinx()
    ax2.bar(x + w/2, switches_means.values, width=w, label="Avg Switches", color="#ff7f0e")
    ax.set_xticks(x)
    ax.set_xticklabels(["DQN_ORIGINAL", "DQN_LONG_TRAINED"])
    ax.set_ylabel("Shannon Entropy", color="#1f77b4")
    ax2.set_ylabel("Average Switches", color="#ff7f0e")
    ax.set_title("DQN Policy Diversity & Dynamics: Original vs Long-Trained", fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_dir / "plot6_dqn_diversity_comparison.png", dpi=200)
    plt.close()

    # 7. Representative 24-Hour Temperature Trajectory (Scenario 5 - Severe Heat)
    scen_name = "Scen_05_SevereHeat_PeakSun"
    sub_ts = df_timeseries[df_timeseries["scenario"] == scen_name]
    fig, ax = plt.subplots(figsize=(10, 5))
    for ctrl, col in zip(controllers, colors):
        c_ts = sub_ts[sub_ts["controller"] == ctrl]
        if not c_ts.empty:
            ax.plot(c_ts["hour"], c_ts["indoor_temp_f"], label=ctrl, color=col, linewidth=1.8)
    if not sub_ts.empty:
        p_low = sub_ts["preferred_low_f"].iloc[0]
        p_high = sub_ts["preferred_high_f"].iloc[0]
        ax.axhline(p_high, color="red", linestyle="--", label="Pref High (74°F)")
        ax.axhline(p_low, color="blue", linestyle="--", label="Pref Low (70°F)")
    ax.set_title(f"24-Hour Indoor Temperature Trajectory ({scen_name})", fontsize=13, fontweight="bold")
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Indoor Temp (°F)")
    ax.legend(loc="upper right", fontsize=8)
    plt.tight_layout()
    plt.savefig(output_dir / "plot7_representative_24h_trajectory.png", dpi=200)
    plt.close()

    # 8. Representative Solar/Tariff Behavior (Scenario 19 - Solar + Peak Tariff Mix)
    scen_name = "Scen_19_Solar_PeakTariff_Mix"
    sub_ts = df_timeseries[df_timeseries["scenario"] == scen_name]
    fig, ax = plt.subplots(figsize=(10, 5))
    for ctrl, col in zip(["WISP_RULE_BASED", "WISP_DQN_ORIGINAL", "WISP_DQN_LONG_TRAINED"], ["#2ca02c", "#d62728", "#9467bd"]):
        c_ts = sub_ts[sub_ts["controller"] == ctrl]
        if not c_ts.empty:
            ax.plot(c_ts["hour"], c_ts["energy_kwh"], label=f"{ctrl} Power/Energy", color=col, linewidth=1.8)
    ax.set_title(f"24-Hour Energy Dispatch under Peak Tariff ($45.0) & Solar (6 kW)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Energy Consumed per 5-min Step (kWh)")
    ax.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(output_dir / "plot8_solar_tariff_dispatch.png", dpi=200)
    plt.close()


def execute_full_final_benchmark(
    output_dir_str: str = "backend/app/rl/results/final_benchmark",
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Executes the full 20-scenario x 5-controller 24-hour benchmark.
    """
    out_dir = Path(output_dir_str)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Prediction Engine and Agents
    pred_engine = NeuralPredictionEngine()
    
    agent_orig = DQNAgent()
    agent_orig.load_checkpoint("backend/models/saved_models/best_dqn_agent.pth")

    agent_long = DQNAgent()
    agent_long.load_checkpoint("backend/models/saved_models/dqn_phase10_long_training.pth")

    rule_ctrl = RuleBasedController()
    thermostat = SimpleThermostatController()

    controllers = [
        "NO_CONTROL",
        "SIMPLE_THERMOSTAT",
        "WISP_RULE_BASED",
        "WISP_DQN_ORIGINAL",
        "WISP_DQN_LONG_TRAINED",
    ]

    scenarios = get_20_benchmark_scenarios()
    all_metrics: List[BenchmarkEpisodeMetrics] = []
    all_ts_rows: List[Dict[str, Any]] = []

    print(f"Starting Final Benchmark: {len(scenarios)} scenarios x {len(controllers)} controllers (288 steps/episode)...")

    for sc in scenarios:
        for ctrl in controllers:
            m, ts = run_single_benchmark_episode(
                controller_name=ctrl,
                scenario=sc,
                pred_engine=pred_engine,
                agent_original=agent_orig,
                agent_long=agent_long,
                rule_ctrl=rule_ctrl,
                thermostat=thermostat,
            )
            all_metrics.append(m)
            all_ts_rows.extend(ts)

    df_metrics = pd.DataFrame([asdict(m) for m in all_metrics])
    df_ts = pd.DataFrame(all_ts_rows)

    # Save summary and timeseries
    df_metrics.to_csv(out_dir / "final_benchmark_summary.csv", index=False)
    with open(out_dir / "final_benchmark_summary.json", "w") as f:
        json.dump(df_metrics.to_dict(orient="records"), f, indent=2)

    df_ts.to_csv(out_dir / "final_benchmark_timeseries.csv", index=False)
    # Save subsampled timeseries to JSON to prevent excessive file size
    with open(out_dir / "final_benchmark_timeseries.json", "w") as f:
        json.dump(df_ts.iloc[::6].to_dict(orient="records"), f, indent=2)

    # 2. DQN Model Comparison
    dqn_sub = df_metrics[df_metrics["controller"].isin(["WISP_DQN_ORIGINAL", "WISP_DQN_LONG_TRAINED"])]
    dqn_comp_dict = {}
    for c in ["WISP_DQN_ORIGINAL", "WISP_DQN_LONG_TRAINED"]:
        sub = dqn_sub[dqn_sub["controller"] == c]
        dqn_comp_dict[c] = {
            "comfort_violation_pct_mean": round(float(sub["comfort_violation_pct"].mean()), 2),
            "avg_temp_deviation_mean": round(float(sub["avg_temp_deviation"].mean()), 3),
            "max_temp_deviation_mean": round(float(sub["max_temp_deviation"].mean()), 3),
            "total_energy_kwh_mean": round(float(sub["total_energy_kwh"].mean()), 4),
            "total_cost_mean": round(float(sub["total_cost"].mean()), 4),
            "total_switches_mean": round(float(sub["total_switches"].mean()), 2),
            "cumulative_reward_mean": round(float(sub["cumulative_reward"].mean()), 4),
            "no_action_pct_mean": round(float(sub["no_action_pct"].mean()), 1),
            "cool_low_pct_mean": round(float(sub["cool_low_pct"].mean()), 1),
            "cool_medium_pct_mean": round(float(sub["cool_medium_pct"].mean()), 1),
            "cool_high_pct_mean": round(float(sub["cool_high_pct"].mean()), 1),
            "precool_pct_mean": round(float(sub["precool_pct"].mean()), 1),
            "action_entropy_mean": round(float(sub["action_entropy"].mean()), 4),
            "unique_actions_mean": round(float(sub["unique_actions_count"].mean()), 2),
            "consecutive_identical_pct_mean": round(float(sub["consecutive_identical_pct"].mean()), 2),
        }
    df_dqn_comp = pd.DataFrame(dqn_comp_dict).T
    df_dqn_comp.to_csv(out_dir / "dqn_model_comparison.csv")
    with open(out_dir / "dqn_model_comparison.json", "w") as f:
        json.dump(dqn_comp_dict, f, indent=2)

    # 3. Context Responsiveness Paired Tests
    df_context = run_paired_context_responsiveness_tests(agent_long, out_dir)

    # 4. Paired Comparisons across Scenarios
    paired_rows = []
    for sc in scenarios:
        row_orig = df_metrics[(df_metrics["scenario"] == sc.name) & (df_metrics["controller"] == "WISP_DQN_ORIGINAL")].iloc[0]
        row_long = df_metrics[(df_metrics["scenario"] == sc.name) & (df_metrics["controller"] == "WISP_DQN_LONG_TRAINED")].iloc[0]
        row_rule = df_metrics[(df_metrics["scenario"] == sc.name) & (df_metrics["controller"] == "WISP_RULE_BASED")].iloc[0]

        paired_rows.append({
            "scenario": sc.name,
            # DQN_LONG vs DQN_ORIGINAL
            "diff_comfort_LONG_minus_ORIG": round(float(row_long["comfort_violation_pct"] - row_orig["comfort_violation_pct"]), 2),
            "diff_tempdev_LONG_minus_ORIG": round(float(row_long["avg_temp_deviation"] - row_orig["avg_temp_deviation"]), 3),
            "diff_energy_LONG_minus_ORIG": round(float(row_long["total_energy_kwh"] - row_orig["total_energy_kwh"]), 4),
            "diff_cost_LONG_minus_ORIG": round(float(row_long["total_cost"] - row_orig["total_cost"]), 4),
            "diff_reward_LONG_minus_ORIG": round(float(row_long["cumulative_reward"] - row_orig["cumulative_reward"]), 4),
            "diff_entropy_LONG_minus_ORIG": round(float(row_long["action_entropy"] - row_orig["action_entropy"]), 4),
            # DQN_LONG vs RULE_BASED
            "diff_comfort_LONG_minus_RULE": round(float(row_long["comfort_violation_pct"] - row_rule["comfort_violation_pct"]), 2),
            "diff_tempdev_LONG_minus_RULE": round(float(row_long["avg_temp_deviation"] - row_rule["avg_temp_deviation"]), 3),
            "diff_energy_LONG_minus_RULE": round(float(row_long["total_energy_kwh"] - row_rule["total_energy_kwh"]), 4),
            "diff_cost_LONG_minus_RULE": round(float(row_long["total_cost"] - row_rule["total_cost"]), 4),
            "diff_reward_LONG_minus_RULE": round(float(row_long["cumulative_reward"] - row_rule["cumulative_reward"]), 4),
            # DQN_ORIGINAL vs RULE_BASED
            "diff_comfort_ORIG_minus_RULE": round(float(row_orig["comfort_violation_pct"] - row_rule["comfort_violation_pct"]), 2),
            "diff_energy_ORIG_minus_RULE": round(float(row_orig["total_energy_kwh"] - row_rule["total_energy_kwh"]), 4),
            "diff_cost_ORIG_minus_RULE": round(float(row_orig["total_cost"] - row_rule["total_cost"]), 4),
            "diff_reward_ORIG_minus_RULE": round(float(row_orig["cumulative_reward"] - row_rule["cumulative_reward"]), 4),
        })

    df_paired = pd.DataFrame(paired_rows)
    df_paired.to_csv(out_dir / "paired_comparisons.csv", index=False)
    with open(out_dir / "paired_comparisons.json", "w") as f:
        json.dump(paired_rows, f, indent=2)

    # 5. Generate Visualizations
    generate_benchmark_visualizations(df_metrics, df_ts, out_dir)

    print(f"Final Benchmark Complete! Output files saved to: {out_dir}")
    return df_metrics, df_ts, df_dqn_comp, df_context, df_paired


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    execute_full_final_benchmark()

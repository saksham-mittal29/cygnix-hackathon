"""
diagnostics.py
--------------
Phase 10: Master Diagnostic, Stress-Testing, and Ablation Study Engine for Wisp RL.

Implements:
1. Q-Value Inspection across representative thermal and economic states.
2. Systematic Stress-Testing across wide operational matrices.
3. Feature Ablation Studies (Full, No-Forecast, No-Confidence, No-Preference, No-Solar, No-Tariff, Minimal).
4. Reward-Weight Sensitivity Analysis.
5. Long-Training Diagnostic (300 episodes x 24 steps = 7,200 transitions).
6. Policy Diversity & Action Entropy Analysis.
"""

from dataclasses import asdict, dataclass
import json
import logging
import math
from pathlib import Path
import random
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch

from backend.app.core.actions import WispAction

ACTION_LIST = list(WispAction)
from backend.app.core.types import (
    PredictionResult,
    RewardWeights,
    ThermalState,
    Disturbance,
)
from backend.app.personalization.preferences import OccupantPreferences
from backend.app.prediction.neural_engine import NeuralPredictionEngine
from backend.app.rl.agent import DQNAgent, DQNConfig
from backend.app.rl.dqn import ACTION_DIM, OBSERVATION_DIM
from backend.app.rl.observation import extract_dqn_observation
from backend.app.simulation.environment import WispEnv, WispEnvState

logger = logging.getLogger("wisp.phase10_diagnostics")


# ----------------------------------------------------------------------
# PART 1: Q-VALUE INSPECTOR
# ----------------------------------------------------------------------
def inspect_q_values(
    checkpoint_path: str = "backend/models/saved_models/best_dqn_agent.pth",
    output_dir: str = "backend/app/rl/results",
) -> pd.DataFrame:
    """
    Evaluates raw Q-values for all 6 discrete actions across 8 representative states.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    agent = DQNAgent()
    agent.load_checkpoint(checkpoint_path)
    agent.online_net.eval()

    # 8 Representative States
    states_def = [
        {
            "scenario": "State_1_Comfortable",
            "desc": "Indoor 72°F in [70, 74]°F, mild outdoor 75°F, solar 1kW, tariff 10",
            "t_in": 72.0, "h_in": 45.0, "t_out": 75.0, "t_p5": 72.1, "t_p15": 72.3, "t_p30": 72.6,
            "conf": 0.92, "p_low": 70.0, "p_high": 74.0, "solar": 1.0, "tariff": 10.0,
        },
        {
            "scenario": "State_2_Moderately_Warm",
            "desc": "Indoor 76.5°F > 74°F upper bound, outdoor 82°F, solar 1kW, tariff 10",
            "t_in": 76.5, "h_in": 50.0, "t_out": 82.0, "t_p5": 76.8, "t_p15": 77.2, "t_p30": 77.8,
            "conf": 0.88, "p_low": 70.0, "p_high": 74.0, "solar": 1.0, "tariff": 10.0,
        },
        {
            "scenario": "State_3_Hot_Severe",
            "desc": "Indoor 80.0°F severely above bound, outdoor 95°F, solar 2kW, tariff 12",
            "t_in": 80.0, "h_in": 55.0, "t_out": 95.0, "t_p5": 80.5, "t_p15": 81.2, "t_p30": 82.0,
            "conf": 0.85, "p_low": 70.0, "p_high": 74.0, "solar": 2.0, "tariff": 12.0,
        },
        {
            "scenario": "State_4_High_Solar",
            "desc": "Indoor 75.0°F near upper bound, high solar 6.0 kW, tariff 15",
            "t_in": 75.0, "h_in": 48.0, "t_out": 85.0, "t_p5": 75.3, "t_p15": 75.8, "t_p30": 76.5,
            "conf": 0.90, "p_low": 70.0, "p_high": 74.0, "solar": 6.0, "tariff": 15.0,
        },
        {
            "scenario": "State_5_High_Tariff_Peak",
            "desc": "Indoor 75.0°F, peak tariff 45.0, zero solar",
            "t_in": 75.0, "h_in": 50.0, "t_out": 84.0, "t_p5": 75.3, "t_p15": 75.7, "t_p30": 76.2,
            "conf": 0.90, "p_low": 70.0, "p_high": 74.0, "solar": 0.0, "tariff": 45.0,
        },
        {
            "scenario": "State_6_Narrow_Envelope",
            "desc": "Indoor 73.5°F > 73°F upper bound with narrow band [71, 73]°F",
            "t_in": 73.5, "h_in": 45.0, "t_out": 80.0, "t_p5": 73.8, "t_p15": 74.2, "t_p30": 74.8,
            "conf": 0.91, "p_low": 71.0, "p_high": 73.0, "solar": 1.5, "tariff": 10.0,
        },
        {
            "scenario": "State_7_Overcooled",
            "desc": "Indoor 68.0°F < 70°F lower bound, outdoor 70°F, solar 0kW, tariff 10",
            "t_in": 68.0, "h_in": 40.0, "t_out": 70.0, "t_p5": 68.1, "t_p15": 68.3, "t_p30": 68.7,
            "conf": 0.93, "p_low": 70.0, "p_high": 74.0, "solar": 0.0, "tariff": 10.0,
        },
        {
            "scenario": "State_8_Forecast_Warming",
            "desc": "Indoor 73.0°F (currently ok) but +30min forecast 76.5°F (rapid warming), solar 3kW",
            "t_in": 73.0, "h_in": 45.0, "t_out": 92.0, "t_p5": 73.8, "t_p15": 75.0, "t_p30": 76.5,
            "conf": 0.87, "p_low": 70.0, "p_high": 74.0, "solar": 3.0, "tariff": 10.0,
        },
    ]

    records = []
    for s in states_def:
        state = WispEnvState(
            indoor_temperature_f=s["t_in"],
            indoor_humidity_percent=s["h_in"],
            outdoor_temperature_f=s["t_out"],
            predicted_temperature_t5_f=s["t_p5"],
            predicted_humidity_t5_percent=s["h_in"],
            predicted_temperature_t15_f=s["t_p15"],
            predicted_humidity_t15_percent=s["h_in"],
            predicted_temperature_t30_f=s["t_p30"],
            predicted_humidity_t30_percent=s["h_in"],
            prediction_confidence=s["conf"],
            preferred_temperature_low_f=s["p_low"],
            preferred_temperature_high_f=s["p_high"],
            preferred_humidity_low_percent=30.0,
            preferred_humidity_high_percent=60.0,
            solar_power_kw=s["solar"],
            tariff_currency_per_kwh=s["tariff"],
        )
        obs = extract_dqn_observation(state)
        obs_t = torch.tensor(obs, dtype=torch.float32, device=agent.device).unsqueeze(0)
        with torch.no_grad():
            q_vals = agent.online_net(obs_t).cpu().numpy().flatten()

        best_idx = int(np.argmax(q_vals))
        best_act = ACTION_LIST[best_idx].name

        rec = {
            "scenario": s["scenario"],
            "state_description": s["desc"],
            "Q_NO_ACTION": round(float(q_vals[0]), 4),
            "Q_COOL_LOW": round(float(q_vals[1]), 4),
            "Q_COOL_MEDIUM": round(float(q_vals[2]), 4),
            "Q_COOL_HIGH": round(float(q_vals[3]), 4),
            "Q_PRECOOL": round(float(q_vals[4]), 4),
            "Q_REDUCE_HVAC": round(float(q_vals[5]), 4),
            "selected_action": best_act,
            "q_max_margin_over_no_action": round(float(q_vals[best_idx] - q_vals[0]), 4),
            "q_max_margin_over_second": round(float(q_vals[best_idx] - np.partition(q_vals, -2)[-2]), 4),
        }
        records.append(rec)

    df = pd.DataFrame(records)
    df.to_csv(out_path / "q_value_analysis.csv", index=False)
    with open(out_path / "q_value_analysis.json", "w") as f:
        json.dump(records, f, indent=2)

    return df


# ----------------------------------------------------------------------
# PART 2: STRESS TESTING
# ----------------------------------------------------------------------
def run_stress_test_matrix(
    checkpoint_path: str = "backend/models/saved_models/best_dqn_agent.pth",
    output_dir: str = "backend/app/rl/results",
) -> pd.DataFrame:
    """
    Executes a multi-parameter sweep across thermal, solar, tariff, and preference conditions.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    agent = DQNAgent()
    agent.load_checkpoint(checkpoint_path)
    pred_engine = NeuralPredictionEngine()

    indoor_temps = [70.0, 72.0, 74.0, 76.0, 78.0, 80.0, 82.0]
    outdoor_temps = [65.0, 75.0, 85.0, 95.0, 105.0]
    envelopes = [
        ("wide", 70.0, 76.0),
        ("normal", 70.0, 74.0),
        ("narrow", 71.0, 73.0),
        ("cool", 68.0, 71.0),
        ("warm", 73.0, 76.0),
    ]
    solars = [0.0, 1.0, 3.0, 5.0, 8.0]
    tariffs = [5.0, 10.0, 25.0, 50.0]

    # Sample representative grid points systematically
    records = []
    sample_idx = 0

    # Grid parameter combinations
    for t_in in indoor_temps:
        for t_out in outdoor_temps:
            for env_name, p_low, p_high in envelopes:
                # Subsample solar & tariff to keep runs fast while spanning extremes
                for sol in [0.0, 5.0]:
                    for tar in [10.0, 50.0]:
                        sample_idx += 1
                        # Build preferences
                        p_low_c = (p_low - 32.0) * 5.0 / 9.0
                        p_high_c = (p_high - 32.0) * 5.0 / 9.0
                        prefs = OccupantPreferences(
                            preferred_temperature_low_c=p_low_c,
                            preferred_temperature_high_c=p_high_c,
                        )

                        # Create environment and reset
                        env = WispEnv(
                            prediction_engine=pred_engine,
                            preferences=prefs,
                            initial_indoor_temp_f=t_in,
                            initial_indoor_humidity=50.0,
                            outdoor_temp_f=t_out,
                            outdoor_humidity=55.0,
                            max_steps_per_episode=6,  # 6 steps = 30 min rollout
                        )
                        state = env.reset()

                        # Evaluate DQN decision
                        obs = extract_dqn_observation(state)
                        obs_t = torch.tensor(obs, dtype=torch.float32, device=agent.device).unsqueeze(0)
                        with torch.no_grad():
                            q_vals = agent.online_net(obs_t).cpu().numpy().flatten()
                        action_idx = int(np.argmax(q_vals))
                        action = ACTION_LIST[action_idx]

                        # Take 1-step physical transition
                        next_state, reward, done, info = env.step(action)

                        # Check comfort deviation
                        t_curr = state.indoor_temperature_f
                        comfort_viol = max(0.0, t_curr - p_high) if t_curr > p_high else (max(0.0, p_low - t_curr) if t_curr < p_low else 0.0)

                        records.append({
                            "sample_id": sample_idx,
                            "initial_temp_f": t_in,
                            "outdoor_temp_f": t_out,
                            "preference_envelope": env_name,
                            "pref_low_f": p_low,
                            "pref_high_f": p_high,
                            "solar_kw": sol,
                            "tariff_currency_per_kwh": tar,
                            "selected_action": action.name,
                            "action_idx": action_idx,
                            "Q_NO_ACTION": round(float(q_vals[0]), 4),
                            "Q_COOL_LOW": round(float(q_vals[1]), 4),
                            "Q_COOL_MEDIUM": round(float(q_vals[2]), 4),
                            "Q_COOL_HIGH": round(float(q_vals[3]), 4),
                            "Q_PRECOOL": round(float(q_vals[4]), 4),
                            "Q_REDUCE_HVAC": round(float(q_vals[5]), 4),
                            "comfort_violation_f": round(comfort_viol, 3),
                            "energy_kwh": round(info.get("energy_consumed_kWh", 0.0), 4),
                            "cost": round(info.get("electricity_cost", 0.0), 4),
                            "switching": info.get("switching_penalty", 0.0),
                            "reward": round(reward, 4),
                        })

    df = pd.DataFrame(records)
    df.to_csv(out_path / "stress_test_results.csv", index=False)
    with open(out_path / "stress_test_results.json", "w") as f:
        json.dump(records[:200], f, indent=2)  # Save first 200 records to JSON

    return df


# ----------------------------------------------------------------------
# PART 3: ABLATION STUDY
# ----------------------------------------------------------------------
def run_feature_ablations(
    checkpoint_path: str = "backend/models/saved_models/best_dqn_agent.pth",
    output_dir: str = "backend/app/rl/results",
) -> pd.DataFrame:
    """
    Performs controlled feature zero-masking and retraining ablations.
    Evaluates policy sensitivity to missing inputs.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    agent = DQNAgent()
    agent.load_checkpoint(checkpoint_path)

    # Standard representative test states
    test_states = [
        # (t_in, t_out, p_low, p_high, solar, tariff, desc)
        (72.0, 75.0, 70.0, 74.0, 1.0, 10.0, "Comfortable"),
        (77.0, 85.0, 70.0, 74.0, 1.0, 10.0, "Warm_Active"),
        (80.0, 95.0, 70.0, 74.0, 2.0, 12.0, "Hot_Severe"),
        (75.0, 85.0, 70.0, 74.0, 6.0, 15.0, "High_Solar"),
        (75.0, 84.0, 70.0, 74.0, 0.0, 45.0, "High_Tariff"),
        (68.0, 70.0, 70.0, 74.0, 0.0, 10.0, "Overcooled"),
    ]

    ablation_masks = {
        "A_FULL": list(range(16)),
        "B_NO_FORECAST": [0, 1, 2, 9, 10, 11, 12, 13, 14, 15],  # Mask features 3..8 (+5,+15,+30 min)
        "C_NO_CONFIDENCE": [0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15],  # Mask feature 9
        "D_NO_PREFERENCE": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 14, 15],  # Mask features 10..13
        "E_NO_SOLAR": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15],  # Mask feature 14
        "F_NO_TARIFF": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],  # Mask feature 15
        "G_MINIMAL": [0, 1, 2],  # Keep only t_in, h_in, t_out
    }

    records = []
    for abl_name, active_indices in ablation_masks.items():
        actions_chosen = []
        q_diffs = []
        for t_in, t_out, p_low, p_high, sol, tar, s_desc in test_states:
            state = WispEnvState(
                indoor_temperature_f=t_in,
                indoor_humidity_percent=50.0,
                outdoor_temperature_f=t_out,
                predicted_temperature_t5_f=t_in + 0.5,
                predicted_humidity_t5_percent=50.0,
                predicted_temperature_t15_f=t_in + 1.0,
                predicted_humidity_t15_percent=50.0,
                predicted_temperature_t30_f=t_in + 1.8,
                predicted_humidity_t30_percent=50.0,
                prediction_confidence=0.88,
                preferred_temperature_low_f=p_low,
                preferred_temperature_high_f=p_high,
                preferred_humidity_low_percent=30.0,
                preferred_humidity_high_percent=60.0,
                solar_power_kw=sol,
                tariff_currency_per_kwh=tar,
            )
            raw_obs = extract_dqn_observation(state)
            
            # Mask inactive features with neutral values (0.5)
            ablated_obs = np.full_like(raw_obs, 0.5, dtype=np.float32)
            for idx in active_indices:
                ablated_obs[idx] = raw_obs[idx]

            obs_t = torch.tensor(ablated_obs, dtype=torch.float32, device=agent.device).unsqueeze(0)
            with torch.no_grad():
                q_vals = agent.online_net(obs_t).cpu().numpy().flatten()

            best_idx = int(np.argmax(q_vals))
            actions_chosen.append(ACTION_LIST[best_idx].name)
            q_diffs.append(float(q_vals[best_idx] - q_vals[0]))

        # Calculate action distribution under ablation
        records.append({
            "ablation_variant": abl_name,
            "features_retained_count": len(active_indices),
            "dominant_action": pd.Series(actions_chosen).mode()[0],
            "action_entropy": round(float(-sum((actions_chosen.count(a)/len(actions_chosen)) * math.log(actions_chosen.count(a)/len(actions_chosen) + 1e-9) for a in set(actions_chosen))), 3),
            "mean_q_margin_over_no_action": round(float(np.mean(q_diffs)), 4),
            "all_actions": ", ".join(actions_chosen),
        })

    df = pd.DataFrame(records)
    df.to_csv(out_path / "ablation_study.csv", index=False)
    with open(out_path / "ablation_study.json", "w") as f:
        json.dump(records, f, indent=2)

    return df


# ----------------------------------------------------------------------
# PART 4: REWARD-WEIGHT SENSITIVITY
# ----------------------------------------------------------------------
def run_reward_sensitivity(
    checkpoint_path: str = "backend/models/saved_models/best_dqn_agent.pth",
    output_dir: str = "backend/app/rl/results",
) -> pd.DataFrame:
    """
    Evaluates policy response across 6 distinct reward weighting regimes.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    agent = DQNAgent()
    agent.load_checkpoint(checkpoint_path)
    pred_engine = NeuralPredictionEngine()

    weight_regimes = {
        "1_DEFAULT": RewardWeights(alpha=1.0, beta=0.1, gamma=0.01, delta=0.5, lambda_solar=0.05),
        "2_COMFORT_HEAVY": RewardWeights(alpha=5.0, beta=0.05, gamma=0.005, delta=0.1, lambda_solar=0.02),
        "3_ENERGY_HEAVY": RewardWeights(alpha=0.5, beta=1.0, gamma=0.01, delta=0.5, lambda_solar=0.05),
        "4_COST_HEAVY": RewardWeights(alpha=0.5, beta=0.1, gamma=0.1, delta=0.5, lambda_solar=0.05),
        "5_SWITCHING_HEAVY": RewardWeights(alpha=1.0, beta=0.1, gamma=0.01, delta=5.0, lambda_solar=0.05),
        "6_SOLAR_HEAVY": RewardWeights(alpha=1.0, beta=0.1, gamma=0.01, delta=0.5, lambda_solar=0.5),
    }

    records = []
    for regime_name, weights in weight_regimes.items():
        # Evaluate across 3 standard test scenarios
        total_rew = 0.0
        total_energy = 0.0
        total_cost = 0.0
        total_comfort = 0.0
        total_switches = 0
        total_solar = 0.0

        for t_in, t_out in [(72.0, 75.0), (77.0, 82.0), (79.0, 90.0)]:
            env = WispEnv(
                prediction_engine=pred_engine,
                reward_weights=weights,
                initial_indoor_temp_f=t_in,
                outdoor_temp_f=t_out,
                max_steps_per_episode=12,
            )
            state = env.reset()
            for step in range(12):
                action, _ = agent.select_action(state, evaluate=True)
                next_state, r, done, info = env.step(action)
                total_rew += r
                total_energy += info.get("energy_consumed_kWh", 0.0)
                total_cost += info.get("electricity_cost", 0.0)
                total_comfort += info.get("comfort_penalty", 0.0)
                total_switches += info.get("switching_penalty", 0.0)
                total_solar += info.get("solar_used_kWh", 0.0)
                state = next_state

        records.append({
            "weight_regime": regime_name,
            "alpha_comfort": weights.alpha,
            "beta_energy": weights.beta,
            "gamma_cost": weights.gamma,
            "delta_switching": weights.delta,
            "lambda_solar": weights.lambda_solar,
            "cumulative_reward": round(total_rew, 4),
            "total_comfort_penalty": round(total_comfort, 4),
            "total_energy_kwh": round(total_energy, 4),
            "total_cost": round(total_cost, 4),
            "total_switching_events": int(total_switches),
            "solar_used_kwh": round(total_solar, 4),
        })

    df = pd.DataFrame(records)
    df.to_csv(out_path / "reward_sensitivity.csv", index=False)
    with open(out_path / "reward_sensitivity.json", "w") as f:
        json.dump(records, f, indent=2)

    return df


# ----------------------------------------------------------------------
# PART 5: LONGER TRAINING DIAGNOSTIC
# ----------------------------------------------------------------------
def run_long_training_diagnostic(
    num_episodes: int = 300,
    steps_per_episode: int = 24,
    output_dir: str = "backend/app/rl/results",
    model_save_path: str = "backend/models/saved_models/dqn_phase10_long_training.pth",
) -> pd.DataFrame:
    """
    Executes a 300-episode x 24-step (7,200 transitions) training run to test
    whether policy collapse is resolved with increased sample experience.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    Path(model_save_path).parent.mkdir(parents=True, exist_ok=True)

    # Set seeds
    seed = 100
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    pred_engine = NeuralPredictionEngine()
    dqn_config = DQNConfig(
        learning_rate=5e-4,
        gamma=0.95,
        batch_size=64,
        replay_capacity=20000,
        target_update_freq=40,
        epsilon_start=1.00,
        epsilon_end=0.02,
        epsilon_decay=0.985,  # Decays smoothly over ~300 episodes
    )
    agent = DQNAgent(config=dqn_config, seed=seed)

    records = []
    print(f"Starting Phase 10 Long Training Diagnostic: {num_episodes} eps x {steps_per_episode} steps...")

    for ep in range(1, num_episodes + 1):
        # Diverse initial conditions
        init_t_in = random.uniform(69.0, 81.0)
        outdoor_t = random.uniform(65.0, 95.0)
        pref_low = random.uniform(21.0, 22.5)  # 69.8 - 72.5°F
        pref_high = random.uniform(23.5, 25.0) # 74.3 - 77.0°F

        prefs = OccupantPreferences(
            preferred_temperature_low_c=pref_low,
            preferred_temperature_high_c=pref_high,
        )

        env = WispEnv(
            prediction_engine=pred_engine,
            preferences=prefs,
            initial_indoor_temp_f=init_t_in,
            outdoor_temp_f=outdoor_t,
            max_steps_per_episode=steps_per_episode,
        )

        state = env.reset()
        obs = extract_dqn_observation(state)

        ep_reward = 0.0
        ep_energy = 0.0
        ep_cost = 0.0
        ep_comfort = 0.0
        ep_switches = 0
        action_counts = {a: 0 for a in WispAction}

        for step in range(steps_per_episode):
            # Select action with epsilon-greedy
            action, action_idx = agent.select_action(obs, evaluate=False)
            action_counts[action] += 1

            # Step environment
            next_state, reward, done, info = env.step(action)
            next_obs = extract_dqn_observation(next_state)

            # Store transition in replay buffer
            agent.replay_buffer.push(obs, action_idx, reward, next_obs, done)

            # Train update
            agent.update()
            if agent.total_steps % dqn_config.target_update_freq == 0:
                agent.sync_target_network()

            ep_reward += reward
            ep_energy += info.get("energy_consumed_kWh", 0.0)
            ep_cost += info.get("electricity_cost", 0.0)
            ep_comfort += info.get("comfort_penalty", 0.0)
            ep_switches += info.get("switching_penalty", 0.0)

            obs = next_obs
            state = next_state
            if done:
                break

        # Decay epsilon
        agent.decay_epsilon()

        rec = {
            "episode": ep,
            "reward": round(ep_reward, 4),
            "energy_kwh": round(ep_energy, 4),
            "cost": round(ep_cost, 4),
            "comfort_penalty": round(ep_comfort, 4),
            "switching_events": int(ep_switches),
            "no_action_pct": round(action_counts[WispAction.NO_ACTION] / steps_per_episode * 100.0, 1),
            "cool_low_pct": round(action_counts[WispAction.COOL_LOW] / steps_per_episode * 100.0, 1),
            "cool_medium_pct": round(action_counts[WispAction.COOL_MEDIUM] / steps_per_episode * 100.0, 1),
            "cool_high_pct": round(action_counts[WispAction.COOL_HIGH] / steps_per_episode * 100.0, 1),
            "precool_pct": round(action_counts[WispAction.PRECOOL] / steps_per_episode * 100.0, 1),
            "reduce_hvac_pct": round(action_counts[WispAction.REDUCE_HVAC] / steps_per_episode * 100.0, 1),
            "epsilon": round(agent.epsilon, 4),
        }
        records.append(rec)

    # Save checkpoint
    agent.save_checkpoint(model_save_path)

    # Save metrics
    df = pd.DataFrame(records)
    df.to_csv(out_path / "long_training_metrics.csv", index=False)
    with open(out_path / "long_training_metrics.json", "w") as f:
        json.dump(records, f, indent=2)

    return df


# ----------------------------------------------------------------------
# PART 6: POLICY DIVERSITY AND SCIENTIFIC SUMMARY
# ----------------------------------------------------------------------
def analyze_policy_diversity(
    stress_df: pd.DataFrame,
    long_train_df: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Computes Shannon action entropy, feature responsiveness, and policy contingency metrics.
    """
    action_counts = stress_df["selected_action"].value_counts().to_dict()
    total_samples = len(stress_df)

    probs = [cnt / total_samples for cnt in action_counts.values()]
    entropy = -sum(p * math.log(p) for p in probs if p > 0)

    # Check responsiveness to key context variables
    temp_corr = float(stress_df.groupby("initial_temp_f")["action_idx"].nunique().max())
    tar_corr = float(stress_df.groupby("tariff_currency_per_kwh")["action_idx"].nunique().max())
    sol_corr = float(stress_df.groupby("solar_kw")["action_idx"].nunique().max())
    pref_corr = float(stress_df.groupby("preference_envelope")["action_idx"].nunique().max())

    # Long training progression
    early_no_action = float(long_train_df.iloc[:30]["no_action_pct"].mean())
    late_no_action = float(long_train_df.iloc[-30]["no_action_pct"].mean())
    late_cool_med = float(long_train_df.iloc[-30]["cool_medium_pct"].mean())

    summary = {
        "total_stress_test_samples": total_samples,
        "unique_actions_in_stress_test": int(stress_df["selected_action"].nunique()),
        "action_entropy": round(entropy, 4),
        "action_distribution_pct": {k: round(v / total_samples * 100.0, 2) for k, v in action_counts.items()},
        "reacts_to_indoor_temperature": temp_corr > 1,
        "reacts_to_tariff": tar_corr > 1,
        "reacts_to_solar": sol_corr > 1,
        "reacts_to_comfort_preference": pref_corr > 1,
        "long_training_early_no_action_pct": round(early_no_action, 2),
        "long_training_late_no_action_pct": round(late_no_action, 2),
        "long_training_late_cool_medium_pct": round(late_cool_med, 2),
    }

    return summary


def run_all_phase10_diagnostics():
    """Runs all Phase 10 diagnostic experiments sequentially."""
    print("=== Phase 10: Part 1 - Q-Value Inspection ===")
    q_df = inspect_q_values()

    print("=== Phase 10: Part 2 - Stress-Test Matrix ===")
    stress_df = run_stress_test_matrix()

    print("=== Phase 10: Part 3 - Feature Ablations ===")
    abl_df = run_feature_ablations()

    print("=== Phase 10: Part 4 - Reward-Weight Sensitivity ===")
    rew_df = run_reward_sensitivity()

    print("=== Phase 10: Part 5 - Long-Training Diagnostic ===")
    long_df = run_long_training_diagnostic(num_episodes=300, steps_per_episode=24)

    print("=== Phase 10: Part 6 - Policy Diversity Analysis ===")
    div_summary = analyze_policy_diversity(stress_df, long_df)

    print("\n--- PHASE 10 DIAGNOSTIC SUMMARY ---")
    print(json.dumps(div_summary, indent=2))
    return q_df, stress_df, abl_df, rew_df, long_df, div_summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_all_phase10_diagnostics()

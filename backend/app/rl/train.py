"""
train.py
--------
Training pipeline for the Wisp DQN Agent (Phase 8).
Trains the DQN controller inside the validated WispEnv across diverse thermal episodes,
recording metrics, tracking losses, and checkpointing optimal weights.
"""

from dataclasses import dataclass, asdict
import json
from pathlib import Path
import random
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import torch

from backend.app.core.actions import WispAction
from backend.app.energy.tariff import TariffModel
from backend.app.energy.solar import SolarModel
from backend.app.personalization.preferences import OccupantPreferences
from backend.app.prediction.neural_engine import NeuralPredictionEngine
from backend.app.rl.agent import DQNAgent, DQNConfig
from backend.app.rl.observation import extract_dqn_observation
from backend.app.simulation.environment import WispEnv, WispEnvState


@dataclass
class TrainingConfig:
    """
    Configuration parameters for the Wisp RL training pipeline.
    """
    num_episodes: int = 60           # Total training episodes
    steps_per_episode: int = 12      # 12 steps x 5 min = 1 hour per episode
    seed: int = 42
    results_dir: str = "backend/app/rl/results"
    checkpoint_dir: str = "backend/models/saved_models"
    device: str = "cpu"
    dqn_config: Optional[DQNConfig] = None


def train_wisp_dqn(
    train_config: Optional[TrainingConfig] = None,
    prediction_engine: Optional[NeuralPredictionEngine] = None,
) -> Tuple[DQNAgent, pd.DataFrame]:
    """
    Executes the DQN training experiment inside WispEnv.

    Returns:
        Tuple of (trained DQNAgent, metrics DataFrame).
    """
    cfg = train_config or TrainingConfig()
    dqn_cfg = cfg.dqn_config or DQNConfig(
        learning_rate=1e-3,
        gamma=0.95,
        batch_size=32,
        replay_capacity=10000,
        target_update_freq=50,
        epsilon_start=1.00,
        epsilon_end=0.05,
        epsilon_decay=0.96, # Decays smoothly over 60 episodes
    )

    # Set seeds for reproducibility
    random.seed(cfg.seed)
    np.random.seed(cfg.seed)
    torch.manual_seed(cfg.seed)

    # Ensure output directories exist
    results_path = Path(cfg.results_dir)
    results_path.mkdir(parents=True, exist_ok=True)
    chkpt_path = Path(cfg.checkpoint_dir)
    chkpt_path.mkdir(parents=True, exist_ok=True)

    # Initialize Prediction Engine & Agent
    pred_engine = prediction_engine or NeuralPredictionEngine(device=cfg.device)
    agent = DQNAgent(config=dqn_cfg, device=cfg.device, seed=cfg.seed)

    metrics_records: List[Dict[str, Any]] = []
    best_reward = -float("inf")

    print(f"Starting Wisp DQN training: {cfg.num_episodes} episodes, {cfg.steps_per_episode} steps/episode...")

    for ep in range(1, cfg.num_episodes + 1):
        # -------------------------------------------------------------
        # DIVERSE EPISODE CONDITIONS GENERATION
        # -------------------------------------------------------------
        init_t_in = random.uniform(72.0, 79.0)     # Varied initial indoor temp
        init_h_in = random.uniform(45.0, 60.0)     # Varied initial indoor humidity
        outdoor_t = random.uniform(70.0, 92.0)     # Varied outdoor ambient temp
        outdoor_h = random.uniform(40.0, 75.0)     # Varied outdoor ambient humidity

        # Varied occupant preferences
        pref_low = random.uniform(22.0, 23.0)      # ~71.6 - 73.4°F
        pref_high = random.uniform(24.0, 25.5)     # ~75.2 - 77.9°F
        prefs = OccupantPreferences(
            preferred_temperature_low_c=pref_low,
            preferred_temperature_high_c=pref_high,
            preferred_humidity_low_percent=40.0,
            preferred_humidity_high_percent=60.0,
        )

        env = WispEnv(
            prediction_engine=pred_engine,
            preferences=prefs,
            initial_indoor_temp_f=init_t_in,
            initial_indoor_humidity=init_h_in,
            outdoor_temp_f=outdoor_t,
            outdoor_humidity=outdoor_h,
            max_steps_per_episode=cfg.steps_per_episode,
        )

        state = env.reset()
        obs = extract_dqn_observation(state)

        # Episode Accumulators
        ep_reward = 0.0
        ep_energy = 0.0
        ep_cost = 0.0
        ep_comfort_pen = 0.0
        ep_switches = 0
        ep_no_action_count = 0
        ep_losses: List[float] = []

        done = False
        prev_act_idx: Optional[int] = None

        while not done:
            action, action_idx = agent.select_action(obs, evaluate=False)

            if action == WispAction.NO_ACTION:
                ep_no_action_count += 1
            if prev_act_idx is not None and prev_act_idx != action_idx:
                ep_switches += 1

            next_state, reward, done, info = env.step(action)
            next_obs = extract_dqn_observation(next_state)

            # Store transition in replay memory
            agent.replay_buffer.push(obs, action_idx, reward, next_obs, done)

            # DQN Optimization Step
            loss = agent.update()
            if loss is not None:
                ep_losses.append(loss)

            # Accumulate diagnostics
            ep_reward += reward
            ep_energy += info["energy_consumed_kWh"]
            ep_cost += info["electricity_cost"]
            ep_comfort_pen += info["comfort_penalty"]

            obs = next_obs
            prev_act_idx = action_idx

        # Decay exploration rate epsilon at episode boundary
        agent.decay_epsilon()

        avg_loss = float(np.mean(ep_losses)) if ep_losses else 0.0
        no_action_pct = round((ep_no_action_count / cfg.steps_per_episode) * 100.0, 1)

        record = {
            "episode": ep,
            "total_reward": round(ep_reward, 4),
            "total_energy_kwh": round(ep_energy, 4),
            "total_cost": round(ep_cost, 4),
            "total_comfort_penalty": round(ep_comfort_pen, 4),
            "switching_count": ep_switches,
            "no_action_pct": no_action_pct,
            "epsilon": round(agent.epsilon, 4),
            "avg_loss": round(avg_loss, 6),
            "episode_length": cfg.steps_per_episode,
            "init_t_in": round(init_t_in, 2),
            "outdoor_t": round(outdoor_t, 2),
        }
        metrics_records.append(record)

        # Checkpoint Best Model
        if ep_reward > best_reward and len(agent.replay_buffer) >= dqn_cfg.batch_size:
            best_reward = ep_reward
            agent.save_checkpoint(
                chkpt_path / "best_dqn_agent.pth",
                metadata={"best_reward": best_reward, "episode": ep, "record": record}
            )

        if ep % 10 == 0 or ep == 1:
            print(f"Episode {ep:3d}/{cfg.num_episodes} | Reward: {ep_reward:7.3f} | Energy: {ep_energy:.3f} kWh | Cost: ${ep_cost:.3f} | NO_ACTION: {no_action_pct}% | eps: {agent.epsilon:.3f} | Loss: {avg_loss:.5f}")

    # Save Final Checkpoint
    agent.save_checkpoint(
        chkpt_path / "final_dqn_agent.pth",
        metadata={"final_reward": ep_reward, "episodes_trained": cfg.num_episodes}
    )

    # Save Metrics Files (CSV and JSON)
    df_metrics = pd.DataFrame(metrics_records)
    df_metrics["moving_avg_reward_10"] = df_metrics["total_reward"].rolling(window=10, min_periods=1).mean().round(4)
    
    csv_out = results_path / "training_metrics.csv"
    json_out = results_path / "training_metrics.json"

    df_metrics.to_csv(csv_out, index=False)
    with open(json_out, "w") as f:
        json.dump(metrics_records, f, indent=2)

    print(f"\nTraining Complete! Checkpoints and metrics saved to:\n  - {chkpt_path / 'best_dqn_agent.pth'}\n  - {csv_out}")
    return agent, df_metrics


if __name__ == "__main__":
    train_wisp_dqn()

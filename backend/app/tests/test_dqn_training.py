"""
test_dqn_training.py
--------------------
Focused test suite for Phase 8: Wisp DQN Agent Training.

Verifies:
1. QNetwork construction with 16 input features and 6 Q-values output
2. Observation extraction and normalization from WispEnvState
3. Exactly 6 Q-values returned by agent
4. Valid WispAction selection
5. ReplayBuffer insertion
6. ReplayBuffer mini-batch sampling
7. Epsilon-greedy exploration and decay
8. Target network weight synchronization
9. Single optimization step with gradient update
10. Checkpoint save and load
11. Short deterministic 3-episode training execution
12. End-to-end DQN <-> WispEnv interaction
"""

import math
from pathlib import Path
import pytest
import numpy as np
import torch

from backend.app.core.actions import WispAction
from backend.app.rl.observation import OBSERVATION_DIM, extract_dqn_observation
from backend.app.rl.dqn import QNetwork, ACTION_DIM
from backend.app.rl.replay_buffer import ReplayBuffer
from backend.app.rl.agent import DQNAgent, DQNConfig
from backend.app.rl.train import train_wisp_dqn, TrainingConfig
from backend.app.simulation.environment import WispEnv, WispEnvState
from backend.app.prediction.neural_engine import NeuralPredictionEngine


@pytest.fixture
def env():
    return WispEnv(
        initial_indoor_temp_f=75.0,
        outdoor_temp_f=85.0,
        max_steps_per_episode=6,
    )


@pytest.fixture
def agent():
    config = DQNConfig(
        learning_rate=1e-3,
        gamma=0.95,
        batch_size=8,
        replay_capacity=100,
        target_update_freq=10,
        epsilon_start=1.0,
        epsilon_end=0.1,
        epsilon_decay=0.9,
    )
    return DQNAgent(config=config, device="cpu", seed=42)


# 1. QNetwork construction
def test_1_q_network_construction():
    net = QNetwork(input_dim=16, output_dim=6, hidden_dims=[128, 64])
    x = torch.randn(4, 16)
    q_vals = net(x)
    assert q_vals.shape == (4, 6)
    assert not torch.isnan(q_vals).any()


# 2. Observation extraction & normalization
def test_2_observation_extraction(env):
    state = env.reset()
    obs = extract_dqn_observation(state)
    assert isinstance(obs, np.ndarray)
    assert obs.shape == (16,)
    assert obs.dtype == np.float32
    assert not np.isnan(obs).any()
    assert not np.isinf(obs).any()


# 3 & 4. Exactly 6 Q-values & valid action selection
def test_3_4_q_values_and_action_selection(agent, env):
    state = env.reset()
    q_vals = agent.get_q_values(state)
    assert q_vals.shape == (6,)
    assert all(math.isfinite(q) for q in q_vals)

    action, action_idx = agent.select_action(state, evaluate=True)
    assert isinstance(action, WispAction)
    assert 0 <= action_idx <= 5


# 5 & 6. ReplayBuffer push and sample
def test_5_6_replay_buffer_push_sample():
    buf = ReplayBuffer(capacity=50, seed=42)
    s = np.zeros(16, dtype=np.float32)
    s_next = np.ones(16, dtype=np.float32)

    for i in range(20):
        buf.push(s, i % 6, float(i * 0.1), s_next, False)

    assert len(buf) == 20
    states, actions, rewards, next_states, dones = buf.sample(8, device="cpu")
    assert states.shape == (8, 16)
    assert actions.shape == (8, 1)
    assert rewards.shape == (8, 1)
    assert next_states.shape == (8, 16)
    assert dones.shape == (8, 1)


# 7. Epsilon-greedy exploration & decay
def test_7_epsilon_greedy_decay(agent):
    assert agent.epsilon == 1.0
    agent.decay_epsilon()
    assert agent.epsilon == pytest.approx(0.9)
    for _ in range(30):
        agent.decay_epsilon()
    assert agent.epsilon >= agent.config.epsilon_end


# 8. Target network synchronization
def test_8_target_network_sync(agent):
    # Modify online weights
    with torch.no_grad():
        for param in agent.online_net.parameters():
            param.add_(1.0)

    # Sync
    agent.sync_target_network()
    for p_online, p_target in zip(agent.online_net.parameters(), agent.target_net.parameters()):
        assert torch.equal(p_online, p_target)


# 9. Single optimization step
def test_9_optimization_step(agent, env):
    state = env.reset()
    obs = extract_dqn_observation(state)

    for _ in range(16):
        action, action_idx = agent.select_action(obs)
        next_state, reward, done, _ = env.step(action)
        next_obs = extract_dqn_observation(next_state)
        agent.replay_buffer.push(obs, action_idx, reward, next_obs, done)
        obs = next_obs

    loss = agent.update()
    assert loss is not None
    assert math.isfinite(loss)
    assert loss >= 0.0


# 10. Checkpoint save and load
def test_10_checkpoint_save_load(agent, tmp_path):
    chkpt_file = tmp_path / "test_dqn_checkpoint.pth"
    agent.save_checkpoint(chkpt_file, metadata={"test_key": "test_val"})

    assert chkpt_file.exists()

    new_agent = DQNAgent(device="cpu", seed=42)
    meta = new_agent.load_checkpoint(chkpt_file)

    assert meta["test_key"] == "test_val"
    for p1, p2 in zip(agent.online_net.parameters(), new_agent.online_net.parameters()):
        assert torch.equal(p1, p2)


# 11 & 12. Short training execution & end-to-end WispEnv interaction
def test_11_12_short_training_run(tmp_path):
    cfg = TrainingConfig(
        num_episodes=3,
        steps_per_episode=6,
        results_dir=str(tmp_path / "results"),
        checkpoint_dir=str(tmp_path / "checkpoints"),
        dqn_config=DQNConfig(
            batch_size=4,
            replay_capacity=50,
            target_update_freq=5,
        ),
    )
    trained_agent, df_metrics = train_wisp_dqn(train_config=cfg)

    assert trained_agent is not None
    assert len(df_metrics) == 3
    assert "total_reward" in df_metrics.columns
    assert (tmp_path / "results" / "training_metrics.csv").exists()
    assert (tmp_path / "results" / "training_metrics.json").exists()
    assert (tmp_path / "checkpoints" / "final_dqn_agent.pth").exists()

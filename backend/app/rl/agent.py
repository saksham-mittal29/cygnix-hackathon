"""
agent.py
--------
Deep Q-Network (DQNAgent) implementation for Wisp Person 3 (Phase 8).
Manages online and target networks, epsilon-greedy exploration, experience replay,
Bellman loss updates, and checkpoint serialization.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
import random
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from backend.app.core.actions import WispAction
from backend.app.rl.observation import OBSERVATION_DIM, extract_dqn_observation
from backend.app.rl.dqn import QNetwork, ACTION_DIM
from backend.app.rl.replay_buffer import ReplayBuffer
from backend.app.simulation.environment import WispEnvState

ACTION_LIST = [
    WispAction.NO_ACTION,
    WispAction.COOL_LOW,
    WispAction.COOL_MEDIUM,
    WispAction.COOL_HIGH,
    WispAction.PRECOOL,
    WispAction.REDUCE_HVAC,
]


@dataclass
class DQNConfig:
    """
    Hyperparameter configuration for DQNAgent.
    """
    learning_rate: float = 1e-3
    gamma: float = 0.95            # Discount factor for 5-minute timestep horizon
    batch_size: int = 64
    replay_capacity: int = 10000
    target_update_freq: int = 100  # Steps between target network sync
    epsilon_start: float = 1.00
    epsilon_end: float = 0.05
    epsilon_decay: float = 0.995   # Multiplicative decay per episode
    hidden_dims: List[int] = None

    def __post_init__(self):
        if self.hidden_dims is None:
            self.hidden_dims = [128, 64]


class DQNAgent:
    """
    DQN Agent for learning optimal Wisp discrete HVAC control policies.
    """

    def __init__(
        self,
        config: Optional[DQNConfig] = None,
        device: str = "cpu",
        seed: Optional[int] = 42,
    ):
        self.config = config or DQNConfig()
        self.device = torch.device(device)
        self.seed = seed

        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
            torch.manual_seed(seed)

        # Networks: Online Q and Target Q
        self.online_net = QNetwork(
            input_dim=OBSERVATION_DIM,
            output_dim=ACTION_DIM,
            hidden_dims=self.config.hidden_dims,
        ).to(self.device)

        self.target_net = QNetwork(
            input_dim=OBSERVATION_DIM,
            output_dim=ACTION_DIM,
            hidden_dims=self.config.hidden_dims,
        ).to(self.device)

        self.sync_target_network()
        self.target_net.eval()

        # Optimizer & Loss Function
        self.optimizer = optim.Adam(self.online_net.parameters(), lr=self.config.learning_rate)
        self.loss_fn = nn.SmoothL1Loss()  # Huber Loss for stable gradients

        # Replay Memory
        self.replay_buffer = ReplayBuffer(capacity=self.config.replay_capacity, seed=seed)

        # Runtime Tracking
        self.epsilon = self.config.epsilon_start
        self.total_steps = 0
        self.total_updates = 0

    def sync_target_network(self) -> None:
        """Copies weights from online network to target network."""
        self.target_net.load_state_dict(self.online_net.state_dict())

    def select_action(
        self,
        state: Union[WispEnvState, Dict[str, Any], np.ndarray],
        evaluate: bool = False,
    ) -> Tuple[WispAction, int]:
        """
        Selects a Wisp action using epsilon-greedy policy (or greedy during evaluation).

        Args:
            state: WispEnvState, dictionary, or extracted feature array.
            evaluate: If True, disables exploration and selects argmax Q(s, a).

        Returns:
            Tuple of (WispAction enum, integer action index 0-5).
        """
        if isinstance(state, (WispEnvState, dict)):
            obs = extract_dqn_observation(state)
        elif isinstance(state, np.ndarray):
            obs = state.astype(np.float32)
        else:
            raise TypeError(f"Invalid state format: {type(state).__name__}")

        # Epsilon-greedy exploration
        if not evaluate and random.random() < self.epsilon:
            action_idx = random.randint(0, ACTION_DIM - 1)
        else:
            obs_t = torch.tensor(obs, dtype=torch.float32, device=self.device).unsqueeze(0)
            self.online_net.eval()
            with torch.no_grad():
                q_values = self.online_net(obs_t)
            action_idx = int(torch.argmax(q_values, dim=1).item())
            self.online_net.train()

        return ACTION_LIST[action_idx], action_idx

    def get_q_values(self, state: Union[WispEnvState, Dict[str, Any], np.ndarray]) -> np.ndarray:
        """Returns the 6 Q-values for the given state."""
        if isinstance(state, (WispEnvState, dict)):
            obs = extract_dqn_observation(state)
        elif isinstance(state, np.ndarray):
            obs = state.astype(np.float32)
        else:
            raise TypeError(f"Invalid state format: {type(state).__name__}")

        obs_t = torch.tensor(obs, dtype=torch.float32, device=self.device).unsqueeze(0)
        self.online_net.eval()
        with torch.no_grad():
            q_values = self.online_net(obs_t)
        return q_values.squeeze().cpu().numpy()

    def update(self) -> Optional[float]:
        """
        Samples a mini-batch from the replay buffer and performs one gradient update step.

        Returns:
            Scalar loss value (or None if buffer has fewer samples than batch_size).
        """
        if len(self.replay_buffer) < self.config.batch_size:
            return None

        states, actions, rewards, next_states, dones = self.replay_buffer.sample(
            self.config.batch_size, device=self.device
        )

        # 1. Compute current Q(s, a) estimates
        self.online_net.train()
        q_eval = self.online_net(states).gather(1, actions)

        # 2. Compute Target Q-values using Target Network: y = r + gamma * max_a' Q_target(s', a') * (1 - done)
        with torch.no_grad():
            q_next = self.target_net(next_states).max(dim=1, keepdim=True)[0]
            q_target = rewards + (self.config.gamma * q_next * (1.0 - dones))

        # 3. Compute loss and optimize
        loss = self.loss_fn(q_eval, q_target)

        self.optimizer.zero_grad()
        loss.backward()
        # Gradient clipping for numerical stability
        torch.nn.utils.clip_grad_norm_(self.online_net.parameters(), max_norm=10.0)
        self.optimizer.step()

        self.total_updates += 1
        self.total_steps += 1

        # Periodic Target Network synchronization
        if self.total_steps % self.config.target_update_freq == 0:
            self.sync_target_network()

        return float(loss.item())

    def decay_epsilon(self) -> None:
        """Decays exploration rate epsilon at episode boundaries."""
        self.epsilon = max(self.config.epsilon_end, self.epsilon * self.config.epsilon_decay)

    def save_checkpoint(
        self,
        filepath: Union[str, Path],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Saves agent weights, optimizer state, and configuration to disk.
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        checkpoint = {
            "online_net_state_dict": self.online_net.state_dict(),
            "target_net_state_dict": self.target_net.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "config": asdict(self.config),
            "epsilon": self.epsilon,
            "total_steps": self.total_steps,
            "total_updates": self.total_updates,
            "observation_dim": OBSERVATION_DIM,
            "action_dim": ACTION_DIM,
            "metadata": metadata or {},
        }
        torch.save(checkpoint, path)

    def load_checkpoint(self, filepath: Union[str, Path]) -> Dict[str, Any]:
        """
        Loads agent weights and configuration from disk.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Checkpoint not found at: {path}")

        checkpoint = torch.load(path, map_location=self.device)
        self.online_net.load_state_dict(checkpoint["online_net_state_dict"])
        self.target_net.load_state_dict(checkpoint["target_net_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.epsilon = checkpoint.get("epsilon", self.config.epsilon_end)
        self.total_steps = checkpoint.get("total_steps", 0)
        self.total_updates = checkpoint.get("total_updates", 0)

        return checkpoint.get("metadata", {})

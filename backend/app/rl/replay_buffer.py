"""
replay_buffer.py
----------------
Experience Replay Buffer for Wisp DQN Agent (Phase 8).
Stores (state, action, reward, next_state, done) transitions and yields randomized mini-batches.
"""

from collections import deque
import random
from typing import Deque, List, Optional, Tuple, Union
import numpy as np
import torch


class ReplayBuffer:
    """
    Circular experience replay buffer for off-policy DQN training.
    """

    def __init__(self, capacity: int = 10000, seed: Optional[int] = 42):
        self.capacity = capacity
        self.buffer: Deque[Tuple[np.ndarray, int, float, np.ndarray, bool]] = deque(maxlen=capacity)
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

    def push(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
    ) -> None:
        """Appends a transition tuple to the replay memory."""
        self.buffer.append((
            np.array(state, dtype=np.float32),
            int(action),
            float(reward),
            np.array(next_state, dtype=np.float32),
            bool(done),
        ))

    def sample(
        self,
        batch_size: int,
        device: Union[str, torch.device] = "cpu",
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Samples a mini-batch of transitions as PyTorch tensors.

        Returns:
            Tuple of (states, actions, rewards, next_states, dones)
        """
        if len(self.buffer) < batch_size:
            raise ValueError(f"Cannot sample batch of size {batch_size} from buffer of size {len(self.buffer)}")

        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        t_states = torch.tensor(np.array(states), dtype=torch.float32, device=device)
        t_actions = torch.tensor(np.array(actions), dtype=torch.long, device=device).unsqueeze(1)
        t_rewards = torch.tensor(np.array(rewards), dtype=torch.float32, device=device).unsqueeze(1)
        t_next_states = torch.tensor(np.array(next_states), dtype=torch.float32, device=device)
        t_dones = torch.tensor(np.array(dones), dtype=torch.float32, device=device).unsqueeze(1)

        return t_states, t_actions, t_rewards, t_next_states, t_dones

    def __len__(self) -> int:
        return len(self.buffer)

"""
dqn.py
------
PyTorch Deep Q-Network (QNetwork) for Wisp Person 3 (Phase 8).
Maps a 16-dimensional observation vector to exactly 6 Q-values corresponding to the discrete action space:
0: NO_ACTION
1: COOL_LOW
2: COOL_MEDIUM
3: COOL_HIGH
4: PRECOOL
5: REDUCE_HVAC
"""

from typing import List, Optional
import torch
import torch.nn as nn

from backend.app.rl.observation import OBSERVATION_DIM
from backend.app.core.actions import WispAction

ACTION_DIM = len(WispAction)  # Exactly 6 actions


class QNetwork(nn.Module):
    """
    Multi-layer perceptron (MLP) approximating the Q-function Q(s, a).
    """

    def __init__(
        self,
        input_dim: int = OBSERVATION_DIM,
        output_dim: int = ACTION_DIM,
        hidden_dims: Optional[List[int]] = None,
    ):
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.hidden_dims = hidden_dims or [128, 64]

        layers: List[nn.Module] = []
        prev_dim = input_dim
        for h_dim in self.hidden_dims:
            layers.append(nn.Linear(prev_dim, h_dim))
            layers.append(nn.ReLU())
            prev_dim = h_dim

        # Final Q-value output layer
        layers.append(nn.Linear(prev_dim, output_dim))

        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Computes Q-values for all 6 discrete Wisp actions given state tensor x.

        Args:
            x: Tensor of shape (batch_size, input_dim) or (input_dim,)

        Returns:
            Q-values tensor of shape (batch_size, 6) or (6,)
        """
        return self.network(x)

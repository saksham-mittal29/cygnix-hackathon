"""
actions.py
----------
Core action definitions for Wisp Person 3 simulation and control.
Maintains the exact 6-action discrete action space and their simulation control intensities.
"""

from enum import Enum
from typing import Dict


class WispAction(str, Enum):
    """
    Discrete action space for Wisp HVAC and thermal management.
    """
    NO_ACTION = "NO_ACTION"
    COOL_LOW = "COOL_LOW"
    COOL_MEDIUM = "COOL_MEDIUM"
    COOL_HIGH = "COOL_HIGH"
    PRECOOL = "PRECOOL"
    REDUCE_HVAC = "REDUCE_HVAC"

    def __str__(self) -> str:
        return self.value


# Simulation cooling intensity fractions [0.0 to 1.0]
# Note: These represent simulation control intensities, NOT claims about real Ecobee compressor staging.
ACTION_COOLING_INTENSITY: Dict[WispAction, float] = {
    WispAction.NO_ACTION: 0.0,
    WispAction.COOL_LOW: 0.33,
    WispAction.COOL_MEDIUM: 0.66,
    WispAction.COOL_HIGH: 1.00,
    WispAction.PRECOOL: 1.00,
    WispAction.REDUCE_HVAC: 0.0,
}


def get_cooling_intensity(action: WispAction) -> float:
    """Returns the simulation cooling intensity fraction for a given action."""
    if not isinstance(action, WispAction):
        raise TypeError(f"Expected WispAction instance, got {type(action).__name__}")
    return ACTION_COOLING_INTENSITY[action]


def is_cooling_active(action: WispAction) -> bool:
    """Returns True if the action demands active cooling power."""
    return get_cooling_intensity(action) > 0.0

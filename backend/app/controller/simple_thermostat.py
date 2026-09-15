"""
Simple Thermostat Baseline Controller for Wisp System.

A transparent, reactive baseline without access to:
- Predictive horizons (+5, +15, +30 min)
- Conformal prediction confidence
- Dynamic tariff rates
- Solar generation forecasts
- Q-values or neural representations

Operates solely on instantaneous indoor temperature vs. preferred temperature bounds.
"""

from backend.app.core.actions import WispAction
from backend.app.simulation.environment import WispEnvState


class SimpleThermostatController:
    """
    Standard reactive thermostat controller with deadband.
    """

    def __init__(self, deadband_f: float = 0.5):
        self.deadband_f = deadband_f
        self.last_action: WispAction = WispAction.NO_ACTION

    def select_action(self, state: WispEnvState) -> WispAction:
        """
        Select action based purely on current indoor temperature and preference bounds.
        """
        t_in = state.indoor_temperature_f
        high = state.preferred_temperature_high_f
        low = state.preferred_temperature_low_f

        if t_in > high + 2.0:
            action = WispAction.COOL_HIGH
        elif t_in > high + self.deadband_f:
            action = WispAction.COOL_MEDIUM
        elif t_in > high:
            action = WispAction.COOL_LOW
        elif t_in < low - self.deadband_f:
            action = WispAction.REDUCE_HVAC
        else:
            action = WispAction.NO_ACTION

        self.last_action = action
        return action

    def reset(self):
        self.last_action = WispAction.NO_ACTION

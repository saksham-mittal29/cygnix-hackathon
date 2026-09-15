"""
base.py
-------
Abstract Base Class for the Wisp Prediction Engine.
Defines the clean, standardized prediction interface contract.

Person 2's real ML model (LSTM / Neural State-Space / Physics-Informed) will
subclass this BasePredictionEngine and return a PredictionResult.
"""

from abc import ABC, abstractmethod
from backend.app.core.types import (
    ThermalState,
    Disturbance,
    PredictionResult,
)
from backend.app.core.actions import WispAction


class BasePredictionEngine(ABC):
    """
    Abstract prediction engine interface for Wisp thermal dynamics.
    
    Contract:
    Given:
      - current_thermal: Current indoor temperature, humidity, setpoints
      - action: Control decision executed over the 5-minute timestep
      - disturbance: Outdoor temperature, humidity, solar irradiance, time
    Returns:
      - PredictionResult: Forecasted trajectory at +5, +15, and +30 minutes with confidence score.
    """

    @abstractmethod
    def predict(
        self,
        current_thermal: ThermalState,
        action: WispAction,
        disturbance: Disturbance,
    ) -> PredictionResult:
        """
        Generates thermal trajectory predictions for +5, +15, and +30 minutes.

        Args:
            current_thermal: Current building thermal state at timestamp t.
            action: Wisp control action taken during [t, t + 5min].
            disturbance: Outdoor and environmental disturbance during [t, t + 5min].

        Returns:
            PredictionResult containing:
                - temp_t5, temp_t15, temp_t30
                - hum_t5, hum_t15, hum_t30
                - confidence
        """
        pass

    @property
    def engine_name(self) -> str:
        """Returns the human-readable identifier of the prediction engine."""
        return self.__class__.__name__

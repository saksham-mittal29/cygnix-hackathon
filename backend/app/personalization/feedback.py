"""
feedback.py
-----------
Occupant interaction and feedback data model for Wisp Person 3.
Captures explicit user responses (ACCEPT vs OVERRIDE) and environmental context.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Any, Optional
from backend.app.core.actions import WispAction


class UserResponse(str, Enum):
    """
    Occupant response type to automated recommendation.
    """
    ACCEPT = "ACCEPT"      # Occupant accepted / did not intervene
    OVERRIDE = "OVERRIDE"  # Occupant chose a manual action


@dataclass(frozen=True)
class FeedbackRecord:
    """
    Detailed record of an occupant interaction event.
    """
    timestamp: Any
    occupant_id: str
    recommended_action: WispAction
    user_response: UserResponse
    actual_user_action: Optional[WispAction]
    indoor_temperature_c: float
    indoor_humidity_percent: float
    prediction_confidence: Optional[float] = None
    tariff_currency_per_kwh: Optional[float] = None

    def __post_init__(self):
        # Validate that actual_user_action is provided when OVERRIDE is specified
        if self.user_response == UserResponse.OVERRIDE:
            if self.actual_user_action is None:
                raise ValueError("actual_user_action must be provided when user_response is OVERRIDE")
        elif self.user_response == UserResponse.ACCEPT:
            if self.actual_user_action is not None and self.actual_user_action != self.recommended_action:
                raise ValueError("actual_user_action cannot differ from recommended_action when user_response is ACCEPT")

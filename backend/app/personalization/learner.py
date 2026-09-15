"""
learner.py
----------
Incremental and statistical preference learner for Wisp Person 3.
Gradually adapts occupant comfort preferences based on explicit ACCEPT and OVERRIDE events.
"""

from typing import List, Optional
from backend.app.core.actions import WispAction, is_cooling_active
from backend.app.personalization.preferences import OccupantPreferences
from backend.app.personalization.feedback import FeedbackRecord, UserResponse


class PreferenceLearner:
    """
    Incremental learner that updates occupant comfort boundaries safely and gradually.
    Avoids drastic reactions to single isolated events.
    """

    def __init__(
        self,
        learning_rate: float = 0.05,
        max_single_step_delta_c: float = 0.1,
        min_preference_band_width_c: float = 1.0,
    ):
        """
        Initializes PreferenceLearner.

        Args:
            learning_rate: Adaptation rate factor (default: 0.05).
            max_single_step_delta_c: Maximum temperature shift allowed in a single event (°C).
            min_preference_band_width_c: Minimum allowable width between low and high setpoints (°C).
        """
        if not (0.0 < learning_rate <= 0.5):
            raise ValueError(f"learning_rate must be in (0, 0.5], got {learning_rate}")
        if max_single_step_delta_c <= 0:
            raise ValueError(f"max_single_step_delta_c must be positive, got {max_single_step_delta_c}")

        self.learning_rate = learning_rate
        self.max_single_step_delta_c = max_single_step_delta_c
        self.min_band_width_c = min_preference_band_width_c

    def update(
        self,
        preferences: OccupantPreferences,
        feedback: FeedbackRecord,
    ) -> OccupantPreferences:
        """
        Calculates an incremental update to OccupantPreferences based on one feedback event.

        Args:
            preferences: Current OccupantPreferences.
            feedback: FeedbackRecord event.

        Returns:
            Updated OccupantPreferences with bounded shifts.
        """
        new_low_c = preferences.preferred_temperature_low_c
        new_high_c = preferences.preferred_temperature_high_c
        temp = feedback.indoor_temperature_c

        if feedback.user_response == UserResponse.OVERRIDE:
            # Case 1: Occupant manually triggered cooling (feels warm)
            if feedback.actual_user_action in [WispAction.COOL_LOW, WispAction.COOL_MEDIUM, WispAction.COOL_HIGH, WispAction.PRECOOL]:
                if temp >= preferences.preferred_temperature_low_c:
                    discrepancy = preferences.preferred_temperature_high_c - temp
                    calculated_step = self.learning_rate * abs(discrepancy) if discrepancy != 0 else self.learning_rate * 0.5
                    step = min(self.max_single_step_delta_c, max(0.01, calculated_step))
                    new_high_c -= step

            # Case 2: Occupant reduced cooling / turned off HVAC (feels cool or saving cost)
            elif feedback.actual_user_action in [WispAction.REDUCE_HVAC, WispAction.NO_ACTION]:
                if temp <= preferences.preferred_temperature_high_c:
                    step = min(self.max_single_step_delta_c, self.learning_rate * 0.5)
                    new_low_c += step

        elif feedback.user_response == UserResponse.ACCEPT:
            # Acceptance confirms comfort at current temperature
            if abs(temp - preferences.preferred_temperature_high_c) < 0.5:
                step = min(self.max_single_step_delta_c * 0.2, self.learning_rate * 0.1)
                new_high_c += step
            elif abs(temp - preferences.preferred_temperature_low_c) < 0.5:
                step = min(self.max_single_step_delta_c * 0.2, self.learning_rate * 0.1)
                new_low_c -= step

        # Apply Guardrails & Enforce Minimum Band Width
        new_low_c = max(preferences.min_temp_bound_c, min(preferences.max_temp_bound_c - self.min_band_width_c, new_low_c))
        new_high_c = max(new_low_c + self.min_band_width_c, min(preferences.max_temp_bound_c, new_high_c))

        return OccupantPreferences(
            occupant_id=preferences.occupant_id,
            preferred_temperature_low_c=round(new_low_c, 4),
            preferred_temperature_high_c=round(new_high_c, 4),
            preferred_humidity_low_percent=preferences.preferred_humidity_low_percent,
            preferred_humidity_high_percent=preferences.preferred_humidity_high_percent,
            min_temp_bound_c=preferences.min_temp_bound_c,
            max_temp_bound_c=preferences.max_temp_bound_c,
            min_humidity_bound_pct=preferences.min_humidity_bound_pct,
            max_humidity_bound_pct=preferences.max_humidity_bound_pct,
        )

    def batch_update(
        self,
        preferences: OccupantPreferences,
        feedbacks: List[FeedbackRecord],
    ) -> OccupantPreferences:
        """Applies a sequence of feedback records sequentially to update preferences."""
        current_pref = preferences
        for fb in feedbacks:
            current_pref = self.update(current_pref, fb)
        return current_pref

"""
test_personalization.py
-----------------------
Unit tests for Phase 3: Occupant Personalization.

Tests:
A. Default preference creation
B. Custom preference creation
C. Comfortable temperature
D. Temperature below preferred range
E. Temperature above preferred range
F. Humidity inside preferred range
G. Humidity outside preferred range
H. Combined comfort penalty
I. ACCEPT feedback
J. OVERRIDE feedback
K. Override with actual user action
L. Accepted action with no actual override
M. Repeated feedback updates preference gradually
N. One override does NOT cause a dramatic preference change
O. Preference values remain within reasonable configured bounds
P. Invalid temperature/humidity inputs are handled correctly
"""

import pytest
from datetime import datetime
from backend.app.core.actions import WispAction
from backend.app.personalization.preferences import (
    OccupantPreferences,
    create_eco_profile,
    create_comfort_first_profile,
)
from backend.app.personalization.comfort_model import ComfortModel
from backend.app.personalization.feedback import FeedbackRecord, UserResponse
from backend.app.personalization.learner import PreferenceLearner


# Test A: Default preference creation
def test_a_default_preference_creation():
    pref = OccupantPreferences()
    assert pref.occupant_id == "default_occupant"
    assert pref.preferred_temperature_low_c == 23.0
    assert pref.preferred_temperature_high_c == 25.0
    assert pref.preferred_humidity_low_percent == 40.0
    assert pref.preferred_humidity_high_percent == 60.0


# Test B: Custom preference creation
def test_b_custom_preference_creation():
    pref = OccupantPreferences(
        occupant_id="user_123",
        preferred_temperature_low_c=21.5,
        preferred_temperature_high_c=24.5,
        preferred_humidity_low_percent=35.0,
        preferred_humidity_high_percent=55.0,
    )
    assert pref.occupant_id == "user_123"
    assert pref.preferred_temperature_low_c == 21.5
    assert pref.preferred_temperature_high_c == 24.5


# Test C: Comfortable temperature
def test_c_comfortable_temperature():
    pref = OccupantPreferences(preferred_temperature_low_c=23.0, preferred_temperature_high_c=25.0)
    res = ComfortModel.evaluate(indoor_temp_c=24.0, indoor_humidity_pct=50.0, preferences=pref)
    assert res.is_comfortable is True
    assert res.temperature_deviation_c == 0.0
    assert res.temperature_penalty == 0.0
    assert res.comfort_penalty == 0.0


# Test D: Temperature below preferred range
def test_d_temperature_below_preferred_range():
    pref = OccupantPreferences(preferred_temperature_low_c=23.0, preferred_temperature_high_c=25.0)
    res = ComfortModel.evaluate(indoor_temp_c=21.0, indoor_humidity_pct=50.0, preferences=pref)
    assert res.is_comfortable is False
    assert res.temperature_deviation_c == 2.0
    assert res.temperature_penalty > 0.0
    assert res.humidity_penalty == 0.0


# Test E: Temperature above preferred range
def test_e_temperature_above_preferred_range():
    pref = OccupantPreferences(preferred_temperature_low_c=23.0, preferred_temperature_high_c=25.0)
    res = ComfortModel.evaluate(indoor_temp_c=27.0, indoor_humidity_pct=50.0, preferences=pref)
    assert res.is_comfortable is False
    assert res.temperature_deviation_c == 2.0
    assert res.temperature_penalty > 0.0


# Test F: Humidity inside preferred range
def test_f_humidity_inside_preferred_range():
    pref = OccupantPreferences(preferred_humidity_low_percent=40.0, preferred_humidity_high_percent=60.0)
    res = ComfortModel.evaluate(indoor_temp_c=24.0, indoor_humidity_pct=45.0, preferences=pref)
    assert res.is_comfortable is True
    assert res.humidity_deviation_percent == 0.0
    assert res.humidity_penalty == 0.0


# Test G: Humidity outside preferred range
def test_g_humidity_outside_preferred_range():
    pref = OccupantPreferences(preferred_humidity_low_percent=40.0, preferred_humidity_high_percent=60.0)
    res = ComfortModel.evaluate(indoor_temp_c=24.0, indoor_humidity_pct=75.0, preferences=pref)
    assert res.is_comfortable is False
    assert res.humidity_deviation_percent == 15.0
    assert res.humidity_penalty > 0.0
    assert res.temperature_penalty == 0.0


# Test H: Combined comfort penalty
def test_h_combined_comfort_penalty():
    pref = OccupantPreferences(
        preferred_temperature_low_c=23.0,
        preferred_temperature_high_c=25.0,
        preferred_humidity_low_percent=40.0,
        preferred_humidity_high_percent=60.0,
    )
    res = ComfortModel.evaluate(indoor_temp_c=27.0, indoor_humidity_pct=70.0, preferences=pref)
    assert res.is_comfortable is False
    assert res.temperature_deviation_c == 2.0
    assert res.humidity_deviation_percent == 10.0
    assert res.comfort_penalty == pytest.approx(res.temperature_penalty + res.humidity_penalty, rel=1e-4)


# Test I: ACCEPT feedback
def test_i_accept_feedback():
    fb = FeedbackRecord(
        timestamp=datetime(2026, 7, 1, 14, 0),
        occupant_id="occ_1",
        recommended_action=WispAction.NO_ACTION,
        user_response=UserResponse.ACCEPT,
        actual_user_action=None,
        indoor_temperature_c=24.0,
        indoor_humidity_percent=50.0,
        prediction_confidence=0.95,
        tariff_currency_per_kwh=10.0,
    )
    assert fb.user_response == UserResponse.ACCEPT
    assert fb.actual_user_action is None


# Test J & K: OVERRIDE feedback with actual user action
def test_j_k_override_feedback():
    fb = FeedbackRecord(
        timestamp=datetime(2026, 7, 1, 14, 5),
        occupant_id="occ_1",
        recommended_action=WispAction.NO_ACTION,
        user_response=UserResponse.OVERRIDE,
        actual_user_action=WispAction.COOL_LOW,
        indoor_temperature_c=25.8,
        indoor_humidity_percent=55.0,
    )
    assert fb.user_response == UserResponse.OVERRIDE
    assert fb.actual_user_action == WispAction.COOL_LOW


# Test L: Accepted action with no actual override
def test_l_accepted_action_validation():
    fb1 = FeedbackRecord(
        timestamp=100,
        occupant_id="occ_1",
        recommended_action=WispAction.COOL_LOW,
        user_response=UserResponse.ACCEPT,
        actual_user_action=WispAction.COOL_LOW,
        indoor_temperature_c=24.0,
        indoor_humidity_percent=50.0,
    )
    assert fb1.user_response == UserResponse.ACCEPT

    with pytest.raises(ValueError):
        FeedbackRecord(
            timestamp=100,
            occupant_id="occ_1",
            recommended_action=WispAction.NO_ACTION,
            user_response=UserResponse.OVERRIDE,
            actual_user_action=None,
            indoor_temperature_c=26.0,
            indoor_humidity_percent=50.0,
        )


# Test M: Repeated feedback updates preference gradually
def test_m_repeated_feedback_updates_preference_gradually():
    learner = PreferenceLearner(learning_rate=0.05, max_single_step_delta_c=0.1)
    pref = OccupantPreferences(preferred_temperature_low_c=23.0, preferred_temperature_high_c=25.0)

    current_pref = pref
    for i in range(10):
        fb = FeedbackRecord(
            timestamp=i * 300,
            occupant_id="occ_1",
            recommended_action=WispAction.NO_ACTION,
            user_response=UserResponse.OVERRIDE,
            actual_user_action=WispAction.COOL_LOW,
            indoor_temperature_c=25.5,
            indoor_humidity_percent=50.0,
        )
        current_pref = learner.update(current_pref, fb)

    assert current_pref.preferred_temperature_high_c < 25.0
    assert current_pref.preferred_temperature_high_c > 23.5


# Test N: One override does NOT cause a dramatic preference change
def test_n_single_override_not_dramatic():
    learner = PreferenceLearner(max_single_step_delta_c=0.1)
    pref = OccupantPreferences(preferred_temperature_low_c=23.0, preferred_temperature_high_c=25.0)

    fb = FeedbackRecord(
        timestamp=0,
        occupant_id="occ_1",
        recommended_action=WispAction.NO_ACTION,
        user_response=UserResponse.OVERRIDE,
        actual_user_action=WispAction.COOL_HIGH,
        indoor_temperature_c=28.0,
        indoor_humidity_percent=50.0,
    )
    updated = learner.update(pref, fb)

    delta = round(abs(pref.preferred_temperature_high_c - updated.preferred_temperature_high_c), 4)
    assert delta <= 0.1, f"Single step delta ({delta}) was too large!"
    assert updated.preferred_temperature_high_c >= 24.9


# Test O: Preference values remain within reasonable configured bounds
def test_o_preference_bounds_enforced():
    learner = PreferenceLearner(learning_rate=0.5, max_single_step_delta_c=0.5)
    pref = OccupantPreferences(
        preferred_temperature_low_c=18.0,
        preferred_temperature_high_c=20.0,
        min_temp_bound_c=17.0,
        max_temp_bound_c=28.0,
    )

    current_pref = pref
    for i in range(50):
        fb = FeedbackRecord(
            timestamp=i,
            occupant_id="occ_1",
            recommended_action=WispAction.NO_ACTION,
            user_response=UserResponse.OVERRIDE,
            actual_user_action=WispAction.COOL_HIGH,
            indoor_temperature_c=19.0,
            indoor_humidity_percent=50.0,
        )
        current_pref = learner.update(current_pref, fb)

    assert current_pref.preferred_temperature_low_c >= current_pref.min_temp_bound_c
    assert current_pref.preferred_temperature_high_c <= current_pref.max_temp_bound_c
    assert current_pref.preferred_temperature_high_c >= current_pref.preferred_temperature_low_c + 1.0


# Test P: Invalid temperature/humidity inputs handled correctly
def test_p_invalid_inputs_handled():
    with pytest.raises(ValueError):
        OccupantPreferences(preferred_temperature_low_c=26.0, preferred_temperature_high_c=24.0)

    with pytest.raises(ValueError):
        OccupantPreferences(preferred_humidity_low_percent=70.0, preferred_humidity_high_percent=50.0)

    pref = OccupantPreferences()
    with pytest.raises(ValueError):
        ComfortModel.evaluate(indoor_temp_c=100.0, indoor_humidity_pct=50.0, preferences=pref)

    with pytest.raises(ValueError):
        ComfortModel.evaluate(indoor_temp_c=24.0, indoor_humidity_pct=-5.0, preferences=pref)

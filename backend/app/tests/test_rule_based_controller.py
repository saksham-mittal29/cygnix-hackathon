"""
test_rule_based_controller.py
-----------------------------
Comprehensive test suite for Phase 5: Wisp Rule-Based Controller.

Verifies:
1. Controller initialization and default config
2. Comfortable state -> NO_ACTION
3. Mild warming -> COOL_LOW
4. Moderate warming -> COOL_MEDIUM
5. Severe warming -> COOL_HIGH
6. Precool scenario (current comfort + future warming + solar/tariff context) -> PRECOOL
7. Overcooling / setback scenario -> REDUCE_HVAC
8. High tariff discourages non-critical aggressive cooling
9. Solar availability enables proactive cooling
10. Severe discomfort overrides cost/solar constraints
11. Low prediction confidence prevents premature aggressive cooling
12. High prediction confidence enables proactive actions
13. Previous action hysteresis considerations
14. Determinism
15. Reachability of all 6 actions
16. Invalid state handling and rejection
17. Closed-loop integration test with WispEnv
"""

import pytest
from backend.app.core.actions import WispAction
from backend.app.controller.rule_based import RuleBasedController, ControllerConfig
from backend.app.simulation.environment import WispEnv, WispEnvState


def make_base_state(**kwargs):
    """Helper to create test state dictionary with default comfortable values."""
    base = {
        "indoor_temperature_f": 74.0,
        "indoor_humidity_percent": 50.0,
        "outdoor_temperature_f": 82.0,
        "predicted_temperature_t5_f": 74.2,
        "predicted_humidity_t5_percent": 50.1,
        "predicted_temperature_t15_f": 74.5,
        "predicted_humidity_t15_percent": 50.2,
        "predicted_temperature_t30_f": 74.8,
        "predicted_humidity_t30_percent": 50.5,
        "prediction_confidence": 0.90,
        "preferred_temperature_low_f": 72.5,
        "preferred_temperature_high_f": 76.0,
        "preferred_humidity_low_percent": 40.0,
        "preferred_humidity_high_percent": 60.0,
        "solar_power_kw": 2.5,
        "tariff_currency_per_kwh": 10.0,
    }
    base.update(kwargs)
    return base


# 1. Controller initializes
def test_1_controller_initializes():
    ctrl = RuleBasedController()
    assert ctrl is not None
    assert ctrl.config.mild_warning_margin_f == 0.30


# 2. Comfortable current + future state -> NO_ACTION
def test_2_comfortable_state_produces_no_action():
    ctrl = RuleBasedController()
    state = make_base_state(
        indoor_temperature_f=74.0,
        predicted_temperature_t5_f=74.2,
        predicted_temperature_t15_f=74.5,
        predicted_temperature_t30_f=74.8,
    )
    action = ctrl.select_action(state)
    assert action == WispAction.NO_ACTION


# 3. Mild predicted warming -> COOL_LOW
def test_3_mild_warming_produces_cool_low():
    ctrl = RuleBasedController()
    # T_high = 76.0, T_pred_30 = 76.6 (overshoot = 0.6, confidence = 0.60 -> effective = 0.36 >= 0.30)
    state = make_base_state(
        indoor_temperature_f=75.5,
        predicted_temperature_t5_f=75.8,
        predicted_temperature_t15_f=76.2,
        predicted_temperature_t30_f=76.6,
        prediction_confidence=0.60, # Moderate confidence -> COOL_LOW
        solar_power_kw=0.0,
    )
    action = ctrl.select_action(state)
    assert action == WispAction.COOL_LOW


# 4. Moderate predicted warming -> COOL_MEDIUM
def test_4_moderate_warming_produces_cool_medium():
    ctrl = RuleBasedController()
    # T_high = 76.0, T_pred_30 = 77.8 (overshoot = 1.8, confidence = 0.85 -> effective = 1.53 >= 1.0)
    state = make_base_state(
        indoor_temperature_f=76.2,
        predicted_temperature_t5_f=76.8,
        predicted_temperature_t15_f=77.4,
        predicted_temperature_t30_f=77.8,
        prediction_confidence=0.85,
    )
    action = ctrl.select_action(state)
    assert action == WispAction.COOL_MEDIUM


# 5. Severe predicted warming -> COOL_HIGH
def test_5_severe_warming_produces_cool_high():
    ctrl = RuleBasedController()
    # T_high = 76.0, T_curr = 78.8 (> 76.0 + 2.2)
    state = make_base_state(
        indoor_temperature_f=78.8,
        predicted_temperature_t5_f=79.2,
        predicted_temperature_t15_f=79.8,
        predicted_temperature_t30_f=80.5,
    )
    action = ctrl.select_action(state)
    assert action == WispAction.COOL_HIGH


# 6. Future discomfort with current comfort -> PRECOOL
def test_6_precool_when_future_warming_and_favorable_solar():
    ctrl = RuleBasedController()
    # T_curr = 74.5 (comfortable, <= 76.0), but T_pred_30 = 76.2 (approaching T_high),
    # high confidence (0.90), abundant solar (3.0 kW)
    state = make_base_state(
        indoor_temperature_f=74.5,
        predicted_temperature_t5_f=75.0,
        predicted_temperature_t15_f=75.6,
        predicted_temperature_t30_f=76.2,
        prediction_confidence=0.90,
        solar_power_kw=3.0,
        tariff_currency_per_kwh=8.0,
    )
    action = ctrl.select_action(state)
    assert action == WispAction.PRECOOL


# 7. Comfortable conditions while HVAC can be reduced -> REDUCE_HVAC
def test_7_reduce_hvac_when_cool_and_stable():
    ctrl = RuleBasedController()
    # T_low = 72.5, T_curr = 72.8 (<= 72.5 + 0.5), future temp stable
    state = make_base_state(
        indoor_temperature_f=72.8,
        predicted_temperature_t5_f=73.0,
        predicted_temperature_t15_f=73.2,
        predicted_temperature_t30_f=73.5,
    )
    action = ctrl.select_action(state)
    assert action == WispAction.REDUCE_HVAC


# 8. High tariff discourages unnecessary aggressive cooling
def test_8_high_tariff_discourages_aggressive_cooling():
    ctrl = RuleBasedController()
    # Moderate predicted warming (T_pred_30 = 77.6, effective overshoot = 0.85 * 1.6 = 1.36 >= 1.0),
    # but high tariff (20.0), no solar (0 kW), and current temp is still mild (75.5 <= 76.0)
    # -> downshift from COOL_MEDIUM to COOL_LOW
    state = make_base_state(
        indoor_temperature_f=75.5,
        predicted_temperature_t5_f=76.2,
        predicted_temperature_t15_f=77.0,
        predicted_temperature_t30_f=77.6,
        prediction_confidence=0.85,
        solar_power_kw=0.0,
        tariff_currency_per_kwh=20.0,  # Peak tariff
    )
    action = ctrl.select_action(state)
    assert action == WispAction.COOL_LOW


# 9. Solar availability enables proactive cooling
def test_9_solar_enables_proactive_cooling():
    ctrl = RuleBasedController()
    # Identical thermal condition:
    state_no_solar = make_base_state(
        indoor_temperature_f=74.5,
        predicted_temperature_t5_f=75.0,
        predicted_temperature_t15_f=75.6,
        predicted_temperature_t30_f=76.2,
        prediction_confidence=0.90,
        solar_power_kw=0.0,
        tariff_currency_per_kwh=18.0,  # Peak tariff with no solar -> avoid PRECOOL
    )
    assert ctrl.select_action(state_no_solar) == WispAction.NO_ACTION

    state_with_solar = make_base_state(
        indoor_temperature_f=74.5,
        predicted_temperature_t5_f=75.0,
        predicted_temperature_t15_f=75.6,
        predicted_temperature_t30_f=76.2,
        prediction_confidence=0.90,
        solar_power_kw=3.5,            # Abundant solar covers precooling
        tariff_currency_per_kwh=18.0,
    )
    assert ctrl.select_action(state_with_solar) == WispAction.PRECOOL


# 10. Severe discomfort overrides cost considerations
def test_10_severe_discomfort_overrides_high_tariff():
    ctrl = RuleBasedController()
    # T_curr = 79.5 (severe > 76.0 + 2.2), Peak tariff ($50/kWh), 0 solar
    state = make_base_state(
        indoor_temperature_f=79.5,
        predicted_temperature_t5_f=80.0,
        predicted_temperature_t15_f=80.5,
        predicted_temperature_t30_f=81.0,
        solar_power_kw=0.0,
        tariff_currency_per_kwh=50.0,
    )
    action = ctrl.select_action(state)
    assert action == WispAction.COOL_HIGH


# 11. Low prediction confidence does not trigger unnecessarily aggressive cooling
def test_11_low_confidence_prevents_aggressive_cooling():
    ctrl = RuleBasedController()
    # +30 min prediction predicts extreme spike (80.0°F), but current temp is comfortable (74.0°F)
    # and confidence is very low (0.05) -> should not jump to COOL_HIGH
    state = make_base_state(
        indoor_temperature_f=74.0,
        predicted_temperature_t5_f=74.2,
        predicted_temperature_t15_f=76.0,
        predicted_temperature_t30_f=80.0,
        prediction_confidence=0.05,
    )
    action = ctrl.select_action(state)
    assert action != WispAction.COOL_HIGH
    assert action == WispAction.NO_ACTION


# 12. High prediction confidence allows stronger proactive action
def test_12_high_confidence_allows_proactive_action():
    ctrl = RuleBasedController()
    state = make_base_state(
        indoor_temperature_f=75.0,
        predicted_temperature_t5_f=75.5,
        predicted_temperature_t15_f=76.5,
        predicted_temperature_t30_f=77.0,
        prediction_confidence=0.95,
        solar_power_kw=3.0,
    )
    action = ctrl.select_action(state)
    assert action == WispAction.PRECOOL


# 13. Previous action is considered for hysteresis
def test_13_previous_action_hysteresis():
    ctrl = RuleBasedController()
    # T_curr = 75.8, T_pred_30 = 76.4, confidence = 0.50 -> effective_overshoot = 0.50 * 0.4 = 0.20
    # mild_warning_margin_f = 0.30, switching_hysteresis = 0.15 (threshold = 0.15)
    state = make_base_state(
        indoor_temperature_f=75.8,
        predicted_temperature_t5_f=76.0,
        predicted_temperature_t15_f=76.2,
        predicted_temperature_t30_f=76.4,
        prediction_confidence=0.50,
    )
    # When previous action was NO_ACTION -> selects NO_ACTION
    action_from_none = ctrl.select_action(state, previous_action=WispAction.NO_ACTION)
    assert action_from_none == WispAction.NO_ACTION

    # When previous action was COOL_LOW -> maintains COOL_LOW to prevent fluttering
    action_from_cool = ctrl.select_action(state, previous_action=WispAction.COOL_LOW)
    assert action_from_cool == WispAction.COOL_LOW


# 14. Controller is deterministic
def test_14_controller_determinism():
    ctrl = RuleBasedController()
    state = make_base_state(indoor_temperature_f=76.5, predicted_temperature_t30_f=77.5)
    action1 = ctrl.select_action(state)
    action2 = ctrl.select_action(state)
    assert action1 == action2


# 15. All six actions are reachable under appropriate states
def test_15_all_six_actions_reachable():
    ctrl = RuleBasedController()
    seen_actions = set()

    test_states = [
        # 1. NO_ACTION
        make_base_state(indoor_temperature_f=74.0, predicted_temperature_t30_f=74.5),
        # 2. COOL_LOW
        make_base_state(indoor_temperature_f=75.5, predicted_temperature_t30_f=76.6, prediction_confidence=0.6),
        # 3. COOL_MEDIUM
        make_base_state(indoor_temperature_f=76.2, predicted_temperature_t30_f=77.8, prediction_confidence=0.85),
        # 4. COOL_HIGH
        make_base_state(indoor_temperature_f=79.0, predicted_temperature_t30_f=80.5),
        # 5. PRECOOL
        make_base_state(indoor_temperature_f=74.5, predicted_temperature_t30_f=76.2, prediction_confidence=0.9, solar_power_kw=3.0),
        # 6. REDUCE_HVAC
        make_base_state(indoor_temperature_f=72.8, predicted_temperature_t30_f=73.2),
    ]

    for s in test_states:
        action = ctrl.select_action(s)
        seen_actions.add(action)

    for action in WispAction:
        assert action in seen_actions, f"Action {action} was not reachable!"


# 16. Invalid state is rejected clearly
def test_16_invalid_state_rejected():
    ctrl = RuleBasedController()
    with pytest.raises(TypeError):
        ctrl.select_action("invalid_state_string")  # type: ignore

    with pytest.raises(ValueError):
        ctrl.select_action({"some_random_key": 123})


# 17. Closed-loop integration test with WispEnv
def test_17_closed_loop_integration_with_env():
    env = WispEnv(
        initial_indoor_temp_f=76.0,
        outdoor_temp_f=85.0,
        max_steps_per_episode=6,
    )
    ctrl = RuleBasedController()

    state = env.reset()
    assert isinstance(state, WispEnvState)

    prev_action = None
    for step_num in range(6):
        action = ctrl.select_action(state, previous_action=prev_action)
        assert isinstance(action, WispAction)

        next_state, reward, done, info = env.step(action)
        assert isinstance(next_state, WispEnvState)
        assert isinstance(reward, float)
        assert info["action"] == action.value

        state = next_state
        prev_action = action

    assert done is True

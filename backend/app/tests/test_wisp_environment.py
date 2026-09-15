"""
test_wisp_environment.py
------------------------
Comprehensive test suite for Phase 4: Wisp Simulation Environment (WispEnv).

Verifies all 28 required items:
1. Initialization
2. reset() functionality
3. reset() determinism
4. Required observation state fields
5. All 6 discrete actions accepted
6. Invalid action rejection
7-12. Valid transitions for all 6 actions
13. Cooling actions cooler than NO_ACTION
14. Horizons +5, +15, +30 representation
15. Deterministic predictions
16. Valid confidence score
17. Solar integration
18. Tariff integration
19. EnergySimulator integration
20. ComfortModel integration
21. Multi-objective reward calculation
22. Action switching penalty
23. Multi-step consecutive rollout
24. Reset clears accumulators
25. Episode termination
26. Battery-free state verification
27. 5-minute timestep energy math
28. Info dictionary diagnostics completeness
"""

import pytest
from backend.app.core.actions import WispAction
from backend.app.simulation.environment import WispEnv, WispEnvState, SimulatedPredictionProvider


@pytest.fixture
def env():
    return WispEnv(
        initial_indoor_temp_f=75.0,
        initial_indoor_humidity=55.0,
        outdoor_temp_f=85.0,
        outdoor_humidity=60.0,
        max_steps_per_episode=12,
    )


# 1. WispEnv initializes
def test_1_env_initializes(env):
    assert env is not None
    assert env.max_steps_per_episode == 12
    assert env.current_step == 0


# 2 & 3. reset() works and is deterministic
def test_2_3_reset_works_and_deterministic(env):
    s1 = env.reset()
    s2 = env.reset()
    assert isinstance(s1, WispEnvState)
    assert s1 == s2
    assert s1.indoor_temperature_f == 75.0
    assert s1.indoor_humidity_percent == 55.0


# 4. reset() returns all required state fields
def test_4_required_state_fields(env):
    s = env.reset()
    required_fields = [
        "indoor_temperature_f",
        "indoor_humidity_percent",
        "outdoor_temperature_f",
        "predicted_temperature_t5_f",
        "predicted_humidity_t5_percent",
        "predicted_temperature_t15_f",
        "predicted_humidity_t15_percent",
        "predicted_temperature_t30_f",
        "predicted_humidity_t30_percent",
        "prediction_confidence",
        "preferred_temperature_low_f",
        "preferred_temperature_high_f",
        "preferred_humidity_low_percent",
        "preferred_humidity_high_percent",
        "solar_power_kw",
        "tariff_currency_per_kwh",
    ]
    state_dict = s.to_dict()
    for f in required_fields:
        assert f in state_dict, f"Missing required state field: {f}"
        assert isinstance(state_dict[f], (int, float))


# 5. All six actions are accepted
def test_5_all_six_actions_accepted(env):
    actions = [
        WispAction.NO_ACTION,
        WispAction.COOL_LOW,
        WispAction.COOL_MEDIUM,
        WispAction.COOL_HIGH,
        WispAction.PRECOOL,
        WispAction.REDUCE_HVAC,
    ]
    for action in actions:
        env.reset()
        next_state, reward, done, info = env.step(action)
        assert isinstance(next_state, WispEnvState)
        assert isinstance(reward, float)
        assert done is False
        assert info["action"] == action.value


# 6. Invalid action is rejected
def test_6_invalid_action_rejected(env):
    env.reset()
    with pytest.raises(TypeError):
        env.step("INVALID_ACTION_STRING")  # type: ignore

    with pytest.raises(TypeError):
        env.step(123)  # type: ignore


# 7-12. Individual action transitions
def test_7_12_individual_action_transitions(env):
    for a in WispAction:
        env.reset()
        ns, r, done, info = env.step(a)
        assert ns.indoor_temperature_f is not None
        assert info["action"] == a.value


# 13. Cooling actions produce stronger cooling behavior than NO_ACTION
def test_13_cooling_stronger_than_no_action(env):
    env.reset()
    s_no_action, _, _, _ = env.step(WispAction.NO_ACTION)

    env.reset()
    s_cool_low, _, _, _ = env.step(WispAction.COOL_LOW)

    env.reset()
    s_cool_med, _, _, _ = env.step(WispAction.COOL_MEDIUM)

    env.reset()
    s_cool_high, _, _, _ = env.step(WispAction.COOL_HIGH)

    # In hot outdoor ambient (85°F), NO_ACTION will drift warmer, cooling will drop temp
    assert s_cool_high.indoor_temperature_f < s_cool_med.indoor_temperature_f
    assert s_cool_med.indoor_temperature_f < s_cool_low.indoor_temperature_f
    assert s_cool_low.indoor_temperature_f < s_no_action.indoor_temperature_f


# 14 & 15. Prediction horizons +5/+15/+30 exist and are deterministic
def test_14_15_prediction_horizons_deterministic(env):
    env.reset()
    ns1, _, _, _ = env.step(WispAction.COOL_HIGH)

    env.reset()
    ns2, _, _, _ = env.step(WispAction.COOL_HIGH)

    assert ns1.predicted_temperature_t5_f == ns2.predicted_temperature_t5_f
    assert ns1.predicted_temperature_t15_f == ns2.predicted_temperature_t15_f
    assert ns1.predicted_temperature_t30_f == ns2.predicted_temperature_t30_f

    # +30 min cooling should be cooler than +15, which is cooler than +5
    assert ns1.predicted_temperature_t30_f < ns1.predicted_temperature_t15_f < ns1.predicted_temperature_t5_f


# 16. Confidence is valid
def test_16_confidence_valid(env):
    s = env.reset()
    assert 0.0 <= s.prediction_confidence <= 1.0


# 17 & 18. Solar and Tariff integration
def test_17_18_solar_and_tariff_integration(env):
    s = env.reset()
    assert s.solar_power_kw >= 0.0
    assert s.tariff_currency_per_kwh > 0.0


# 19. EnergySimulator integration
def test_19_energy_simulator_integration(env):
    env.reset()
    _, _, _, info = env.step(WispAction.COOL_HIGH)
    assert "energy_consumed_kWh" in info
    assert "solar_used_kWh" in info
    assert "grid_import_kWh" in info
    assert "electricity_cost" in info
    assert info["energy_consumed_kWh"] > 0.0


# 20. ComfortModel integration
def test_20_comfort_model_integration(env):
    env.reset()
    _, _, _, info = env.step(WispAction.NO_ACTION)
    assert "comfort_penalty" in info
    assert info["comfort_penalty"] >= 0.0


# 21. Reward is calculated
def test_21_reward_calculated(env):
    env.reset()
    _, r, _, info = env.step(WispAction.COOL_MEDIUM)
    assert isinstance(r, float)
    assert info["reward"] == pytest.approx(r, rel=1e-5)


# 22. Action switching penalty works
def test_22_switching_penalty_works(env):
    env.reset()
    # Step 1: NO_ACTION (first action -> no switching penalty)
    _, _, _, info1 = env.step(WispAction.NO_ACTION)
    assert info1["switching_penalty"] == 0.0

    # Step 2: NO_ACTION again -> no switching penalty
    _, _, _, info2 = env.step(WispAction.NO_ACTION)
    assert info2["switching_penalty"] == 0.0

    # Step 3: Switch to COOL_HIGH -> switching penalty = 1.0
    _, _, _, info3 = env.step(WispAction.COOL_HIGH)
    assert info3["switching_penalty"] == 1.0


# 23. Multiple consecutive steps work
def test_23_multi_step_rollout(env):
    env.reset()
    total_steps = 5
    for i in range(total_steps):
        ns, r, done, info = env.step(WispAction.COOL_LOW)
        assert info["step"] == i + 1
        assert done is False


# 24. reset() clears accumulated state
def test_24_reset_clears_accumulators(env):
    env.reset()
    for _ in range(4):
        env.step(WispAction.COOL_HIGH)

    assert env.current_step == 4
    assert env.cumulative_energy_kwh > 0.0

    env.reset()
    assert env.current_step == 0
    assert env.cumulative_reward == 0.0
    assert env.cumulative_energy_kwh == 0.0
    assert env.cumulative_cost == 0.0


# 25. Episode terminates at configured length
def test_25_episode_termination(env):
    env.reset()
    done = False
    step_count = 0
    while not done:
        _, _, done, info = env.step(WispAction.NO_ACTION)
        step_count += 1

    assert step_count == env.max_steps_per_episode
    assert done is True


# 26. No battery state exists
def test_26_no_battery_state_exists(env):
    s = env.reset()
    state_dict = s.to_dict()
    for k in state_dict.keys():
        assert "battery" not in k.lower()

    _, _, _, info = env.step(WispAction.NO_ACTION)
    for k in info.keys():
        assert "battery" not in k.lower()


# 27. 5-minute timestep energy math
def test_27_five_minute_energy_math(env):
    env.reset()
    # COOL_HIGH: hvac_power = 3.5 kW + base_load = 0.5 kW = 4.0 kW
    # 4.0 kW * (5/60 h) = 4.0 * (1/12) = 0.333333 kWh
    _, _, _, info = env.step(WispAction.COOL_HIGH)
    expected_energy = 4.0 * (5.0 / 60.0)
    assert pytest.approx(info["energy_consumed_kWh"], rel=1e-4) == expected_energy


# 28. info dictionary contains required diagnostics
def test_28_info_diagnostics(env):
    env.reset()
    _, _, _, info = env.step(WispAction.COOL_LOW)
    expected_keys = [
        "step",
        "action",
        "previous_action",
        "indoor_temperature_f",
        "indoor_humidity_percent",
        "predicted_temperature_t5_f",
        "predicted_temperature_t15_f",
        "predicted_temperature_t30_f",
        "predicted_humidity_t5_percent",
        "predicted_humidity_t15_percent",
        "predicted_humidity_t30_percent",
        "prediction_confidence",
        "comfort_penalty",
        "energy_consumed_kWh",
        "solar_used_kWh",
        "grid_import_kWh",
        "solar_surplus_kWh",
        "electricity_cost",
        "switching_penalty",
        "reward",
    ]
    for key in expected_keys:
        assert key in info, f"Missing diagnostic key in info: {key}"

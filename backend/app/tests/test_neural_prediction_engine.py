"""
test_neural_prediction_engine.py
--------------------------------
Comprehensive test suite for Phase 6 & 7: NeuralPredictionEngine integration.

Verifies:
1. NeuralPredictionEngine initialization & loading weights from best_lstm_model.pth
2. Loading validation_residuals.npy into AdaptiveConformalInference
3. Action vector encoding for all 6 discrete Wisp actions (with runtime normalization & setpoint scaling)
4. Disturbance vector encoding with cyclical hour and day features
5. State vector encoding with motion support
6. 12-step sliding history buffer behavior and cold-start replication
7. Real PyTorch model inference producing valid PredictionResult (+5, +15, +30 min)
8. Real inference for all six Wisp actions
9. Confidence score normalized to [0.0, 1.0]
10. Integration with WispEnv (running WispEnv with NeuralPredictionEngine)
11. Closed-loop control test with RuleBasedController + WispEnv + NeuralPredictionEngine
"""

import math
from pathlib import Path
import pytest
import torch

from backend.app.core.actions import WispAction
from backend.app.core.types import Disturbance, PredictionResult, ThermalState
from backend.app.prediction.neural_engine import (
    NeuralPredictionEngine,
    HEAT_SP_MEAN,
    HEAT_SP_STD,
    COOL_SP_MEAN,
    COOL_SP_STD,
)
from backend.app.simulation.environment import WispEnv, WispEnvState
from backend.app.controller.rule_based import RuleBasedController


@pytest.fixture
def neural_engine():
    return NeuralPredictionEngine(device="cpu")


@pytest.fixture
def sample_thermal():
    return ThermalState(
        indoor_temperature=75.0,
        indoor_humidity=50.0,
        thermostat_temperature=75.0,
        heat_setpoint=68.0,
        cool_setpoint=75.0,
    )


@pytest.fixture
def sample_disturbance():
    return Disturbance(
        outdoor_temperature=85.0,
        outdoor_humidity=60.0,
        solar_irradiance_w_m2=500.0,
        hour_of_day=14,  # 2:00 PM
        day_of_week=3,   # Thursday
    )


# 1. NeuralPredictionEngine initialization & weights loaded
def test_1_neural_engine_initializes_and_loads_weights(neural_engine):
    assert neural_engine is not None
    assert neural_engine.weights_loaded is True
    assert neural_engine.model_path.exists()
    assert isinstance(neural_engine.model, torch.nn.Module)


# 2. Residuals loaded into ACI
def test_2_residuals_loaded_into_aci(neural_engine):
    assert neural_engine.residuals_loaded is True
    assert neural_engine.residuals_path.exists()
    conf = neural_engine.aci.get_confidence_score()
    assert 0 <= conf <= 100


# 3. Action vector encoding for all 6 actions
def test_3_action_vector_encoding():
    norm_heat_68 = (68.0 - HEAT_SP_MEAN) / HEAT_SP_STD
    norm_cool_75 = (75.0 - COOL_SP_MEAN) / COOL_SP_STD
    norm_cool_73 = (73.0 - COOL_SP_MEAN) / COOL_SP_STD
    norm_cool_77 = (77.0 - COOL_SP_MEAN) / COOL_SP_STD

    # NO_ACTION -> [0, 0, 0, norm_heat, norm_cool]
    a_no = NeuralPredictionEngine.encode_action_vector(WispAction.NO_ACTION, 68.0, 75.0)
    assert a_no == [0.0, 0.0, 0.0, pytest.approx(norm_heat_68), pytest.approx(norm_cool_75)]

    # COOL_LOW -> [0, 0.33, 0.33, norm_heat, norm_cool]
    a_low = NeuralPredictionEngine.encode_action_vector(WispAction.COOL_LOW, 68.0, 75.0)
    assert a_low == [0.0, 0.33, 0.33, pytest.approx(norm_heat_68), pytest.approx(norm_cool_75)]

    # COOL_MEDIUM -> [0, 0.66, 0.66, norm_heat, norm_cool]
    a_med = NeuralPredictionEngine.encode_action_vector(WispAction.COOL_MEDIUM, 68.0, 75.0)
    assert a_med == [0.0, 0.66, 0.66, pytest.approx(norm_heat_68), pytest.approx(norm_cool_75)]

    # COOL_HIGH -> [0, 1.00, 1.00, norm_heat, norm_cool]
    a_high = NeuralPredictionEngine.encode_action_vector(WispAction.COOL_HIGH, 68.0, 75.0)
    assert a_high == [0.0, 1.00, 1.00, pytest.approx(norm_heat_68), pytest.approx(norm_cool_75)]

    # PRECOOL -> [0, 1.00, 1.00, norm_heat, norm_cool - 2]
    a_precool = NeuralPredictionEngine.encode_action_vector(WispAction.PRECOOL, 68.0, 75.0)
    assert a_precool == [0.0, 1.00, 1.00, pytest.approx(norm_heat_68), pytest.approx(norm_cool_73)]

    # REDUCE_HVAC -> [0, 0, 0, norm_heat, norm_cool + 2]
    a_reduce = NeuralPredictionEngine.encode_action_vector(WispAction.REDUCE_HVAC, 68.0, 75.0)
    assert a_reduce == [0.0, 0.0, 0.0, pytest.approx(norm_heat_68), pytest.approx(norm_cool_77)]


# 4. Disturbance vector encoding
def test_4_disturbance_vector_encoding(sample_disturbance):
    d_vec = NeuralPredictionEngine.encode_disturbance_vector(sample_disturbance)
    assert len(d_vec) == 6

    # Cyclical hour=14 -> sin(2*pi*14/24), cos(2*pi*14/24)
    expected_hour_sin = math.sin(2.0 * math.pi * 14.0 / 24.0)
    expected_hour_cos = math.cos(2.0 * math.pi * 14.0 / 24.0)
    assert pytest.approx(d_vec[2], rel=1e-4) == expected_hour_sin
    assert pytest.approx(d_vec[3], rel=1e-4) == expected_hour_cos


# 5. History buffer and cold start replication
def test_5_history_buffer_and_cold_start(neural_engine, sample_thermal, sample_disturbance):
    neural_engine.reset()
    assert len(neural_engine.history_s) == 0

    s_vec = neural_engine.encode_state_vector(sample_thermal)
    a_vec = neural_engine.encode_action_vector(WispAction.NO_ACTION)
    d_vec = neural_engine.encode_disturbance_vector(sample_disturbance)

    t_s, t_a, t_d = neural_engine._update_and_get_history_tensors(s_vec, a_vec, d_vec)

    # Replicated 12 times on cold start
    assert len(neural_engine.history_s) == 12
    assert t_s.shape == (1, 12, 3)
    assert t_a.shape == (1, 12, 5)
    assert t_d.shape == (1, 12, 6)

    # Next step shifts buffer by 1
    neural_engine._update_and_get_history_tensors(s_vec, a_vec, d_vec)
    assert len(neural_engine.history_s) == 12


# 6. Real model inference completes and produces valid physical PredictionResult
def test_6_real_model_inference_prediction_result(neural_engine, sample_thermal, sample_disturbance):
    pred = neural_engine.predict(sample_thermal, WispAction.NO_ACTION, sample_disturbance)
    assert isinstance(pred, PredictionResult)

    # Check finite physical numbers in realistic Fahrenheit / Humidity ranges
    assert 40.0 <= pred.temp_t5 <= 100.0
    assert 40.0 <= pred.temp_t15 <= 100.0
    assert 40.0 <= pred.temp_t30 <= 100.0
    assert 10.0 <= pred.hum_t5 <= 90.0
    assert 10.0 <= pred.hum_t15 <= 90.0
    assert 10.0 <= pred.hum_t30 <= 90.0

    # Check confidence is within [0.0, 1.0]
    assert 0.0 <= pred.confidence <= 1.0
    assert pred.metadata["engine"] == "NeuralPredictionEngine"
    assert pred.metadata["weights_loaded"] is True


# 7. Real inference across all 6 actions produces physical outputs
def test_7_real_inference_all_six_actions(neural_engine, sample_thermal, sample_disturbance):
    for action in WispAction:
        pred = neural_engine.predict(sample_thermal, action, sample_disturbance)
        assert isinstance(pred, PredictionResult)
        assert 40.0 <= pred.temp_t5 <= 100.0
        assert 10.0 <= pred.hum_t5 <= 90.0


# 8. WispEnv integration with real NeuralPredictionEngine
def test_8_wispenv_with_neural_prediction_engine(neural_engine):
    env = WispEnv(
        prediction_engine=neural_engine,
        initial_indoor_temp_f=75.0,
        outdoor_temp_f=85.0,
        max_steps_per_episode=6,
    )

    state = env.reset()
    assert isinstance(state, WispEnvState)
    assert 50.0 <= state.predicted_temperature_t5_f <= 90.0
    assert 50.0 <= state.predicted_temperature_t15_f <= 90.0
    assert 50.0 <= state.predicted_temperature_t30_f <= 90.0

    # Execute one step with real model
    next_state, reward, done, info = env.step(WispAction.COOL_HIGH)
    assert isinstance(next_state, WispEnvState)
    assert isinstance(reward, float)
    assert math.isfinite(reward)
    assert done is False
    assert info["action"] == WispAction.COOL_HIGH.value


# 9. Closed-loop control test with RuleBasedController + WispEnv + NeuralPredictionEngine
def test_9_closed_loop_controller_with_neural_engine(neural_engine):
    env = WispEnv(
        prediction_engine=neural_engine,
        initial_indoor_temp_f=76.0,
        outdoor_temp_f=88.0,
        max_steps_per_episode=6,
    )
    ctrl = RuleBasedController()

    state = env.reset()
    prev_action = None

    for step_idx in range(6):
        action = ctrl.select_action(state, previous_action=prev_action)
        assert isinstance(action, WispAction)

        next_state, reward, done, info = env.step(action)
        assert isinstance(next_state, WispEnvState)
        assert math.isfinite(reward)

        state = next_state
        prev_action = action

    assert done is True
    assert env.current_step == 6
    assert env.cumulative_energy_kwh > 0.0

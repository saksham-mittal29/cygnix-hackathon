"""
observation.py
--------------
Observation feature extraction and normalization for the Wisp DQN Agent (Phase 8).
Converts structured WispEnvState into a fixed 16-dimensional numerical feature vector.

Features Included:
1. indoor_temperature_f (normalized relative to [60, 90]°F)
2. indoor_humidity_percent (normalized relative to [0, 100]%)
3. outdoor_temperature_f (normalized relative to [40, 110]°F)
4. predicted_temperature_t5_f (normalized relative to [60, 90]°F)
5. predicted_humidity_t5_percent (normalized relative to [0, 100]%)
6. predicted_temperature_t15_f (normalized relative to [60, 90]°F)
7. predicted_humidity_t15_percent (normalized relative to [0, 100]%)
8. predicted_temperature_t30_f (normalized relative to [60, 90]°F)
9. predicted_humidity_t30_percent (normalized relative to [0, 100]%)
10. prediction_confidence (direct [0.0, 1.0])
11. preferred_temperature_low_f (normalized relative to [60, 90]°F)
12. preferred_temperature_high_f (normalized relative to [60, 90]°F)
13. preferred_humidity_low_percent (normalized relative to [0, 100]%)
14. preferred_humidity_high_percent (normalized relative to [0, 100]%)
15. solar_power_kw (normalized relative to [0, 10] kW)
16. tariff_currency_per_kwh (normalized relative to [0, 30] currency/kWh)

Zero Leakage: All features are available at decision time t.
"""

from typing import Union, Dict, Any, List
import numpy as np

from backend.app.simulation.environment import WispEnvState

OBSERVATION_DIM = 16

# Normalization scaling constants for stable neural network inputs
TEMP_MIN = 60.0
TEMP_MAX = 90.0

OUTDOOR_TEMP_MIN = 40.0
OUTDOOR_TEMP_MAX = 110.0

HUM_MIN = 0.0
HUM_MAX = 100.0

SOLAR_MAX_KW = 10.0
TARIFF_MAX_CURRENCY = 30.0


def extract_dqn_observation(state: Union[WispEnvState, Dict[str, Any]]) -> np.ndarray:
    """
    Extracts and normalizes the 16-dimensional observation vector from WispEnvState.

    Args:
        state: WispEnvState observation or dictionary.

    Returns:
        np.ndarray of shape (16,) with dtype float32.
    """
    if isinstance(state, WispEnvState):
        d = state.to_dict()
    elif isinstance(state, dict):
        d = state
    else:
        raise TypeError(f"Expected WispEnvState or dict, got {type(state).__name__}")

    try:
        # 1-3. Current Conditions
        t_in = (float(d["indoor_temperature_f"]) - TEMP_MIN) / (TEMP_MAX - TEMP_MIN)
        h_in = (float(d["indoor_humidity_percent"]) - HUM_MIN) / (HUM_MAX - HUM_MIN)
        t_out = (float(d["outdoor_temperature_f"]) - OUTDOOR_TEMP_MIN) / (OUTDOOR_TEMP_MAX - OUTDOOR_TEMP_MIN)

        # 4-9. Multi-Horizon Predictions
        t_p5 = (float(d["predicted_temperature_t5_f"]) - TEMP_MIN) / (TEMP_MAX - TEMP_MIN)
        h_p5 = (float(d["predicted_humidity_t5_percent"]) - HUM_MIN) / (HUM_MAX - HUM_MIN)
        t_p15 = (float(d["predicted_temperature_t15_f"]) - TEMP_MIN) / (TEMP_MAX - TEMP_MIN)
        h_p15 = (float(d["predicted_humidity_t15_percent"]) - HUM_MIN) / (HUM_MAX - HUM_MIN)
        t_p30 = (float(d["predicted_temperature_t30_f"]) - TEMP_MIN) / (TEMP_MAX - TEMP_MIN)
        h_p30 = (float(d["predicted_humidity_t30_percent"]) - HUM_MIN) / (HUM_MAX - HUM_MIN)

        # 10. Prediction Confidence
        conf = float(np.clip(float(d.get("prediction_confidence", 1.0)), 0.0, 1.0))

        # 11-14. Personalization Preferences
        pref_t_low = (float(d["preferred_temperature_low_f"]) - TEMP_MIN) / (TEMP_MAX - TEMP_MIN)
        pref_t_high = (float(d["preferred_temperature_high_f"]) - TEMP_MIN) / (TEMP_MAX - TEMP_MIN)
        pref_h_low = (float(d["preferred_humidity_low_percent"]) - HUM_MIN) / (HUM_MAX - HUM_MIN)
        pref_h_high = (float(d["preferred_humidity_high_percent"]) - HUM_MIN) / (HUM_MAX - HUM_MIN)

        # 15-16. Energy & Grid Signals
        sol = float(np.clip(float(d.get("solar_power_kw", 0.0)) / SOLAR_MAX_KW, 0.0, 1.0))
        tar = float(np.clip(float(d.get("tariff_currency_per_kwh", 10.0)) / TARIFF_MAX_CURRENCY, 0.0, 1.0))

    except KeyError as e:
        raise ValueError(f"State missing required field for DQN observation: {e}")

    vec = np.array([
        t_in, h_in, t_out,
        t_p5, h_p5, t_p15, h_p15, t_p30, h_p30,
        conf,
        pref_t_low, pref_t_high, pref_h_low, pref_h_high,
        sol, tar
    ], dtype=np.float32)

    return vec

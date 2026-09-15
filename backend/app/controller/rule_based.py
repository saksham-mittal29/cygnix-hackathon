"""
rule_based.py
-------------
Deterministic Rule-Based Controller for Wisp Person 3 (Phase 5).

Selects from the 6 discrete WispAction choices based on:
1. Current indoor conditions (temperature, humidity)
2. Multi-horizon predicted conditions (+5, +15, +30 min)
3. Prediction confidence score
4. Occupant comfort preferences (lower/upper temperature and humidity bounds)
5. Environmental and grid signals (outdoor temp, solar power kW, electricity tariff)
6. Previous action (switching mitigation and hysteresis)

Design Hierarchy:
1. Occupant comfort preservation (Primary objective: severe discomfort overrides cost)
2. Overcooling prevention & energy conservation (REDUCE_HVAC when cool and stable)
3. Predictive & solar-driven pre-cooling (PRECOOL when future warming is anticipated & favorable energy context)
4. Multi-tiered active cooling (COOL_LOW, COOL_MEDIUM, COOL_HIGH based on thermal severity)
5. Tariff sensitivity (downshifts cooling intensity during peak tariff when near boundary)
6. Switching stabilization (hysteresis margin to prevent rapid action fluttering)
7. Passive comfort preservation (NO_ACTION as first-class baseline)
"""

from dataclasses import dataclass
from typing import Optional, Union, Dict, Any

from backend.app.core.actions import WispAction
from backend.app.simulation.environment import WispEnvState


@dataclass
class ControllerConfig:
    """
    Heuristic configuration parameters and threshold margins for RuleBasedController.
    All values have clear defaults and are fully configurable.
    """
    # Temperature threshold margins relative to preferred_temperature_high_f (°F)
    mild_warning_margin_f: float = 0.30     # Effective overshoot >= 0.30°F -> COOL_LOW
    moderate_warning_margin_f: float = 1.00 # Effective overshoot >= 1.00°F -> COOL_MEDIUM
    severe_warning_margin_f: float = 2.20   # Effective overshoot >= 2.20°F -> COOL_HIGH

    # Precooling threshold parameters (°F)
    precool_lead_margin_f: float = 0.20     # T_pred_30 >= T_high - 0.20 while T_curr <= T_high
    
    # Overcooling / Setback threshold relative to preferred_temperature_low_f (°F)
    cool_setback_margin_f: float = 0.50     # T_curr <= T_low + 0.50 -> REDUCE_HVAC

    # Humidity warning margin relative to preferred_humidity_high_percent (%)
    humidity_high_margin_pct: float = 5.0   # RH > RH_high + 5.0 -> requires cooling/dehumidification

    # Prediction Confidence Thresholds [0.0, 1.0]
    confidence_high_threshold: float = 0.75 # Allows proactive PRECOOL and confident horizon scaling
    confidence_low_threshold: float = 0.35  # Below this, future predictions are discounted

    # Energy & Tariff Signal Thresholds
    expensive_tariff_threshold: float = 15.0 # Currency per kWh above which peak conservation applies
    solar_favorable_threshold_kw: float = 1.5 # Solar kW above which proactive cooling is encouraged

    # Switching Hysteresis Margin (°F)
    switching_hysteresis_margin_f: float = 0.15 # Margin to prevent fluttering between adjacent actions


class RuleBasedController:
    """
    Deterministic rule-based HVAC controller for Wisp.
    """

    def __init__(self, config: Optional[ControllerConfig] = None):
        self.config = config or ControllerConfig()

    def select_action(
        self,
        state: Union[WispEnvState, Dict[str, Any]],
        previous_action: Optional[WispAction] = None,
    ) -> WispAction:
        """
        Determines the optimal discrete WispAction for the given state.

        Args:
            state: Current WispEnvState observation (or dictionary with matching fields).
            previous_action: Optional previous WispAction for switching mitigation.

        Returns:
            Selected WispAction.
        """
        # 1. State extraction and validation
        if isinstance(state, WispEnvState):
            data = state.to_dict()
        elif isinstance(state, dict):
            data = state
        else:
            raise TypeError(f"Expected WispEnvState or dict, got {type(state).__name__}")

        # Required fields extraction
        try:
            t_curr = float(data["indoor_temperature_f"])
            h_curr = float(data["indoor_humidity_percent"])
            t_pred_5 = float(data["predicted_temperature_t5_f"])
            t_pred_15 = float(data["predicted_temperature_t15_f"])
            t_pred_30 = float(data["predicted_temperature_t30_f"])
            h_pred_30 = float(data.get("predicted_humidity_t30_percent", h_curr))
            confidence = float(data.get("prediction_confidence", 1.0))
            t_low = float(data["preferred_temperature_low_f"])
            t_high = float(data["preferred_temperature_high_f"])
            h_high = float(data["preferred_humidity_high_percent"])
            solar_kw = float(data.get("solar_power_kw", 0.0))
            tariff = float(data.get("tariff_currency_per_kwh", 10.0))
        except KeyError as e:
            raise ValueError(f"State missing required field for controller: {e}")

        # Derive effective thermal overshoots
        raw_max_pred = max(t_pred_5, t_pred_15, t_pred_30)
        curr_over_temp = t_curr - t_high
        raw_pred_over_temp = raw_max_pred - t_high

        # Effective overshoot combines current overshoot and confidence-weighted future overshoot
        if raw_pred_over_temp > 0:
            effective_overshoot = max(curr_over_temp, confidence * raw_pred_over_temp)
        else:
            effective_overshoot = curr_over_temp

        humidity_over = max(h_curr, h_pred_30) - h_high

        # Energy context flags
        is_expensive_tariff = tariff >= self.config.expensive_tariff_threshold
        is_solar_abundant = solar_kw >= self.config.solar_favorable_threshold_kw

        # -------------------------------------------------------------
        # RULE 1: SEVERE DISCOMFORT (Comfort-First: overrides cost/solar)
        # -------------------------------------------------------------
        if curr_over_temp >= self.config.severe_warning_margin_f or (
            effective_overshoot >= self.config.severe_warning_margin_f and confidence >= self.config.confidence_high_threshold
        ):
            return WispAction.COOL_HIGH

        # -------------------------------------------------------------
        # RULE 2: OVERCOOLING / SETBACK OPPORTUNITY (Energy Conservation)
        # If current temp is near or below preferred low bound (e.g. <= 73°F)
        # and not predicted to rapidly overheat -> REDUCE_HVAC
        # -------------------------------------------------------------
        if t_curr <= (t_low + self.config.cool_setback_margin_f) and raw_max_pred <= t_high:
            return WispAction.REDUCE_HVAC

        # -------------------------------------------------------------
        # RULE 3: MODERATE WARMING / HIGH HUMIDITY
        # -------------------------------------------------------------
        if effective_overshoot >= self.config.moderate_warning_margin_f or (
            humidity_over >= self.config.humidity_high_margin_pct
        ):
            # If tariff is expensive and no solar, downshift to COOL_LOW if current condition isn't extreme
            if is_expensive_tariff and not is_solar_abundant and curr_over_temp < self.config.moderate_warning_margin_f:
                return WispAction.COOL_LOW
            return WispAction.COOL_MEDIUM

        # -------------------------------------------------------------
        # RULE 4: PRECOOL OPPORTUNITY
        # Currently comfortable (T_curr <= T_high), but +30 min prediction
        # is warming up toward/beyond upper bound, with high confidence and
        # favorable conditions (abundant solar OR normal/cheap tariff).
        # -------------------------------------------------------------
        if (
            t_curr <= t_high
            and t_pred_30 >= (t_high - self.config.precool_lead_margin_f)
            and confidence >= self.config.confidence_high_threshold
        ):
            # If tariff is expensive, only precool if solar is actively available
            if is_expensive_tariff and not is_solar_abundant:
                return WispAction.NO_ACTION
            return WispAction.PRECOOL

        # -------------------------------------------------------------
        # RULE 5: MILD WARMING DEVIATION
        # -------------------------------------------------------------
        if effective_overshoot >= self.config.mild_warning_margin_f:
            return WispAction.COOL_LOW

        # -------------------------------------------------------------
        # RULE 6: HYSTERESIS & STABILIZATION WITH PREVIOUS ACTION
        # If previous action was COOL_LOW and conditions are near the boundary,
        # avoid unnecessary switching unless temperature has fully stabilized.
        # -------------------------------------------------------------
        if previous_action == WispAction.COOL_LOW and (
            effective_overshoot >= (self.config.mild_warning_margin_f - self.config.switching_hysteresis_margin_f)
        ):
            return WispAction.COOL_LOW

        # -------------------------------------------------------------
        # RULE 7: DEFAULT COMFORTABLE STATE -> NO_ACTION
        # Current and future conditions comfortably within envelope
        # -------------------------------------------------------------
        return WispAction.NO_ACTION

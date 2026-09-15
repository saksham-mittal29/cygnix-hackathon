"""
main.py
-------
Entrypoint for the Wisp FastAPI backend server.
Exposes the real Person 2 Neural Prediction Engine and the trained Person 3 Wisp DQN Controller.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import json
import logging
import torch
import numpy as np

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.app.core.actions import WispAction, get_cooling_intensity
from backend.app.core.types import ThermalState, Disturbance, RewardBreakdown, RewardWeights
from backend.app.energy.simulator import EnergySimulator
from backend.app.personalization.comfort_model import ComfortModel, ComfortEvaluation
from backend.app.personalization.preferences import OccupantPreferences
from backend.app.prediction.neural_engine import NeuralPredictionEngine
from backend.app.rl.agent import DQNAgent
from backend.app.rl.observation import extract_dqn_observation
from backend.app.simulation.environment import WispEnvState

logger = logging.getLogger("wisp.api")

app = FastAPI(title="Wisp Climate Control API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Initialize Real Neural Prediction Engine (Person 2)
engine = NeuralPredictionEngine(device="cpu")

# 2. Initialize Real Wisp DQN RL Controller (Person 3 - Long-Trained DQN)
dqn_agent = DQNAgent()
model_path_long = Path(__file__).resolve().parent / "models" / "saved_models" / "dqn_phase10_long_training.pth"
model_path_orig = Path(__file__).resolve().parent / "models" / "saved_models" / "best_dqn_agent.pth"

if model_path_long.exists():
    dqn_agent.load_checkpoint(model_path_long)
    logger.info("Loaded Wisp Long-Trained DQN checkpoint into API.")
elif model_path_orig.exists():
    dqn_agent.load_checkpoint(model_path_orig)
    logger.info("Loaded Wisp Original DQN checkpoint into API.")

# Energy & Comfort Simulators
energy_sim = EnergySimulator()
reward_weights = RewardWeights(alpha=1.0, beta=0.1, gamma=0.01, delta=0.5, lambda_solar=0.05)


class PredictRequest(BaseModel):
    zone_id: str = "main"
    current_temp: float = 72.0
    target_temp: Optional[float] = 72.0
    current_humidity: Optional[float] = 50.0
    outdoor_temp: Optional[float] = 85.0
    outdoor_humidity: Optional[float] = 55.0
    solar_kw: Optional[float] = 2.0
    tariff_rate: Optional[float] = 10.0
    preferred_temp_low: Optional[float] = 70.0
    preferred_temp_high: Optional[float] = 74.0
    preferred_hum_low: Optional[float] = 30.0
    preferred_hum_high: Optional[float] = 60.0
    mode: str = "COOLING"


ACTION_EXPLANATIONS = {
    WispAction.NO_ACTION: "Temperature is within the preferred comfort range. Zero active HVAC cooling required.",
    WispAction.COOL_LOW: "Cooling is being applied gradually to maintain steady comfort with minimal energy.",
    WispAction.COOL_MEDIUM: "Moderate cooling is selected to control predicted warming and stabilize indoor conditions.",
    WispAction.COOL_HIGH: "Strong cooling is selected because predicted temperature exceeds the comfort boundary.",
    WispAction.PRECOOL: "Precooling is selected because future warming is predicted under favorable energy conditions.",
    WispAction.REDUCE_HVAC: "HVAC cooling is being curtailed because the space is below or near the preferred low threshold.",
}


@app.get("/")
def read_root():
    return {
        "status": "ok",
        "service": "Wisp Climate Control API",
        "controller": "Wisp DQN",
        "model_loaded": dqn_agent.online_net is not None,
    }


@app.post("/api/predict")
def predict(req: PredictRequest):
    # Determine bounds
    p_low = req.preferred_temp_low if req.preferred_temp_low is not None else 70.0
    p_high = req.preferred_temp_high if req.preferred_temp_high is not None else 74.0
    if req.target_temp is not None and req.preferred_temp_high is None:
        p_high = req.target_temp + 2.0
        p_low = req.target_temp - 2.0

    curr_hum = req.current_humidity if req.current_humidity is not None else 50.0
    out_temp = req.outdoor_temp if req.outdoor_temp is not None else 85.0
    out_hum = req.outdoor_humidity if req.outdoor_humidity is not None else 55.0
    sol_kw = req.solar_kw if req.solar_kw is not None else 2.0
    tar_rate = req.tariff_rate if req.tariff_rate is not None else 10.0

    # 1. Query baseline prediction with NO_ACTION to build initial trajectory
    thermal_curr = ThermalState(
        indoor_temperature=req.current_temp,
        indoor_humidity=curr_hum,
        thermostat_temperature=req.current_temp,
        heat_setpoint=p_low,
        cool_setpoint=p_high,
    )
    dist = Disturbance(
        outdoor_temperature=out_temp,
        outdoor_humidity=out_hum,
        solar_irradiance_w_m2=sol_kw * 100.0,
        hour_of_day=14,
        day_of_week=2,
    )

    baseline_pred = engine.predict(thermal_curr, WispAction.NO_ACTION, dist)

    # 2. Build exact WispEnvState observation for DQN
    env_state = WispEnvState(
        indoor_temperature_f=req.current_temp,
        indoor_humidity_percent=curr_hum,
        outdoor_temperature_f=out_temp,
        predicted_temperature_t5_f=baseline_pred.temp_t5,
        predicted_humidity_t5_percent=baseline_pred.hum_t5,
        predicted_temperature_t15_f=baseline_pred.temp_t15,
        predicted_humidity_t15_percent=baseline_pred.hum_t15,
        predicted_temperature_t30_f=baseline_pred.temp_t30,
        predicted_humidity_t30_percent=baseline_pred.hum_t30,
        prediction_confidence=baseline_pred.confidence,
        preferred_temperature_low_f=p_low,
        preferred_temperature_high_f=p_high,
        preferred_humidity_low_percent=req.preferred_hum_low or 30.0,
        preferred_humidity_high_percent=req.preferred_hum_high or 60.0,
        solar_power_kw=sol_kw,
        tariff_currency_per_kwh=tar_rate,
    )

    # 3. Select Real Wisp Action from Trained DQN
    action, action_idx = dqn_agent.select_action(env_state, evaluate=True)

    # Extract all 6 Q-values
    obs = extract_dqn_observation(env_state)
    obs_t = torch.tensor(obs, dtype=torch.float32, device=dqn_agent.device).unsqueeze(0)
    dqn_agent.online_net.eval()
    with torch.no_grad():
        q_vals = dqn_agent.online_net(obs_t).cpu().numpy().flatten()

    q_dict = {
        "NO_ACTION": round(float(q_vals[0]), 4),
        "COOL_LOW": round(float(q_vals[1]), 4),
        "COOL_MEDIUM": round(float(q_vals[2]), 4),
        "COOL_HIGH": round(float(q_vals[3]), 4),
        "PRECOOL": round(float(q_vals[4]), 4),
        "REDUCE_HVAC": round(float(q_vals[5]), 4),
    }

    # 4. Predict Trajectory Under the Selected Action
    active_pred = engine.predict(thermal_curr, action, dist)

    # 5. Compute Physical Energy, Cost, and Reward Breakdown
    cooling_intensity = get_cooling_intensity(action)
    hvac_kw = 3.5 * cooling_intensity
    total_kw = hvac_kw + 0.5  # 0.5 kW base building load
    from datetime import datetime, timezone
    now_dt = datetime.now(timezone.utc)

    energy_res = energy_sim.simulate_step(
        timestamp=now_dt,
        load_power_kw=total_kw,
        solar_power_kw=sol_kw,
        tariff_rate=tar_rate,
    )

    temp_c = (req.current_temp - 32.0) * 5.0 / 9.0
    prefs_obj = OccupantPreferences(
        preferred_temperature_low_c=(p_low - 32.0) * 5.0 / 9.0,
        preferred_temperature_high_c=(p_high - 32.0) * 5.0 / 9.0,
        preferred_humidity_low_percent=req.preferred_hum_low or 30.0,
        preferred_humidity_high_percent=req.preferred_hum_high or 60.0,
    )
    comfort_eval = ComfortModel.evaluate(
        indoor_temp_c=temp_c,
        indoor_humidity_pct=curr_hum,
        preferences=prefs_obj,
    )

    reward_breakdown = RewardBreakdown(
        comfort_penalty=comfort_eval.comfort_penalty,
        energy_consumed=energy_res.load_energy_kwh,
        monetary_cost=energy_res.electricity_cost,
        switching_penalty=0.0,
        solar_energy_used=energy_res.solar_used_kwh,
    )
    step_reward = reward_breakdown.compute_total(reward_weights)

    confidence_pct = int(round(active_pred.confidence * 100))

    return {
        "zone_id": req.zone_id,
        "controller": "Wisp DQN",
        "action": action.name,
        "action_val": action.value,
        "explanation": ACTION_EXPLANATIONS.get(action, "Optimal action selected by Wisp DQN."),
        "q_values": q_dict,
        "confidence_score": confidence_pct,
        "current_temp": round(req.current_temp, 2),
        "current_humidity": round(curr_hum, 2),
        "outdoor_temp": round(out_temp, 2),
        "preferred_temp_low": round(p_low, 2),
        "preferred_temp_high": round(p_high, 2),
        "preferred_hum_low": round(req.preferred_hum_low or 30.0, 1),
        "preferred_hum_high": round(req.preferred_hum_high or 60.0, 1),
        "solar_kw": round(sol_kw, 2),
        "tariff_rate": round(tar_rate, 4),
        "energy_kwh": round(energy_res.load_energy_kwh, 4),
        "hvac_power_kw": round(hvac_kw, 2),
        "estimated_cost": round(energy_res.electricity_cost, 4),
        "solar_used_kwh": round(energy_res.solar_used_kwh, 4),
        "grid_import_kwh": round(energy_res.grid_import_kwh, 4),
        "comfort_penalty": round(comfort_eval.comfort_penalty, 4),
        "reward": round(step_reward, 4),
        "trajectory": [
            {"time_offset": 5, "predicted_temp": active_pred.temp_t5},
            {"time_offset": 15, "predicted_temp": active_pred.temp_t15},
            {"time_offset": 30, "predicted_temp": active_pred.temp_t30}
        ],
        "humidity_trajectory": [
            {"time_offset": 5, "predicted_hum": active_pred.hum_t5},
            {"time_offset": 15, "predicted_hum": active_pred.hum_t15},
            {"time_offset": 30, "predicted_hum": active_pred.hum_t30}
        ],
    }


class LogSimulationRequest(BaseModel):
    timestamp: str
    time_of_day: str
    initial_temp: float
    outdoor_temp: float
    target_band: str
    solar_kw: float
    base_tariff: float
    legacy_cost: float
    neural_cost: float
    total_savings: float
    actions_taken: list

@app.post("/api/log_simulation")
def log_simulation(req: LogSimulationRequest):
    logs_path = Path(__file__).parent / "data" / "processed" / "simulation_logs.json"
    logs = []
    if logs_path.exists():
        with open(logs_path, "r") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    
    logs.insert(0, req.model_dump()) # Prepend latest
    # Keep last 50
    logs = logs[:50]
    
    with open(logs_path, "w") as f:
        json.dump(logs, f, indent=2)
        
    return {"status": "success"}

@app.get("/api/sim_logs")
def get_sim_logs():
    logs_path = Path(__file__).parent / "data" / "processed" / "simulation_logs.json"
    if logs_path.exists():
        with open(logs_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

@app.get("/api/metrics")
def get_metrics():
    metrics_path = Path(__file__).parent / "data" / "processed" / "metrics.json"
    if metrics_path.exists():
        with open(metrics_path, "r") as f:
            return json.load(f)
    return {"error": "Metrics not generated yet."}

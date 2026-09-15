from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import json

from backend.app.core.actions import WispAction
from backend.app.core.types import ThermalState, Disturbance
from backend.app.prediction.neural_engine import NeuralPredictionEngine

app = FastAPI(title="Wisp Climate Control API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = NeuralPredictionEngine(device="cpu")

class PredictRequest(BaseModel):
    zone_id: str
    current_temp: float
    target_temp: float
    mode: str = "COOLING"


@app.post("/api/predict")
def predict(req: PredictRequest):
    thermal = ThermalState(
        indoor_temperature=req.current_temp,
        indoor_humidity=50.0,
        thermostat_temperature=req.current_temp,
        heat_setpoint=68.0,
        cool_setpoint=req.target_temp,
    )
    dist = Disturbance(
        outdoor_temperature=85.0,
        outdoor_humidity=60.0,
        solar_irradiance_w_m2=500.0,
        hour_of_day=14,
        day_of_week=2,
    )

    action = WispAction.COOL_HIGH if req.current_temp > req.target_temp else WispAction.NO_ACTION
    res = engine.predict(thermal, action, dist)

    confidence_pct = int(round(res.confidence * 100))

    return {
        "zone_id": req.zone_id,
        "trajectory": [
            {"time_offset": 5, "predicted_temp": res.temp_t5},
            {"time_offset": 15, "predicted_temp": res.temp_t15},
            {"time_offset": 30, "predicted_temp": res.temp_t30}
        ],
        "confidence_score": confidence_pct,
        "humidity_trajectory": [
            {"time_offset": 5, "predicted_hum": res.hum_t5},
            {"time_offset": 15, "predicted_hum": res.hum_t15},
            {"time_offset": 30, "predicted_hum": res.hum_t30}
        ],
    }


@app.get("/api/metrics")
def get_metrics():
    metrics_path = Path(__file__).parent / "data" / "processed" / "metrics.json"
    if metrics_path.exists():
        with open(metrics_path, "r") as f:
            return json.load(f)
    return {"error": "Metrics not generated yet."}

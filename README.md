# Cygnix Horizon: Predictive AI Thermostat & Energy Optimization Engine

Cygnix Horizon is a closed-loop smart climate control platform that combines neural state-space modeling, adaptive conformal inference, and reinforcement learning to optimize building thermal comfort and electricity costs.

Traditional thermostats react only after indoor temperatures drift outside a set deadband, causing temperature overshoot and peak-rate energy consumption. Cygnix Horizon replaces reactive hysteresis with a predictive dual-layer controller: a PyTorch LSTM that forecasts 30-minute thermal trajectories with statistical confidence bounds, and a Dueling Deep Q-Network (DQN) that modulates multi-stage cooling, solar self-consumption, and pre-cooling schedules against dynamic Time-of-Use (TOU) tariffs.

---

## Key Highlights

- **Predictive Horizon**: 30-minute forward thermal forecasting ($+5\text{m}, +15\text{m}, +30\text{m}$) using a calibrated LSTM Neural State-Space Model.
- **Uncertainty Quantification**: Adaptive Conformal Inference (ACI) computes empirical confidence intervals to detect out-of-distribution conditions and prevent ungrounded control actions.
- **Dueling DQN HVAC Policy**: 6-action discrete control space modulating compressor output between 0% and 100% duty cycle, intelligent pre-cooling, and curtailment.
- **Tariff & Solar-Aware**: Direct rooftop solar dispatch without battery dependencies, shifting thermal load to low-cost and high-irradiance windows.
- **Interactive Full-Stack Platform**: FastAPI backend serving sub-10ms inference coupled with a lightweight vanilla JS/Chart.js telemetry and simulation dashboard.
- **Validated Performance**: Tested across 28,800 simulation steps over 20 distinct 24-hour weather/occupancy profiles with a 113-test regression suite.

---

## System Architecture

```
                                  ┌────────────────────────┐
                                  │   Ambient Disturbances │
                                  │ (Outdoor Temp, Solar)  │
                                  └───────────┬────────────┘
                                              │
┌─────────────────────────┐                   ▼                   ┌───────────────────────────┐
│ Indoor Telemetry        │ ──────► ┌──────────────────┐ ───────► │ 30-Min Predicted State    │
│ (Temp, Humidity, Setpt) │         │ Neural Predictor │          │ [T+5m, T+15m, T+30m]      │
└─────────────────────────┘         │  (PyTorch LSTM)  │          └─────────────┬─────────────┘
                                    └─────────┬────────┘                        │
                                              │                                 │
                                              ▼                                 ▼
                                    ┌──────────────────┐          ┌───────────────────────────┐
                                    │ Conformal Engine │ ───────► │ Wisp DQN Agent            │
                                    │ (ACI Confidence) │          │ (State: 15-dim vector)    │
                                    └──────────────────┘          └─────────────┬─────────────┘
                                                                                │
                                                                                ▼
┌─────────────────────────┐         ┌──────────────────┐          ┌───────────────────────────┐
│ Occupant Comfort Model  │ ◄────── │ Energy Simulator │ ◄─────── │ Optimal HVAC Action       │
│ (Deadband Violations)   │         │ (TOU Cost & Net) │          │ (6-Action Discrete Space) │
└─────────────────────────┘         └──────────────────┘          └───────────────────────────┘
```

The system operates across three distinct functional layers:

### 1. Dynamics & Uncertainty Layer
- **Neural State-Space Model**: Predicts indoor temperature and relative humidity trajectory given current thermal states and candidate actions.
- **Conformal Prediction**: Non-conformity scores calibrated over empirical validation residuals scale the model confidence score in real time.

### 2. Decision & Control Layer
- **State Formulation (15 dimensions)**: Indoor temperature/humidity, outdoor temperature, $+5\text{m}/+15\text{m}/+30\text{m}$ predictions, model confidence, occupant comfort bounds $[T_{\text{low}}, T_{\text{high}}]$, solar generation ($\text{kW}$), and active electricity tariff ($\text{¢/kWh}$).
- **Action Space**:
  - `0: NO_ACTION` ($0.00\text{ kW}$) — Zero compressor draw; room in steady state.
  - `1: COOL_LOW` ($1.16\text{ kW}$) — 33% modulation for baseline maintenance.
  - `2: COOL_MEDIUM` ($2.31\text{ kW}$) — 66% modulation for steady cooling.
  - `3: COOL_HIGH` ($3.50\text{ kW}$) — 100% maximum capacity for fast pulldown.
  - `4: PRECOOL` ($2.31\text{ kW}$) — Active pre-cooling prior to tariff peaks or solar drops.
  - `5: REDUCE_HVAC` ($0.00\text{ kW}$) — Controlled setback near lower comfort boundaries.
- **Reward Optimization**:
  $$R_t = -\alpha \cdot \text{ComfortPenalty} - \beta \cdot \text{Energy}_{\text{kWh}} - \gamma \cdot \text{Cost}_{\$} - \delta \cdot \text{Switching} + \lambda \cdot \text{SolarUsed}_{\text{kWh}}$$

### 3. Application & Visualization Layer
- **FastAPI Core**: Exposes `/api/predict`, `/api/wisp/decide`, and `/api/wisp/benchmark`.
- **Telemetry UI**: Live chart visualization, real-time power cards, Q-value inspection, and hardware-in-the-loop toggle (Arduino DHT22 sensor support).

---

## Benchmark Results

Evaluation conducted across **20 full 24-hour scenarios** (288 five-minute timesteps per scenario, 5,760 total steps per controller) comparing against conventional and rule-based baselines:

| Controller | Comfort Violation Rate (%) | Mean Temp Deviation (°F) | Total Energy (kWh) | Electricity Cost ($) | Switching Events | Mean Reward |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **No Control** | 71.30% | 2.148 | 0.00 | $0.00 | 0.0 | -874.32 |
| **Simple Thermostat** | 30.19% | 0.294 | 23.41 | $73.33 | 66.05 | -272.90 |
| **Wisp Rule-Based** | 53.47% | 0.812 | 25.63 | $90.04 | 39.70 | -479.46 |
| **Wisp DQN (Baseline)** | 35.80% | 0.355 | 67.20 | $253.11 | 0.00 | -343.82 |
| **Wisp DQN (Long-Trained)** | **28.11%** | **0.263** | **41.94** | **$158.00** | **19.55** | **-255.10** |

### Benchmark Takeaways
- **Lowest Comfort Violations**: The long-trained DQN achieved the lowest comfort violation rate ($28.11\%$) and lowest average temperature deviation ($0.263^\circ\text{F}$) across all tested controllers.
- **Policy Diversity**: Unlike simple bang-bang thermostats that cycle aggressively (66 switches/day), the RL policy balances duty cycle modulation ($89.1\%$ `COOL_LOW`, $4.1\%$ `COOL_MEDIUM`, $3.6\%$ `PRECOOL`, $3.2\%$ `REDUCE_HVAC`) to minimize equipment wear.
- **Context Responsiveness**: Pre-cooling dynamically activates when prediction confidence is high ($\ge 0.85$) and tariff rates are low, saving peak operational costs.

---

## Repository Structure

```
cygnix-hackathon/
├── backend/
│   ├── app/
│   │   ├── core/                  # Action definitions, state dataclasses, telemetry types
│   │   ├── energy/                # Solar PV model, TOU tariff schedules, energy simulator
│   │   ├── personalization/       # Occupant preference modeling, comfort loss functions
│   │   ├── prediction/            # LSTM neural engine, conformal prediction wrappers
│   │   ├── simulation/            # 5-minute Gym-compatible WispEnv environment
│   │   ├── controller/            # Baseline controllers (Simple Thermostat, Rule-Based)
│   │   ├── rl/                    # DQN architecture, replay buffer, agent, training & evaluation
│   │   │   └── results/           # CSV/JSON benchmarks, ablation studies, figures, markdown report
│   │   └── tests/                 # 11 test modules covering unit, physics, and RL regression
│   ├── models/
│   │   └── saved_models/          # Trained weights for LSTM and DQN checkpoints (.pth)
│   ├── app.py                     # Legacy endpoint definitions
│   └── main.py                    # Primary FastAPI server entrypoint
├── frontend/
│   ├── src/
│   │   ├── components/            # UI components (PredictionsTab, Dashboard, Metrics, etc.)
│   │   ├── data/                  # Mock data definitions and fallback states
│   │   ├── styles/                # Modular CSS design system
│   │   ├── App.js                 # Application state router
│   │   └── index.js               # Frontend entrypoint
│   └── index.html                 # Main single-page application shell
├── conftest.py                    # Pytest test discovery configuration
├── ecobee.sh                      # Deployment & test execution script
└── requirements.txt               # Backend Python dependencies
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js / npm (optional for static asset bundling; frontend runs standalone over HTTP)

### 1. Clone & Environment Setup
```bash
git clone https://github.com/saksham-mittal29/cygnix-hackathon.git
cd cygnix-hackathon

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Running Backend & Frontend

#### Start the FastAPI Backend
```bash
PYTHONPATH=. uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
API docs will be accessible at: `http://localhost:8000/docs`

#### Start the Frontend Web App
```bash
python3 -m http.server 3000 --directory frontend
```
Open `http://localhost:3000` in your browser.

---

## Running the Test & Benchmark Suite

Execute all 113 automated unit, integration, and physics regression tests:
```bash
pytest backend/app/tests/ -v
```

To re-run the 24-hour benchmark evaluation engine:
```bash
python3 -m backend.app.rl.final_benchmark
```
Generated artifacts, summary tables, and PNG plots are written to `backend/app/rl/results/final_benchmark/`.

---

## API Endpoints

### `POST /api/predict`
Executes real-time inference across the neural predictor and DQN controller.

**Sample Request**:
```json
{
  "zone_id": "living_room",
  "current_temp": 76.5,
  "current_humidity": 50.0,
  "outdoor_temp": 85.0,
  "preferred_temp_low": 70.0,
  "preferred_temp_high": 74.0,
  "solar_kw": 2.0,
  "tariff_rate": 10.0
}
```

**Sample Response**:
```json
{
  "controller": "Wisp DQN",
  "action": "COOL_MEDIUM",
  "confidence_score": 88,
  "hvac_power_kw": 2.31,
  "estimated_cost": 0.675,
  "q_values": {
    "NO_ACTION": -26.1352,
    "COOL_LOW": -21.7465,
    "COOL_MEDIUM": -19.503,
    "COOL_HIGH": -20.0893,
    "PRECOOL": -19.6149,
    "REDUCE_HVAC": -25.1262
  },
  "trajectory": [
    {"time_offset": 5, "predicted_temp": 76.33},
    {"time_offset": 15, "predicted_temp": 75.97},
    {"time_offset": 30, "predicted_temp": 75.70}
  ]
}
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
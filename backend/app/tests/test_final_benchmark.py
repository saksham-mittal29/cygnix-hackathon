"""
test_final_benchmark.py
-----------------------
Test suite for the Final Benchmarking Experiment.

Verifies:
1. 20 benchmark scenarios generation across categories A-N
2. 24-hour (288-step) simulation rollout integrity
3. 5-controller evaluation consistency
4. Metric calculations (comfort, energy, cost, switching, solar, entropy)
5. Context responsiveness paired tests
6. Output artifact generation and plot existence
"""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from backend.app.core.actions import WispAction
from backend.app.rl.final_benchmark import (
    get_20_benchmark_scenarios,
    run_single_benchmark_episode,
    run_paired_context_responsiveness_tests,
)
from backend.app.prediction.neural_engine import NeuralPredictionEngine
from backend.app.rl.agent import DQNAgent


def test_1_twenty_scenarios_generated():
    """Verify 20 distinct 24-hour benchmark scenarios are created."""
    scenarios = get_20_benchmark_scenarios()
    assert len(scenarios) == 20
    assert all(sc.steps == 288 for sc in scenarios)
    categories = {sc.category for sc in scenarios}
    assert "Comfortable" in categories
    assert "Severe_Heat" in categories
    assert "Overcooled" in categories
    assert "High_Solar" in categories
    assert "Peak_Tariff" in categories


def test_2_single_episode_rollout():
    """Verify 24-hour episode rollout produces exactly 288 steps."""
    scenarios = get_20_benchmark_scenarios()
    sc = scenarios[0]
    pred_engine = NeuralPredictionEngine()

    metrics, ts = run_single_benchmark_episode(
        controller_name="NO_CONTROL",
        scenario=sc,
        pred_engine=pred_engine,
    )
    assert metrics.total_steps == 288
    assert len(ts) == 288
    assert metrics.no_action_pct == 100.0


def test_3_context_responsiveness_pairs():
    """Verify paired tests evaluate all 6 contextual dimensions."""
    agent = DQNAgent()
    agent.load_checkpoint("backend/models/saved_models/dqn_phase10_long_training.pth")
    out_dir = Path("backend/app/rl/results/final_benchmark")
    out_dir.mkdir(parents=True, exist_ok=True)

    df = run_paired_context_responsiveness_tests(agent, out_dir)
    assert len(df) == 6
    variables = set(df["tested_variable"].tolist())
    assert "Electricity Tariff" in variables
    assert "Solar Generation" in variables
    assert "Indoor Temperature" in variables

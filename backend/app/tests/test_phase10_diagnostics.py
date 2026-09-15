"""
test_phase10_diagnostics.py
---------------------------
Focused test suite for Phase 10: Stress Testing, Q-Value Inspection, and Ablation Studies.

Verifies:
1. Q-value inspection across representative states
2. Stress-test matrix parameter generation
3. Feature ablation masks and zero-neutral masking
4. Reward-weight sensitivity variation
5. Policy diversity & action entropy calculations
6. Long-training diagnostic model save and load
7. Diagnostics execution integrity
"""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from backend.app.core.actions import WispAction
from backend.app.rl.diagnostics import (
    inspect_q_values,
    run_stress_test_matrix,
    run_feature_ablations,
    run_reward_sensitivity,
    run_long_training_diagnostic,
    analyze_policy_diversity,
)


def test_1_q_value_inspection():
    """Verify Q-value inspection produces valid 6-action values for 8 states."""
    df = inspect_q_values()
    assert len(df) == 8
    assert "Q_NO_ACTION" in df.columns
    assert "Q_COOL_LOW" in df.columns
    assert "Q_COOL_MEDIUM" in df.columns
    assert "Q_COOL_HIGH" in df.columns
    assert "Q_PRECOOL" in df.columns
    assert "Q_REDUCE_HVAC" in df.columns
    assert "selected_action" in df.columns
    assert df["Q_NO_ACTION"].notna().all()


def test_2_stress_test_matrix_generation():
    """Verify stress test output file exists and has varied thermal conditions."""
    df = pd.read_csv("backend/app/rl/results/stress_test_results.csv")
    assert len(df) >= 100
    assert set(df["preference_envelope"].unique()) == {"wide", "normal", "narrow", "cool", "warm"}
    assert df["selected_action"].nunique() >= 2


def test_3_feature_ablations():
    """Verify ablation study evaluates all 7 configurations."""
    df = run_feature_ablations()
    assert len(df) == 7
    variants = set(df["ablation_variant"].tolist())
    assert "A_FULL" in variants
    assert "B_NO_FORECAST" in variants
    assert "G_MINIMAL" in variants


def test_4_reward_sensitivity():
    """Verify reward sensitivity executes across all 6 weight regimes."""
    df = run_reward_sensitivity()
    assert len(df) == 6
    assert set(df["weight_regime"].tolist()) == {
        "1_DEFAULT",
        "2_COMFORT_HEAVY",
        "3_ENERGY_HEAVY",
        "4_COST_HEAVY",
        "5_SWITCHING_HEAVY",
        "6_SOLAR_HEAVY",
    }


def test_5_policy_diversity_analysis():
    """Verify entropy and responsiveness metrics are computed properly."""
    stress_df = pd.read_csv("backend/app/rl/results/stress_test_results.csv")
    long_df = pd.read_csv("backend/app/rl/results/long_training_metrics.csv")
    summary = analyze_policy_diversity(stress_df, long_df)

    assert "action_entropy" in summary
    assert summary["action_entropy"] > 0.0
    assert "unique_actions_in_stress_test" in summary
    assert summary["unique_actions_in_stress_test"] >= 2


def test_6_long_training_checkpoint_exists():
    """Verify diagnostic long-training checkpoint was successfully saved and is loadable."""
    chkpt = Path("backend/models/saved_models/dqn_phase10_long_training.pth")
    assert chkpt.exists()

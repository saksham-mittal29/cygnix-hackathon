"""
Prediction package for Wisp Person 3.
"""

from backend.app.prediction.base import BasePredictionEngine
from backend.app.prediction.neural_engine import NeuralPredictionEngine

__all__ = [
    "BasePredictionEngine",
    "NeuralPredictionEngine",
]

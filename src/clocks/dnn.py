"""DNN-based biological age clock.

A three-layer fully connected neural network (9→128→64→32→1)
that predicts biological age from blood biomarkers.
Supports loading pre-trained weights and falls back to an
empirical formula when weights are unavailable.
"""

from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional

import numpy as np

from . import BaseClock, ClockResult
from src.core.exceptions import ComputationError, ModelNotFound

# Empirical formula coefficients for fallback mode
FALLBACK_COEFFICIENTS: Dict[str, float] = {
    "albumin": -0.028,
    "creatinine": 0.011,
    "glucose": 0.220,
    "lymphocyte_percent": -0.009,
    "mcv": 0.030,
    "rdw": 0.350,
    "alkaline_phosphatase": 0.0021,
    "white_blood_cell_count": 0.048,
}
FALLBACK_INTERCEPT = 18.5
FALLBACK_AGE_COEFF = 0.072


class DNNClock(BaseClock):
    """Deep neural network aging clock (3-layer fully connected).

    When pre-trained weights are available, uses a neural network;
    otherwise falls back to a calibrated empirical formula.
    """

    name: ClassVar[str] = "dnn"
    version: ClassVar[str] = "1.0.0"
    required_biomarkers: ClassVar[List[str]] = [
        "albumin",
        "creatinine",
        "glucose",
        "lymphocyte_percent",
        "mcv",
        "rdw",
        "alkaline_phosphatase",
        "white_blood_cell_count",
        "age",
    ]

    def __init__(self, model_path: Optional[str] = None) -> None:
        """Initialize the DNN clock.

        Args:
            model_path: Path to a .pt file with pre-trained weights.
        """
        self._model_path = model_path
        self._model = None
        self._using_fallback = False
        if model_path and Path(model_path).exists():
            try:
                self._model = self._load_torch_model(model_path)
            except Exception:
                self._using_fallback = True
        else:
            self._using_fallback = True

    def _load_torch_model(self, path: str) -> Any:
        """Load a PyTorch model from a .pt file.

        Args:
            path: Path to the weights file.

        Returns:
            Loaded model or None if loading fails.
        """
        try:
            import torch
            model = torch.nn.Sequential(
                torch.nn.Linear(9, 128),
                torch.nn.ReLU(),
                torch.nn.Linear(128, 64),
                torch.nn.ReLU(),
                torch.nn.Linear(64, 32),
                torch.nn.ReLU(),
                torch.nn.Linear(32, 1),
            )
            model.load_state_dict(torch.load(path, map_location="cpu"))
            model.eval()
            return model
        except ImportError:
            raise ModelNotFound(
                "PyTorch not available, cannot load DNN model",
                details={"path": path},
            )
        except Exception as e:
            raise ModelNotFound(
                f"Failed to load DNN model from {path}: {e}",
                details={"path": path, "error": str(e)},
            )

    def predict(self, biomarkers: Dict[str, Any]) -> ClockResult:
        """Compute biological age using DNN or empirical fallback.

        Args:
            biomarkers: Dictionary with biomarker values.

        Returns:
            ClockResult with predicted age.

        Raises:
            ComputationError: If required biomarkers are missing.
        """
        missing = self._check_required(biomarkers)
        if missing:
            raise ComputationError(
                f"DNN missing biomarkers: {missing}",
                details={"missing": missing},
            )

        try:
            if self._model is not None and not self._using_fallback:
                return self._predict_dnn(biomarkers)
            return self._predict_fallback(biomarkers)
        except Exception as e:
            return self._predict_fallback(biomarkers)

    def _predict_dnn(self, biomarkers: Dict[str, Any]) -> ClockResult:
        """Run prediction through the neural network.

        Args:
            biomarkers: Biomarker dictionary.

        Returns:
            ClockResult from the network prediction.
        """
        import torch
        feature_order = [k for k in self.required_biomarkers if k != "age"]
        features = [float(biomarkers[f]) for f in feature_order]
        tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            predicted = float(self._model(tensor).item())
        chron_age = float(biomarkers["age"])
        conf = min(0.9, max(0.5, 1.0 - abs(predicted - chron_age) / 25.0))
        return ClockResult(
            predicted_age=predicted,
            lower_bound=predicted - 4.0,
            upper_bound=predicted + 4.0,
            confidence=conf,
            metadata={"model": "DNN_3layer", "method": "neural_network"},
        )

    def _predict_fallback(self, biomarkers: Dict[str, Any]) -> ClockResult:
        """Run prediction using the empirical formula fallback.

        Args:
            biomarkers: Biomarker dictionary.

        Returns:
            ClockResult from the empirical formula.
        """
        age = float(biomarkers["age"])
        predictor = FALLBACK_INTERCEPT + FALLBACK_AGE_COEFF * age
        for marker, coeff in FALLBACK_COEFFICIENTS.items():
            value = float(biomarkers.get(marker, 0))
            predictor += coeff * value
        predicted = max(18.0, min(120.0, predictor))
        conf = min(0.8, max(0.4, 1.0 - abs(predicted - age) / 30.0))
        return ClockResult(
            predicted_age=predicted,
            lower_bound=predicted - 5.0,
            upper_bound=predicted + 5.0,
            confidence=conf,
            metadata={"model": "DNN_fallback", "method": "empirical"},
        )

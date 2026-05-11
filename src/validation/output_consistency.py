"""Output consistency checker — detects anomalies against historical trajectories.

Compares current assessment results against stored historical data
to identify anomalous jumps in biological age that may indicate
measurement error or genuine health changes.
"""

from typing import Any, Dict, List, Optional, Tuple


class OutputConsistency:
    """Checks output consistency against historical trajectories.

    Maintains a history of assessment results and flags anomalous
    deviations from the expected aging trajectory.

    Attributes:
        max_history: Maximum number of historical records to retain.
        anomaly_threshold: Z-score threshold for anomaly flagging (default 2.0).
    """

    def __init__(
        self,
        max_history: int = 10,
        anomaly_threshold: float = 2.0,
    ) -> None:
        self.max_history = max_history
        self.anomaly_threshold = anomaly_threshold
        self._history: List[Dict[str, Any]] = []

    def add_record(self, record: Dict[str, Any]) -> None:
        """Add a new assessment record to the history.

        Args:
            record: Assessment record with at least 'biological_age'
                    and 'chronological_age'.
        """
        self._history.append({
            "biological_age": record.get("biological_age", 0),
            "chronological_age": record.get("chronological_age", 0),
            "timestamp": record.get("timestamp", ""),
            "confidence": record.get("confidence", 0),
        })
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history:]

    def check(
        self, current: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check the current assessment for consistency with history.

        Args:
            current: Current assessment with at least 'biological_age'
                     and 'chronological_age'.

        Returns:
            Dict with consistency assessment: is_consistent, warnings,
            expected_age, z_score.
        """
        bio_age = current.get("biological_age", 0)
        chron_age = current.get("chronological_age", 0)

        if len(self._history) < 2:
            self.add_record(current)
            return {
                "is_consistent": True,
                "warnings": [],
                "expected_age": None,
                "z_score": None,
                "note": "历史数据不足，无法进行一致性检查",
            }

        # Compute expected age from historical trend
        expected = self._predict_expected(chron_age)
        if expected is None:
            self.add_record(current)
            return {
                "is_consistent": True,
                "warnings": [],
                "expected_age": None,
                "z_score": None,
            }

        # Compute deviation
        historical_std = self._compute_historical_std()
        if historical_std == 0:
            self.add_record(current)
            return {"is_consistent": True, "warnings": [], "expected_age": expected, "z_score": 0.0}

        z_score = abs(bio_age - expected) / historical_std
        is_consistent = z_score < self.anomaly_threshold

        warnings = []
        if not is_consistent:
            direction = "高于" if bio_age > expected else "低于"
            warnings.append(
                f"生物年龄异常: 当前值{bio_age:.1f}岁{direction}预期值{expected:.1f}岁 "
                f"(Z-score={z_score:.2f}，阈值={self.anomaly_threshold})"
            )
            if z_score > 3.0:
                warnings.append("偏差极大(Z>3)，强烈建议核实数据质量或重复检测")

        self.add_record(current)

        return {
            "is_consistent": is_consistent,
            "warnings": warnings,
            "expected_age": round(expected, 1),
            "z_score": round(z_score, 2),
        }

    def _predict_expected(self, chron_age: float) -> Optional[float]:
        """Predict expected biological age from historical trend.

        Uses simple linear regression on chronological age.

        Args:
            chron_age: Current chronological age.

        Returns:
            Expected biological age or None if insufficient data.
        """
        if len(self._history) < 2:
            return None

        x = [r["chronological_age"] for r in self._history]
        y = [r["biological_age"] for r in self._history]

        n = len(x)
        mean_x = sum(x) / n
        mean_y = sum(y) / n

        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        denominator = sum((xi - mean_x) ** 2 for xi in x)

        if denominator == 0:
            return mean_y

        slope = numerator / denominator
        intercept = mean_y - slope * mean_x
        return intercept + slope * chron_age

    def _compute_historical_std(self) -> float:
        """Compute standard deviation of biological ages in history.

        Returns:
            Standard deviation or 0 if insufficient data.
        """
        if len(self._history) < 2:
            return 0.0

        values = [r["biological_age"] for r in self._history]
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
        return variance ** 0.5

    def get_trajectory(self) -> List[Dict[str, Any]]:
        """Get the stored historical trajectory.

        Returns:
            List of historical assessment records.
        """
        return list(self._history)

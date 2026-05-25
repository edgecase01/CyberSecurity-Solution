"""Placeholder ML inference — replace ScamModelPredictor with your ONNX pipeline."""

import random
from typing import Any


class ScamModelPredictor:
    """Dummy scam classifier until real ONNX models are wired in."""

    def predict_text(self, text: str, subject: str = "") -> dict[str, Any]:
        """Classify email body/subject (placeholder for ONNX text model)."""
        return self.predict({"text": text, "subject": subject, "content_type": "email"})

    def predict(self, features: dict[str, Any]) -> dict[str, Any]:
        confidence = round(random.uniform(0.0, 1.0), 4)
        is_scam = confidence >= 0.5

        return {
            "is_scam": is_scam,
            "confidence": confidence,
            "label": "scam" if is_scam else "legitimate",
            "model_version": "placeholder-v0",
            "features_received": list(features.keys()),
        }

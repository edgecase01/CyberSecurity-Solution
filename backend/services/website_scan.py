"""Orchestrate scrape → ML predict → structured scan result."""

import json
from typing import Any

from ml_service import ScamModelPredictor
from scraper import ScrapeFeatures, scrape_url

_predictor = ScamModelPredictor()


async def run_website_scan(url: str, timeout: float) -> dict[str, Any]:
    features: ScrapeFeatures = await scrape_url(url, timeout=timeout)
    feature_dict = features.to_dict()
    prediction = _predictor.predict(feature_dict)

    return {
        "features": feature_dict,
        "prediction": prediction,
    }


def result_to_json(result: dict[str, Any]) -> str:
    return json.dumps(result)

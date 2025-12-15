# modules/model_core.py
# -*- coding: utf-8 -*-

"""
Thin orchestration layer:
1. Calls external inference API for labels.
2. Runs local recommender with returned labels.
"""

from __future__ import annotations
from typing import Dict
from PIL import Image

from modules.inference_client import analyze_image
from modules.recommender_pair import GenderedRecommender


def infer_labels(image: Image.Image) -> Dict[str, str]:
    """
    Send image to external inference service.
    Returns {
        "color": <str>,
        "style": <str>,
        "category": <str>,
        "part": "Top" | "Bottom"
    }
    """
    try:
        return analyze_image(image)
    except Exception as e:
        print("[model_core][ERROR] external inference failed:", e)
        return {
            "color": None,
            "style": None,
            "category": None,
            "part": None,
        }


def infer_and_recommend(
    image: Image.Image,
    recommender: GenderedRecommender,
    gender: str,
    k: int = 3,
) -> Dict:
    """
    Run external inference, then generate recommendations with the local recommender.
    """
    labels = infer_labels(image)

    if labels.get("color") is None:
        return {
            "input_label": labels,
            "recommendations": []
        }

    item = {
        "color": labels["color"],
        "style": labels["style"],
        "category": labels["category"],
        "part": labels["part"],
    }

    try:
        recs = recommender.recommend(item, gender=gender, K=k)
    except Exception as e:
        print("[model_core][ERROR] recommend failed:", e)
        recs = []

    return {
        "input_label": labels,
        "recommendations": recs
    }

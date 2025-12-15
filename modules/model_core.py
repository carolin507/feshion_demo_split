# modules/model_core.py
# -*- coding: utf-8 -*-

"""
model_core.py

新版功能：
1. 提供統一介面給前端（wardrobe.py）
2. 整合：
    - AI image classifier（可替換：CLIP / YOLO / etc.）
    - GenderedRecommender（共現 + 機率式混合推薦器）
3. 提供兩個核心 API：
    - infer_labels(image)                     → 影像推論
    - infer_and_recommend(image, gender, K)  → 影像推論 + 推薦
"""

from __future__ import annotations
from typing import Dict
from PIL import Image

# === 影像 AI 模型（未來可更換） ===
try:
    from modules.ai_models.clip_classifier import ClipClassifier
    _fashion_model = ClipClassifier()
    print("[model_core] ClipClassifier 已成功載入")
except Exception as e:
    print(f"[model_core][WARN] ClipClassifier 載入失敗：{e}")
    _fashion_model = None

# === 新版推薦器 ===
from modules.recommender_pair import GenderedRecommender


# ============================================================
# 1) 影像辨識 API（你們前端會呼叫這個）
# ============================================================

def infer_labels(image: Image.Image) -> Dict[str, str]:
    """
    統一的影像分析入口。

    回傳格式：
    {
        "color": <str>,
        "style": <str>,
        "category": <str>,
        "part": "Top" | "Bottom"
    }
    """

    if _fashion_model is None:
        # 若沒有模型 → 用 placeholder（不讓前端壞掉）
        return {
            "color": "White",
            "style": "Solid",
            "category": "Shirt",
            "part": "Top"
        }

    try:
        return _fashion_model.analyze(image)
    except Exception as e:
        print("[model_core][ERROR] analyze failed:", e)
        return {
            "color": None,
            "style": None,
            "category": None,
            "part": None,
        }


# ============================================================
# 2) 主功能：影像分析 + 共現推薦（新推薦器）
# ============================================================

def infer_and_recommend(
    image: Image.Image,
    recommender: GenderedRecommender,
    gender: str,
    k: int = 3,
) -> Dict:
    """
    image → AI labels → 推薦器 → K 個推薦結果

    回傳：
    {
        "input_label": {...},
        "recommendations": [ item1, item2, item3 ]
    }
    """

    # ---- Step 1：影像辨識 ----
    labels = infer_labels(image)

    if labels.get("color") is None:
        # 若 model 載入失敗不 crash
        return {
            "input_label": labels,
            "recommendations": []
        }

    # ---- Step 2：將辨識結果轉為推薦器的 item 格式 ----
    item = {
        "color": labels["color"],
        "style": labels["style"],
        "category": labels["category"],
        "part": labels["part"],  # Top or Bottom
    }

    # ---- Step 3：性別推薦器 ----
    try:
        recs = recommender.recommend(
            item,
            gender=gender,
            K=k
        )
    except Exception as e:
        print("[model_core][ERROR] recommend failed:", e)
        recs = []

    return {
        "input_label": labels,
        "recommendations": recs
    }

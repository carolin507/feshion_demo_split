# modules/inference.py
# -*- coding: utf-8 -*-

"""
影像辨識推論模組 inference.py
--------------------------------
此版本專門給前端呼叫，用於：
1. 對上傳圖片進行 CLIP 辨識（顏色 / 花紋 / 類別 / 上下身 part）
2. 回傳與前端相容的字典格式

真正的 AI 模型邏輯放在：
    modules/model_core.py

此檔案僅負責「轉接」與「格式化輸出」。
"""

from __future__ import annotations

from PIL import Image
from modules.model_core import infer_labels


def predict_labels(image: Image.Image, gender: str):
    """
    給前端的主要入口：

    輸入：
        - image: PIL.Image
        - gender: "female" | "male"

    輸出格式（100% 與前端一致）：
    {
        "color": "White",
        "pattern": "Striped",
        "category": "T-Shirt",
        "part": "Top",
        "gender": "female"
    }
    """

    # 1. 用 CLIP 推論影像標籤（color/style/category/part）
    labels = infer_labels(image)

    # 2. 回傳與前端預期完全相符的結構
    #    pattern = style（為了配合 wardrobe.py 現有欄位）
    return {
        "color": labels["color"],
        "pattern": labels["style"],       # 前端顯示「花紋」的欄位
        "category": labels["category"],
        "part": labels["part"],           # 可選（目前前端沒顯示，但保留）
        "gender": gender,
    }

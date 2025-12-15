# modules/ai_models/clip_classifier.py
# -*- coding: utf-8 -*-

from __future__ import annotations
from typing import Dict, List
import torch
import clip
from PIL import Image

from modules.ai_models.base_model import BaseFashionModel


# ------------------------------------------------------------
# Label 定義
# ------------------------------------------------------------
COLOR_LABELS = [
    "Black", "Gray", "White", "Beige", "Orange",
    "Pink", "Red", "Green", "Brown", "Blue",
    "Yellow", "Purple"
]

STYLE_LABELS = ["Solid", "Striped", "Floral", "Plaid", "Spotted"]

CATEGORY_LABELS = [
    "Top", "T-Shirt", "Shirt", "Cardigan", "Blazer",
    "Sweatshirt", "Vest", "Jacket", "Dress", "Coat",
    "Skirt", "Pants", "Jeans", "Jumpsuit"
]

# ------------------------------------------------------------
# 多 Prompt 上下身分類（最有效！）
# ------------------------------------------------------------
PART_LABELS = {
    "Top": [
        "a person wearing a T-shirt",
        "a person wearing a shirt",
        "a person wearing a sweater",
        "a person wearing a jacket",
        "a person wearing a hoodie",
        "a person wearing a coat"
    ],
    "Bottom": [
        "a person wearing pants",
        "a person wearing jeans",
        "a person wearing a skirt",
        "a person wearing shorts",
        "a person wearing trousers"
    ]
}


# ============================================================
# ClipClassifier（修正版）
# ============================================================
class ClipClassifier(BaseFashionModel):

    def __init__(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        # 1. 載入 CLIP 模型
        self.model, self.preprocess = clip.load("ViT-B/32", device=device)

        # 2. 文本 embedding
        self.color_text_feats    = self._encode_prompts([f"a photo of {c} color" for c in COLOR_LABELS])
        self.style_text_feats    = self._encode_prompts([f"a photo of {s} fabric pattern" for s in STYLE_LABELS])
        self.category_text_feats = self._encode_prompts([f"a photo of a {cat}" for cat in CATEGORY_LABELS])

        # Part: 多 prompt → 每組 embedding
        self.part_text_feats = {
            part: self._encode_prompts(prompts)
            for part, prompts in PART_LABELS.items()
        }

    # --------------------------------------------------------
    # Prompts → Embedding
    # --------------------------------------------------------
    def _encode_prompts(self, prompts: List[str]):
        tokens = clip.tokenize(prompts).to(self.device)
        with torch.no_grad():
            feats = self.model.encode_text(tokens)
        feats /= feats.norm(dim=-1, keepdim=True)
        return feats

    # --------------------------------------------------------
    # Image → Embedding
    # --------------------------------------------------------
    def _image_to_features(self, image: Image.Image):
        img_tensor = self.preprocess(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            feats = self.model.encode_image(img_tensor)
        feats /= feats.norm(dim=-1, keepdim=True)
        return feats

    # --------------------------------------------------------
    # 一般 label：Top-1（顏色 / 花紋 / 類別）
    # --------------------------------------------------------
    def _top_label(self, image_feat, text_feats, labels):
        sims = (image_feat @ text_feats.T)[0]
        idx = torch.argmax(sims).item()
        return labels[idx]

    # --------------------------------------------------------
    # 對外 API：AI 辨識
    # --------------------------------------------------------
    def analyze(self, image: Image.Image) -> Dict[str, str]:

        img_feat = self._image_to_features(image)

        # 顏色 / 花紋 / 類別
        color    = self._top_label(img_feat, self.color_text_feats, COLOR_LABELS)
        style    = self._top_label(img_feat, self.style_text_feats, STYLE_LABELS)
        category = self._top_label(img_feat, self.category_text_feats, CATEGORY_LABELS)

        # ----------------------------------------------------
        # Part（Top / Bottom）採用 average similarity method
        # ----------------------------------------------------
        part_scores = {}

        for part_name, feats in self.part_text_feats.items():
            sims = (img_feat @ feats.T)[0]      # shape [N]
            part_scores[part_name] = float(sims.mean())

        part = max(part_scores, key=part_scores.get)

        return {
            "color": color,
            "style": style,
            "category": category,
            "part": part  # "Top" or "Bottom"
        }

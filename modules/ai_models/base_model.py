# modules/ai_models/base_model.py
# -*- coding: utf-8 -*-

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict
from PIL import Image


class BaseFashionModel(ABC):
    """
    所有影像分析模型（CLIP / YOLO / EPyNet ...）都要繼承這個介面。
    確保 model_core.py 與前端不需要跟著改。
    """

    @abstractmethod
    def analyze(self, image: Image.Image) -> Dict[str, str]:
        """
        輸入：
            image: PIL.Image

        輸出（所有實作都要遵守這個格式）：
        {
            "color": <str>,
            "style": <str>,
            "category": <str>,
            "part": "Top" or "Bottom"
        }
        """
        raise NotImplementedError

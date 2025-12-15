# -*- coding: utf-8 -*-
"""
cooccurrence_recommender.py

從「上半身 × 下半身」共現資料建立簡單的推薦系統模組。

整理自你們在 Colab 的《推薦系統2_0.ipynb》，
但改寫成乾淨、可直接匯入專案使用的 Python module。

核心概念：
- DataFrame 每一列代表一套穿搭
- 至少需要兩個欄位：`top`、`bottom`
- 每個欄位都是 dict，格式為：
    {"color": <str>, "style": <str>, "category": <str>}

你可以先用 create_mock_data() 產生測試資料，
之後再把 RichWear / verified_photo_data.csv 處理成同樣格式，即可直接套用。
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple, Literal

import pandas as pd


PartType = Literal["Top", "Bottom"]

# ------------------------------------------------------------
# 資料結構定義
# ------------------------------------------------------------

@dataclass(frozen=True)
class Item:
    """代表一件單品的精簡描述。"""

    color: str
    style: str
    category: str
    part: PartType  # "Top" or "Bottom"

    @classmethod
    def from_dict(cls, d: Dict, part: PartType) -> "Item":
        return cls(
            color=str(d.get("color", "")).strip(),
            style=str(d.get("style", "")).strip(),
            category=str(d.get("category", "")).strip(),
            part=part,
        )

    def key(self) -> Tuple[str, str, str]:
        """用來當作共現矩陣的 key。"""
        return (self.color, self.style, self.category)


# ------------------------------------------------------------
# 建立共現表的推薦器
# ------------------------------------------------------------

class CoOccurrenceRecommender:
    """
    使用「上衣 × 下著」共現次數做推薦。

    Attributes
    ----------
    top2bottom : dict
        top_key -> Counter(bottom_key -> count)
    bottom2top : dict
        bottom_key -> Counter(top_key -> count)
    """

    def __init__(self, df: pd.DataFrame) -> None:
        """
        Parameters
        ----------
        df : pandas.DataFrame
            必須至少包含兩個欄位：
            - 'top' : dict(color, style, category)
            - 'bottom' : dict(color, style, category)
        """
        self.df = df.copy()
        self.top2bottom = defaultdict(Counter)
        self.bottom2top = defaultdict(Counter)
        self._build_counts()

    # ---- internal helpers ----
    @staticmethod
    def _item_to_key(item_dict: Dict[str, str]) -> Tuple[str, str, str]:
        return (
            str(item_dict.get("color", "")).strip(),
            str(item_dict.get("style", "")).strip(),
            str(item_dict.get("category", "")).strip(),
        )

    def _build_counts(self) -> None:
        """掃過整個 DataFrame，建立 top → bottom / bottom → top 的次數表。"""
        for _, row in self.df.iterrows():
            top = row.get("top")
            bottom = row.get("bottom")
            if not isinstance(top, dict) or not isinstance(bottom, dict):
                # 若格式不正確就跳過
                continue

            t_key = self._item_to_key(top)
            b_key = self._item_to_key(bottom)

            self.top2bottom[t_key][b_key] += 1
            self.bottom2top[b_key][t_key] += 1

    # ---- API：由 top 找 bottom ----
    def recommend_from_top(
        self,
        top_item: Dict[str, str] | Item,
        k: int = 3,
    ) -> List[Dict[str, str]]:
        """
        給定一件上半身單品，推薦最常一起出現的下半身。

        Parameters
        ----------
        top_item : dict 或 Item
            需要有 color/style/category 三個欄位。
        k : int
            回傳前 k 名。

        Returns
        -------
        list of dict
            每個元素格式：
            {
                "color": ...,
                "style": ...,
                "category": ...,
                "count": 共現次數
            }
        """
        if isinstance(top_item, Item):
            t_key = top_item.key()
        else:
            t_key = self._item_to_key(top_item)

        counter = self.top2bottom.get(t_key, Counter())
        results = []
        for b_key, cnt in counter.most_common(k):
            color, style, cat = b_key
            results.append(
                {
                    "color": color,
                    "style": style,
                    "category": cat,
                    "count": int(cnt),
                }
            )
        return results

    # ---- API：由 bottom 找 top ----
    def recommend_from_bottom(
        self,
        bottom_item: Dict[str, str] | Item,
        k: int = 3,
    ) -> List[Dict[str, str]]:
        """給定一件下半身單品，推薦最常一起出現的上半身。"""
        if isinstance(bottom_item, Item):
            b_key = bottom_item.key()
        else:
            b_key = self._item_to_key(bottom_item)

        counter = self.bottom2top.get(b_key, Counter())
        results = []
        for t_key, cnt in counter.most_common(k):
            color, style, cat = t_key
            results.append(
                {
                    "color": color,
                    "style": style,
                    "category": cat,
                    "count": int(cnt),
                }
            )
        return results


# ------------------------------------------------------------
# 工具函式：建立測試用假資料 DataFrame
# ------------------------------------------------------------

def create_mock_data() -> pd.DataFrame:
    """
    建立一小份手刻的 top/bottom 組合，方便在本地測試 recommender。

    回傳的 DataFrame 已符合 CoOccurrenceRecommender 的輸入格式。
    """
    data = [
        {
            "top": {"color": "Gray", "style": "Plaid", "category": "Shirt"},
            "bottom": {"color": "Green", "style": "Solid", "category": "Pants"},
        },
        {
            "top": {"color": "Gray", "style": "Plaid", "category": "Shirt"},
            "bottom": {"color": "Green", "style": "Solid", "category": "Pants"},
        },
        {
            "top": {"color": "Pink", "style": "Floral", "category": "Blazer"},
            "bottom": {"color": "Blue", "style": "Solid", "category": "Skirt"},
        },
        {
            "top": {"color": "White", "style": "Striped", "category": "T-Shirt"},
            "bottom": {"color": "Blue", "style": "Solid", "category": "Skirt"},
        },
        {
            "top": {"color": "White", "style": "Striped", "category": "T-Shirt"},
            "bottom": {"color": "Blue", "style": "Solid", "category": "Jeans"},
        },
        {
            "top": {"color": "Gray", "style": "Plaid", "category": "Shirt"},
            "bottom": {"color": "Black", "style": "Plaid", "category": "Pants"},
        },
        {
            "top": {"color": "Orange", "style": "Solid", "category": "Cardigan"},
            "bottom": {"color": "Brown", "style": "Solid", "category": "Jeans"},
        },
        {
            "top": {"color": "Purple", "style": "Solid", "category": "Coat"},
            "bottom": {"color": "Blue", "style": "Solid", "category": "Skirt"},
        },
        {
            "top": {"color": "Gray", "style": "Plaid", "category": "Shirt"},
            "bottom": {"color": "White", "style": "Solid", "category": "Jeans"},
        },
        {
            "top": {"color": "Pink", "style": "Spotted", "category": "Top"},
            "bottom": {"color": "Yellow", "style": "Solid", "category": "Skirt"},
        },
        {
            "top": {"color": "Blue", "style": "Solid", "category": "Jacket"},
            "bottom": {"color": "Black", "style": "Striped", "category": "Skirt"},
        },
        {
            "top": {"color": "White", "style": "Striped", "category": "T-Shirt"},
            "bottom": {"color": "Blue", "style": "Solid", "category": "Jeans"},
        },
        {
            "top": {"color": "White", "style": "Solid", "category": "T-Shirt"},
            "bottom": {"color": "Blue", "style": "Solid", "category": "Jeans"},
        },
        {
            "top": {"color": "Green", "style": "Striped", "category": "T-Shirt"},
            "bottom": {"color": "Blue", "style": "Solid", "category": "Jeans"},
        },
        {
            "top": {"color": "Green", "style": "Solid", "category": "Sweatshirt"},
            "bottom": {"color": "Gray", "style": "Solid", "category": "Pants"},
        },
        {
            "top": {"color": "Red", "style": "Plaid", "category": "Cardigan"},
            "bottom": {"color": "Blue", "style": "Solid", "category": "Skirt"},
        },
        {
            "top": {"color": "Yellow", "style": "Solid", "category": "Top"},
            "bottom": {"color": "Black", "style": "Solid", "category": "Pants"},
        },
        {
            "top": {"color": "Gray", "style": "Plaid", "category": "Shirt"},
            "bottom": {"color": "Purple", "style": "Solid", "category": "Skirt"},
        },
        {
            "top": {"color": "Beige", "style": "Striped", "category": "Blazer"},
            "bottom": {"color": "Blue", "style": "Solid", "category": "Skirt"},
        },
        {
            "top": {"color": "Green", "style": "Plaid", "category": "Jacket"},
            "bottom": {"color": "Brown", "style": "Solid", "category": "Pants"},
        },
        {
            "top": {"color": "Purple", "style": "Solid", "category": "Cardigan"},
            "bottom": {"color": "Blue", "style": "Solid", "category": "Skirt"},
        },
        {
            "top": {"color": "Gray", "style": "Plaid", "category": "Shirt"},
            "bottom": {"color": "Black", "style": "Solid", "category": "Pants"},
        },
        {
            "top": {"color": "White", "style": "Floral", "category": "Top"},
            "bottom": {"color": "Blue", "style": "Solid", "category": "Skirt"},
        },
        {
            "top": {"color": "Pink", "style": "Solid", "category": "Coat"},
            "bottom": {"color": "Blue", "style": "Solid", "category": "Skirt"},
        },
    ]
    return pd.DataFrame(data)


# ------------------------------------------------------------
# 方便前端使用的 helper
# ------------------------------------------------------------

def recommend_bottom_from_labels(
    recommender: CoOccurrenceRecommender,
    color: str,
    style: str,
    category: str,
    k: int = 3,
) -> List[Dict[str, str]]:
    """
    提供給前端 / 其他模組使用的簡化接口。

    Example
    -------
    df = create_mock_data()
    rec = CoOccurrenceRecommender(df)
    results = recommend_bottom_from_labels(rec, "White", "Striped", "T-Shirt")
    """
    item = {"color": color, "style": style, "category": category}
    return recommender.recommend_from_top(item, k=k)

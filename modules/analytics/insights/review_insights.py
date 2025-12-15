"""Review Insight Engine: 核心指標與建議。"""

from __future__ import annotations

from typing import Dict, List
import pandas as pd


def generate_review_insights(reviews: pd.DataFrame) -> Dict[str, List[str]]:
    if reviews.empty:
        return {"core": [], "actions": []}

    total_reviews = len(reviews)
    avg_rating = reviews["rating"].mean() if "rating" in reviews.columns else None
    recommended_pct = reviews["recommended"].mean() * 100 if "recommended" in reviews.columns else None
    pos_share = (
        (reviews["sentiment_label"].str.lower() == "positive").mean() * 100
        if "sentiment_label" in reviews.columns
        else None
    )
    neg_share = (
        (reviews["sentiment_label"].str.lower() == "negative").mean() * 100
        if "sentiment_label" in reviews.columns
        else None
    )

    core: List[str] = []
    core.append(f"評論 {total_reviews:,} 筆，平均 {avg_rating:.2f}★。" if avg_rating is not None else f"評論 {total_reviews:,} 筆。")
    if recommended_pct is not None:
        core.append(f"推薦率 {recommended_pct:.1f}%")
    if pos_share is not None and neg_share is not None:
        core.append(f"情緒占比：正面 {pos_share:.1f}% / 負面 {neg_share:.1f}%")

    actions: List[str] = []
    if neg_share and neg_share > 20:
        actions.append("負評占比偏高，優先盤點熱門負評關鍵字並回覆/補償。")
    if recommended_pct and recommended_pct < 70:
        actions.append("推薦率不足 70%，發放滿意度調查並針對低星客戶追蹤。")
    if pos_share and pos_share > 60:
        actions.append("放大正面聲量：截取高星評論做社群素材或商品頁精選。")

    return {"core": core, "actions": actions}

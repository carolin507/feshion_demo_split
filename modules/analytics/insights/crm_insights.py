"""CRM Insight Engine: 產出各圖表的重點敘述。"""

from __future__ import annotations

from typing import Dict, List
import pandas as pd


def _fmt_pct(numerator: float, denominator: float) -> str:
    """Format percentage safely."""
    return f"{(numerator / denominator):.1%}" if denominator else "N/A"


def _insight_segment(rfm: pd.DataFrame) -> List[str]:
    if rfm.empty or "segment" not in rfm.columns:
        return []
    seg_counts = rfm["segment"].value_counts()
    total = seg_counts.sum()
    lines: List[str] = []
    if not seg_counts.empty:
        lines.append(f"主力客群為 **{seg_counts.index[0]}**，占 {_fmt_pct(seg_counts.iloc[0], total)}。")
    if "monetary" in rfm.columns:
        vip_avg = rfm.loc[rfm["segment"] == "VIP / Champions", "monetary"].mean()
        overall_avg = rfm["monetary"].mean()
        if pd.notna(vip_avg) and pd.notna(overall_avg) and overall_avg:
            lift = (vip_avg - overall_avg) / overall_avg
            lines.append(f"VIP 客群客單較平均提升 {lift:.1%}，值得加碼關懷。")
    return lines


def _insight_geo(rfm: pd.DataFrame) -> List[str]:
    if rfm.empty or "country" not in rfm.columns:
        return []
    counts = rfm["country"].value_counts()
    total = counts.sum()
    lines: List[str] = []
    if not counts.empty:
        lines.append(f"主要市場在 **{counts.index[0]}**，客戶占 {_fmt_pct(counts.iloc[0], total)}。")
    if len(counts) >= 3:
        top3_share = counts.head(3).sum()
        lines.append(f"前三國家合計占 {_fmt_pct(top3_share, total)}，集中度高。")
    return lines


def _insight_revenue_trend(sales_full: pd.DataFrame) -> List[str]:
    if sales_full.empty or "sale_date_order" not in sales_full.columns or "item_total" not in sales_full.columns:
        return []
    monthly = (
        sales_full.groupby(pd.Grouper(key="sale_date_order", freq="MS"))["item_total"]
        .sum()
        .reset_index()
        .sort_values("sale_date_order")
    )
    if monthly.empty:
        return []
    recent_rev = monthly["item_total"].iloc[-1]
    prev_rev = monthly["item_total"].iloc[-2] if len(monthly) >= 2 else None
    best_row = monthly.loc[monthly["item_total"].idxmax()]
    lines: List[str] = []
    if prev_rev is not None and prev_rev > 0:
        growth = (recent_rev - prev_rev) / prev_rev
        lines.append(f"最新月份營收為 ${recent_rev:,.0f}，較前期變動 {growth:.1%}。")
    lines.append(f"高峰出現在 {best_row['sale_date_order'].strftime('%Y-%m')}，營收 ${best_row['item_total']:,.0f}。")
    return lines


def _insight_channel(sales_full: pd.DataFrame) -> List[str]:
    if sales_full.empty or "channel_order" not in sales_full.columns:
        return []
    counts = sales_full["channel_order"].value_counts()
    total = counts.sum()
    lines: List[str] = []
    if not counts.empty:
        lines.append(f"主要訂單來源為 **{counts.index[0]}**，占 {_fmt_pct(counts.iloc[0], total)}。")
    if len(counts) > 1:
        tail_share = _fmt_pct(counts.iloc[1:].sum(), total)
        lines.append(f"其他渠道合計占 {tail_share}，可評估分流或投放成效。")
    return lines


def _insight_products(sales_full: pd.DataFrame) -> List[str]:
    if sales_full.empty or "product_name" not in sales_full.columns or "item_total" not in sales_full.columns:
        return []
    top_products = (
        sales_full.groupby("product_name")["item_total"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    total_revenue = sales_full["item_total"].sum()
    lines: List[str] = []
    if not top_products.empty:
        leader = top_products.iloc[0]
        lines.append(f"銷售冠軍 **{leader['product_name']}** 貢獻 {_fmt_pct(leader['item_total'], total_revenue)} 營收。")
    if len(top_products) >= 3:
        top3_rev = top_products.head(3)["item_total"].sum()
        lines.append(f"Top 3 商品合計占 {_fmt_pct(top3_rev, total_revenue)}，組合促銷可再放大。")
    return lines


def _insight_age_segment(rfm: pd.DataFrame) -> List[str]:
    if rfm.empty or "age_range" not in rfm.columns:
        return []
    age_counts = rfm["age_range"].value_counts()
    total = age_counts.sum()
    lines: List[str] = []
    if not age_counts.empty:
        lines.append(f"最多客群集中在 **{age_counts.index[0]}**，占 {_fmt_pct(age_counts.iloc[0], total)}。")
    if "segment" in rfm.columns:
        vip_age = rfm.loc[rfm["segment"] == "VIP / Champions", "age_range"].value_counts()
        if not vip_age.empty:
            lines.append(f"VIP 主要來自 {vip_age.index[0]}，可針對該年齡層規劃專屬活動。")
    return lines


def generate_crm_insights(rfm: pd.DataFrame, sales_full: pd.DataFrame) -> Dict[str, List[str]]:
    """產出 CRM Dashboard 使用的 Insight 結構。"""
    total_customers = rfm["customer_id"].nunique() if "customer_id" in rfm.columns else len(rfm)
    vip_count = int((rfm["segment"] == "VIP / Champions").sum()) if "segment" in rfm.columns else 0
    vip_pct = vip_count / total_customers if total_customers else 0
    avg_monetary = float(rfm["monetary"].mean()) if "monetary" in rfm.columns else None
    core = [
        f"總客戶 {total_customers:,} 人，VIP {vip_count} ({vip_pct:.1%})。",
    ]
    if avg_monetary:
        core.append(f"平均客單 ${avg_monetary:,.0f}，可再針對高價值客群加碼。")

    actions = []
    if vip_pct > 0.1:
        actions.append("針對 VIP / Champions 設計會員專屬任務、推薦與補貨通知。")
    if avg_monetary:
        actions.append("以平均客單為門檻設置階梯折扣，帶動客單上移。")
    if "country" in rfm.columns and not rfm["country"].empty:
        lead_country = rfm["country"].value_counts().index[0]
        actions.append(f"在主要市場 {lead_country} 推出在地化訊息或分眾 EDM。")

    return {
        "core": core,
        "actions": actions,
        "segment": _insight_segment(rfm),
        "geo": _insight_geo(rfm),
        "revenue_trend": _insight_revenue_trend(sales_full),
        "channel": _insight_channel(sales_full),
        "products": _insight_products(sales_full),
        "age_segment": _insight_age_segment(rfm),
    }

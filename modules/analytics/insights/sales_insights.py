"""Sales Insight Engine: outputs highlights and actions for sales dashboards."""

from __future__ import annotations

from typing import Dict, List
import pandas as pd


def _fmt_pct(numerator: float, denominator: float) -> str:
    return f"{(numerator / denominator):.1%}" if denominator else "N/A"


def _fmt_currency(value: float) -> str:
    return f"${value:,.0f}"


def _insight_revenue_trend(sales: pd.DataFrame) -> List[str]:
    if sales.empty or "order_date" not in sales.columns or "revenue" not in sales.columns:
        return []
    monthly = (
        sales.assign(order_date=pd.to_datetime(sales["order_date"]))
        .groupby(pd.Grouper(key="order_date", freq="MS"))["revenue"]
        .sum()
        .reset_index()
        .sort_values("order_date")
    )
    if monthly.empty:
        return []
    lines: List[str] = []
    recent = monthly["revenue"].iloc[-1]
    prev = monthly["revenue"].iloc[-2] if len(monthly) >= 2 else None
    best_row = monthly.loc[monthly["revenue"].idxmax()]
    lines.append(f"最新月份營收 {_fmt_currency(recent)}。")
    if prev and prev > 0:
        growth = (recent - prev) / prev
        lines.append(f"月增率 {growth:.1%}，需持續追蹤變動原因。")
    lines.append(f"峰值出現在 {best_row['order_date'].strftime('%Y-%m')}，營收 {_fmt_currency(best_row['revenue'])}。")
    if len(monthly) >= 3:
        last3 = monthly["revenue"].tail(3)
        momentum = last3.pct_change().mean()
        lines.append(f"近 3 個月平均動能 {momentum:.1%}，可依此設定下季目標。")
    return lines


def _insight_price_band(sales: pd.DataFrame) -> List[str]:
    if sales.empty or "unit_price" not in sales.columns or "revenue" not in sales.columns:
        return []
    bins = [0, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500, float("inf")]
    labels = [
        "<50",
        "50-100",
        "100-150",
        "150-200",
        "200-250",
        "250-300",
        "300-350",
        "350-400",
        "400-450",
        "450-500",
        "500+",
    ]
    banded = sales.copy()
    banded["price_band_fine"] = pd.cut(
        banded["unit_price"],
        bins=bins,
        labels=labels,
        right=False,
        include_lowest=True,
    )
    agg = (
        banded.groupby("price_band_fine")["revenue"]
        .sum()
        .reindex(labels)
        .reset_index()
        .rename(columns={"price_band_fine": "band"})
    )
    total = agg["revenue"].sum()
    if total == 0:
        return []
    lines: List[str] = []
    top = agg.sort_values("revenue", ascending=False).iloc[0]
    lines.append(f"主要成交落在 **{top['band']}**，占 {_fmt_pct(top['revenue'], total)}。")
    low_band = agg[agg["band"] == "<50"]["revenue"].iloc[0]
    if low_band / total > 0.15:
        lines.append("低價帶占比偏高，可搭配加購/滿額門檻提升客單。")
    high_band = agg[agg["band"] == "500+"]["revenue"].iloc[0]
    if high_band / total > 0.1:
        lines.append("高價帶貢獻可觀，考慮 VIP 專屬折扣或分期選項，鞏固高值客群。")
    mid_share = agg.loc[agg["band"].isin(["200-250", "250-300", "300-350"])]["revenue"].sum() / total
    if mid_share < 0.2:
        lines.append("中價帶占比低，評估推出組合或優惠券拉升中價帶轉換。")
    return lines


def _insight_color(color_sales: pd.DataFrame) -> List[str]:
    if color_sales.empty or "color" not in color_sales.columns or "revenue" not in color_sales.columns:
        return []
    color_sorted = color_sales.sort_values("revenue", ascending=False)
    total = color_sorted["revenue"].sum()
    lines: List[str] = []
    top = color_sorted.iloc[0]
    lines.append(f"熱賣色系為 **{top['color']}**，占 {_fmt_pct(top['revenue'], total)} 營收。")
    if len(color_sorted) >= 3:
        top3 = color_sorted.head(3)["revenue"].sum()
        lines.append(f"前三色佔 {_fmt_pct(top3, total)}，可做主打色專區或再版。")
    tail_share = (
        color_sorted.tail(max(1, len(color_sorted) // 3))["revenue"].sum() / total
        if total
        else 0
    )
    if tail_share < 0.1:
        lines.append("長尾色系貢獻低，可縮減庫存或併入組合清倉。")
    return lines


def _insight_size(size_sales: pd.DataFrame) -> List[str]:
    if size_sales.empty or "size" not in size_sales.columns or "revenue" not in size_sales.columns:
        return []
    size_sorted = size_sales.sort_values("revenue", ascending=False)
    total = size_sorted["revenue"].sum()
    lines: List[str] = []
    top = size_sorted.iloc[0]
    lines.append(f"最熱銷尺碼為 **{top['size']}**，占 {_fmt_pct(top['revenue'], total)} 營收。")
    if len(size_sorted) >= 3:
        tail = size_sorted.tail(1).iloc[0]
        lines.append(f"最弱尺碼 {tail['size']} 占 {_fmt_pct(tail['revenue'], total)}，可調整採購或搭配促銷。")
    return lines


def _insight_top_sku(sales: pd.DataFrame, top_n: int = 10) -> List[str]:
    if sales.empty or "sku" not in sales.columns or "revenue" not in sales.columns:
        return []
    sku_rev = (
        sales.groupby("sku")["revenue"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    total = sku_rev["revenue"].sum()
    lines: List[str] = []
    top = sku_rev.iloc[0]
    lines.append(f"銷售冠軍 SKU **{top['sku']}** 貢獻 {_fmt_pct(top['revenue'], total)}。")
    if len(sku_rev) >= top_n:
        top_share = sku_rev.head(top_n)["revenue"].sum()
        lines.append(f"Top {top_n} SKU 合計占 {_fmt_pct(top_share, total)}，可優先補貨與投放。")
    if total:
        tail_share = sku_rev.tail(max(1, len(sku_rev) // 4))["revenue"].sum() / total
        if tail_share < 0.1:
            lines.append("尾端 SKU 貢獻低，建議進行下架或加價購清庫。")
    return lines


def _insight_weekday(sales: pd.DataFrame) -> List[str]:
    if sales.empty or "weekday" not in sales.columns or "revenue" not in sales.columns:
        return []
    wd = sales.groupby("weekday")["revenue"].sum().reset_index()
    total = wd["revenue"].sum()
    if total == 0:
        return []
    lines: List[str] = []
    best = wd.loc[wd["revenue"].idxmax()]
    lines.append(f"最佳營收日為 **{best['weekday']}**，占 {_fmt_pct(best['revenue'], total)}。")
    weekend = wd[wd["weekday"].isin(["Saturday", "Sunday"])]["revenue"].sum()
    weekday_rev = total - weekend
    if weekend and weekend / total > 0.5:
        lines.append("週末占比過半，可安排週末限定促銷或直播。")
    elif weekday_rev / total > 0.6:
        lines.append("平日占比高，可嘗試週中驅動活動（會員日、限時免運）。")
    return lines


def generate_sales_insights(
    sales_clean: pd.DataFrame,
    color_sales: pd.DataFrame | None = None,
    size_sales: pd.DataFrame | None = None,
) -> Dict[str, List[str]]:
    """產出銷售儀表板使用的 Insight 與行動建議。"""
    color_sales = color_sales if color_sales is not None else pd.DataFrame()
    size_sales = size_sales if size_sales is not None else pd.DataFrame()
    total_revenue = sales_clean["revenue"].sum()
    total_orders = sales_clean["order_id"].nunique() if "order_id" in sales_clean.columns else len(sales_clean)
    avg_order_value = total_revenue / total_orders if total_orders else 0
    core = [
        f"總營收 {_fmt_currency(total_revenue)}，訂單 {total_orders:,} 筆，AOV {_fmt_currency(avg_order_value)}。",
    ]
    actions = [
        "針對高 AOV 客群推出加價購或 VIP 禮遇。",
        "依價格帶拆分素材，低價帶以組合/加購，高價帶以分期/會員折扣推動。",
        "主打 Top SKU 與主力渠道，並對尾端 SKU 做清庫或加購策略。",
    ]

    return {
        "core": core,
        "actions": actions,
        "revenue_trend": _insight_revenue_trend(sales_clean),
        "price_band": _insight_price_band(sales_clean),
        "color": _insight_color(color_sales),
        "size": _insight_size(size_sales),
        "top_sku": _insight_top_sku(sales_clean),
        "weekday": _insight_weekday(sales_clean),
    }

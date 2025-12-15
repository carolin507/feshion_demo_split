# pages/dashboard_sales.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from modules.analytics.insights.sales_insights import generate_sales_insights

# Warm, red-leaning palette to keep all pies cohesive
WARM = [
    "#E12D39",
    "#F14952",
    "#FF5A5F",
    "#FF7A70",
    "#FF9E7A",
    "#F97316",
    "#F4A261",
    "#F59E0B",
    "#FBBF24",
]
WARM_EXT = (
    px.colors.sequential.Reds
    + px.colors.sequential.OrRd
    + px.colors.sequential.YlOrRd
    + WARM
)


@st.cache_data
def load_sales_data():
    base = "data/processed/sales/"

    sales_clean = pd.read_csv(base + "sales_clean.csv")
    daily = pd.read_csv(base + "daily_sales.csv")
    monthly = pd.read_csv(base + "monthly_sales.csv")
    sku = pd.read_csv(base + "sku_sales.csv")
    color = pd.read_csv(base + "color_sales.csv")
    size = pd.read_csv(base + "size_sales.csv")
    price_band = pd.read_csv(base + "price_band_sales.csv")

    return sales_clean, daily, monthly, sku, color, size, price_band


def render_sales_dashboard():
    ACCENT = "#FF5A5F"
    SAND = "#F9F5F0"
    INK = "#1C1917"
    MUTED = "#78716C"
    px.defaults.color_discrete_sequence = WARM
    px.defaults.color_continuous_scale = "OrRd"

    st.markdown(
        f"""
        <style>
          .block-container {{
            padding-top: 1.2rem;
            padding-bottom: 1.2rem;
            background: {SAND};
          }}
          h3, h4 {{ color: {INK}; font-family: 'Noto Sans TC', 'Inter', sans-serif; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("## 銷售分析 Sales Performance Dashboard")
    st.markdown(
        f"""
        <div style="
            font-size:13px;
            color:{MUTED};
            background:rgba(0,0,0,0.03);
            padding:8px 10px;
            border-radius:10px;
            margin:4px 0 10px;
        ">
        ※本產品展示的數據模型與分析成果，是基於公開的 Kaggle 電商資料集進行建構與演示。點此前往
        <a href="https://www.kaggle.com/datasets/shilongzhuang/-women-clothing-ecommerce-sales-data" target="_blank">Kaggle 資料集連結</a>。
        </div>
        """,
        unsafe_allow_html=True,
    )

    (
        sales_clean,
        daily_sales,
        monthly_sales,
        sku_sales,
        color_sales,
        size_sales,
        price_band_sales,
    ) = load_sales_data()

    insights = generate_sales_insights(sales_clean, color_sales, size_sales)

    def _insight_box(title: str, lines: list[str]) -> None:
        if not lines:
            return
        st.markdown(
            f"""
            <div style="
                margin-top:10px;
                padding:12px 14px;
                border:1px solid #E7E5E4;
                border-radius:12px;
                background:#FFFBEB;
            ">
              <div style="font-size:12px;color:{MUTED};letter-spacing:0.08em;text-transform:uppercase;">{title}</div>
              <ul style="margin:6px 0 0 18px;color:{INK};font-size:13px;line-height:1.5;">
                {"".join(f"<li>{line}</li>" for line in lines)}
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def _metric_card(label: str, value: str, helper: str | None = None) -> None:
        st.markdown(
            f"""
            <div style="
                background:white;
                border:1px solid #E7E5E4;
                border-radius:14px;
                padding:16px 18px;
                box-shadow:0 12px 32px rgba(0,0,0,0.05);
                min-height:120px;
            ">
                <div style="font-size:13px;color:{MUTED};text-transform:uppercase;letter-spacing:0.08em;">{label}</div>
                <div style="font-size:26px;font-weight:700;color:{INK};margin-top:6px;">{value}</div>
                {f'<div style="margin-top:4px;color:#A8A29E;font-size:12px;">{helper}</div>' if helper else ''}
            </div>
            """,
            unsafe_allow_html=True,
        )

    def _color_map(labels):
        palette = WARM_EXT
        return {label: palette[i % len(palette)] for i, label in enumerate(labels)}

    # KPI row
    st.markdown("#### 整體表現 KPI")
    total_revenue = sales_clean["revenue"].sum()
    total_orders = sales_clean["order_id"].nunique()
    total_items = sales_clean["quantity"].sum()
    avg_order_value = total_revenue / total_orders if total_orders else 0

    col1, col2, col3, col4 = st.columns(4, gap="medium")
    with col1:
        _metric_card("總營收", f"${total_revenue:,.0f}", helper="Revenue")
    with col2:
        _metric_card("訂單數", f"{total_orders:,}", helper="唯一 order_id")
    with col3:
        _metric_card("銷售件數", f"{total_items:,}", helper="quantity sum")
    with col4:
        _metric_card("平均訂單金額 (AOV)", f"${avg_order_value:,.0f}", helper="Revenue / Orders")

    _insight_box("Core Insights", insights.get("core", []))
    _insight_box("Action Plan", insights.get("actions", []))

    st.markdown("---")

    # Monthly revenue
    st.markdown("#### 月度營收")
    monthly_sales["year_month"] = monthly_sales["year"].astype(str) + "-" + monthly_sales["month"].astype(str)
    fig_month = px.bar(
        monthly_sales,
        x="year_month",
        y="revenue",
        color_discrete_sequence=[ACCENT],
        text_auto=True,
    )
    fig_month.update_layout(
        xaxis_title="月份",
        yaxis_title="營收",
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=30, b=10),
    )
    st.plotly_chart(fig_month, use_container_width=True)
    _insight_box("Insight", insights.get("revenue_trend", []))

    st.markdown("---")

    # Products
    st.markdown("#### 商品")
    left, right = st.columns((1.4, 1))
    with left:
        st.markdown("##### Top 10 商品營收")
        top_sorted = (
            sku_sales.nlargest(10, "revenue")
            .sort_values("revenue", ascending=False)
        )
        top_sorted = top_sorted.copy()
        top_sorted["sku"] = top_sorted["sku"].astype(str)
        fig_top10 = go.Figure()
        fig_top10.add_trace(
            go.Bar(
                x=top_sorted["revenue"],
                y=top_sorted["sku"],
                orientation="h",
                marker=dict(color=WARM[3]),
                hoverinfo="skip",
                showlegend=False,
                width=0.4,
            )
        )
        fig_top10.add_trace(
            go.Scatter(
                x=top_sorted["revenue"],
                y=top_sorted["sku"],
                mode="markers+text",
                marker=dict(color=WARM[0], size=12),
                text=[f"${v:,.0f}" for v in top_sorted["revenue"]],
                textposition="middle right",
                hovertemplate="SKU %{y}<br>Revenue: $%{x:,.2f}<extra></extra>",
                showlegend=False,
            )
        )
        fig_top10.update_layout(
            xaxis_title="營收",
            yaxis_title="SKU",
            margin=dict(l=10, r=20, t=10, b=10),
            plot_bgcolor="white",
            paper_bgcolor="white",
            hovermode="y",
        )
        fig_top10.update_xaxes(tickformat="$,.0f", gridcolor="#F5F5F4", zeroline=False)
        fig_top10.update_yaxes(
            type="category",
            categoryorder="array",
            categoryarray=list(top_sorted["sku"]),
            gridcolor="#F5F5F4",
        )
        st.plotly_chart(fig_top10, use_container_width=True)
        _insight_box("Insight", insights.get("top_sku", []))

    with right:
        st.empty()

    st.markdown("---")

    # Pies row
    st.markdown("#### 尺寸 / 顏色 / 價格帶")
    pie_cols = st.columns(3)
    with pie_cols[0]:
        st.markdown("##### 尺寸銷售佔比")
        size_map = _color_map(size_sales["size"])
        fig_size = px.pie(
            size_sales,
            names="size",
            values="revenue",
            color="size",
            color_discrete_map=size_map,
            color_discrete_sequence=WARM,
        )
        fig_size.update_traces(textposition="inside", textinfo="percent+label")
        fig_size.update_layout(margin=dict(l=0, r=0, t=10, b=10), paper_bgcolor="white", showlegend=False)
        st.plotly_chart(fig_size, use_container_width=True)
        _insight_box("Insight", insights.get("size", []))
    with pie_cols[1]:
        st.markdown("##### 顏色銷售佔比")
        color_map = _color_map(color_sales["color"])
        fig_color = px.pie(
            color_sales,
            names="color",
            values="revenue",
            color="color",
            color_discrete_map=color_map,
            color_discrete_sequence=WARM,
        )
        fig_color.update_traces(textposition="inside", textinfo="percent+label")
        fig_color.update_layout(margin=dict(l=0, r=0, t=10, b=10), paper_bgcolor="white", showlegend=False)
        st.plotly_chart(fig_color, use_container_width=True)
        _insight_box("Insight", insights.get("color", []))
    with pie_cols[2]:
        st.markdown("##### 價格帶銷售占比")
        price_bins = [0, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500, float("inf")]
        price_labels = [
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
        price_banded = sales_clean.copy()
        price_banded["price_fine"] = pd.cut(
            price_banded["unit_price"],
            bins=price_bins,
            labels=price_labels,
            right=False,
            include_lowest=True,
        )
        price_fine_sales = (
            price_banded.groupby("price_fine")["revenue"]
            .sum()
            .reindex(price_labels)
            .reset_index()
            .rename(columns={"price_fine": "price_band"})
        )
        fig_price = px.pie(
            price_fine_sales,
            names="price_band",
            values="revenue",
            hole=0.4,
            color_discrete_sequence=WARM,
        )
        fig_price.update_traces(textposition="inside", textinfo="percent+label")
        fig_price.update_layout(margin=dict(l=0, r=0, t=10, b=10), paper_bgcolor="white", showlegend=False)
        st.plotly_chart(fig_price, use_container_width=True)
        _insight_box("Insight", insights.get("price_band", []))

    # Weekday
    st.markdown("#### 星期別銷售表現")
    weekday_sales = sales_clean.groupby("weekday")["revenue"].sum().reset_index()
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday_sales["weekday"] = pd.Categorical(weekday_sales["weekday"], categories=weekday_order, ordered=True)
    weekday_sales = weekday_sales.sort_values("weekday")
    fig_weekday = px.bar(
        weekday_sales,
        x="weekday",
        y="revenue",
        color_discrete_sequence=[ACCENT],
        text_auto=True,
    )
    fig_weekday.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis_title="",
        yaxis_title="營收",
    )
    st.plotly_chart(fig_weekday, use_container_width=True)
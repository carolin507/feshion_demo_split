# pages/dashboard_crm.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional
from modules.analytics.insights.crm_insights import generate_crm_insights

ACCENT = "#FF5A5F"
SAND = "#F9F5F0"
INK = "#1C1917"
MUTED = "#78716C"
WARM = ["#FF5A5F", "#F97316", "#E9C46A", "#F4A261", "#FB7185", "#F59E0B"]


@st.cache_data
def load_crm_data():
    """載入 rfm_engine 匯出的 CRM 資料並處理日期欄位。"""
    rfm = pd.read_csv("data/processed/crm/customers_rfm.csv")
    sales_full = pd.read_csv("data/processed/crm/sales_full.csv")

    if "sale_date_order" in sales_full.columns:
        sales_full["sale_date_order"] = pd.to_datetime(sales_full["sale_date_order"])

    return rfm, sales_full


def _metric_card(label: str, value: str, helper: Optional[str] = None) -> None:
    """Render a metric card similar to the React dashboard look."""
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


def render_crm_dashboard():
    """CRM & 客戶洞察 Dashboard，版型取自 React App.tsx。"""
    rfm, sales_full = load_crm_data()
    insights = generate_crm_insights(rfm, sales_full)
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
          .css-18e3th9 {{ padding-top: 0 !important; }}
          hr {{ border-color: #E7E5E4; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("## CRM客戶洞察")
    st.caption("仿照 React 版介面：聚焦 VIP、銷售渠道與暢銷商品。")
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
        <a href="https://www.kaggle.com/datasets/joycemara/european-fashion-store-multitable-dataset" target="_blank">Kaggle 資料集連結</a>。
        </div>
        """,
        unsafe_allow_html=True,
    )

    total_customers = rfm["customer_id"].nunique() if "customer_id" in rfm.columns else len(rfm)
    vip_count = int((rfm["segment"] == "VIP / Champions").sum()) if "segment" in rfm.columns else None
    avg_monetary = float(rfm["monetary"].mean()) if "monetary" in rfm.columns else None
    revenue_total = float(sales_full["item_total"].sum()) if "item_total" in sales_full.columns else None

    recent_mask = None
    if "sale_date_order" in sales_full.columns:
        recent_mask = sales_full["sale_date_order"] >= (pd.Timestamp.today() - pd.Timedelta(days=30))
    monthly_orders = int(recent_mask.sum()) if recent_mask is not None else None

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

    vip_text = "N/A"
    if vip_count is not None and total_customers:
        vip_text = f"{vip_count} ({vip_count / total_customers:.1%})"

    with st.container():
        col1, col2, col3, col4 = st.columns(4, gap="medium")
        with col1:
            _metric_card("總客戶", f"{total_customers:,}", helper="唯一 customer_id")
        with col2:
            _metric_card("VIP 佔比", vip_text, helper="VIP / Champions")
        with col3:
            monetary_text = f"${avg_monetary:,.0f}" if avg_monetary else "N/A"
            _metric_card("平均客單 (Monetary)", monetary_text, helper="RFM monetary 平均")
        with col4:
            revenue_text = f"${revenue_total:,.0f}" if revenue_total else "N/A"
            helper = "近 30 天訂單數" if monthly_orders is not None else "總營收"
            value = f"{monthly_orders:,}" if monthly_orders is not None else revenue_text
            _metric_card("近期動能", value, helper=helper)

    _insight_box("Core Insights", insights.get("core", []))
    _insight_box("Action Plan", insights.get("actions", []))

    st.markdown("---")

    st.markdown("#### 分群與地理概覽")
    col_seg, col_geo = st.columns((1.1, 1))

    with col_seg:
        if "segment" in rfm.columns:
            seg_counts = rfm["segment"].value_counts().reset_index()
            seg_counts.columns = ["segment", "count"]
            fig_seg = px.treemap(
                seg_counts,
                path=["segment"],
                values="count",
                color="count",
                color_continuous_scale="OrRd",
                title="RFM Segment 客戶結構",
            )
            fig_seg.update_layout(
                margin=dict(l=0, r=0, t=50, b=0),
                paper_bgcolor="white",
            )
            st.plotly_chart(fig_seg, use_container_width=True)
            _insight_box("Insight", insights.get("segment", []))
        else:
            st.info("缺少 segment 欄位，無法顯示 RFM 分群。")

    with col_geo:
        if "country" in rfm.columns:
            country_counts = rfm["country"].value_counts().reset_index()
            country_counts.columns = ["country", "count"]
            fig_country = px.choropleth(
                country_counts,
                locations="country",
                locationmode="country names",
                color="count",
                color_continuous_scale="Reds",
                title="客戶國家分佈",
                scope="europe",
            )
            fig_country.update_geos(
                fitbounds="locations",
                projection_scale=4.2,
                center=dict(lat=54, lon=12),
                showcountries=True,
                showcoastlines=True,
                coastlinecolor="#d4d4d4",
                landcolor="#ffffff",
            )
            fig_country.update_layout(
                margin=dict(l=0, r=0, t=50, b=0),
                height=480,
            )
            st.plotly_chart(fig_country, use_container_width=True)
            _insight_box("Insight", insights.get("geo", []))
        else:
            st.info("缺少 country 欄位，無法顯示地理分佈。")

    st.markdown("---")

    st.markdown("#### 銷售與渠道")
    col_trend, col_channel = st.columns((1.3, 1))

    with col_trend:
        if "sale_date_order" in sales_full.columns and "item_total" in sales_full.columns:
            monthly = (
                sales_full
                .groupby(pd.Grouper(key="sale_date_order", freq="MS"))["item_total"]
                .sum()
                .reset_index()
            )
            fig_trend = px.area(
                monthly,
                x="sale_date_order",
                y="item_total",
                title="月度營收走勢",
                color_discrete_sequence=[ACCENT],
            )
            fig_trend.update_layout(
                xaxis_title="月份",
                yaxis_title="營收",
                margin=dict(l=10, r=10, t=50, b=10),
                plot_bgcolor="white",
                paper_bgcolor="white",
            )
            st.plotly_chart(fig_trend, use_container_width=True)
            _insight_box("Insight", insights.get("revenue_trend", []))
        else:
            st.info("缺少 sale_date_order 或 item_total 欄位，無法產出營收走勢。")

    with col_channel:
        if "channel_order" in sales_full.columns:
            fig_channel = px.pie(
                sales_full,
                names="channel_order",
                title="訂單渠道分佈",
                hole=0.55,
                color_discrete_sequence=WARM,
            )
            fig_channel.update_traces(textposition="outside", textinfo="percent+label")
            fig_channel.update_layout(
                margin=dict(l=10, r=10, t=50, b=10),
                showlegend=False,
                paper_bgcolor="white",
            )
            st.plotly_chart(fig_channel, use_container_width=True)
            _insight_box("Insight", insights.get("channel", []))
        else:
            st.info("缺少 channel_order 欄位，無法顯示渠道分佈。")

    st.markdown("---")

    st.markdown("#### 暢銷商品與客群")
    col_prod, col_age = st.columns((1.2, 1))

    with col_prod:
        if "product_name" in sales_full.columns and "item_total" in sales_full.columns:
            top_products = (
                sales_full.groupby("product_name")["item_total"]
                .sum()
                .sort_values(ascending=False)
                .head(10)
                .reset_index()
            )
            y_labels = top_products["product_name"].iloc[::-1]
            x_vals = top_products["item_total"].iloc[::-1]
            fig_top = go.Figure()
            fig_top.add_trace(
                go.Bar(
                    y=y_labels,
                    x=x_vals,
                    orientation="h",
                    marker=dict(color="#FEE2E2"),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
            fig_top.add_trace(
                go.Scatter(
                    y=y_labels,
                    x=x_vals,
                    mode="markers+text",
                    marker=dict(color=ACCENT, size=12),
                    text=[f"${v:,.0f}" for v in x_vals],
                    textposition="middle right",
                    showlegend=False,
                )
            )
            fig_top.update_layout(
                title="Top 10 銷售商品 (Lollipop)",
                xaxis_title="營收",
                yaxis_title="商品",
                margin=dict(l=10, r=10, t=50, b=10),
                plot_bgcolor="white",
                paper_bgcolor="white",
                hovermode="y",
            )
            st.plotly_chart(fig_top, use_container_width=True)
            _insight_box("Insight", insights.get("products", []))
        else:
            st.info("缺少 product_name 或 item_total 欄位，無法顯示暢銷商品。")

    with col_age:
        if "age_range" in rfm.columns and "segment" in rfm.columns:
            heat = pd.crosstab(rfm["age_range"], rfm["segment"])
            fig_age = px.imshow(
                heat,
                color_continuous_scale="Reds",
                title="年齡層 x RFM 分群 (Heatmap)",
                labels=dict(x="Segment", y="Age Range", color="人數"),
            )
            fig_age.update_layout(
                margin=dict(l=10, r=10, t=50, b=10),
                plot_bgcolor="white",
                paper_bgcolor="white",
            )
            st.plotly_chart(fig_age, use_container_width=True)
            _insight_box("Insight", insights.get("age_segment", []))
        else:
            st.info("缺少 age_range 或 segment 欄位，無法顯示年齡分布。")

    st.markdown("---")

    st.markdown("#### 最近訂單快覽")
    if not sales_full.empty:
        preview_cols = [
            col
            for col in ["sale_id", "sale_date_order", "country", "channel_order", "item_total"]
            if col in sales_full.columns
        ]
        if preview_cols:
            recent = sales_full.sort_values(
                by=["sale_date_order"] if "sale_date_order" in preview_cols else preview_cols[0],
                ascending=False,
            ).head(15)
            st.dataframe(
                recent[preview_cols].rename(
                    columns={
                        "sale_id": "訂單",
                        "sale_date_order": "日期",
                        "country": "國家",
                        "channel_order": "渠道",
                        "item_total": "金額",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("無預覽欄位可顯示。")
    else:
        st.info("sales_full 為空，無法顯示訂單資料。")

    st.markdown("---")

    st.markdown("##### RFM 樣本")
    rfm_cols = [col for col in ["customer_id", "segment", "recency", "frequency", "monetary", "country"] if col in rfm.columns]
    if rfm_cols:
        st.dataframe(
            rfm[rfm_cols].head(20),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("缺少 RFM 欄位，無法顯示樣本表格。")
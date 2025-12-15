# pages/dashboard_reviews.py
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from modules.analytics.insights.review_insights import generate_review_insights
from wordcloud import WordCloud

POSITIVE_COLORS = ["#22C55E", "#34D399", "#4ADE80", "#86EFAC", "#A7F3D0"]
NEGATIVE_COLORS = ["#EF4444", "#F97316", "#FB7185", "#FDBA74", "#FECACA"]
FONT_CANDIDATES = [
    Path("assets/fonts/NotoSansTC-Regular.otf"),
    Path("assets/fonts/NotoSansTC-Regular.ttf"),
    Path("assets/fonts/NotoSansTC-Medium.otf"),
]
FONT_PATH = next((str(p) for p in FONT_CANDIDATES if p.exists()), None)


@st.cache_data
def load_reviews_data():
    base = "data/processed/reviews/"
    reviews = pd.read_csv(base + "reviews_processed.csv")
    keywords = pd.read_csv(base + "review_keywords.csv")
    return reviews, keywords


def _top_keywords_from_reviews(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame({"word": [], "count": []})
    words = (
        df["review"]
        .fillna("")
        .str.lower()
        .str.replace(r"[^a-z0-9\\s]", " ", regex=True)
        .str.split()
    )
    counts: dict[str, int] = {}
    for lst in words:
        for w in lst:
            if len(w) <= 2:
                continue
            counts[w] = counts.get(w, 0) + 1
    freq = pd.DataFrame({"word": list(counts.keys()), "count": list(counts.values())})
    return freq.sort_values("count", ascending=False).head(n)


def _wordcloud_array(freq_df: pd.DataFrame, colormap: str):
    if freq_df.empty:
        return None
    clean_df = (
        freq_df.copy()
        .dropna(subset=["word", "count"])
        .assign(word=lambda d: d["word"].astype(str))
        .assign(count=lambda d: pd.to_numeric(d["count"], errors="coerce"))
    )
    clean_df = clean_df[clean_df["count"] > 0].head(20)
    if clean_df.empty:
        return None
    freq_map = dict(zip(clean_df["word"], clean_df["count"]))
    if not freq_map:
        return None
    wc = WordCloud(
        width=760,
        height=440,
        background_color="white",
        colormap=colormap,
        prefer_horizontal=0.9,
        max_words=20,
        font_path=FONT_PATH,
        margin=2,
        max_font_size=110,
    ).generate_from_frequencies(freq_map)
    return wc.to_array()


def render_reviews_dashboard():
    ACCENT = "#F59E0B"
    SAND = "#F9F5F0"
    INK = "#1C1917"
    MUTED = "#78716C"
    px.defaults.color_discrete_sequence = POSITIVE_COLORS
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

    st.markdown("## 顧客評價分析 Review & VOC Dashboard")
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
        <a href="https://www.kaggle.com/datasets/nicapotato/womens-ecommerce-clothing-reviews" target="_blank">Kaggle 資料集連結</a>。
        </div>
        """,
        unsafe_allow_html=True,
    )

    reviews, keywords = load_reviews_data()
    insights = generate_review_insights(reviews)

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

    # KPI row
    st.markdown("#### 評價關鍵指標 KPI")
    total_reviews = len(reviews)
    avg_rating = reviews["rating"].mean()
    recommended_pct = reviews["recommended"].mean() * 100

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        _metric_card("總評論數", f"{total_reviews:,}")
    with c2:
        _metric_card("平均星等", f"{avg_rating:.2f} ★")
    with c3:
        _metric_card("推薦率", f"{recommended_pct:.1f}%", helper="recommended = 1")

    _insight_box("Core Insights", insights.get("core", []))
    _insight_box("Action Plan", insights.get("actions", []))

    st.markdown("---")

    # Rating distribution + Age view side-by-side
    st.markdown("#### 評分分布（1–5 星）與年齡表現")
    col_rate, col_age = st.columns(2, gap="large")

    with col_rate:
        rating_counts = (
            reviews.groupby("rating")
            .size()
            .reset_index(name="count")
            .sort_values("rating")
        )
        fig_rating = px.pie(
            rating_counts,
            names="rating",
            values="count",
            color="rating",
            color_discrete_sequence=[ACCENT, "#FCD34D", "#F59E0B", "#EA580C", "#C2410C"],
            hole=0.35,
        )
        fig_rating.update_traces(textposition="inside", textinfo="percent+label")
        fig_rating.update_layout(
            title="Rating Share (1–5 星)",
            margin=dict(l=0, r=0, t=40, b=0),
            showlegend=False,
        )
        st.plotly_chart(fig_rating, use_container_width=True)

    with col_age:
        st.caption("年齡層 vs 平均評分（10 歲區間）")
        age_bins = list(range(0, 101, 10))
        age_labels = [f"{b}-{b+9}" for b in age_bins[:-1]]
        reviews["age_bin"] = pd.cut(
            reviews["Age"],
            bins=age_bins,
            labels=age_labels,
            right=False,
            include_lowest=True,
        )
        age_rating = (
            reviews.groupby("age_bin")["rating"]
            .mean()
            .reset_index()
            .sort_values("age_bin")
        )
        fig_age = px.line(
            age_rating,
            x="age_bin",
            y="rating",
            markers=True,
            line_shape="spline",
            color_discrete_sequence=[ACCENT],
        )
        fig_age.update_layout(
            title="平均星等（依年齡層）",
            yaxis_title="平均星等",
            xaxis_title="年齡區間",
            margin=dict(l=10, r=10, t=40, b=40),
        )
        st.plotly_chart(fig_age, use_container_width=True)

    st.markdown("---")

    # Sentiment split + word clouds
    st.markdown("#### 正面 / 負面 關鍵字 (Top 20 文字雲)")
    positive_reviews = reviews[reviews["sentiment_label"].str.lower() == "positive"]
    negative_reviews = reviews[reviews["sentiment_label"].str.lower() == "negative"]

    col_pos, col_neg = st.columns(2)
    with col_pos:
        st.markdown("##### 正面關鍵字 Top 20")
        if "sentiment" in keywords.columns:
            pos_kw = keywords[keywords["sentiment"].str.lower() == "positive"].head(20)
        else:
            pos_kw = _top_keywords_from_reviews(positive_reviews)
        pos_wc = _wordcloud_array(pos_kw, colormap="YlGn")
        if pos_wc is not None:
            st.image(pos_wc, use_container_width=True, caption="正面關鍵字文字雲")
        else:
            st.info("尚無正面關鍵字資料")
        fig_kw_pos = px.bar(
            pos_kw,
            x="word",
            y="count",
            text_auto=True,
            color_discrete_sequence=POSITIVE_COLORS,
        )
        fig_kw_pos.update_layout(xaxis_tickangle=-45, margin=dict(l=10, r=10, t=10, b=60))
        st.plotly_chart(fig_kw_pos, use_container_width=True)

    with col_neg:
        st.markdown("##### 負面關鍵字 Top 20")
        if "sentiment" in keywords.columns:
            neg_kw = keywords[keywords["sentiment"].str.lower() == "negative"].head(20)
        else:
            neg_kw = _top_keywords_from_reviews(negative_reviews)
        neg_wc = _wordcloud_array(neg_kw, colormap="OrRd")
        if neg_wc is not None:
            st.image(neg_wc, use_container_width=True, caption="負面關鍵字文字雲")
        else:
            st.info("尚無負面關鍵字資料")
        fig_kw_neg = px.bar(
            neg_kw,
            x="word",
            y="count",
            text_auto=True,
            color_discrete_sequence=NEGATIVE_COLORS,
        )
        fig_kw_neg.update_layout(xaxis_tickangle=-45, margin=dict(l=10, r=10, t=10, b=60))
        st.plotly_chart(fig_kw_neg, use_container_width=True)

    # Positive / Negative by department
    col_pos2, col_neg2 = st.columns(2)
    with col_pos2:
        st.markdown("##### 正面評價數（部門）")
        pos_dept = (
            positive_reviews.groupby("Department Name")["rating"]
            .count()
            .reset_index()
            .rename(columns={"rating": "count"})
            .sort_values("count", ascending=False)
        )
        fig_pos_dept = px.bar(
            pos_dept,
            x="Department Name",
            y="count",
            text_auto=True,
            color_discrete_sequence=POSITIVE_COLORS,
        )
        fig_pos_dept.update_layout(
            xaxis_title="部門",
            yaxis_title="正面評價數",
            margin=dict(l=10, r=10, t=20, b=60),
            plot_bgcolor="white",
            paper_bgcolor="white",
        )
        st.plotly_chart(fig_pos_dept, use_container_width=True)

    with col_neg2:
        st.markdown("##### 負面評價數（部門）")
        neg_dept = (
            negative_reviews.groupby("Department Name")["rating"]
            .count()
            .reset_index()
            .rename(columns={"rating": "count"})
            .sort_values("count", ascending=False)
        )
        fig_neg_dept = px.bar(
            neg_dept,
            x="Department Name",
            y="count",
            text_auto=True,
            color_discrete_sequence=NEGATIVE_COLORS,
        )
        fig_neg_dept.update_layout(
            xaxis_title="部門",
            yaxis_title="負面評價數",
            margin=dict(l=10, r=10, t=20, b=60),
            plot_bgcolor="white",
            paper_bgcolor="white",
        )
        st.plotly_chart(fig_neg_dept, use_container_width=True)

    st.markdown("---")

    # Age bins (10-year)
    st.markdown("#### 年齡層 vs 平均評分（10 歲區間）")
    age_bins = list(range(0, 101, 10))
    age_labels = [f"{b}-{b+9}" for b in age_bins[:-1]]
    reviews["age_bin"] = pd.cut(
        reviews["Age"],
        bins=age_bins,
        labels=age_labels,
        right=False,
        include_lowest=True,
    )
    age_rating = (
        reviews.groupby("age_bin")["rating"]
        .mean()
        .reset_index()
        .sort_values("age_bin")
    )
    fig_age = px.bar(
        age_rating,
        x="age_bin",
        y="rating",
        text_auto=True,
        color_discrete_sequence=[ACCENT],
    )
    fig_age.update_layout(
        title="Average Rating by Age Bin",
        xaxis_title="年齡區間",
        yaxis_title="平均星等",
        margin=dict(l=10, r=10, t=40, b=60),
    )
    st.plotly_chart(fig_age, use_container_width=True)

    st.markdown("---")

    # Latest reviews cards
    st.markdown("#### 最新正負面評價")
    col_lp, col_ln = st.columns(2)

    def _review_cards(df, title, color):
        if df.empty:
            st.info(f"尚無{title}。")
            return
        df_sorted = df.sort_values("rating", ascending=False).head(5)
        for _, row in df_sorted.iterrows():
            def _safe(val):
                if pd.isna(val):
                    return ""
                return str(val)

            title_txt = _safe(row.get("Title", "")).strip()
            review_txt = _safe(row.get("review", ""))
            review_snippet = review_txt.strip()
            review_snippet = review_snippet[:240] + ("..." if len(review_snippet) > 240 else "")
            dept_txt = _safe(row.get("Department Name", ""))
            class_txt = _safe(row.get("Class Name", ""))
            rating_val = _safe(row.get("rating", ""))
            st.markdown(
                f"""
                <div style="border:1px solid #E7E5E4;border-radius:12px;padding:12px 14px;margin-bottom:10px;background:white;">
                  <div style="font-weight:700;color:{color};margin-bottom:4px;">{title} · {rating_val}★</div>
                  <div style="color:#1C1917;font-weight:600;">{title_txt}</div>
                  <div style="color:#57534E;margin-top:6px;">{review_snippet}</div>
                  <div style="color:#A8A29E;font-size:12px;margin-top:6px;">部門: {dept_txt} · 類別: {class_txt}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_lp:
        st.markdown("##### 正面最新 5 筆")
        _review_cards(positive_reviews, "Positive", POSITIVE_COLORS[0])
    with col_ln:
        st.markdown("##### 負面最新 5 筆")
        _review_cards(negative_reviews, "Negative", NEGATIVE_COLORS[0])



# Alias for legacy import
def render_color_trends():
    return render_reviews_dashboard()

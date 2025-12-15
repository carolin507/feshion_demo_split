# pages/wardrobe.py

import base64
from io import BytesIO
from textwrap import dedent

import streamlit as st
from PIL import Image

from ui.layout import card, product_grid
from modules.utils import zh_label, color_to_zh, pattern_to_zh, category_to_zh
from modules.recommender_pair import GenderedRecommender
from modules.model_core import infer_labels, infer_and_recommend


# ------------------------------------------------------------
# 顏色 HEX 表
# ------------------------------------------------------------
COLOR_HEX = {
    "Black": "#2b2b2b",
    "Gray": "#7d7d7d",
    "White": "#f6f6f6",
    "Beige": "#e9dcc6",
    "Orange": "#f0a35c",
    "Pink": "#f3a6b4",
    "Red": "#d95555",
    "Green": "#5e8c6a",
    "Brown": "#7a5537",
    "Blue": "#3f68b5",
    "Yellow": "#f3d75c",
    "Purple": "#8b6fb5",
}
LIGHT_COLORS = {"White", "Beige", "Yellow", "Pink", "Orange"}



# ============================================================
# 主渲染函式
# ============================================================

def render_wardrobe(RECOMMENDER: GenderedRecommender):

    # ------------------------------------------------------------
    # HERO BANNER
    # ------------------------------------------------------------
    st.markdown(dedent("""
        <div class="hero-outer">
            <div class="hero-wrapper">
                <img class="hero-img"
                     src="https://raw.githubusercontent.com/carolin507/fashion-demo-assets/main/assets/hero_banner.jpg">
                <div class="hero-overlay">
                    <div>
                        <div class="hero-title">AI 穿搭靈感推薦</div>
                        <div class="hero-sub">上傳穿搭 → AI 幫你分析顏色 / 花紋 / 類別並推薦下身單品</div>
                    </div>
                </div>
            </div>
        </div>
    """), unsafe_allow_html=True)


    # ------------------------------------------------------------
    # Intro Card
    # ------------------------------------------------------------
    st.markdown(card(
        "AI 穿搭靈感推薦｜AI Wardrobe",
        "<p class='subtle'>上傳穿搭照，AI 會辨識顏色 / 花紋 / 類別，並根據共現資料推薦最適合的下身搭配。</p>"
    ), unsafe_allow_html=True)


    # ============================================================
    # STEP 1：上傳圖片 + 性別
    # ============================================================
    st.markdown("""
    <style>
    :where(div[data-testid="stVerticalBlock"]:has(> .step1-card-sentinel)) {
        background: linear-gradient(135deg, #fffaf3, #f3f0ea);
        border: 1px solid #e6dece;
        border-radius: 16px;
        padding: 18px 18px 12px;
        box-shadow: 0 14px 28px rgba(0,0,0,0.06);
        margin-bottom: 16px;
    }
    .step1-title {font-weight: 800; font-size: 18px; color: #2f241e; margin-bottom: 6px;}
    .step1-desc {font-size: 13px; color: #6a5f52; margin-bottom: 12px;}
    .gender-box {
        border: 1px solid #e6dece;
        background: linear-gradient(135deg, #fff7ee, #f3f0ea);
        border-radius: 14px;
        padding: 14px 16px 10px;
        box-shadow: 0 14px 28px rgba(0,0,0,0.06);
        margin-bottom: 12px;
    }
    .gender-box .gender-label {
        font-weight: 700;
        color: #3a2b1f;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
    }
    .gender-box .pill {
        background: #c7773c;
        color: #fff;
        font-size: 12px;
        padding: 4px 10px;
        border-radius: 999px;
    }
    .gender-box .hint {
        font-size: 13px;
        color: #6a5f52;
        margin-top: 6px;
    }
    .gender-box [data-testid="stRadio"] > div[role="radiogroup"] {
        display: flex;
        gap: 10px;
    }
    .gender-box [data-testid="stRadio"] label {
        padding: 10px 14px;
        border-radius: 12px;
        border: 1px solid #e6dece;
        background: #fff;
        box-shadow: 0 8px 18px rgba(0,0,0,0.06);
        min-width: 110px;
        justify-content: center;
    }
    .gender-box [data-testid="stRadio"] p {
        font-weight: 700;
        margin-bottom: 0;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="step1-card-sentinel"></div>', unsafe_allow_html=True)
        st.markdown('<div class="step1-title">STEP 1｜上傳你的穿搭照</div>', unsafe_allow_html=True)
        st.markdown('<div class="step1-desc">選擇性別並上傳穿搭圖片。</div>', unsafe_allow_html=True)

        col_left, col_right = st.columns([1, 2])

        with col_left:
            st.markdown(
                """
                <div class="gender-box">
                    <div class="gender-label">
                        性別｜Gender
                        <span class="pill">必選</span>
                    </div>
                """,
                unsafe_allow_html=True,
            )
            gender = st.radio(
                "Gender",
                ["women", "men"],
                horizontal=True,
                format_func=lambda g: "女款" if g == "women" else "男款",
                label_visibility="collapsed",
                key="gender-choice",
            )
            st.markdown(
                '<div class="hint">AI 會依性別微調剪裁、版型與風格推薦</div></div>',
                unsafe_allow_html=True,
            )

        with col_right:
            uploaded_img = st.file_uploader(
                "上傳穿搭圖片（JPG / PNG）",
                type=["jpg", "jpeg", "png"]
            )

    if not uploaded_img:
        st.markdown(card(
            "尚未上傳圖片",
            "<p class='subtle'>上傳穿搭照即可示範完整 AI Flow。</p>"
        ), unsafe_allow_html=True)
        return


    # ============================================================
    # 顯示上傳圖片
    # ============================================================
    img = Image.open(uploaded_img).convert("RGB")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_b64 = base64.b64encode(buffer.getvalue()).decode()


    # ============================================================
    # STEP 2：AI 辨識 + 推薦（一次完成）
    # ============================================================
    st.subheader("AI 辨識結果")

    result = infer_and_recommend(
        image=img,
        recommender=RECOMMENDER,
        gender=gender,
        k=3,
    )

    labels = result.get("input_label", {})
    recommendations = result.get("recommendations", [])


    if not labels:
        st.error("⚠️ AI 模型無法辨識圖片，可能未成功載入。")
        return


    # 顯示辨識結果
    c1, c2 = st.columns([1.1, 0.9])

    with c1:
        st.markdown(card(
            "你的穿搭照片",
            f'<img src="data:image/png;base64,{img_b64}" class="uploaded-photo"/>'
        ), unsafe_allow_html=True)

    with c2:
        st.markdown(card(
            "AI 辨識結果",
            f"""
            <p><strong>顏色：</strong>{zh_label(labels['color'], color_to_zh)}</p>
            <p><strong>花紋：</strong>{zh_label(labels['style'], pattern_to_zh)}</p>
            <p><strong>品類：</strong>{zh_label(labels['category'], category_to_zh)}</p>
            <p><strong>部位：</strong>{labels['part']}</p>
            """
        ), unsafe_allow_html=True)


    # ============================================================
    # STEP 3：推薦結果（3 欄 Grid）
    # ============================================================


    st.subheader("AI 推薦單品（共現推薦）")

    if not recommendations:
        st.info("目前沒有推薦結果。")
        return

    # ------------------------------------------------------------
    # 自己建立推薦卡片的 HTML（避免 card() 破壞 HTML）
    # ------------------------------------------------------------

    st.markdown("""
    <style>
    .recs-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        grid-gap: 22px;
        margin-top: 20px;
    }

    .rec-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 14px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.06);
    }

    .rec-img {
        width: 100%;
        aspect-ratio: 4 / 3;
        object-fit: contain;
        background: #f8f5ef;
        border-radius: 12px;
        margin-bottom: 10px;
    }

    .tag-row {
        display: flex;
        align-items: center;
        margin-bottom: 6px;
    }

    .tag-label {
        margin-right: 6px;
        font-weight: 600;
        color: #6a5f52;
    }

    .color-tag {
        padding: 6px 14px;
        border-radius: 8px;
        font-size: 14px;
    }

    .tag {
        background: #f7f2eb;
        padding: 6px 14px;
        border-radius: 8px;
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

    
    cards = []
    BASE_URL = "https://raw.githubusercontent.com/carolin507/fashion-demo-assets/main/assets/streetstyle/"

    for rec in recommendations[:3]:
        color = rec.get("color")
        style = rec.get("style")
        cat = rec.get("category")
        image_path = rec.get("filename")
        url = BASE_URL + image_path if image_path else ""

        cards.append(dedent(f'''<div class="rec-card">
    <img src="{url}" class="rec-img"/>
    <div class="tag-row">
        <div class="tag-label">\u984f\u8272\uff1a</div>
        <span class="color-tag"
            style="background:{COLOR_HEX.get(color, '#888')};
                color:{'#2f241e' if color in LIGHT_COLORS else '#fff'};">
            {zh_label(color, color_to_zh)}
        </span>
    </div>
    <div class="tag-row">
        <div class="tag-label">\u98a8\u683c\uff1a</div>
        <span class="tag">{zh_label(style, pattern_to_zh)}</span>
    </div>
    <div class="tag-row">
        <div class="tag-label">\u985e\u5225\uff1a</div>
        <span class="tag">{zh_label(cat, category_to_zh)}</span>
    </div>
</div>
'''))

    html = f'<div class="recs-grid">{"".join(cards)}</div>'

    st.markdown(html, unsafe_allow_html=True)

    st.markdown(
        """
        <div style="
            margin: 16px 0 0;
            padding: 10px 12px;
            border: 1px solid #e7e5e4;
            background: rgba(0,0,0,0.03);
            border-radius: 10px;
            color: #4b5563;
            font-size: 13px;
            line-height: 1.55;
        ">
          We thank the NCHC Sci-DM project for data service and technical support.
          The project is funded by the Ministry of Science and Technology (MOST) ( MOST 108-2634-F-492-001).
          <a href="https://scidm.nchc.org.tw/dataset/richwear-fashion-ai" target="_blank">Data source link</a>.
        </div>
        """,
        unsafe_allow_html=True,
    )


    # ============================================================
    # STEP 4：精選商品
    # ============================================================
    # st.subheader("精選商品")

    # product_files = [
    #     "638992503203300000.jpg",
    #     "638993154193030000.jpg",
    #     "638993413666200000.jpg",
    #     "638993433208400000.jpg",
    #     "638993433310200000.jpg",
    # ]

    # product_base = (
    #     "https://raw.githubusercontent.com/carolin507/"
    #     "fashion-demo-assets/main/assets/product/"
    # )

    # st.markdown(product_grid(product_files, product_base), unsafe_allow_html=True)

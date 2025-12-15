# app.py

import streamlit as st
import pandas as pd
import json

# ------------------------------------------------------------
# Streamlit page config
# ------------------------------------------------------------
st.set_page_config(page_title="Lookbook Studio", layout="wide")

# ------------------------------------------------------------
# UI Modules
# ------------------------------------------------------------
from ui.css import load_global_css
from ui.topnav import render_topnav

# ------------------------------------------------------------
# Pages
# ------------------------------------------------------------
from pages.wardrobe import render_wardrobe
from pages.lookbook import render_lookbook
from pages.dashboard_trend_analysis import render_color_trends
from pages.project_intro import render_project_intro
from pages.dashboard_crm import render_crm_dashboard
from pages.dashboard_sales import render_sales_dashboard
from pages.dashboard_reviews import render_reviews_dashboard


# ------------------------------------------------------------
# Recommender (New Architecture)
# ------------------------------------------------------------
from modules.recommender_pair import GenderedRecommender


# ------------------------------------------------------------
# Load verified_photo_data.json → Build GenderedRecommender
# ------------------------------------------------------------
@st.cache_resource
def load_recommender():
    json_path = "data/verified_photo_data.json"

    try:
        # 讀取 item-level JSON
        with open(json_path, "r", encoding="utf-8") as f:
            items = json.load(f)

        df = pd.DataFrame(items)

        # 建立推薦器（性別分流）
        recommender = GenderedRecommender(df)
        return recommender

    except Exception as e:
        st.error(f"⚠️ 無法讀取推薦資料：{json_path}\n{e}")
        return None


# 建立推薦器
RECOMMENDER = load_recommender()


# ------------------------------------------------------------
# Load Global CSS
# ------------------------------------------------------------
st.markdown(load_global_css(), unsafe_allow_html=True)

# 背景色設定（你原本的 style）
st.markdown("""
<style>
:root { --bg-main: #f8f4ec; }
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------
# Initialize session state
# ------------------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "intro"


# ------------------------------------------------------------
# Sync URL param → page routing
# ------------------------------------------------------------
allowed_pages = {"wardrobe", "lookbook", "dashboard", "crm", "sales", "reviews", "intro"}

try:
    params = st.query_params  # 新版 API
except Exception:
    params = st.experimental_get_query_params()  # fallback


if "page" in params:
    value = params["page"]
    page_val = value[0] if isinstance(value, list) else value
    st.session_state.page = page_val if page_val in allowed_pages else "intro"


# ------------------------------------------------------------
# Top Navigation Bar
# ------------------------------------------------------------
render_topnav()


# ------------------------------------------------------------
# Page Routing
# ------------------------------------------------------------
page = st.session_state.page

if page == "wardrobe":
    render_wardrobe(RECOMMENDER)

elif page == "lookbook":
    render_lookbook()

elif page == "dashboard":
    render_color_trends()

elif page == "intro":
    render_project_intro()

elif page == "crm":
     render_crm_dashboard()
     
elif page == "sales":
    render_sales_dashboard()

elif page == "reviews":
    render_reviews_dashboard()

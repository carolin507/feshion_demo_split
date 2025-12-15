# ai-optimization.py (Frontend Application)

import streamlit as st
import pandas as pd
from PIL import Image
import io

# --- UI & Page Modules ---
from ui.css import load_global_css
from ui.topnav import render_topnav
from pages.lookbook import render_lookbook
from pages.dashboard_trend_analysis import render_color_trends
from pages.project_intro import render_project_intro
from pages.dashboard_crm import render_crm_dashboard

# --- API Client ---
# The recommender is now an API client, not a local model processor.
from modules.recommender_pair import APIRecommender

# Page Config
st.set_page_config(page_title="Lookbook Studio", layout="wide")

# --- New Wardrobe Page Logic ---
def render_wardrobe(recommender: APIRecommender):
    """
    Renders the 'My Wardrobe' page, now powered by the API.
    This function replaces the original one from `pages/wardrobe.py`.
    """
    st.title("AI 造型師")
    st.write("上傳您的一件上衣或下著，AI 將為您推薦最合適的搭配單品。")

    # --- Input Fields ---
    col1, col2 = st.columns([1, 2])
    with col1:
        gender = st.radio("請選擇推薦風格：", ("男性", "女性"), key="gender_selection")
        uploaded_file = st.file_uploader(
            "上傳您的單品圖片", type=["jpg", "jpeg", "png"]
        )

    # --- Recommendation Logic ---
    if uploaded_file is not None:
        try:
            # Display the uploaded image
            image = Image.open(uploaded_file)
            with col2:
                st.image(image, caption="您上傳的單品", width=300)

            # On button press, call the API
            if st.button("生成穿搭推薦", key="generate_recommendation"):
                with st.spinner("AI 正在為您搭配中，請稍候..."):
                    # Convert gender to the format expected by the API ('male'/'female')
                    gender_api_format = "male" if gender == "男性" else "female"

                    # Call the API through our client
                    recommendations_df = recommender.recommend(
                        img=image,
                        gender=gender_api_format
                    )

                    # --- Display Results ---
                    if not recommendations_df.empty:
                        st.subheader("為您推薦的搭配單品：")
                        # Display images with details
                        rec_cols = st.columns(len(recommendations_df))
                        for idx, row in recommendations_df.iterrows():
                            with rec_cols[idx]:
                                if row.get("image_url"):
                                    st.image(row["image_url"], caption=f"{row.get('category', '')} - {row.get('color', '')}")
                                else:
                                    st.write(f"No image for {row.get('category', '')}")
                    else:
                        st.error("抱歉，無法生成推薦。請檢查 API 服務是否正在運行，或稍後再試。")

        except Exception as e:
            st.error(f"處理圖片時發生錯誤：{e}")


# --- Page Definitions ---
PAGE_MAP = {
    "intro": {
        "title": "專案介紹",
        "render_func": render_project_intro,
        "needs_recommender": False,
    },
    "wardrobe": {
        "title": "我的衣櫃",
        "render_func": render_wardrobe,
        "needs_recommender": True, # This page needs the API client
    },
    "lookbook": {
        "title": "風格穿搭",
        "render_func": render_lookbook,
        "needs_recommender": False,
    },
    "dashboard": {
        "title": "色彩趨勢",
        "render_func": render_color_trends,
        "needs_recommender": False,
    },
    "crm": {
        "title": "顧客關係管理",
        "render_func": render_crm_dashboard,
        "needs_recommender": False,
    },
}

# --- Model/Client Loading ---
@st.cache_resource
def load_recommender():
    """
    Loads the APIRecommender client.
    This is now a lightweight operation.
    """
    # In a real deployment, you might get this URL from an environment variable
    # For local testing, it points to our local FastAPI server
    api_url = "http://127.0.0.1:8000"
    return APIRecommender(api_base_url=api_url)

# --- Main App Logic ---
def main():
    """Main function to run the Streamlit frontend app."""
    st.markdown(load_global_css(), unsafe_allow_html=True)
    st.markdown("""<style>:root { --bg-main: #f8f4ec; }</style>""", unsafe_allow_html=True)

    # Page navigation
    if "page" not in st.session_state:
        st.session_state.page = "intro"
    query_params = st.query_params
    if "page" in query_params:
        page_val = query_params.get("page", ["intro"])[0]
        st.session_state.page = page_val if page_val in PAGE_MAP else "intro"

    render_topnav(PAGE_MAP)

    current_page_key = st.session_state.page
    page_config = PAGE_MAP[current_page_key]

    # Render the selected page
    if page_config["needs_recommender"]:
        recommender_client = load_recommender()
        page_config["render_func"](recommender_client)
    else:
        page_config["render_func"]()

if __name__ == "__main__":
    main()

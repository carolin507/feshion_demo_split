import streamlit as st


def render_topnav():
    menu = [
        {"label": "解決方案", "target": "intro"},
        {"label": "AI 穿搭靈感", "target": "wardrobe"},
        {"label": "Lookbook 靈感庫", "target": "lookbook"},
        {
            "label": "商業洞察儀表板",
            "children": [
                ("色彩潮流分析", "dashboard"),
                ("商品銷售分析", "sales"),
                ("CRM客戶洞察", "crm"),
                ("顧客評價分析", "reviews"),
            ],
        },
    ]

    current = st.session_state.get("page", "intro")

    nav_left, nav_right = st.columns([1.2, 3], vertical_alignment="center")

    with nav_left:
        st.markdown('<div class="topnav-left brand">Lookbook Studio</div>', unsafe_allow_html=True)

    with nav_right:
        st.markdown('<div class="topnav-right">', unsafe_allow_html=True)

        btn_cols = st.columns(len(menu), gap="small")

        for item, col in zip(menu, btn_cols):
            with col:
                target = item.get("target")
                children = item.get("children", [])
                child_targets = {child_target for _, child_target in children}
                is_active = (target and current == target) or (children and current in child_targets)
                default_target = target or (children[0][1] if children else None)

                clicked = st.button(
                    item["label"],
                    key=f"nav_{item['label']}",
                    type="primary" if is_active else "secondary",
                    use_container_width=True,
                )
                if clicked and default_target:
                    st.session_state.page = default_target
                    try:
                        st.query_params = {"page": default_target}
                    except Exception:
                        st.experimental_set_query_params(page=default_target)
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    bi_children = next((item.get("children", []) for item in menu if "children" in item), [])
    bi_targets = {child_target for _, child_target in bi_children}

    # Show subnav only when viewing BI pages (keeps it collapsed otherwise)
    if bi_children and current in bi_targets:
        st.markdown(
            '<div class="topnav-subnav">'
            '<div class="topnav-subtitle">商業智慧 BI</div>'
            '<div class="pill-row">',
            unsafe_allow_html=True,
        )
        pill_cols = st.columns(len(bi_children), gap="small")
        for (text, target), col in zip(bi_children, pill_cols):
            with col:
                clicked = st.button(
                    text,
                    key=f"nav_bi_{target}",
                    type="primary" if current == target else "secondary",
                )
                if clicked:
                    st.session_state.page = target
                    try:
                        st.query_params = {"page": target}
                    except Exception:
                        st.experimental_set_query_params(page=target)
                    st.rerun()
        st.markdown('</div></div>', unsafe_allow_html=True)

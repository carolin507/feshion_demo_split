# ui/layout.py
import streamlit as st


def card(title, body_html):
    """Wrap content in a styled card; body is stripped to avoid code blocks."""
    clean = body_html.strip()
    return (
        "<div class=\"card\">"
        f"<div class=\"card-title\">{title}</div>"
        f"{clean}"
        "</div>"
    )


def product_grid(files, base):
    items = "".join(
        (
            "<div class=\"product-card\">"
            f"<img src=\"{base}{f}\">"
            "<div class=\"caption\">精選單品</div>"
            "</div>"
        )
        for f in files
    )
    return (
        "<div class=\"card\">"
        "<div class=\"card-title\">精選單品推薦</div>"
        "<div class=\"product-grid\">"
        f"{items}"
        "</div>"
        "</div>"
    )


def lookbook_carousel(images, base_url):
    """Wardrobe mini lookbook carousel with fixed slots and fade transitions."""

    if not images:
        st.info("No Lookbook images are available yet.")
        return

    st.markdown("### Street Lookbook")

    base_url = base_url.rstrip("/")
    full_paths = [f"{base_url}/{img}" for img in images][:16]

    slot_count = min(4, len(full_paths)) if len(full_paths) >= 3 else max(1, len(full_paths))
    slots = [[] for _ in range(slot_count)]
    for idx, path in enumerate(full_paths):
        slots[idx % slot_count].append(path)

    st.markdown(
        f'<div class="mini-lookbook-grid" style="--slot-count:{slot_count};">',
        unsafe_allow_html=True,
    )

    for group in slots:
        images_for_slot = group or full_paths[:1]
        img_count = max(1, len(images_for_slot))

        st.markdown(
            f'<div class="mini-lookbook-slot" style="--img-count:{img_count};">',
            unsafe_allow_html=True,
        )

        for idx, img_url in enumerate(images_for_slot):
            first_class = " first-img" if idx == 0 else ""
            st.markdown(
                f"""
                <img src="{img_url}" class="mini-lookbook-img fade-img{first_class}"
                     style="--i:{idx};" alt="street look">
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

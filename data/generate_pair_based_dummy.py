import pandas as pd
import json
import os

# -------------------------------------------
# Label 定義
# -------------------------------------------

pattern_labels = ["Solid", "Striped", "Floral", "Plaid", "Spotted"]

color_labels = [
    "Black", "Gray", "White", "Beige", "Orange",
    "Pink", "Red", "Green", "Brown", "Blue", "Yellow", "Purple"
]

top_categories = [
    "Top", "T-Shirt", "Shirt", "Cardigan", "Blazer",
    "Sweatshirt", "Vest", "Jacket", "Coat",
    "Dress", "Jumpsuit", "Kimono_Yukata", "Swimwear"
]

bottom_categories = [
    "Skirt", "Pants", "Jeans", "Shorts", "Jumpsuit"
]

# 非服飾：略過，不參與 top-bottom 分類
ignore_categories = [
    "Shoes", "Sandals", "Boots", "Pumps",
    "Sneakers", "Scarf", "Bag", "Stockings"
]

# -------------------------------------------
# URL builder，避免重複 .jpg
# -------------------------------------------
def build_image_url(photo):
    base = (
        "https://raw.githubusercontent.com/carolin507/"
        "fashion-demo-assets/main/assets/streetstyle/"
    )
    
    # photo 名稱若已經有 .jpg，就不要再加
    if str(photo).lower().endswith(".jpg"):
        return base + str(photo)
    else:
        return base + str(photo) + ".jpg"


# -------------------------------------------
# 解析 v_labels
# -------------------------------------------
def parse_vlabels(vlabel_str):
    labels = [x.strip() for x in vlabel_str.split(",")]

    colors = [x for x in labels if x in color_labels]
    patterns = [x for x in labels if x in pattern_labels]
    categories = [x for x in labels if x not in (color_labels + pattern_labels + ignore_categories)]

    return colors, patterns, categories


# -------------------------------------------
# 分配 top-bottom 的屬性
# -------------------------------------------
def assign_attributes(colors, patterns, categories):

    # ----- COLOR -----
    if len(colors) >= 2:
        top_color, bottom_color = colors[0], colors[1]
    elif len(colors) == 1:
        top_color = bottom_color = colors[0]
    else:
        top_color = bottom_color = "Unknown"

    # ----- PATTERN -----
    if len(patterns) >= 2:
        top_pattern, bottom_pattern = patterns[0], patterns[1]
    elif len(patterns) == 1:
        top_pattern = bottom_pattern = patterns[0]
    else:
        top_pattern = bottom_pattern = "Unknown"

    # ----- CATEGORY -----
    top_cat = next((c for c in categories if c in top_categories), None)
    bottom_cat = next((c for c in categories if c in bottom_categories), None)

    # case 1：同時有 top + bottom → ok
    if top_cat and bottom_cat:
        pass

    # case 2：只有 top 類別（Ex: Dress）
    elif top_cat and not bottom_cat:
        bottom_cat = top_cat

    # case 3：只有 bottom 類別
    elif bottom_cat and not top_cat:
        top_cat = bottom_cat

    # case 4：都沒有（非常少見）
    else:
        top_cat = bottom_cat = "Unknown"

    return top_color, bottom_color, top_pattern, bottom_pattern, top_cat, bottom_cat


# -------------------------------------------
# Main：建立 verified_photo_data
# -------------------------------------------
def build_verified_photo_data(
    input_csv="data/df_pairs.csv",
    json_output="data/verified_photo_data.json",
    csv_output="data/verified_photo_data.csv"
):

    df = pd.read_csv(input_csv)
    output_rows = []

    for _, row in df.iterrows():

        # gender
        g = str(row.get("gender", "F")).upper()
        gender = "women" if g == "F" else "men"

        # v_labels parsing
        vlabels = str(row.get("v_labels", ""))
        colors, patterns, categories = parse_vlabels(vlabels)

        # 分配 top-bottom
        top_color, bottom_color, top_pattern, bottom_pattern, top_cat, bottom_cat = \
            assign_attributes(colors, patterns, categories)

        # URL
        photo = row.get("photo", "")
        url = build_image_url(photo)

        record = {
            "gender": gender,
            "top": {
                "color": top_color,
                "style": top_pattern,
                "category": top_cat
            },
            "bottom": {
                "color": bottom_color,
                "style": bottom_pattern,
                "category": bottom_cat
            },
            "top_url": url,
            "bottom_url": url
        }

        output_rows.append(record)

    # ---------------- JSON ----------------
    with open(json_output, "w", encoding="utf-8") as f:
        json.dump(output_rows, f, ensure_ascii=False, indent=2)

    # ---------------- CSV ----------------
    flat_rows = []
    for r in output_rows:
        flat_rows.append({
            "gender": r["gender"],
            "top_color": r["top"]["color"],
            "top_style": r["top"]["style"],
            "top_category": r["top"]["category"],
            "bottom_color": r["bottom"]["color"],
            "bottom_style": r["bottom"]["style"],
            "bottom_category": r["bottom"]["category"],
            "top_url": r["top_url"],
            "bottom_url": r["bottom_url"]
        })

    pd.DataFrame(flat_rows).to_csv(csv_output, index=False, encoding="utf-8-sig")

    print("✔ 完成 verified_photo_data 假資料生成！")
    print(f"📁 JSON：{json_output}")
    print(f"📁 CSV：{csv_output}")
    print(f"📊 筆數：{len(output_rows)}")


if __name__ == "__main__":
    build_verified_photo_data()

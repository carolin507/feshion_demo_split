# ------------------------------------------------------------
# Check label completeness:
# gender × color × style × category
# ------------------------------------------------------------

import itertools
import pandas as pd
from pathlib import Path


# ============================
# 1. Label 定義（理論全集）
# ============================

gender = ["men", "women"]

color_labels = [
    "Black", "Gray", "White", "Beige", "Orange",
    "Pink", "Red", "Green", "Brown", "Blue",
    "Yellow", "Purple"
]

style_labels = ["Solid", "Striped", "Floral", "Plaid", "Spotted"]

category_labels = [
    "Top", "T-Shirt", "Shirt", "Cardigan", "Blazer",
    "Sweatshirt", "Vest", "Jacket", "Dress", "Coat",
    "Skirt", "Pants", "Jeans", "Jumpsuit"
]


# ============================
# 2. 工具：Label 標準化
# ============================

def normalize(series: pd.Series) -> pd.Series:
    """
    Canonicalize labels:
    - cast to string
    - strip whitespace
    - lower case
    """
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
    )


# ============================
# 3. 產生理論組合全集
# ============================

expected_df = pd.DataFrame(
    list(itertools.product(
        gender,
        color_labels,
        style_labels,
        category_labels
    )),
    columns=["gender", "color", "style", "category"]
)

# normalize expected
for c in expected_df.columns:
    expected_df[c] = normalize(expected_df[c])

print("Expected combinations:", len(expected_df))  # 1680


# ============================
# 4. 讀取實際 image_label
# ============================

BASE_DIR = Path(__file__).resolve().parent
csv_path = BASE_DIR / "image_label_index.csv"

if not csv_path.exists():
    raise FileNotFoundError(f"CSV not found: {csv_path}")

image_df = pd.read_csv(csv_path)

# 只保留關鍵欄位並去重
actual_df = (
    image_df[["gender", "color", "style", "category"]]
    .drop_duplicates()
    .reset_index(drop=True)
)

# normalize actual
for c in actual_df.columns:
    actual_df[c] = normalize(actual_df[c])

print("Actual combinations:", len(actual_df))


# ============================
# 5. 快速檢查交集（debug 用）
# ============================

print("\n--- Intersection Check ---")
for c in ["gender", "color", "style", "category"]:
    exp_set = set(expected_df[c])
    act_set = set(actual_df[c])
    inter = exp_set & act_set

    print(f"[{c}] expected={len(exp_set)} actual={len(act_set)} intersection={len(inter)}")
    print("  actual sample:", sorted(list(act_set))[:10])


# ============================
# 6. 找出缺漏組合
# ============================

missing_df = expected_df.merge(
    actual_df,
    on=["gender", "color", "style", "category"],
    how="left",
    indicator=True
)

missing_df = (
    missing_df[missing_df["_merge"] == "left_only"]
    .drop(columns="_merge")
)

print("\nMissing combinations:", len(missing_df))


# ============================
# 7. 輸出結果（供分析 / 補資料）
# ============================

out_path = BASE_DIR / "missing_label_combinations.csv"
missing_df.to_csv(out_path, index=False)

print(f"Missing combinations saved to: {out_path}")


# ============================
# 8. 防呆：檢查實際資料中「不在定義內」的值
# ============================

ALLOWED = {
    "gender": set(gender),
    "color": set(c.lower() for c in color_labels),
    "style": set(s.lower() for s in style_labels),
    "category": set(c.lower() for c in category_labels),
}

print("\n--- Unexpected Label Values ---")
for col, allowed in ALLOWED.items():
    actual_values = set(actual_df[col])
    unexpected = sorted(list(actual_values - allowed))
    if unexpected:
        print(f"[WARN] {col} unexpected values ({len(unexpected)}):", unexpected)
    else:
        print(f"[OK] {col}: all values within definition")

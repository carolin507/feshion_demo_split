import itertools
import pandas as pd

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

expected_df = pd.DataFrame(
    list(itertools.product(gender, color_labels, style_labels, category_labels)),
    columns=["gender", "color", "style", "category"]
)

print("Expected combinations:", len(expected_df))  # 應為 1680

image_df = pd.read_csv("data\image_label_index.csv")

# 只保留四個關鍵欄位，並去重
actual_df = (
    image_df[["gender", "color", "style", "category"]]
    .drop_duplicates()
    .reset_index(drop=True)
)

print("Actual combinations:", len(actual_df))


cols = ["gender", "color", "style", "category"]

for c in cols:
    exp_set = set(expected_df[c].dropna().astype(str))
    act_set = set(actual_df[c].dropna().astype(str))
    inter = exp_set & act_set
    print(f"\n[{c}] expected={len(exp_set)} actual={len(act_set)} intersection={len(inter)}")
    print("  actual sample:", list(sorted(act_set))[:10])

missing_df = expected_df.merge(
    actual_df,
    on=["gender", "color", "style", "category"],
    how="left",
    indicator=True
)

missing_df = missing_df[missing_df["_merge"] == "left_only"]
missing_df = missing_df.drop(columns="_merge")

print("Missing combinations:", len(missing_df))

missing_df.to_csv("missing_label_combinations.csv", index=False)

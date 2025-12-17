# ------------------------------------------------------------
# Generate image label index from assets/output
# ------------------------------------------------------------
# 功能：
# 1. 掃描 assets/output 底下所有圖片檔名
# 2. 從檔名解析 gender / color / style / category
# 3. 正規化 gender（mans → men, womans → women）
# 4. 輸出成 data/image_label_index.csv
# ------------------------------------------------------------

print("🚀 script started")

from pathlib import Path
import pandas as pd
import re


print("🚀 script loaded, __name__ =", __name__)

# ============================================================
# 基本路徑設定（以專案根目錄為基準）
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
IMAGE_DIR = BASE_DIR / "assets" / "output"
OUTPUT_CSV = BASE_DIR / "data" / "image_label_index.csv"


# ============================================================
# Gender 正規化對照表
# ============================================================

GENDER_MAP = {
    "mans": "men",
    "man": "men",
    "mens": "men",
    "womans": "women",
    "woman": "women",
    "womens": "women",
}


# ============================================================
# Step 1. 列出圖片檔案
# ============================================================

def list_image_files(image_dir: Path) -> pd.DataFrame:
    if not image_dir.exists():
        raise FileNotFoundError(f"Image directory not found: {image_dir}")

    valid_ext = {".png", ".jpg", ".jpeg", ".webp"}

    files = [
        f.name
        for f in image_dir.iterdir()
        if f.is_file() and f.suffix.lower() in valid_ext
    ]

    return pd.DataFrame({"filename": files})


# ============================================================
# Step 2. 從檔名解析 labels（含 gender 正規化）
# ============================================================

def parse_labels_from_filename(filename: str) -> dict:
    name = filename.lower()

    # 移除副檔名
    name = re.sub(r"\.(png|jpg|jpeg|webp)$", "", name)

    # 移除 (2)、(10)
    name = re.sub(r"\(\d+\)", "", name)

    # 移除 _764 這種尾碼
    name = re.sub(r"_\d+$", "", name)

    parts = name.split("_")

    raw_gender = parts[0] if len(parts) > 0 else None
    gender = GENDER_MAP.get(raw_gender, raw_gender)

    return {
        "gender": gender,
        "color": parts[1] if len(parts) > 1 else None,
        "style": parts[2] if len(parts) > 2 else None,
        "category": parts[3] if len(parts) > 3 else None,
    }


# ============================================================
# Step 3. 建立圖片 label index
# ============================================================

def build_image_label_index(image_dir: Path) -> pd.DataFrame:
    df_images = list_image_files(image_dir)

    rows = []
    for filename in df_images["filename"]:
        labels = parse_labels_from_filename(filename)
        labels["filename"] = filename
        rows.append(labels)

    df = pd.DataFrame(rows)

    # 欄位順序整理（閱讀性）
    return df[["filename", "gender", "color", "style", "category"]]


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    print("✅ main block entered")
    print("📂 Image directory:", IMAGE_DIR)

    df = build_image_label_index(IMAGE_DIR)

    print(f"🖼️  Found {len(df)} images")
    print(df.head())

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print(f"✅ Image label index saved to: {OUTPUT_CSV}")

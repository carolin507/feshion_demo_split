# ------------------------------------------------------------
# Pair-based 共現推薦器 for Streamlit
#   - 性別推薦 (Gendered)
#   - 共現推薦 (Co-occurrence)
#   - Naive Bayes 補位 (Hybrid)
#   - 自動帶出正確圖片 URL
# ------------------------------------------------------------

import random
import math
from collections import defaultdict, Counter
from functools import lru_cache
import pandas as pd

IMAGE_INDEX_PATH = "data/image_label_index.csv"
IMAGE_BASE_URL = (
    "https://raw.githubusercontent.com/"
    "carolin507/fashion_demo_split/main/assets/output/"
)

# ------------------------------------------------------------
# Image helpers
# ------------------------------------------------------------
def _normalize_label(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip().lower()


@lru_cache(maxsize=1)
def load_image_index(csv_path: str = IMAGE_INDEX_PATH):
    """Load image_label_index.csv once; return None on failure."""
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"[recommender_pair] image index not found: {csv_path}")
        return None
    except Exception as exc:
        print(f"[recommender_pair] failed to load image index: {exc}")
        return None

    df = df.copy()
    for col in ["gender", "color", "style", "category"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.lower()

    return df


def _filter_by_conditions(image_db: pd.DataFrame, conditions):
    filtered = image_db
    for col, val in conditions:
        if not val:
            return pd.DataFrame()
        filtered = filtered[filtered[col] == val]
    return filtered


def resolve_image_url(image_db, gender, color, style, category):
    """
    Resolve an image URL from the indexed image database using priority rules.

    Priority order:
      1. gender + color + style + category
      2. gender + color + category
      3. gender + color
      4. gender
    Returns a raw GitHub URL or None.
    """
    if image_db is None or image_db.empty:
        return None

    g = _normalize_label(gender)
    c = _normalize_label(color)
    s = _normalize_label(style)
    cat = _normalize_label(category)

    if not g:
        return None

    priorities = [
        [("gender", g), ("color", c), ("style", s), ("category", cat)],
        [("gender", g), ("color", c), ("category", cat)],
        [("gender", g), ("color", c)],
        [("gender", g)],
    ]

    for conds in priorities:
        candidates = _filter_by_conditions(image_db, conds)
        if not candidates.empty:
            filename = random.choice(candidates["filename"].tolist())
            if filename:
                return f"{IMAGE_BASE_URL}{filename}"

    return None


# ------------------------------------------------------------
# Utility： labels_equal
# ------------------------------------------------------------
def labels_equal(a: dict, b: dict) -> bool:
    """顏色 / 花紋 / 類別都相同才算一致"""
    return (
        a.get("color") == b.get("color") and
        a.get("style") == b.get("style") and
        a.get("category") == b.get("category")
    )


# ------------------------------------------------------------
# OutfitRecommender（Naive Bayes 模型）
# ------------------------------------------------------------
class OutfitRecommender:
    def __init__(self, df: pd.DataFrame):
        self.df = df

        self.color_matrix = defaultdict(Counter)
        self.style_matrix = defaultdict(Counter)
        self.cat_matrix = defaultdict(Counter)

        self.all_colors = set()
        self.all_styles = set()
        self.all_cats = set()

        self.top_items = []
        self.bottom_items = []

        self._build_matrices()
        self._collect_unique_items()

    def _build_matrices(self):
        """建立顏色 / 花紋 / 類別的雙向共現表"""
        for _, row in self.df.iterrows():
            A = row["top"]
            B = row["bottom"]

            # vocabulary 建立
            self.all_colors.update([A["color"], B["color"]])
            self.all_styles.update([A["style"], B["style"]])
            self.all_cats.update([A["category"], B["category"]])

            # 雙向 color
            self.color_matrix[A["color"]][B["color"]] += 1
            self.color_matrix[B["color"]][A["color"]] += 1

            # 雙向 style
            self.style_matrix[A["style"]][B["style"]] += 1
            self.style_matrix[B["style"]][A["style"]] += 1

            # 雙向 category
            self.cat_matrix[A["category"]][B["category"]] += 1
            self.cat_matrix[B["category"]][A["category"]] += 1

    def _collect_unique_items(self):
        """收集 top / bottom 去重後的 item"""
        seen_top = set()
        seen_bottom = set()

        for _, row in self.df.iterrows():
            t = tuple(sorted(row["top"].items()))
            b = tuple(sorted(row["bottom"].items()))

            if t not in seen_top:
                seen_top.add(t)
                self.top_items.append(row["top"])

            if b not in seen_bottom:
                seen_bottom.add(b)
                self.bottom_items.append(row["bottom"])

    def _prob(self, matrix, from_value, to_value, vocab_set):
        """Laplace smoothing"""
        counter = matrix[from_value]
        total = sum(counter.values()) + len(vocab_set)
        count = counter.get(to_value, 0) + 1
        return count / total

    def score_item_to_item(self, A, B):
        """Naive Bayes：log probability"""
        p_color = self._prob(self.color_matrix, A["color"], B["color"], self.all_colors)
        p_style = self._prob(self.style_matrix, A["style"], B["style"], self.all_styles)
        p_cat = self._prob(self.cat_matrix, A["category"], B["category"], self.all_cats)

        return math.log(p_color) + math.log(p_style) + math.log(p_cat)

    def recommend(self, itemA, K=3):
        """選出 top 或 bottom 的推薦"""
        if itemA["part"].lower() == "top":
            candidates = self.bottom_items
            target_part = "Bottom"
        else:
            candidates = self.top_items
            target_part = "Top"

        scored = []
        for itemB in candidates:
            score = self.score_item_to_item(itemA, itemB)
            cpy = dict(itemB)
            cpy["part"] = target_part
            cpy["score_source"] = "naive_bayes"
            scored.append((score, cpy))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [b for _, b in scored[:K]]


# ------------------------------------------------------------
# Hybrid Recommender（共現 + Naive Bayes）
# ------------------------------------------------------------
class HybridRecommender:
    def __init__(self, df):
        self.df = df
        self.nb = OutfitRecommender(df)

        self.top2bottom = defaultdict(Counter)
        self.bottom2top = defaultdict(Counter)

        self._build_cooccurrence()

    def _item_key(self, item_dict):
        return (item_dict["color"], item_dict["style"], item_dict["category"])

    def _key_to_item(self, key):
        c, s, cat = key
        return {"color": c, "style": s, "category": cat}

    def _build_cooccurrence(self):
        for _, row in self.df.iterrows():
            tk = self._item_key(row["top"])
            bk = self._item_key(row["bottom"])

            self.top2bottom[tk][bk] += 1
            self.bottom2top[bk][tk] += 1

    def _cooccur(self, item, part):
        key = self._item_key(item)

        if part == "top":
            counter = self.top2bottom.get(key, Counter())
            target_part = "Bottom"
        else:
            counter = self.bottom2top.get(key, Counter())
            target_part = "Top"

        res = []
        for item_key, cnt in counter.most_common():
            rec = self._key_to_item(item_key)
            rec["part"] = target_part
            rec["score"] = cnt
            rec["score_source"] = "cooccurrence"
            res.append(rec)

        return res

    def recommend(self, item, K=3):
        part = item.get("part", "").lower()
        results = self._cooccur(item, part)

        # 不足 K → 用 Naive Bayes 補
        if len(results) < K:
            needed = K - len(results)
            nb_candidates = self.nb.recommend(item, K=K * 2)

            seen = {self._item_key(r) for r in results}

            for nb_item in nb_candidates:
                key = self._item_key(nb_item)
                if key not in seen:
                    results.append(nb_item)
                    seen.add(key)
                if len(results) >= K:
                    break

        return results[:K]


# ------------------------------------------------------------
# 圖片 URL 匹配邏輯（非常重要）
# ------------------------------------------------------------
def match_image_url(df: pd.DataFrame, item: dict, gender: str):
    """Backward-compatible wrapper that delegates to resolve_image_url."""
    return resolve_image_url(
        load_image_index(),
        gender=gender,
        color=item.get("color"),
        style=item.get("style"),
        category=item.get("category"),
    )


# ------------------------------------------------------------
# Gendered Recommender（最終版本）
# ------------------------------------------------------------
class GenderedRecommender:
    def __init__(self, df):
        self.df = df  # ⭐ 用於圖片搜尋
        self.models = {}
        self.image_db = load_image_index()

        for g in ["men", "women"]:
            sub = df[df["gender"].str.lower() == g]
            if not sub.empty:
                self.models[g] = HybridRecommender(sub)

    def recommend(self, item, gender, K=3):
        g = gender.lower()

        if g not in self.models:
            raise ValueError(f"無此性別模型：{gender}")

        raw_results = self.models[g].recommend(item, K=K)

        # ⭐ 加入圖片 URL
        enriched = []
        for rec in raw_results:
            rec = dict(rec)
            image_url = resolve_image_url(
                self.image_db,
                gender=gender,
                color=rec.get("color"),
                style=rec.get("style"),
                category=rec.get("category"),
            )
            rec["image_url"] = image_url
            rec["filename"] = image_url.rsplit("/", 1)[-1] if image_url else None
            enriched.append(rec)

        return enriched

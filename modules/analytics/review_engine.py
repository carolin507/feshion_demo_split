# modules/analytics/review_engine.py

import os
import pandas as pd
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import spacy
from tqdm import tqdm

# ==============================
# NLP 模型初始化
# ==============================

# VADER
try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon")

# spaCy — 只開 tokenizer + POS tagger（速度快 10 倍）
try:
    nlp = spacy.load("en_core_web_sm", disable=["parser", "ner", "lemmatizer"])
except:
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm", disable=["parser", "ner", "lemmatizer"])


class ReviewEngine:
    def __init__(self, data_path="data/raw/reviews/reviews.csv"):
        self.data_path = data_path
        self.df = pd.read_csv(self.data_path)
        self.clean_data()

    # --------------------------------------------
    # STEP 1：欄位清理
    # --------------------------------------------
    def clean_data(self):
        df = self.df.copy()

        df.rename(
            columns={
                "Review Text": "review",
                "Rating": "rating",
                "Recommended IND": "recommended",
                "Positive Feedback Count": "positive_feedback",
            },
            inplace=True,
        )

        df["review"] = df["review"].fillna("").astype(str)
        df["rating"] = df["rating"].fillna(0).astype(int)
        df["recommended"] = df["recommended"].fillna(0).astype(int)

        df["review_length"] = df["review"].str.len()

        self.df = df

    # --------------------------------------------
    # STEP 2：情緒分類（VADER + Rating 強化版本）
    # --------------------------------------------
    def add_sentiment(self):
        sia = SentimentIntensityAnalyzer()
        df = self.df.copy()

        df["sentiment_score_raw"] = df["review"].apply(
            lambda x: sia.polarity_scores(x)["compound"]
        )

        def classify(row):
            score = row["sentiment_score_raw"]
            rating = row["rating"]

            # ⭐ Rule 1：強烈高分 → 必定 Positive
            if rating >= 4:
                return "Positive"

            # ⭐ Rule 2：強烈低分 → 必定 Negative
            if rating <= 2:
                return "Negative"

            # ⭐ Rule 3：中間 3 星用 VADER 判斷語氣
            if score >= 0.2:
                return "Positive"
            elif score <= -0.2:
                return "Negative"
            else:
                return "Neutral"

        df["sentiment_label"] = df.apply(classify, axis=1)
        self.df = df

    # --------------------------------------------
    # STEP 3：形容詞（ADJ）關鍵字萃取 + 雙重限制
    # --------------------------------------------
    def extract_keywords(self, top_n_per_sentiment=50, min_review_length=8):
        df = self.df.copy()

        # 過濾掉沒有內容的評論
        df = df[df["review_length"] >= min_review_length]

        # 雙重限制（真正正向）
        pos_df = df[(df["sentiment_label"] == "Positive") & (df["rating"] >= 4)]

        # 雙重限制（真正負向）
        neg_df = df[(df["sentiment_label"] == "Negative") & (df["rating"] <= 2)]

        groups = {
            "Positive": pos_df,
            "Negative": neg_df
        }

        results = []

        for sentiment, subset_df in groups.items():
            subset = subset_df["review"]

            print(f"\n[萃取 {sentiment} 關鍵字] → 評論數量：{len(subset)}")

            all_adjs = []

            # tqdm progress bar
            for text in tqdm(subset, desc=f"Processing {sentiment}", ncols=90):
                doc = nlp(text.lower())

                # ⭐ 只抓形容詞（ADJ）— 真正情緒詞
                adjs = [token.lemma_ for token in doc if token.pos_ == "ADJ"]
                all_adjs.extend(adjs)

            # 若沒有 ADJ 則跳過
            if len(all_adjs) == 0:
                continue

            freq = pd.Series(all_adjs).value_counts().reset_index()
            freq.columns = ["word", "count"]
            freq["sentiment"] = sentiment

            results.append(freq.head(top_n_per_sentiment))

        if results:
            keywords = pd.concat(results, ignore_index=True)
        else:
            keywords = pd.DataFrame(columns=["word", "count", "sentiment"])

        self.keywords = keywords
        return keywords

    # --------------------------------------------
    # STEP 4：輸出處理後資料
    # --------------------------------------------
    def export_processed(self, out_dir="data/processed/reviews"):
        os.makedirs(out_dir, exist_ok=True)

        self.df.to_csv(os.path.join(out_dir, "reviews_processed.csv"), index=False)
        self.keywords.to_csv(os.path.join(out_dir, "review_keywords.csv"), index=False)

        print("\nReview processed files exported successfully!")

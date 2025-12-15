# modules/clip_inference.py

import torch
import clip
from PIL import Image


class CLIPInference:
    def __init__(self, device=None, model_name="ViT-B/32"):
        # 設定 device
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        # 載入 CLIP 模型與 preprocess（與 notebook 完全一致）
        self.model, self.preprocess = clip.load(model_name, device=self.device)

        # -------------------------------
        # Label groups
        # -------------------------------
        self.color_labels = ["Black", "Gray", "White", "Beige", "Orange",
                             "Pink", "Red", "Green", "Brown", "Blue", "Yellow", "Purple"]

        self.category_labels = [
            "sleeveless", "Top", "T-Shirt", "Shirt", "Cardigan", "Blazer",
            "Sweatshirt", "Vest", "Jacket", "Dress", "Coat",
            "Skirt", "Pants", "Jeans", "Jumpsuit"
        ]

        self.style_labels = ["Solid", "Striped", "Floral", "Plaid", "Spotted"]

        self.body_part_labels = ["upper body clothing", "lower body clothing"]

        # -------------------------------
        # Precompute text embeddings
        # -------------------------------
        self.color_text_feats = self._compute_text_features(self.color_labels)
        self.category_text_feats = self._compute_text_features(self.category_labels)
        self.style_text_feats = self._compute_text_features(self.style_labels)
        self.part_text_feats = self._compute_text_features(self.body_part_labels)

    # ---------------------------------------------------
    # 計算文字 features
    # ---------------------------------------------------
    def _compute_text_features(self, labels):
        prompts = [f"a photo of a {label} clothing" for label in labels]   # 與 notebook 一致
        tokens = clip.tokenize(prompts).to(self.device)
        with torch.no_grad():
            text_feats = self.model.encode_text(tokens)
        text_feats /= text_feats.norm(dim=-1, keepdim=True)
        return text_feats

    # ---------------------------------------------------
    # 1️⃣ 圖片 → CLIP Image embedding
    # ---------------------------------------------------
    def encode_image(self, img: Image.Image):
        img_tensor = self.preprocess(img).unsqueeze(0).to(self.device)
        with torch.no_grad():
            image_feat = self.model.encode_image(img_tensor)
        image_feat /= image_feat.norm(dim=-1, keepdim=True)
        return image_feat  # shape [1,512]

    # ---------------------------------------------------
    # 2️⃣ 計算 top-k label（與 notebook 同邏輯）
    # ---------------------------------------------------
    def top_k_labels(self, image_feat, text_feats, labels, k=1, threshold=0.20):
        sims = image_feat @ text_feats.T
        sims = sims[0]  # shape [L]

        topk_scores, topk_idx = torch.topk(sims, k)
        results = []

        for score, idx in zip(topk_scores, topk_idx):
            score_val = float(score.item())
            if score_val < threshold:
                results.append(("Unknown", score_val))
            else:
                results.append((labels[idx], score_val))

        return results

    # ---------------------------------------------------
    # 3️⃣ Notebook 的完整推論流程 → color / style / category / part
    # ---------------------------------------------------
    def classify_attributes(self, img: Image.Image):
        image_feat = self.encode_image(img)

        # color
        color_top3 = self.top_k_labels(image_feat, self.color_text_feats, self.color_labels, k=3)
        color = color_top3[0][0]

        # style
        style_top = self.top_k_labels(image_feat, self.style_text_feats, self.style_labels)
        style = style_top[0][0]

        # category
        category_top = self.top_k_labels(image_feat, self.category_text_feats, self.category_labels)
        category = category_top[0][0]

        # body part
        part_top = self.top_k_labels(image_feat, self.part_text_feats, self.body_part_labels)
        part_label = part_top[0][0]

        if part_label == "upper body clothing":
            part = "Top"
        elif part_label == "lower body clothing":
            part = "Bottom"
        else:
            part = "Unknown"

        return {
            "color": color,
            "style": style,
            "category": category,
            "part": part,
            "embedding": image_feat[0].cpu().numpy().tolist()  # ⭐ 重要：加入 embedding
        }

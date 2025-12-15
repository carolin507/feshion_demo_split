# modules/recommend.py

def recommend_bottom(color, category, gender):

    bottom_colors = {
        "Red": ["White","Black","Blue"],
        "White": ["Black","Blue","Khaki"],
        "Black": ["White","Beige","Denim"],
        "Blue": ["White","Beige","Black"],
        "Beige": ["Black","Denim","Brown"],
    }

    top_like = {"Top","T-Shirt","Shirt","Cardigan","Blazer","Sweatshirt","Vest","Jacket","Coat"}
    dress_like = {"Dress","Jumpsuit","Kimono_Yukata","Swimwear"}

    if category in top_like:
        cats = ["牛仔褲", "西裝褲", "裙裝"]
    elif category in dress_like:
        cats = ["外套", "配件", "鞋款"]
    else:
        cats = ["上衣", "鞋款"]

    return {
        "bottom_color": bottom_colors.get(color, ["Black"]),
        "bottom_category": cats
    }

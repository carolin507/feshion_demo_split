# modules/utils.py

color_labels = [
    "Black","Gray","White","Beige","Orange","Pink","Red","Green",
    "Brown","Blue","Yellow","Purple"
]

pattern_labels = ["Solid","Striped","Floral","Plaid","Spotted"]

category_labels = [
    "Top","T-Shirt","Shirt","Cardigan","Blazer","Sweatshirt","Vest","Jacket",
    "Dress","Coat","Skirt","Pants","Jeans","Jumpsuit","Kimono_Yukata","Swimwear","Stockings"
]

color_to_zh = {
    "Black": "黑色", "Gray": "灰色", "White": "白色", "Beige": "米色",
    "Orange": "橙色", "Pink": "粉色", "Red": "紅色", "Green": "綠色",
    "Brown": "棕色", "Blue": "藍色", "Yellow": "黃色", "Purple": "紫色",
}

pattern_to_zh = {
    "Solid": "純色", "Striped": "條紋", "Floral": "碎花",
    "Plaid": "格紋", "Spotted": "點點",
}

category_to_zh = {
    "Top": "上衣", "T-Shirt": "T恤", "Shirt": "襯衫", "Cardigan": "開襟衫",
    "Blazer": "西裝外套", "Sweatshirt": "大學T", "Vest": "背心", "Jacket": "夾克",
    "Dress": "連身裙", "Coat": "大衣", "Skirt": "裙裝", "Pants": "長褲",
    "Jeans": "牛仔褲", "Jumpsuit": "連身裝", "Kimono_Yukata": "和服/浴衣",
    "Swimwear": "泳裝", "Stockings": "襪子",
}

def zh_label(label, table):
    return table.get(label, label)

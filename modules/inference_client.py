from __future__ import annotations

from io import BytesIO
from typing import Dict

import requests
from PIL import Image

API_URL = "https://carolin96057-fashion-clip-inference.hf.space/analyze"


def analyze_image(image: Image.Image, api_url: str = API_URL) -> Dict[str, str]:
    """
    Send an image to the external inference API and return labels.
    """
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    files = {"file": ("image.png", buffer, "image/png")}
    resp = requests.post(api_url, files=files, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    return {
        "color": data.get("color"),
        "style": data.get("style"),
        "category": data.get("category"),
        "part": data.get("part"),
    }

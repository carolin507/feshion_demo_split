# test_inference_client.py
from PIL import Image
from modules.inference_client import analyze_image

img = Image.open("test.jpg")
result = analyze_image(img)
print(result)

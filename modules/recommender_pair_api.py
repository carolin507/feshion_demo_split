# modules/recommender_pair.py (Re-purposed as API Client)

import requests
import pandas as pd
from PIL import Image
import io

# The new 'recommender' is a client that calls our FastAPI backend.
class APIRecommender:
    """
    A client to interact with the backend recommender API.
    It sends an image and gender to the API and gets recommendations back.
    """
    def __init__(self, api_base_url="http://127.0.0.1:8000"):
        """
        Initializes the recommender with the API's base URL.

        Args:
            api_base_url (str): The base URL where the FastAPI service is running.
        """
        self.api_url = f"{api_base_url}/recommendations/"

    def recommend(self, img: Image.Image, gender: str, top_n: int = 5):
        """
        Gets recommendations by calling the backend API.

        Args:
            img (PIL.Image.Image): The user's uploaded image.
            gender (str): The desired gender for recommendations ('male' or 'female').
            top_n (int): The number of recommendations to fetch (this is handled by the API).

        Returns:
            pd.DataFrame: A DataFrame containing the recommendations, with columns
                          like 'image_url', 'category', 'color', etc. Returns an empty
                          DataFrame if an error occurs.
        """
        if not isinstance(img, Image.Image):
            print("Error: Input 'img' must be a PIL Image object.")
            return pd.DataFrame()

        print(f"Sending request to {self.api_url} for gender: {gender}")

        # Convert PIL Image to in-memory bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        # --- Prepare the request for the FastAPI endpoint ---
        # The endpoint expects a multipart/form-data with 'gender' and 'image'
        files = {'image': ('image.png', img_byte_arr, 'image/png')}
        data = {'gender': gender}

        try:
            # --- Send the request ---
            response = requests.post(self.api_url, files=files, data=data, timeout=60)

            # --- Handle the response ---
            if response.status_code == 200:
                print("Successfully received recommendations from API.")
                # The API returns a JSON object like: {"recommendations": [...]}
                api_result = response.json()
                recommendations = api_result.get("recommendations", [])

                # Convert the list of recommendation dicts to a DataFrame
                df = pd.DataFrame(recommendations)
                return df
            else:
                # If the API returned an error
                print(f"Error from API: Status {response.status_code}")
                try:
                    # Try to print the error message from the API's JSON response
                    print(f"API Error Details: {response.json()}")
                except Exception:
                    # If the response is not JSON
                    print(f"API Response: {response.text}")
                return pd.DataFrame()

        except requests.exceptions.RequestException as e:
            # If there's a network error (e.g., the API server is not running)
            print(f"Failed to connect to the API server at {self.api_url}.")
            print(f"Error details: {e}")
            return pd.DataFrame()

# Note: The original GenderedRecommender, HybridRecommender, and other
# co-occurrence logic have been removed. That logic now lives in the
# backend service defined in `api.py`. This file is now just a client.

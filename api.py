import uvicorn
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
import io
from PIL import Image
import pandas as pd
import json

# Assuming recommender_pair is in the modules directory
# and the script is run from the project root
from modules.recommender_pair import GenderedRecommender

# --- App & Model Initialization ---

app = FastAPI(
    title="Lookbook Recommender API",
    description="An API to get clothing recommendations based on an uploaded image.",
    version="0.1.0",
)

# Global variable to hold the recommender instance
recommender = None

@app.on_event("startup")
def load_model():
    """
    Load the GenderedRecommender model at application startup.
    This is more efficient than loading it for each request.
    """
    global recommender
    print("Loading model...")
    try:
        # Load the base dataset for the recommender
        json_path = "data/verified_photo_data.json"
        with open(json_path, "r", encoding="utf-8") as f:
            items = json.load(f)
        df = pd.DataFrame(items)
        recommender = GenderedRecommender(df)
        print("Model loaded successfully!")
    except Exception as e:
        print(f"Error loading model: {e}")
        # In a real-world scenario, you might want the app to fail
        # if the model can't be loaded.
        recommender = None

# --- API Endpoints ---

@app.get("/")
def read_root():
    """
    A welcome endpoint for the API.
    """
    return {"message": "Welcome to the Lookbook Recommender API"}

@app.post("/recommendations/")
async def get_recommendations(
    gender: str = Form(...),
    image: UploadFile = File(...)
):
    """
    Receives an image and a gender, and returns clothing recommendations.

    - **gender**: The gender to recommend for ('male' or 'female').
    - **image**: The uploaded image file.
    """
    if recommender is None:
        return JSONResponse(
            status_code=503,
            content={"error": "Model is not available. Please try again later."}
        )

    # Read image contents
    try:
        contents = await image.read()
        pil_image = Image.open(io.BytesIO(contents))
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid image file."}
        )

    # Get recommendations from the model
    try:
        recommendations = recommender.recommend(
            img=pil_image,
            gender=gender,
            top_n=5,
        )

        # Convert recommendations to a JSON-serializable format if they are not already
        if isinstance(recommendations, pd.DataFrame):
            result = recommendations.to_dict(orient="records")
        else:
            result = recommendations

        return JSONResponse(status_code=200, content={"recommendations": result})

    except Exception as e:
        # Catch potential errors during the recommendation process
        return JSONResponse(
            status_code=500,
            content={"error": f"An unexpected error occurred: {str(e)}"}
        )

# --- Main execution block ---

if __name__ == "__main__":
    """
    Run the FastAPI app locally using Uvicorn.
    Usage: python api.py
    """
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

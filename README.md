# Fashion Demo (Streamlit UI Only)

This repository now contains the Streamlit frontend only. All AI inference runs on an external Hugging Face Spaces FastAPI service.

## Inference API
- Endpoint: POST /analyze
- Response JSON keys: color, style, category, part
- Configure the API URL in `modules/inference_client.py` (`API_URL`).

## Run locally

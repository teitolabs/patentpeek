# /backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import models
import services

app = FastAPI()

# --- CORS Middleware ---
# Allows your frontend (e.g., running on localhost:3000) to talk to the backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, change this to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints ---

@app.post("/api/generate-query", response_model=models.GenerateResponse)
async def handle_generate_query(request: models.GenerateRequest):
    """
    Receives structured data from the frontend and generates a query string and URL.
    This single endpoint handles both 'google' and 'uspto' formats.
    """
    try:
        return services.generate_query(request)
    except HTTPException as e:
        raise e  # Re-raise known HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.post("/api/parse-query", response_model=models.ParseResponse)
async def handle_parse_query(request: models.ParseRequest):
    """
    Receives a raw query string and deconstructs it into a structured
    representation for the frontend UI.
    """
    try:
        return services.parse_query(request)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.post("/api/convert-query", response_model=models.ConvertResponse)
async def handle_convert_query(request: models.ConvertRequest):
    """
    Converts a query string from a source format to a target format.
    """
    try:
        return services.convert_query_service(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error during conversion: {e}")

# To run the app:
# uvicorn main:app --reload
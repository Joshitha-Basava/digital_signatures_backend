from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from routes.auth_routes import router as auth_router
from routes.document_routes import router as document_router
from routes.qr_routes import router as qr_router
from config import HOST, PORT, db, initialize_firebase  # Import Firebase init
import requests
from fastapi.responses import Response

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow frontend requests
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# ✅ Initialize Firebase at Startup
@app.on_event("startup")
async def startup_db_client():
    try:
        await db.command("ping")  # Test MongoDB connection
        print("✅ MongoDB Connected Successfully!")
    except Exception as e:
        print(f"❌ MongoDB Connection Failed: {e}")

    # ✅ Initialize Firebase
    initialize_firebase()

@app.get("/fetch_qr")
async def fetch_qr(qr_url: str):
    """
    Fetch QR code image from Firebase Storage and serve it as a response.
    """
    try:
        response = requests.get(qr_url, stream=True)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch QR code image")

        return Response(content=response.content, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching QR code: {str(e)}")
    
app.include_router(auth_router, prefix="/api/auth")
app.include_router(document_router, prefix="/api/document")
app.include_router(qr_router, prefix="/api/qr")

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, reload=True)

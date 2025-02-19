import os
import json
import firebase_admin
from firebase_admin import credentials, storage
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI")

# ✅ Initialize MongoDB
client = AsyncIOMotorClient(MONGO_URI)
db = client.qr_authentication

# ✅ Firebase Initialization Function
def initialize_firebase():
    global bucket  # Ensure bucket is accessible globally
    try:
        FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")
        if not FIREBASE_CREDENTIALS:
            raise ValueError("❌ Firebase credentials missing!")

        # ✅ Parse JSON directly instead of writing to a file
        cred_data = json.loads(FIREBASE_CREDENTIALS)
        cred = credentials.Certificate(cred_data)

        if not firebase_admin._apps:  # ✅ Prevent multiple initializations
            firebase_admin.initialize_app(cred, {
                "storageBucket": os.getenv("FIREBASE_BUCKET")
            })

        bucket = storage.bucket()
        print("✅ Firebase Initialized Successfully!")
    except Exception as e:
        print(f"❌ Firebase Initialization Failed: {e}")
        bucket = None

# ✅ Upload function for Firebase Storage
def upload_to_firebase(file_path, destination_blob_name):
    """Uploads a file to Firebase Storage and returns the URL."""
    try:
        if not bucket:
            raise RuntimeError("Firebase is not initialized!")

        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(file_path)
        blob.make_public()
        return blob.public_url
    except Exception as e:
        print(f"❌ Firebase Upload Failed: {e}")
        return None

# JWT Secret Key
SECRET_KEY = os.getenv("JWT_SECRET")

# Server Config
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))

# JWT Expiry Time
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", 1))

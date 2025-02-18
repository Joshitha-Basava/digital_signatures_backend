import jwt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer

# Load environment variables
load_dotenv()

# Retrieve secret key and expiry time from environment variables
SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET is missing from environment variables!")

JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", 1))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_jwt(user_id: str) -> str:
    """
    Generates a JWT token for the given user ID.
    """
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_jwt(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Decodes and verifies the JWT token.
    """
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded_token
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

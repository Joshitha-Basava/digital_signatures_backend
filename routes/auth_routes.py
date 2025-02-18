from fastapi import APIRouter, HTTPException, Depends
from auth import create_jwt
from models.user import UserModel, LoginModel
from config import db
import bcrypt

router = APIRouter()

@router.post("/register")
async def register(user: UserModel):
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
    new_user = {
        "name": user.name,
        "email": user.email,
        "password": hashed_password,  # Ensure correct hashing
        "role": user.role  # Default: "user"
    }
    await db.users.insert_one(new_user)
    return {"message": "User registered successfully"}

@router.post("/login")
async def login(user: LoginModel):
    existing_user = await db.users.find_one({"email": user.email})
    if not existing_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Ensure stored password is bytes
    stored_password = existing_user["password"]
    if isinstance(stored_password, str): 
        stored_password = stored_password.encode("utf-8")

    if not bcrypt.checkpw(user.password.encode(), stored_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_jwt(str(existing_user["_id"]))  # Generate JWT token
    return {"token": token, "role": existing_user["role"], "user_id": str(existing_user["_id"])}
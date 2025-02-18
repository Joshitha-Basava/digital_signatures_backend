from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId
from datetime import datetime
from typing import Optional

class PyObjectId(ObjectId):
    """Custom class for handling MongoDB ObjectId serialization"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)

class UserModel(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "user"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserDB(UserModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    class Config:
        orm_mode = True
        json_encoders = {ObjectId: str}

class LoginModel(BaseModel):
    email: EmailStr
    password: str

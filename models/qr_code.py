from pydantic import BaseModel, Field
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

class QRCodeModel(BaseModel):
    document_id: str
    qr_code_url: str
    hash_value: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class QRCodeDB(QRCodeModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")  # ✅ Fix: Auto-generate _id

    class Config:
        orm_mode = True
        json_encoders = {ObjectId: str}

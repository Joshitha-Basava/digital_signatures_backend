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

class VerificationLogModel(BaseModel):
    qr_id: str  # Reference to QR Code ID
    verified_by: str  # User who verified the document
    timestamp: datetime = Field(default_factory=datetime.utcnow)  # Auto timestamp
    status: str  # Verification status (e.g., "Success", "Failed")

class VerificationLogDB(VerificationLogModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    class Config:
        orm_mode = True
        json_encoders = {ObjectId: str}

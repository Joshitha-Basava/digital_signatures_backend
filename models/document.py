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

class DocumentModel(BaseModel):
    user_id: str
    document_name: str
    document_type: str
    file_url: str
    digital_signature: str
    public_key_id: str
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DocumentDB(DocumentModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    class Config:
        orm_mode = True
        json_encoders = {ObjectId: str}

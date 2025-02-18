from pydantic import BaseModel
from datetime import datetime

class PublicKeyModel(BaseModel):
    key_id: str  # Unique key ID
    user_id: str  # Link public key to user
    public_key: str  # Store the actual public key in PEM format
    expiry_date: datetime  # Expiry date for validation

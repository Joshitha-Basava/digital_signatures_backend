import rsa
from cryptography.hazmat.primitives import serialization
from datetime import datetime
from bson import ObjectId
from models.public_keys import PublicKeyModel
from config import db  # MongoDB instance

async def get_or_create_keys(user_id):
    """Fetch existing public key or generate a new one if it doesn't exist."""
    
    user_key = await db.public_keys.find_one({"user_id": user_id})
    
    if user_key:
        print("Using existing public key.")
        return None, user_key["public_key"], user_key["key_id"]

    print("Generating new RSA key pair...")
    
    # Generate RSA key pair
    private_key = rsa.newkeys(2048)
    public_key = private_key[1]

    # Serialize public key
    public_pem = public_key.save_pkcs1().decode("utf-8")

    # Define expiry (e.g., 1 year from now)
    expiry_date = datetime.utcnow().replace(year=datetime.utcnow().year + 1)

    # Store public key in MongoDB
    key_entry = PublicKeyModel(
        key_id=str(ObjectId()),  # Generate unique key ID
        user_id=user_id,
        public_key=public_pem,
        expiry_date=expiry_date
    )

    await db.public_keys.insert_one(key_entry.dict(by_alias=True))

    return private_key, public_pem, key_entry.key_id

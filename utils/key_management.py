from ecdsa import SigningKey, NIST256p
from cryptography.hazmat.primitives import serialization
from datetime import datetime
from bson import ObjectId
from models.public_keys import PublicKeyModel
from config import db  # MongoDB instance
from datetime import datetime, timedelta



async def get_or_create_keys(user_id):
    """Fetch existing public key or generate a new one if it doesn't exist."""

    user_key = await db.public_keys.find_one({"user_id": user_id})

    if user_key:
        expiry_date = user_key.get("expiry_date")

        # Convert expiry_date to datetime if it's a string (MongoDB may store it as string)
        if isinstance(expiry_date, str):
            expiry_date = datetime.fromisoformat(expiry_date)

        # Check if the existing key is still valid
        if expiry_date and expiry_date > datetime.utcnow():
            print("Using existing public key.")
            return None, user_key["public_key"], user_key["key_id"]

        print("Existing key expired. Generating a new one...")

        # Delete the expired key
        await db.public_keys.delete_one({"user_id": user_id})

    print("Generating new ECDSA key pair...")

    # Generate ECDSA key pair
    private_key = SigningKey.generate(curve=NIST256p)
    public_key = private_key.verifying_key

    # Serialize public key to PEM format
    public_pem = public_key.to_pem().decode("utf-8")

    # Define expiry (e.g., 1 year from now)
    expiry_date = datetime.utcnow().replace(year=datetime.utcnow().year + 1)

    # Define expiry (5 minutes from now)
    # expiry_date = datetime.utcnow() + timedelta(minutes=5)

    # Store public key in MongoDB
    key_entry = PublicKeyModel(
        key_id=str(ObjectId()),  # Generate unique key ID
        user_id=user_id,
        public_key=public_pem,
        expiry_date=expiry_date
    )

    await db.public_keys.insert_one(key_entry.dict(by_alias=True))

    return private_key, public_pem, key_entry.key_id

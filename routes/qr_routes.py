from fastapi import APIRouter, HTTPException, Depends
from config import db
from auth import verify_jwt
from datetime import datetime
from bson import ObjectId

router = APIRouter()

@router.get("/verify/{hash_value}")
async def verify_qr_code(hash_value: str, user: dict = Depends(verify_jwt)):
    hash_value = hash_value.strip()  # Remove leading/trailing spaces
    print(f"🔍 Incoming hash_value: '{hash_value}'")

    # Fetch all hash values for debugging
    all_hashes = await db.qr_codes.find({}, {"hash_value": 1}).to_list(None)
    stored_hashes = [doc["hash_value"] for doc in all_hashes if "hash_value" in doc]

    print(f"📜 Stored hash values in DB: {stored_hashes}")

    # Direct check
    qr_code = await db.qr_codes.find_one({"hash_value": hash_value})
    
    if qr_code:
        print("✅ Exact match found!")
    else:
        print("❌ Exact match NOT found! Trying regex fallback...")
        qr_code = await db.qr_codes.find_one({"hash_value": {"$regex": f"^{hash_value}$"}})

    if not qr_code:
        print(f"❌ Final check: Hash '{hash_value}' still not found!")
        raise HTTPException(status_code=404, detail="QR Code not found")

    print(f"🔍 QR Code found: {qr_code}")
    
    doc_metadata = await db.documents.find_one({"_id": ObjectId(qr_code["document_id"])})

    if not doc_metadata:
        raise HTTPException(status_code=404, detail="Document metadata missing")

    public_key_id = doc_metadata["public_key_id"]
    public_key_entry = await db.public_keys.find_one({"key_id": public_key_id})

    if not public_key_entry:
        raise HTTPException(status_code=400, detail="Public key not found")

    # Check if the public key has expired
    if public_key_entry["expiry_date"] < datetime.utcnow():
        raise HTTPException(status_code=403, detail="Public key has expired. Access denied.")
    
    await db.documents.update_one({"_id": ObjectId(qr_code["document_id"])}, {"$set": {"is_verified": True}})

    return {
        "status": "Verified",
        "document_name": doc_metadata["document_name"],
        "document_id": qr_code["document_id"],
        "file_url": doc_metadata["file_url"]
    }

@router.get("/{document_id}")
async def get_qr_code(document_id: str):
    qr_code = await db.qrcodes.find_one({"document_id": document_id})
    
    if not qr_code:
        raise HTTPException(status_code=404, detail="QR Code not found")
    
    return {"qr_code_url": qr_code["qr_code_url"], "hash_value": qr_code["hash_value"]}


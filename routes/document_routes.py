import qrcode
import hashlib
import shutil
import os
from datetime import datetime
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Form
from config import db, upload_to_firebase
from auth import verify_jwt
from models.qr_code import QRCodeDB
from utils.key_management import get_or_create_keys 
from fastapi.encoders import jsonable_encoder
from bson import ObjectId

router = APIRouter()

ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "docx"}

def is_allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@router.post("/upload")
async def upload_document(
    document_name: str = Form(...), 
    document_type: str = Form(...), 
    file: UploadFile = File(...), 
    token: dict = Depends(verify_jwt)
):
    print("Upload request received.")
    
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    print(f"User authenticated: {token['user_id']}")

    if not is_allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type")

    # Ensure temp directory exists
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)

    file_path = os.path.join(temp_dir, file.filename)  # Temporary storage before uploading to Firebase
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ✅ Upload to Firebase Storage
    firebase_url = upload_to_firebase(file_path, f"documents/{file.filename}")
    if not firebase_url:
        raise HTTPException(status_code=500, detail="Failed to upload to Firebase")
    
    private_key, public_key, key_id = await get_or_create_keys(token["user_id"])

    # ✅ Compute Digital Signature
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    digital_signature = hasher.hexdigest()

    # ✅ Generate QR Code for the Digital Signature
    qr_code_path = os.path.join(temp_dir, f"{file.filename}.png")
    qr = qrcode.make(digital_signature)
    qr.save(qr_code_path)

    # ✅ Upload QR Code to Firebase
    qr_code_url = upload_to_firebase(qr_code_path, f"qr_codes/{file.filename}.png")
    if not qr_code_url:
        raise HTTPException(status_code=500, detail="Failed to upload QR code to Firebase")

    print("✅ Document uploaded successfully.",key_id)

    # ✅ Save Document in MongoDB
    document = {
        "user_id": token["user_id"],
        "document_name": document_name,
        "document_type": document_type,
        "file_url": firebase_url,
        "digital_signature": digital_signature,
        "public_key_id": key_id,
        "created_at": datetime.utcnow(),
        "is_verified": False,
    }
    result = await db.documents.insert_one(document)
    document_id = str(result.inserted_id)

    qr_code_entry = QRCodeDB(
        document_id=document_id,
        qr_code_url=qr_code_url,
        hash_value=digital_signature,
        created_at=datetime.utcnow()
    )
    await db.qr_codes.insert_one(qr_code_entry.dict(by_alias=True))

    return {
        "file_url": firebase_url,
        "digital_signature": digital_signature,
        "qr_code_url": qr_code_url
    }


@router.get("/documents")
async def get_documents(token: dict = Depends(verify_jwt)):
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    documents = await db.documents.find({"user_id": token["user_id"]}).to_list(None)
    document_ids = [str(doc["_id"]) for doc in documents]
    qr_codes = await db.qr_codes.find({"document_id": {"$in": document_ids}}).to_list(None)
    
    for doc in documents:
        doc_id = str(doc["_id"])
        qr_code = next((qr for qr in qr_codes if qr["document_id"] == doc_id), None)
        if qr_code:
            doc["qr_code_url"] = qr_code["qr_code_url"]
        
        doc["_id"] = str(doc["_id"])

    return jsonable_encoder(documents)

#document delete api
@router.delete("/delete/{document_id}")
async def delete_document(document_id: str, token: dict = Depends(verify_jwt)):
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    document = await db.documents.find_one({"_id": ObjectId(document_id)})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document["user_id"] != token["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    await db.documents.delete_one({"_id": ObjectId(document_id)})
    await db.qr_codes.delete_one({"document_id": document_id})

    return {"status": "Document deleted successfully"}

@router.get("/public_key")
async def get_public_key(token: dict = Depends(verify_jwt)):
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    print(f"User authenticated: {token['user_id']}")

    public_key = await db.public_keys.find_one({"user_id": token["user_id"]})
    if not public_key:
        raise HTTPException(status_code=404, detail="Public key not found")

    # Convert ObjectId fields to string
    public_key["_id"] = str(public_key["_id"])  # Convert MongoDB ObjectId to string
    if "key_id" in public_key and isinstance(public_key["key_id"], ObjectId):
        public_key["key_id"] = str(public_key["key_id"])

    return jsonable_encoder(public_key)

#write api to reset the public key of the user
@router.post("/reset_public_key")
async def reset_public_key(token: dict = Depends(verify_jwt)):
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    private_key, public_key, key_id = await get_or_create_keys(token["user_id"])

    return {"status": "Public key reset successfully", "public_key": public_key, "key_id": key_id}
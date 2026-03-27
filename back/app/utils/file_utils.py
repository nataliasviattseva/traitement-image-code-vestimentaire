# utils/file_utils.py

import os
from fastapi import UploadFile, HTTPException
from uuid import uuid4

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "mp4", "mov"}

# Validate file type and content-type
def validate_upload(file: UploadFile) -> str:
    filename = file.filename.lower()
    ext = filename.split(".")[-1]

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    return ext

# Save file to disk and return metadata
async def persist_upload(file: UploadFile, ext: str) -> dict:
    filename = f"{uuid4()}.{ext}"
    path = os.path.join(UPLOAD_DIR, filename)

    with open(path, "wb") as buffer:
        buffer.write(await file.read())

    return {
        "filename": filename,
        "path": path,
        "url": f"/static/{filename}",  # if you serve uploads via /static route
    }

def extract_public_id(url: str) -> str:
    """
    Extract the public_id from a Cloudinary URL.
    Eg :
    https://res.cloudinary.com/.../upload/v12345/folder/image.jpg
    -> folder/image
    """
    # get the last part of the URL in the file
    filename = url.split("/")[-1]

    # get the part just before (the folder or the public_id)
    folder = url.split("/")[-2]

    # get the part just before (the folder or the public_id)
    public_id = f"{folder}/{filename.split('.')[0]}"

    return public_id
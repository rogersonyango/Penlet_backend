# app/utils/file_upload.py
import os
import uuid
from fastapi import UploadFile
from pathlib import Path

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def save_upload_file(upload_file: UploadFile) -> str:
    """
    Saves an uploaded file to the 'uploads/' directory and returns the relative file path.
    Filename is randomized to avoid collisions.
    """
    file_extension = Path(upload_file.filename).suffix
    safe_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = UPLOAD_DIR / safe_filename

    with file_path.open("wb") as buffer:
        buffer.write(upload_file.file.read())

    # Return relative path as string (e.g., "uploads/abc123.pdf")
    return str(file_path)
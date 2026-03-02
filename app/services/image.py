import os
import json
import asyncio
from typing import List, Optional
from PIL import Image
from fastapi import UploadFile, BackgroundTasks
from app.core.config import settings


class ImageService:
    def __init__(self):
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    def compress_image(self, input_path: str, output_path: str) -> str:
        """Compress image and save to output path."""
        with Image.open(input_path) as img:
            # Convert to RGB if necessary
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Resize if width > max
            if img.width > settings.COMPRESSED_MAX_WIDTH:
                ratio = settings.COMPRESSED_MAX_WIDTH / img.width
                new_height = int(img.height * ratio)
                img = img.resize((settings.COMPRESSED_MAX_WIDTH, new_height), Image.Resampling.LANCZOS)
            
            # Save with compression
            img.save(output_path, "JPEG", quality=settings.COMPRESSED_QUALITY, optimize=True)
        
        return output_path

    async def save_upload(self, file: UploadFile, user_id: int) -> str:
        """Save uploaded file with compression."""
        # Read file
        content = await file.read()
        
        # Generate filename
        ext = file.filename.split(".")[-1].lower() if "." in file.filename else "jpg"
        if ext not in settings.ALLOWED_EXTENSIONS:
            ext = "jpg"
        
        filename = f"{user_id}_{int(asyncio.get_event_loop().time() * 1000)}.{ext}"
        temp_path = os.path.join(settings.UPLOAD_DIR, f"temp_{filename}")
        final_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        # Write temp file
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # Compress
        self.compress_image(temp_path, final_path)
        
        # Remove temp
        os.remove(temp_path)
        
        return filename

    async def save_uploads(self, files: List[UploadFile], user_id: int) -> List[str]:
        """Save multiple uploaded files."""
        filenames = []
        for file in files:
            if file.filename:
                filename = await self.save_upload(file, user_id)
                filenames.append(filename)
        return filenames

    def delete_image(self, filename: str) -> bool:
        """Delete image file."""
        path = os.path.join(settings.UPLOAD_DIR, filename)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def get_image_url(self, filename: str) -> str:
        """Get full URL for image."""
        return f"/uploads/{filename}"


image_service = ImageService()

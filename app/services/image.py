import os
import json
import asyncio
from typing import List
from PIL import Image
from app.core.config import settings
from app.services.storage import storage


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

    def create_thumbnail(self, input_path: str, output_path: str, size: tuple = (200, 200)) -> str:
        """Create thumbnail for image."""
        with Image.open(input_path) as img:
            # Create thumbnail (maintain aspect ratio)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(output_path, "JPEG", quality=70, optimize=True)
        
        return output_path

    async def save_upload(self, file, user_id: int) -> str:
        """Save uploaded file with compression and thumbnail."""
        # Read file
        content = await file.read()
        
        # Generate filename
        ext = file.filename.split(".")[-1].lower() if "." in file.filename else "jpg"
        if ext not in settings.ALLOWED_EXTENSIONS:
            ext = "jpg"
        
        filename = f"{user_id}_{int(asyncio.get_event_loop().time() * 1000)}.{ext}"
        
        # Save to storage (S3 or local)
        url = await storage.upload_file(content, filename)
        
        # For local storage, also compress
        if not storage.use_s3:
            temp_path = os.path.join(settings.UPLOAD_DIR, f"temp_{filename}")
            final_path = os.path.join(settings.UPLOAD_DIR, filename)
            
            # Write temp file
            with open(temp_path, "wb") as f:
                f.write(content)
            
            # Compress
            self.compress_image(temp_path, final_path)
            os.remove(temp_path)
            
            # Create thumbnail
            thumb_path = os.path.join(settings.UPLOAD_DIR, f"thumb_{filename}")
            self.create_thumbnail(final_path, thumb_path)
        
        return filename

    async def save_uploads(self, files: List, user_id: int) -> List[str]:
        """Save multiple uploaded files."""
        filenames = []
        for file in files:
            if file.filename:
                filename = await self.save_upload(file, user_id)
                filenames.append(filename)
        return filenames

    def delete_image(self, filename: str) -> bool:
        """Delete image file."""
        return storage.delete_file(filename)

    def get_image_url(self, filename: str) -> str:
        """Get full URL for image."""
        if storage.use_s3:
            return f"{storage.public_url}/uploads/{filename}"
        return f"/uploads/{filename}"
    
    def get_thumbnail_url(self, filename: str) -> str:
        """Get thumbnail URL for image."""
        if storage.use_s3:
            return f"{storage.public_url}/uploads/thumb_{filename}"
        return f"/uploads/thumb_{filename}"


image_service = ImageService()
